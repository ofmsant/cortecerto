"""Robustez, segurança HTTP e comportamento em situações de borda."""
from datetime import date, time
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from agenda.models import Agendamento, StatusAgendamento, TipoCorte
from agenda.views import _vizinho

from .auxiliares import DIA, SENHA, BaseAgenda, criar, dados, url_agenda


def horario_do_indice(indice):
    """Horários de 15 em 15 minutos a partir das 08:00, sem sobreposição."""
    minutos = 8 * 60 + indice * 15
    return time(minutos // 60, minutos % 60)


class SaidaEscapadaTests(BaseAgenda):
    NOME_COM_HTML = "<script>alert(1)</script>"
    NOME_ESCAPADO = "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_agenda_escapa_html_do_nome(self):
        criar(nome=self.NOME_COM_HTML)
        resposta = self.client.get(url_agenda())
        self.assertNotContains(resposta, self.NOME_COM_HTML)
        self.assertContains(resposta, self.NOME_ESCAPADO)

    def test_historico_escapa_html_do_nome(self):
        criar(nome=self.NOME_COM_HTML, status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.get(reverse("agenda:historico"))
        self.assertNotContains(resposta, self.NOME_COM_HTML)
        self.assertContains(resposta, self.NOME_ESCAPADO)

    def test_confirmacao_de_cancelamento_escapa_html_do_nome(self):
        agendamento = criar(nome=self.NOME_COM_HTML)
        resposta = self.client.get(reverse("agenda:cancelar", args=[agendamento.pk]))
        self.assertNotContains(resposta, self.NOME_COM_HTML)
        self.assertContains(resposta, self.NOME_ESCAPADO)

    def test_mensagem_de_confirmacao_escapa_html_do_nome(self):
        resposta = self.client.post(
            url_agenda(), dados(nome_cliente="<b>x</b>"), follow=True
        )
        self.assertNotContains(resposta, "<b>x</b>")
        self.assertContains(resposta, "&lt;b&gt;x&lt;/b&gt;")

    def test_aspas_no_nome_nao_escapam_do_atributo_html(self):
        criar(nome='" onmouseover="alert(1)')
        resposta = self.client.get(url_agenda())
        self.assertNotContains(resposta, '" onmouseover="alert(1)')
        self.assertContains(resposta, "&quot; onmouseover=&quot;alert(1)")


class MetodosHttpTests(BaseAgenda):
    def test_agenda_so_aceita_get_head_e_post(self):
        for metodo in ("put", "patch", "delete"):
            with self.subTest(metodo=metodo):
                resposta = getattr(self.client, metodo)(url_agenda())
                self.assertEqual(resposta.status_code, 405)

    def test_concluir_so_aceita_post(self):
        agendamento = criar()
        url = reverse("agenda:concluir", args=[agendamento.pk])
        for metodo in ("get", "put", "patch", "delete"):
            with self.subTest(metodo=metodo):
                resposta = getattr(self.client, metodo)(url)
                self.assertEqual(resposta.status_code, 405)
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_cancelar_nao_aceita_put_patch_nem_delete(self):
        agendamento = criar()
        url = reverse("agenda:cancelar", args=[agendamento.pk])
        for metodo in ("put", "patch", "delete"):
            with self.subTest(metodo=metodo):
                resposta = getattr(self.client, metodo)(url)
                self.assertEqual(resposta.status_code, 405)
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_historico_so_aceita_leitura(self):
        url = reverse("agenda:historico")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.head(url).status_code, 200)
        for metodo in ("post", "put", "patch", "delete"):
            with self.subTest(metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(url).status_code, 405)

    def test_nao_existe_rota_de_exclusao_de_agendamento(self):
        agendamento = criar()
        with self.assertRaises(NoReverseMatch):
            reverse("agenda:excluir", args=[agendamento.pk])
        caminhos = [
            f"/agendamentos/{agendamento.pk}/",
            f"/agendamentos/{agendamento.pk}/excluir/",
            f"/agendamentos/{agendamento.pk}/apagar/",
        ]
        for caminho in caminhos:
            with self.subTest(caminho=caminho):
                self.assertEqual(self.client.delete(caminho).status_code, 404)
                self.assertEqual(self.client.post(caminho).status_code, 404)
        self.assertEqual(Agendamento.objects.count(), 1)


class DatasEParametrosTests(BaseAgenda):
    def test_ultimo_dia_do_calendario_nao_quebra_e_nao_oferece_proximo_dia(self):
        resposta = self.client.get(f"{reverse('agenda:inicio')}?data=9999-12-31")
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Próximo dia")
        self.assertContains(resposta, "Dia anterior")

    def test_vizinho_devolve_none_nos_limites_do_calendario(self):
        self.assertIsNone(_vizinho(date.min, -1))
        self.assertIsNone(_vizinho(date.max, 1))
        self.assertEqual(_vizinho(DIA, 1), date(2026, 11, 15))
        self.assertEqual(_vizinho(DIA, -1), date(2026, 11, 13))

    def test_datas_invalidas_voltam_para_hoje_com_aviso(self):
        for texto in ["abc", "2026-13-45", "2026-02-31", "14/11/2026"]:
            with self.subTest(texto=texto):
                resposta = self.client.get(f"{reverse('agenda:inicio')}?data={texto}")
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.context["dia"], timezone.localdate())
                self.assertContains(resposta, "Data inválida")

    def test_data_em_branco_mostra_hoje_sem_aviso(self):
        resposta = self.client.get(f"{reverse('agenda:inicio')}?data=")
        self.assertEqual(resposta.context["dia"], timezone.localdate())
        self.assertNotContains(resposta, "Data inválida")

    def test_horarios_invalidos_no_link_sao_ignorados(self):
        for texto in ["25:99", "meio-dia", "9"]:
            with self.subTest(texto=texto):
                resposta = self.client.get(url_agenda() + f"&horario={texto}")
                self.assertEqual(resposta.status_code, 200)

    def test_mensagem_de_sucesso_aparece_somente_uma_vez(self):
        primeira = self.client.post(url_agenda(), dados(), follow=True)
        self.assertContains(primeira, "registrado para")
        segunda = self.client.get(url_agenda())
        self.assertNotContains(segunda, "registrado para")


class FalhasNaGravacaoTests(BaseAgenda):
    def test_erro_de_integridade_mostra_mensagem_e_nao_quebra(self):
        with mock.patch("agenda.views.AgendamentoForm.save", side_effect=IntegrityError):
            resposta = self.client.post(url_agenda(), dados())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "acabou de ser ocupado")
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_erro_de_validacao_na_gravacao_aparece_no_campo(self):
        erro = ValidationError({"horario": "Horário conflitante simulado."})
        with mock.patch("agenda.views.AgendamentoForm.save", side_effect=erro):
            resposta = self.client.post(url_agenda(), dados())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Horário conflitante simulado.")
        self.assertIn("horario", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)


class AdminSemExclusaoTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_admin_nao_permite_excluir_agendamento(self):
        superusuario = get_user_model().objects.create_superuser(
            username="admin_teste", password=SENHA
        )
        self.client.force_login(superusuario)
        agendamento = criar()

        url = reverse("admin:agenda_agendamento_delete", args=[agendamento.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)

        self.client.post(
            reverse("admin:agenda_agendamento_changelist"),
            {"action": "delete_selected", "_selected_action": [agendamento.pk]},
        )
        self.assertEqual(Agendamento.objects.count(), 1)


class QuantidadeDeConsultasTests(BaseAgenda):
    def contar_consultas(self, url):
        with CaptureQueriesContext(connection) as capturadas:
            resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        return len(capturadas)

    @override_settings(PERIODOS_ATENDIMENTO="08:00-18:00")
    def test_agenda_nao_faz_uma_consulta_por_agendamento(self):
        criar(nome="Cliente 0", horario=horario_do_indice(0), duracao=10)
        url = url_agenda()
        antes = self.contar_consultas(url)
        for i in range(1, 30):
            criar(nome=f"Cliente {i}", horario=horario_do_indice(i), duracao=10)
        depois = self.contar_consultas(url)
        self.assertEqual(antes, depois)

    def test_historico_nao_faz_uma_consulta_por_registro(self):
        criar(
            nome="Cliente 0", horario=horario_do_indice(0), duracao=10,
            status=StatusAgendamento.CONCLUIDO,
        )
        url = reverse("agenda:historico")
        antes = self.contar_consultas(url)
        for i in range(1, 30):
            criar(
                nome=f"Cliente {i}", horario=horario_do_indice(i), duracao=10,
                tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO,
            )
        depois = self.contar_consultas(url)
        self.assertEqual(antes, depois)


class MigracoesTests(TestCase):
    def test_nao_ha_migracoes_pendentes(self):
        # Falha (SystemExit) se o modelo mudou sem a migração correspondente.
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)


@override_settings(SECURE_SSL_REDIRECT=False)
class CabecalhosETransporteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def test_cabecalhos_de_protecao_nas_respostas(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(url_agenda())
        self.assertEqual(resposta["X-Frame-Options"], "DENY")
        self.assertEqual(resposta["X-Content-Type-Options"], "nosniff")

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_e_redirecionado_para_https_quando_ativado(self):
        resposta = self.client.get(reverse("login"))
        self.assertEqual(resposta.status_code, 301)
        self.assertTrue(resposta["Location"].startswith("https://"))

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_cookies_ficam_seguros_quando_https_esta_ativo(self):
        resposta = self.client.post(
            reverse("login"),
            {"username": "usuario_teste", "password": SENHA},
            secure=True,
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.cookies["sessionid"]["secure"])
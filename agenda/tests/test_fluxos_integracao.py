"""Fluxos completos: do login ao logout, passando pelas regras da agenda."""
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

from .auxiliares import DIA, SENHA, BaseAgenda, criar, dados, url_agenda

# Este período existe somente nos testes e é fictício. Não representa o
# horário de atendimento real de ninguém.
PERIODO_DE_TESTE = "09:00-13:00"


def intervalos(resposta):
    return [(livre["inicio"], livre["fim"]) for livre in resposta.context["livres"]]


@override_settings(SECURE_SSL_REDIRECT=False, PERIODOS_ATENDIMENTO=PERIODO_DE_TESTE)
class JornadaCompletaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def entrar(self, cliente=None):
        cliente = cliente or self.client
        resposta = cliente.post(
            reverse("login"), {"username": "usuario_teste", "password": SENHA}
        )
        self.assertEqual(resposta.status_code, 302)
        return cliente

    def test_jornada_do_login_ao_logout(self):
        url = url_agenda()
        historico = reverse("agenda:historico")

        # 1. Sem login, nenhuma página privada abre.
        for destino in (url, historico):
            resposta = self.client.get(destino)
            self.assertEqual(resposta.status_code, 302)
            self.assertTrue(resposta["Location"].startswith(reverse("login")))

        # 2. Login real, pelo formulário.
        self.entrar()

        # 3. Dia vazio: todo o período de teste fica livre.
        resposta = self.client.get(url)
        self.assertContains(resposta, "Nenhum agendamento para este dia.")
        self.assertEqual(intervalos(resposta), [("09:00", "13:00")])

        # 4. Cria três agendamentos.
        self.client.post(
            url, dados(nome_cliente="Cliente A", horario="09:00", tipo="pago")
        )
        self.client.post(
            url, dados(nome_cliente="Cliente B", horario="10:00", tipo="gratuito")
        )
        resposta = self.client.post(
            url,
            dados(nome_cliente="Cliente E", horario="11:00", tipo="gratuito"),
            follow=True,
        )
        self.assertContains(resposta, "Agendamento de Cliente E registrado")
        self.assertEqual(intervalos(resposta), [("12:00", "13:00")])

        # 5. Conflito de horário é recusado e nada é gravado.
        conflito = self.client.post(
            url, dados(nome_cliente="Cliente F", horario="11:30")
        )
        self.assertEqual(conflito.status_code, 200)
        self.assertIn("horario", conflito.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 3)

        # 6. Concluir os dois gratuitos aumenta a contagem de um em um.
        cliente_b = Agendamento.objects.get(nome_cliente="Cliente B")
        cliente_e = Agendamento.objects.get(nome_cliente="Cliente E")
        self.client.post(reverse("agenda:concluir", args=[cliente_e.pk]))
        self.assertEqual(self.client.get(historico).context["total_gratuitos"], 1)
        self.client.post(reverse("agenda:concluir", args=[cliente_b.pk]))
        self.assertEqual(self.client.get(historico).context["total_gratuitos"], 2)

        # 7. Cancelar preserva o registro, não conta e libera o horário.
        cliente_a = Agendamento.objects.get(nome_cliente="Cliente A")
        confirmacao = self.client.get(reverse("agenda:cancelar", args=[cliente_a.pk]))
        self.assertEqual(confirmacao.status_code, 200)
        self.client.post(reverse("agenda:cancelar", args=[cliente_a.pk]))
        cliente_a.refresh_from_db()
        self.assertEqual(cliente_a.status, StatusAgendamento.CANCELADO)
        self.assertEqual(Agendamento.objects.count(), 3)

        resposta = self.client.get(historico)
        self.assertEqual(resposta.context["total_gratuitos"], 2)
        self.assertContains(resposta, "Cliente A")
        self.assertContains(resposta, "cc-status-cancelado")
        self.assertEqual(
            intervalos(self.client.get(url)),
            [("09:00", "10:00"), ("12:00", "13:00")],
        )

        # 8. Logout encerra a sessão e as páginas voltam a ficar protegidas.
        self.client.post(reverse("logout"))
        for destino in (url, historico):
            self.assertEqual(self.client.get(destino).status_code, 302)

    def test_dados_ficam_no_banco_e_aparecem_em_uma_nova_sessao(self):
        self.entrar()
        self.client.post(
            url_agenda(), dados(nome_cliente="Cliente A", horario="09:00")
        )
        outro_navegador = self.entrar(Client())
        resposta = outro_navegador.get(url_agenda())
        self.assertContains(resposta, "Cliente A")
        self.assertEqual(Agendamento.objects.get().nome_cliente, "Cliente A")


class CenarioDeValidacaoTests(BaseAgenda):
    """Reproduz o cenário planejado para a validação, só com dados fictícios."""

    @override_settings(PERIODOS_ATENDIMENTO=PERIODO_DE_TESTE)
    def test_tres_tarefas_do_roteiro_de_validacao(self):
        criar(nome="Cliente A", horario=time(9, 0), tipo=TipoCorte.PAGO)
        criar(nome="Cliente B", horario=time(10, 0), tipo=TipoCorte.PAGO)
        criar(
            nome="Cliente C", data=date(2026, 11, 10), horario=time(9, 0),
            tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO,
        )
        criar(
            nome="Cliente D", data=date(2026, 11, 11), horario=time(9, 0),
            tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO,
        )

        # Tarefa 1: 9h e 10h ocupados, 11h livre.
        resposta = self.client.get(url_agenda(DIA))
        self.assertContains(resposta, "Cliente A")
        self.assertContains(resposta, "Cliente B")
        self.assertEqual(intervalos(resposta), [("11:00", "13:00")])

        # Tarefa 2: corte gratuito para Cliente E em 14/11/2026, às 11h.
        resposta = self.client.post(
            url_agenda(DIA),
            dados(
                nome_cliente="Cliente E", data="2026-11-14", horario="11:00",
                duracao_minutos="60", tipo="gratuito",
            ),
            follow=True,
        )
        self.assertContains(resposta, "Cliente E")
        self.assertContains(resposta, 'class="cc-selo cc-selo-gratuito">Gratuito</span>')

        # Tarefa 3: concluir e conferir que a contagem vai de 2 para 3.
        historico = reverse("agenda:historico")
        self.assertEqual(self.client.get(historico).context["total_gratuitos"], 2)
        cliente_e = Agendamento.objects.get(nome_cliente="Cliente E")
        self.client.post(reverse("agenda:concluir", args=[cliente_e.pk]))
        resposta = self.client.get(historico)
        self.assertEqual(resposta.context["total_gratuitos"], 3)
        self.assertContains(resposta, "Cliente E")
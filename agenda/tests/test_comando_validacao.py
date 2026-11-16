from datetime import date
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

from .auxiliares import DIA, BaseAgenda, dados, url_agenda


class ComandoPrepararValidacaoTests(BaseAgenda):
    def executar(self, *argumentos):
        saida = StringIO()
        call_command("preparar_validacao", *argumentos, stdout=saida)
        return saida.getvalue()

    def test_cria_o_cenario_de_demonstracao(self):
        saida = self.executar()
        self.assertEqual(Agendamento.objects.count(), 4)
        self.assertEqual(
            set(Agendamento.objects.values_list("nome_cliente", flat=True)),
            {"Cliente A", "Cliente B", "Cliente C", "Cliente D"},
        )
        self.assertIn("Cortes gratuitos concluídos no início: 2", saida)

    def test_estado_inicial_do_roteiro(self):
        self.executar()
        do_dia = list(Agendamento.objects.do_dia(DIA))
        self.assertEqual([a.horario.hour for a in do_dia], [9, 10])
        self.assertTrue(all(a.status == StatusAgendamento.AGENDADO for a in do_dia))
        self.assertEqual(Agendamento.objects.gratuitos_concluidos().count(), 2)

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_onze_horas_fica_livre_na_agenda(self):
        self.executar()
        resposta = self.client.get(url_agenda())
        livres = [(l["inicio"], l["fim"]) for l in resposta.context["livres"]]
        self.assertEqual(livres, [("08:00", "09:00"), ("11:00", "12:00")])

    def test_as_tres_tarefas_do_roteiro_levam_a_contagem_de_2_para_3(self):
        self.executar()
        # Tarefa 2: corte gratuito para Cliente E, 14/11/2026, 11h, 60 minutos.
        resposta = self.client.post(url_agenda(), dados(), follow=True)
        self.assertContains(resposta, "Agendamento de Cliente E registrado")
        cliente_e = Agendamento.objects.get(nome_cliente="Cliente E")
        self.assertEqual(cliente_e.tipo, TipoCorte.GRATUITO)

        # Tarefa 3: concluir e conferir o histórico.
        historico = reverse("agenda:historico")
        self.assertEqual(self.client.get(historico).context["total_gratuitos"], 2)
        self.client.post(reverse("agenda:concluir", args=[cliente_e.pk]))
        resposta = self.client.get(historico)
        self.assertEqual(resposta.context["total_gratuitos"], 3)
        self.assertContains(resposta, "Cliente E")

    def test_aceita_outra_data_de_demonstracao(self):
        self.executar("--data-demonstracao=2027-03-10")
        self.assertEqual(Agendamento.objects.do_dia(date(2027, 3, 10)).count(), 2)
        self.assertEqual(Agendamento.objects.gratuitos_concluidos().count(), 2)

    def test_recusa_banco_que_ja_tem_dados(self):
        self.executar()
        with self.assertRaises(CommandError):
            self.executar()
        self.assertEqual(Agendamento.objects.count(), 4)

    def test_recusa_data_invalida(self):
        for valor in ["abc", "2026-02-31", "0001-01-02"]:
            with self.subTest(valor=valor):
                with self.assertRaises(CommandError):
                    self.executar(f"--data-demonstracao={valor}")
        self.assertEqual(Agendamento.objects.count(), 0)
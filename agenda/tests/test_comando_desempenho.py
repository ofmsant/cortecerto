from datetime import date
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from agenda.management.commands.popular_desempenho import PREFIXO, banco_e_o_principal
from agenda.models import Agendamento, StatusAgendamento, TipoCorte

from .auxiliares import BaseAgenda, url_agenda


class ComandoPopularDesempenhoTests(BaseAgenda):
    def executar(self, *argumentos):
        saida = StringIO()
        call_command("popular_desempenho", *argumentos, stdout=saida)
        return saida.getvalue()

    def test_cria_200_agendamentos_validos_por_padrao(self):
        saida = self.executar()
        self.assertEqual(Agendamento.objects.count(), 200)
        self.assertEqual(
            Agendamento.objects.filter(nome_cliente__startswith=PREFIXO).count(), 200
        )
        self.assertIn("Criados 200 agendamentos", saida)

    def test_distribui_status_tipos_e_dias(self):
        self.executar()
        contagem = lambda **filtros: Agendamento.objects.filter(**filtros).count()
        self.assertEqual(contagem(status=StatusAgendamento.AGENDADO), 50)
        self.assertEqual(contagem(status=StatusAgendamento.CONCLUIDO), 100)
        self.assertEqual(contagem(status=StatusAgendamento.CANCELADO), 50)
        self.assertEqual(contagem(tipo=TipoCorte.PAGO), 100)
        self.assertEqual(contagem(tipo=TipoCorte.GRATUITO), 100)
        self.assertEqual(Agendamento.objects.gratuitos_concluidos().count(), 50)
        self.assertEqual(Agendamento.objects.values("data").distinct().count(), 20)

    def test_pode_concentrar_tudo_em_um_dia(self):
        self.executar("--por-dia=200")
        self.assertEqual(Agendamento.objects.count(), 200)
        self.assertEqual(Agendamento.objects.values("data").distinct().count(), 1)
        resposta = self.client.get(url_agenda(date(2030, 1, 1)))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Teste Desempenho 200")

    def test_historico_e_paginado_com_os_dados_de_teste(self):
        self.executar()
        resposta = self.client.get(reverse("agenda:historico"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Página 1 de 6")  # 150 registros, 25 por página
        self.assertEqual(resposta.context["total_gratuitos"], 50)

    def test_recusa_rodar_duas_vezes_no_mesmo_banco(self):
        self.executar()
        with self.assertRaises(CommandError):
            self.executar()
        self.assertEqual(Agendamento.objects.count(), 200)

    def test_recusa_argumentos_invalidos(self):
        invalidos = [
            ["--quantidade=0"],
            ["--quantidade=1001"],
            ["--por-dia=0"],
            ["--por-dia=201"],
            ["--data-inicial=abc"],
            ["--data-inicial=9999-12-31", "--quantidade=20", "--por-dia=1"],
        ]
        for argumentos in invalidos:
            with self.subTest(argumentos=argumentos):
                with self.assertRaises(CommandError):
                    self.executar(*argumentos)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_reconhece_o_banco_principal_pelo_nome_do_arquivo(self):
        self.assertTrue(banco_e_o_principal("db.sqlite3"))
        self.assertTrue(banco_e_o_principal(Path("pasta") / "db.sqlite3"))
        self.assertFalse(banco_e_o_principal("desempenho.sqlite3"))
        self.assertFalse(banco_e_o_principal(Path("pasta") / "desempenho.sqlite3"))
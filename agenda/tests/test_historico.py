from datetime import date, time, timedelta

from django.urls import reverse

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

from .auxiliares import BaseAgenda, criar, dados, url_agenda


class HistoricoTests(BaseAgenda):
    def setUp(self):
        super().setUp()
        self.url = reverse("agenda:historico")

    def test_sem_registros_mostra_estado_vazio_e_contagem_zero(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "agenda/historico.html")
        self.assertContains(resposta, "Nenhum atendimento registrado no histórico ainda.")
        self.assertEqual(resposta.context["total_gratuitos"], 0)

    def test_concluido_aparece_com_dados_e_tipo(self):
        criar(nome="Cliente A", tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Cliente A")
        self.assertContains(resposta, "14/11/2026 às 09:00")
        self.assertContains(resposta, 'class="cc-selo cc-selo-gratuito">Gratuito</span>')
        self.assertContains(resposta, 'class="cc-status cc-status-concluido">Concluído</span>')

    def test_cancelado_aparece_identificado(self):
        criar(nome="Cliente B", status=StatusAgendamento.CANCELADO)
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Cliente B")
        self.assertContains(resposta, 'class="cc-status cc-status-cancelado">Cancelado</span>')

    def test_agendamento_ainda_ativo_nao_aparece(self):
        criar(nome="Cliente C", status=StatusAgendamento.AGENDADO)
        resposta = self.client.get(self.url)
        self.assertNotContains(resposta, "Cliente C")

    def test_mais_recentes_aparecem_primeiro(self):
        criar(nome="Cliente Antigo", data=date(2026, 10, 1), status=StatusAgendamento.CONCLUIDO)
        criar(nome="Cliente Novo", data=date(2026, 11, 1), status=StatusAgendamento.CONCLUIDO)
        conteudo = self.client.get(self.url).content.decode()
        self.assertLess(conteudo.index("Cliente Novo"), conteudo.index("Cliente Antigo"))

    def test_contagem_considera_somente_gratuitos_concluidos(self):
        criar(horario=time(8, 0), tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO)
        criar(horario=time(9, 0), tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO)
        criar(horario=time(10, 0), tipo=TipoCorte.GRATUITO, status=StatusAgendamento.AGENDADO)
        criar(horario=time(11, 0), tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CANCELADO)
        criar(horario=time(12, 0), tipo=TipoCorte.PAGO, status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.context["total_gratuitos"], 2)
        self.assertContains(resposta, 'id="total-gratuitos">2</p>')

    def test_pagina_e_dividida_em_blocos(self):
        inicio = date(2026, 9, 1)
        for i in range(30):
            criar(
                nome=f"Cliente {i}",
                data=inicio + timedelta(days=i),
                status=StatusAgendamento.CONCLUIDO,
            )
        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url + "?pagina=2")
        self.assertEqual(len(primeira.context["pagina"]), 25)
        self.assertEqual(len(segunda.context["pagina"]), 5)
        self.assertContains(primeira, "Página 1 de 2")

    def test_pagina_invalida_nao_quebra(self):
        resposta = self.client.get(self.url + "?pagina=abc")
        self.assertEqual(resposta.status_code, 200)


class FluxoCompletoTests(BaseAgenda):
    """Cenário da validação: dois gratuitos concluídos antes, o terceiro entra ao concluir."""

    def test_concluir_o_terceiro_gratuito_leva_a_contagem_de_2_para_3(self):
        criar(
            nome="Cliente C", data=date(2026, 11, 10), horario=time(9, 0),
            tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO,
        )
        criar(
            nome="Cliente D", data=date(2026, 11, 11), horario=time(9, 0),
            tipo=TipoCorte.GRATUITO, status=StatusAgendamento.CONCLUIDO,
        )
        historico = reverse("agenda:historico")
        self.assertEqual(self.client.get(historico).context["total_gratuitos"], 2)

        self.client.post(url_agenda(), dados(nome_cliente="Cliente E"))
        agendamento = Agendamento.objects.get(nome_cliente="Cliente E")
        # Ainda agendado: não entra na contagem nem no histórico.
        resposta = self.client.get(historico)
        self.assertEqual(resposta.context["total_gratuitos"], 2)

        self.client.post(reverse("agenda:concluir", args=[agendamento.pk]))
        resposta = self.client.get(historico)
        self.assertEqual(resposta.context["total_gratuitos"], 3)
        self.assertContains(resposta, "Cliente E")

    def test_repetir_a_conclusao_nao_conta_duas_vezes(self):
        self.client.post(url_agenda(), dados())
        agendamento = Agendamento.objects.get()
        url = reverse("agenda:concluir", args=[agendamento.pk])
        self.client.post(url)
        self.client.post(url)
        resposta = self.client.get(reverse("agenda:historico"))
        self.assertEqual(resposta.context["total_gratuitos"], 1)

    def test_dados_persistem_ao_recarregar_a_pagina(self):
        self.client.post(url_agenda(), dados())
        primeira = self.client.get(url_agenda())
        segunda = self.client.get(url_agenda())
        self.assertContains(primeira, "Cliente E")
        self.assertContains(segunda, "Cliente E")
from datetime import date, time, timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

from .auxiliares import DIA, BaseAgenda, criar, dados, url_agenda


class ConsultaAgendaTests(BaseAgenda):
    def test_lista_somente_os_agendamentos_da_data(self):
        criar(nome="Cliente A", horario=time(9, 0))
        criar(nome="Cliente B", horario=time(10, 0), tipo=TipoCorte.GRATUITO)
        criar(nome="Cliente C", data=DIA + timedelta(days=1))
        resposta = self.client.get(url_agenda())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Cliente A")
        self.assertContains(resposta, "Cliente B")
        self.assertNotContains(resposta, "Cliente C")
        self.assertContains(resposta, "09:00 às 10:00")
        self.assertContains(resposta, "10:00 às 11:00")

    def test_identifica_tipo_por_texto_e_classe(self):
        criar(nome="Cliente A", horario=time(9, 0), tipo=TipoCorte.PAGO)
        criar(nome="Cliente B", horario=time(10, 0), tipo=TipoCorte.GRATUITO)
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, 'class="cc-selo cc-selo-pago">Pago</span>')
        self.assertContains(resposta, 'class="cc-selo cc-selo-gratuito">Gratuito</span>')

    def test_mostra_o_status_de_cada_agendamento(self):
        criar(nome="Cliente A", horario=time(9, 0))
        criar(nome="Cliente B", horario=time(10, 0), status=StatusAgendamento.CONCLUIDO)
        criar(nome="Cliente C", horario=time(11, 0), status=StatusAgendamento.CANCELADO)
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "cc-status-agendado")
        self.assertContains(resposta, "cc-status-concluido")
        self.assertContains(resposta, "cc-status-cancelado")

    def test_dia_sem_agendamentos_mostra_estado_vazio(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "Nenhum agendamento para este dia.")

    def test_sem_data_mostra_hoje(self):
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["dia"], timezone.localdate())

    def test_data_invalida_volta_para_hoje_com_aviso(self):
        resposta = self.client.get(f"{reverse('agenda:inicio')}?data=abc")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["dia"], timezone.localdate())
        self.assertContains(resposta, "Data inválida")

    def test_navegacao_para_dia_anterior_e_seguinte(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "?data=2026-11-13")
        self.assertContains(resposta, "?data=2026-11-15")

    def test_agendamento_ativo_tem_botoes_de_concluir_e_cancelar(self):
        agendamento = criar()
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, reverse("agenda:concluir", args=[agendamento.pk]))
        self.assertContains(resposta, reverse("agenda:cancelar", args=[agendamento.pk]))

    def test_cancelado_e_concluido_nao_tem_botoes_de_acao(self):
        cancelado = criar(nome="Cliente A", horario=time(9, 0), status=StatusAgendamento.CANCELADO)
        concluido = criar(nome="Cliente B", horario=time(10, 0), status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.get(url_agenda())
        for agendamento in (cancelado, concluido):
            self.assertNotContains(resposta, reverse("agenda:concluir", args=[agendamento.pk]))
            self.assertNotContains(resposta, reverse("agenda:cancelar", args=[agendamento.pk]))

    def test_formulario_vem_com_a_data_consultada_e_horario_do_link(self):
        resposta = self.client.get(url_agenda() + "&horario=11:00")
        self.assertContains(resposta, 'value="2026-11-14"')
        self.assertContains(resposta, 'value="11:00"')

    def test_horario_invalido_no_link_e_ignorado(self):
        resposta = self.client.get(url_agenda() + "&horario=abc")
        self.assertEqual(resposta.status_code, 200)


class HorariosLivresTests(BaseAgenda):
    def test_sem_periodos_avisa_e_nao_inventa_horarios(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "ainda não foram configurados")
        self.assertEqual(resposta.context["livres"], [])

    @override_settings(PERIODOS_ATENDIMENTO="abc")
    def test_periodos_invalidos_avisam_sem_quebrar_a_pagina(self):
        resposta = self.client.get(url_agenda())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "inválida")

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_mostra_intervalos_livres_descontando_agendamentos_ativos(self):
        criar(horario=time(9, 0), duracao=60)
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "08:00 às 09:00")
        self.assertContains(resposta, "10:00 às 12:00")

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_cancelado_nao_ocupa_horario_na_agenda(self):
        criar(horario=time(9, 0), duracao=60, status=StatusAgendamento.CANCELADO)
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "08:00 às 12:00")

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_periodo_totalmente_ocupado_avisa_que_nao_ha_livres(self):
        criar(horario=time(8, 0), duracao=240)
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "Não há horários livres nesta data")


class CriarAgendamentoTests(BaseAgenda):
    def test_cria_agendamento_valido_e_redireciona_para_a_data(self):
        resposta = self.client.post(url_agenda(), dados())
        self.assertRedirects(resposta, url_agenda(DIA))
        agendamento = Agendamento.objects.get()
        self.assertEqual(agendamento.nome_cliente, "Cliente E")
        self.assertEqual(agendamento.data, DIA)
        self.assertEqual(agendamento.horario, time(11, 0))
        self.assertEqual(agendamento.duracao_minutos, 60)
        self.assertEqual(agendamento.tipo, TipoCorte.GRATUITO)
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_mostra_confirmacao_e_o_agendamento_na_agenda(self):
        resposta = self.client.post(url_agenda(), dados(), follow=True)
        self.assertContains(
            resposta, "Agendamento de Cliente E registrado para 14/11/2026 às 11:00."
        )
        self.assertContains(resposta, "11:00 às 12:00")

    def test_armazena_o_tipo_pago(self):
        self.client.post(url_agenda(), dados(tipo="pago"))
        self.assertEqual(Agendamento.objects.get().tipo, TipoCorte.PAGO)

    def test_redireciona_para_a_data_do_agendamento_criado(self):
        outra = date(2026, 11, 20)
        resposta = self.client.post(url_agenda(DIA), dados(data="2026-11-20"))
        self.assertRedirects(resposta, url_agenda(outra))

    def test_campos_obrigatorios_sao_validados_no_servidor(self):
        for campo in ["nome_cliente", "data", "horario", "duracao_minutos", "tipo"]:
            with self.subTest(campo=campo):
                resposta = self.client.post(url_agenda(), dados(**{campo: ""}))
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(campo, resposta.context["formulario"].errors)
                self.assertEqual(Agendamento.objects.count(), 0)

    def test_nome_so_com_espacos_e_rejeitado(self):
        resposta = self.client.post(url_agenda(), dados(nome_cliente="   "))
        self.assertIn("nome_cliente", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_rejeita_nome_acima_de_100_caracteres(self):
        resposta = self.client.post(url_agenda(), dados(nome_cliente="a" * 101))
        self.assertIn("nome_cliente", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_aceita_nome_com_100_caracteres(self):
        self.client.post(url_agenda(), dados(nome_cliente="a" * 100))
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_rejeita_tipo_invalido(self):
        resposta = self.client.post(url_agenda(), dados(tipo="cortesia"))
        self.assertIn("tipo", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_rejeita_duracao_invalida(self):
        for valor in ["0", "-5", "1441", "abc"]:
            with self.subTest(valor=valor):
                resposta = self.client.post(url_agenda(), dados(duracao_minutos=valor))
                self.assertIn("duracao_minutos", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_rejeita_data_inexistente(self):
        resposta = self.client.post(url_agenda(), dados(data="2026-02-31"))
        self.assertIn("data", resposta.context["formulario"].errors)

    def test_rejeita_atendimento_que_passa_da_meia_noite(self):
        resposta = self.client.post(
            url_agenda(), dados(horario="23:30", duracao_minutos="60")
        )
        self.assertIn("duracao_minutos", resposta.context["formulario"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_conflito_de_horario_e_rejeitado_com_mensagem_no_campo(self):
        criar(nome="Cliente A", horario=time(9, 0), duracao=60)
        resposta = self.client.post(url_agenda(), dados(horario="09:30"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("horario", resposta.context["formulario"].errors)
        self.assertContains(resposta, "conflita com o agendamento de Cliente A")
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_horarios_contiguos_sao_aceitos(self):
        criar(horario=time(9, 0), duracao=60)
        resposta = self.client.post(url_agenda(), dados(horario="10:00"))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Agendamento.objects.count(), 2)

    def test_horario_de_agendamento_cancelado_pode_ser_reutilizado(self):
        criar(horario=time(11, 0), status=StatusAgendamento.CANCELADO)
        resposta = self.client.post(url_agenda(), dados(horario="11:00"))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Agendamento.objects.count(), 2)

    def test_envio_duplicado_nao_cria_dois_agendamentos(self):
        primeiro = self.client.post(url_agenda(), dados())
        segundo = self.client.post(url_agenda(), dados())
        self.assertEqual(primeiro.status_code, 302)
        self.assertEqual(segundo.status_code, 200)
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_erro_preserva_os_dados_validos_ja_preenchidos(self):
        resposta = self.client.post(url_agenda(), dados(nome_cliente=""))
        formulario = resposta.context["formulario"]
        self.assertEqual(formulario["horario"].value(), "11:00")
        self.assertEqual(formulario["duracao_minutos"].value(), "60")
        self.assertEqual(formulario["tipo"].value(), "gratuito")
        self.assertContains(resposta, 'value="11:00"')

    def test_erro_aparece_junto_ao_campo_e_marca_o_campo(self):
        resposta = self.client.post(url_agenda(), dados(nome_cliente=""))
        self.assertContains(resposta, 'id="erro-nome_cliente"')
        self.assertContains(resposta, "Este campo é obrigatório.")
        self.assertContains(resposta, "is-invalid")
        self.assertContains(resposta, "Não foi possível salvar o agendamento.")

    def test_get_na_agenda_nao_cria_nada(self):
        self.client.get(url_agenda())
        self.assertEqual(Agendamento.objects.count(), 0)


class ConcluirAgendamentoTests(BaseAgenda):
    def test_conclui_e_mantem_o_registro(self):
        agendamento = criar(tipo=TipoCorte.GRATUITO)
        resposta = self.client.post(
            reverse("agenda:concluir", args=[agendamento.pk]), follow=True
        )
        self.assertRedirects(resposta, url_agenda(DIA))
        self.assertContains(resposta, "Atendimento de Cliente A concluído.")
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.CONCLUIDO)
        self.assertEqual(agendamento.tipo, TipoCorte.GRATUITO)
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_clique_repetido_nao_repete_a_operacao_nem_a_contagem(self):
        agendamento = criar(tipo=TipoCorte.GRATUITO)
        url = reverse("agenda:concluir", args=[agendamento.pk])
        self.client.post(url)
        resposta = self.client.post(url, follow=True)
        self.assertContains(resposta, "já estava concluído")
        self.assertEqual(Agendamento.objects.gratuitos_concluidos().count(), 1)

    def test_nao_conclui_agendamento_cancelado(self):
        agendamento = criar(status=StatusAgendamento.CANCELADO)
        resposta = self.client.post(
            reverse("agenda:concluir", args=[agendamento.pk]), follow=True
        )
        self.assertContains(resposta, "Somente agendamentos ativos podem ser concluídos")
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.CANCELADO)

    def test_get_nao_altera_nada(self):
        agendamento = criar()
        resposta = self.client.get(reverse("agenda:concluir", args=[agendamento.pk]))
        self.assertEqual(resposta.status_code, 405)
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_agendamento_inexistente_da_404(self):
        resposta = self.client.post(reverse("agenda:concluir", args=[9999]))
        self.assertEqual(resposta.status_code, 404)


class CancelarAgendamentoTests(BaseAgenda):
    def test_get_mostra_confirmacao_sem_cancelar(self):
        agendamento = criar()
        resposta = self.client.get(reverse("agenda:cancelar", args=[agendamento.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "agenda/cancelar.html")
        self.assertContains(resposta, "Cliente A")
        self.assertContains(resposta, "Confirmar cancelamento")
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_post_cancela_e_preserva_o_registro(self):
        agendamento = criar(tipo=TipoCorte.GRATUITO)
        resposta = self.client.post(
            reverse("agenda:cancelar", args=[agendamento.pk]), follow=True
        )
        self.assertRedirects(resposta, url_agenda(DIA))
        self.assertContains(resposta, "Agendamento de Cliente A cancelado.")
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.CANCELADO)
        self.assertEqual(Agendamento.objects.count(), 1)
        self.assertEqual(Agendamento.objects.gratuitos_concluidos().count(), 0)

    def test_cancelamento_repetido_nao_altera_nada(self):
        agendamento = criar()
        url = reverse("agenda:cancelar", args=[agendamento.pk])
        self.client.post(url)
        resposta = self.client.post(url, follow=True)
        self.assertContains(resposta, "já estava cancelado")
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_nao_cancela_atendimento_concluido(self):
        agendamento = criar(status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.post(
            reverse("agenda:cancelar", args=[agendamento.pk]), follow=True
        )
        self.assertContains(resposta, "Somente agendamentos ativos podem ser cancelados")
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.CONCLUIDO)

    def test_confirmacao_de_concluido_redireciona_com_aviso(self):
        agendamento = criar(status=StatusAgendamento.CONCLUIDO)
        resposta = self.client.get(
            reverse("agenda:cancelar", args=[agendamento.pk]), follow=True
        )
        self.assertRedirects(resposta, url_agenda(DIA))
        self.assertContains(resposta, "não podem ser cancelados")

    def test_confirmacao_de_cancelado_redireciona_com_aviso(self):
        agendamento = criar(status=StatusAgendamento.CANCELADO)
        resposta = self.client.get(
            reverse("agenda:cancelar", args=[agendamento.pk]), follow=True
        )
        self.assertRedirects(resposta, url_agenda(DIA))
        self.assertContains(resposta, "já está cancelado")

    def test_horario_cancelado_volta_a_ficar_livre(self):
        agendamento = criar(horario=time(9, 0), duracao=60)
        self.client.post(reverse("agenda:cancelar", args=[agendamento.pk]))
        resposta = self.client.post(url_agenda(), dados(horario="09:00"))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Agendamento.objects.count(), 2)

    def test_agendamento_inexistente_da_404(self):
        resposta = self.client.get(reverse("agenda:cancelar", args=[9999]))
        self.assertEqual(resposta.status_code, 404)
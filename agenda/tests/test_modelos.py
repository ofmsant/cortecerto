from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

DIA = date(2026, 11, 14)
OUTRO_DIA = date(2026, 11, 15)


def montar(
    nome_cliente="Cliente A",
    data=DIA,
    horario=time(9, 0),
    duracao_minutos=60,
    tipo=TipoCorte.PAGO,
    status=StatusAgendamento.AGENDADO,
):
    return Agendamento(
        nome_cliente=nome_cliente,
        data=data,
        horario=horario,
        duracao_minutos=duracao_minutos,
        tipo=tipo,
        status=status,
    )


def criar(**campos):
    agendamento = montar(**campos)
    agendamento.save()
    return agendamento


class CriacaoTests(TestCase):
    def test_cria_agendamento_valido_e_persiste(self):
        agendamento = criar()
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.nome_cliente, "Cliente A")
        self.assertEqual(agendamento.data, DIA)
        self.assertEqual(agendamento.horario, time(9, 0))
        self.assertEqual(agendamento.duracao_minutos, 60)
        self.assertIsNotNone(agendamento.criado_em)
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_status_padrao_e_agendado(self):
        self.assertEqual(
            Agendamento().status,
            StatusAgendamento.AGENDADO,
        )

    def test_armazena_tipo_pago_e_gratuito_explicitamente(self):
        pago = criar(horario=time(9, 0), tipo=TipoCorte.PAGO)
        gratuito = criar(horario=time(10, 0), tipo=TipoCorte.GRATUITO)
        pago.refresh_from_db()
        gratuito.refresh_from_db()
        self.assertEqual(pago.tipo, "pago")
        self.assertEqual(gratuito.tipo, "gratuito")

    def test_rejeita_campos_obrigatorios_ausentes(self):
        for campo in [
            "nome_cliente",
            "data",
            "horario",
            "duracao_minutos",
            "tipo",
        ]:
            with self.subTest(campo=campo):
                with self.assertRaises(ValidationError) as contexto:
                    montar(**{campo: None}).full_clean()
                self.assertIn(campo, contexto.exception.message_dict)

    def test_rejeita_nome_vazio(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(nome_cliente="").full_clean()
        self.assertIn("nome_cliente", contexto.exception.message_dict)

    def test_rejeita_nome_so_com_espacos(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(nome_cliente="   ").full_clean()
        self.assertIn("nome_cliente", contexto.exception.message_dict)

    def test_aceita_nome_com_100_caracteres(self):
        montar(nome_cliente="a" * 100).full_clean()

    def test_rejeita_nome_acima_de_100_caracteres(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(nome_cliente="a" * 101).full_clean()
        self.assertIn("nome_cliente", contexto.exception.message_dict)

    def test_rejeita_tipo_invalido(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(tipo="cortesia").full_clean()
        self.assertIn("tipo", contexto.exception.message_dict)

    def test_rejeita_status_invalido(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(status="apagado").full_clean()
        self.assertIn("status", contexto.exception.message_dict)

    def test_rejeita_duracao_zero_ou_negativa(self):
        for duracao in [0, -10]:
            with self.subTest(duracao=duracao):
                with self.assertRaises(ValidationError) as contexto:
                    montar(duracao_minutos=duracao).full_clean()
                self.assertIn(
                    "duracao_minutos",
                    contexto.exception.message_dict,
                )

    def test_rejeita_atendimento_que_passa_da_meia_noite(self):
        with self.assertRaises(ValidationError) as contexto:
            montar(
                horario=time(23, 30),
                duracao_minutos=60,
            ).full_clean()
        self.assertIn(
            "duracao_minutos",
            contexto.exception.message_dict,
        )

    def test_aceita_atendimento_que_termina_a_meia_noite(self):
        montar(
            horario=time(23, 0),
            duracao_minutos=60,
        ).full_clean()

    def test_save_valida_antes_de_gravar(self):
        with self.assertRaises(ValidationError):
            montar(nome_cliente="").save()
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_descarta_segundos_do_horario(self):
        agendamento = criar(horario=time(9, 0, 30))
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.horario, time(9, 0))


class ConflitoTests(TestCase):
    def setUp(self):
        # Existente: 09:00 às 10:00
        self.existente = criar(
            horario=time(9, 0),
            duracao_minutos=60,
        )

    def assertConflita(self, **campos):
        with self.assertRaises(ValidationError) as contexto:
            montar(nome_cliente="Cliente B", **campos).full_clean()
        self.assertIn("horario", contexto.exception.message_dict)

    def test_rejeita_mesmo_horario(self):
        self.assertConflita(horario=time(9, 0))

    def test_rejeita_sobreposicao_no_fim_do_existente(self):
        self.assertConflita(horario=time(9, 30))

    def test_rejeita_sobreposicao_no_inicio_do_existente(self):
        self.assertConflita(
            horario=time(8, 30),
            duracao_minutos=60,
        )

    def test_rejeita_atendimento_contido_no_existente(self):
        self.assertConflita(
            horario=time(9, 15),
            duracao_minutos=15,
        )

    def test_permite_horarios_contiguos(self):
        montar(
            nome_cliente="Cliente B",
            horario=time(10, 0),
        ).full_clean()
        montar(
            nome_cliente="Cliente C",
            horario=time(8, 0),
            duracao_minutos=60,
        ).full_clean()

    def test_permite_mesmo_horario_em_outro_dia(self):
        montar(
            nome_cliente="Cliente B",
            data=OUTRO_DIA,
            horario=time(9, 0),
        ).full_clean()

    def test_respeita_duracao_variavel(self):
        longo = criar(
            nome_cliente="Cliente L",
            horario=time(14, 0),
            duracao_minutos=90,
        )
        self.assertIsNotNone(longo.pk)
        self.assertConflita(
            horario=time(15, 0),
            duracao_minutos=30,
        )
        montar(
            nome_cliente="Cliente B",
            horario=time(15, 30),
            duracao_minutos=30,
        ).full_clean()

    def test_cancelado_nao_bloqueia_horario(self):
        criar(
            nome_cliente="Cliente X",
            horario=time(11, 0),
            status=StatusAgendamento.CANCELADO,
        )
        criar(
            nome_cliente="Cliente Y",
            horario=time(11, 0),
        )
        self.assertEqual(
            Agendamento.objects.filter(
                data=DIA,
                horario=time(11, 0),
            ).count(),
            2,
        )

    def test_horario_volta_a_ficar_disponivel_apos_cancelamento(self):
        self.existente.cancelar()
        novo = criar(
            nome_cliente="Cliente B",
            horario=time(9, 0),
        )
        self.assertEqual(novo.status, StatusAgendamento.AGENDADO)

    def test_concluido_continua_ocupando_o_horario(self):
        self.existente.concluir()
        self.assertConflita(horario=time(9, 0))

    def test_editar_agendamento_nao_conflita_consigo_mesmo(self):
        self.existente.nome_cliente = "Cliente Z"
        self.existente.save()
        self.existente.refresh_from_db()
        self.assertEqual(self.existente.nome_cliente, "Cliente Z")

    def test_save_impede_gravar_agendamento_conflitante(self):
        with self.assertRaises(ValidationError):
            montar(
                nome_cliente="Cliente B",
                horario=time(9, 30),
            ).save()
        self.assertEqual(Agendamento.objects.count(), 1)


class RestricoesDoBancoTests(TestCase):
    def test_banco_impede_mesmo_inicio_quando_ambos_ocupam_horario(self):
        primeiro = montar(nome_cliente="Cliente A")
        segundo = montar(nome_cliente="Cliente B")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Agendamento.objects.bulk_create([primeiro, segundo])

        self.assertEqual(Agendamento.objects.count(), 0)

    def test_banco_permite_mesmo_inicio_quando_um_esta_cancelado(self):
        cancelado = montar(
            nome_cliente="Cliente A",
            status=StatusAgendamento.CANCELADO,
        )
        ativo = montar(nome_cliente="Cliente B")
        Agendamento.objects.bulk_create([cancelado, ativo])
        self.assertEqual(Agendamento.objects.count(), 2)


class CancelamentoTests(TestCase):
    def test_cancelar_preserva_o_registro(self):
        agendamento = criar()
        resultado = agendamento.cancelar()
        self.assertTrue(resultado)
        self.assertEqual(Agendamento.objects.count(), 1)
        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.status,
            StatusAgendamento.CANCELADO,
        )
        self.assertEqual(agendamento.nome_cliente, "Cliente A")

    def test_cancelar_duas_vezes_nao_altera_nada(self):
        agendamento = criar()
        self.assertTrue(agendamento.cancelar())
        self.assertFalse(agendamento.cancelar())
        self.assertEqual(
            agendamento.status,
            StatusAgendamento.CANCELADO,
        )

    def test_nao_cancela_atendimento_concluido(self):
        agendamento = criar()
        agendamento.concluir()
        with self.assertRaises(ValidationError):
            agendamento.cancelar()
        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.status,
            StatusAgendamento.CONCLUIDO,
        )


class ConclusaoTests(TestCase):
    def test_concluir_muda_status_e_mantem_o_tipo(self):
        agendamento = criar(tipo=TipoCorte.GRATUITO)
        self.assertTrue(agendamento.concluir())
        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.status,
            StatusAgendamento.CONCLUIDO,
        )
        self.assertEqual(agendamento.tipo, TipoCorte.GRATUITO)
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_concluir_duas_vezes_nao_repete_a_operacao(self):
        agendamento = criar()
        self.assertTrue(agendamento.concluir())
        self.assertFalse(agendamento.concluir())

    def test_clique_repetido_com_instancia_desatualizada_nao_repete(self):
        primeira = criar()
        segunda = Agendamento.objects.get(pk=primeira.pk)
        self.assertTrue(primeira.concluir())
        self.assertFalse(segunda.concluir())

    def test_nao_conclui_agendamento_cancelado(self):
        agendamento = criar()
        agendamento.cancelar()
        with self.assertRaises(ValidationError):
            agendamento.concluir()
        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.status,
            StatusAgendamento.CANCELADO,
        )


class ContagemDeGratuitosTests(TestCase):
    def test_gratuito_concluido_e_contabilizado(self):
        criar(tipo=TipoCorte.GRATUITO).concluir()
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            1,
        )

    def test_pago_concluido_nao_entra_na_contagem(self):
        criar(tipo=TipoCorte.PAGO).concluir()
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            0,
        )

    def test_gratuito_cancelado_nao_entra_na_contagem(self):
        criar(tipo=TipoCorte.GRATUITO).cancelar()
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            0,
        )

    def test_gratuito_ainda_nao_concluido_nao_entra_na_contagem(self):
        criar(tipo=TipoCorte.GRATUITO)
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            0,
        )

    def test_operacao_repetida_nao_duplica_a_contagem(self):
        agendamento = criar(tipo=TipoCorte.GRATUITO)
        agendamento.concluir()
        agendamento.concluir()
        Agendamento.objects.get(pk=agendamento.pk).concluir()
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            1,
        )

    def test_conta_somente_os_gratuitos_concluidos_entre_varios_registros(self):
        criar(
            horario=time(8, 0),
            tipo=TipoCorte.GRATUITO,
        ).concluir()
        criar(
            horario=time(9, 0),
            tipo=TipoCorte.GRATUITO,
        ).concluir()
        criar(
            horario=time(10, 0),
            tipo=TipoCorte.GRATUITO,
        )
        criar(
            horario=time(11, 0),
            tipo=TipoCorte.GRATUITO,
        ).cancelar()
        criar(
            horario=time(12, 0),
            tipo=TipoCorte.PAGO,
        ).concluir()
        self.assertEqual(
            Agendamento.objects.gratuitos_concluidos().count(),
            2,
        )


class ConsultasTests(TestCase):
    def test_do_dia_retorna_somente_a_data_pedida(self):
        criar(data=DIA, horario=time(9, 0))
        criar(data=OUTRO_DIA, horario=time(9, 0))
        self.assertEqual(
            Agendamento.objects.do_dia(DIA).count(),
            1,
        )

    def test_historico_traz_concluidos_e_cancelados_do_mais_recente_ao_mais_antigo(self):
        concluido = criar(data=DIA, horario=time(9, 0))
        concluido.concluir()
        cancelado = criar(data=OUTRO_DIA, horario=time(9, 0))
        cancelado.cancelar()
        criar(data=OUTRO_DIA, horario=time(15, 0))

        historico = list(Agendamento.objects.historico())
        self.assertEqual(historico, [cancelado, concluido])

    def test_texto_do_agendamento(self):
        agendamento = criar()
        self.assertEqual(
            str(agendamento),
            "Cliente A em 14/11/2026 às 09:00",
        )
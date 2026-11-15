from datetime import date, time

from django.test import SimpleTestCase, TestCase, override_settings

from agenda.disponibilidade import (
    Intervalo,
    formatar_minutos,
    intervalos_livres,
    interpretar_periodos,
    periodos_configurados,
)
from agenda.models import Agendamento, StatusAgendamento, TipoCorte

DIA = date(2026, 11, 14)


def criar(horario, duracao, status=StatusAgendamento.AGENDADO):
    return Agendamento.objects.create(
        nome_cliente="Cliente A",
        data=DIA,
        horario=horario,
        duracao_minutos=duracao,
        tipo=TipoCorte.PAGO,
        status=status,
    )


class InterpretarPeriodosTests(SimpleTestCase):
    def test_texto_vazio_nao_define_periodos(self):
        self.assertEqual(interpretar_periodos(""), [])
        self.assertEqual(interpretar_periodos("   "), [])

    def test_interpreta_um_periodo(self):
        self.assertEqual(
            interpretar_periodos("08:00-12:00"),
            [Intervalo(480, 720)],
        )

    def test_interpreta_varios_periodos_e_ordena(self):
        self.assertEqual(
            interpretar_periodos("14:00-18:00, 08:00-12:00"),
            [Intervalo(480, 720), Intervalo(840, 1080)],
        )

    def test_rejeita_formato_invalido(self):
        for texto in [
            "8-12",
            "08:00/12:00",
            "abc",
            "08:00-12:00-14:00",
        ]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    interpretar_periodos(texto)

    def test_rejeita_horario_inexistente(self):
        for texto in [
            "25:00-26:00",
            "08:60-12:00",
            "08:00-24:30",
        ]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    interpretar_periodos(texto)

    def test_rejeita_periodo_que_termina_antes_de_comecar(self):
        with self.assertRaises(ValueError):
            interpretar_periodos("12:00-08:00")
        with self.assertRaises(ValueError):
            interpretar_periodos("08:00-08:00")

    def test_rejeita_periodos_sobrepostos(self):
        with self.assertRaises(ValueError):
            interpretar_periodos("08:00-12:00,11:00-15:00")

    def test_formata_minutos(self):
        self.assertEqual(formatar_minutos(570), "09:30")
        self.assertEqual(formatar_minutos(1440), "24:00")


class ConfiguracaoTests(SimpleTestCase):
    @override_settings(PERIODOS_ATENDIMENTO="")
    def test_sem_configuracao_nao_ha_periodos(self):
        self.assertEqual(periodos_configurados(), [])

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_le_periodos_da_configuracao(self):
        self.assertEqual(
            periodos_configurados(),
            [Intervalo(480, 720)],
        )


class IntervalosLivresTests(TestCase):
    @override_settings(PERIODOS_ATENDIMENTO="")
    def test_sem_periodos_configurados_nao_ha_horarios_livres(self):
        self.assertEqual(intervalos_livres(DIA), [])

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_dia_sem_agendamentos_fica_todo_livre(self):
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(480, 720)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_desconta_agendamento_ativo(self):
        criar(time(9, 0), 60)
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(480, 540), Intervalo(600, 720)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_desconta_agendamento_concluido(self):
        criar(
            time(9, 0),
            60,
            status=StatusAgendamento.CONCLUIDO,
        )
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(480, 540), Intervalo(600, 720)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_cancelado_nao_ocupa_horario(self):
        criar(
            time(9, 0),
            60,
            status=StatusAgendamento.CANCELADO,
        )
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(480, 720)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_duracoes_diferentes_geram_intervalos_diferentes(self):
        criar(time(8, 0), 30)
        criar(time(10, 0), 90)
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(510, 600), Intervalo(690, 720)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_agendamento_que_invade_o_periodo_por_fora(self):
        criar(time(7, 30), 60)
        criar(time(11, 30), 60)
        self.assertEqual(
            intervalos_livres(DIA),
            [Intervalo(510, 690)],
        )

    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_periodo_totalmente_ocupado_nao_tem_livres(self):
        criar(time(8, 0), 240)
        self.assertEqual(intervalos_livres(DIA), [])
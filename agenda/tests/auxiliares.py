"""Funções e classe-base compartilhadas pelos testes das telas."""
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

SENHA = "SenhaDeTeste#2026"
DIA = date(2026, 11, 14)


def url_agenda(dia=DIA):
    return f"{reverse('agenda:inicio')}?data={dia.isoformat()}"


def criar(
    nome="Cliente A",
    data=DIA,
    horario=time(9, 0),
    duracao=60,
    tipo=TipoCorte.PAGO,
    status=StatusAgendamento.AGENDADO,
):
    return Agendamento.objects.create(
        nome_cliente=nome,
        data=data,
        horario=horario,
        duracao_minutos=duracao,
        tipo=tipo,
        status=status,
    )


def dados(**extra):
    """Dados válidos de formulário (cliente fictício, corte gratuito às 11h)."""
    base = {
        "nome_cliente": "Cliente E",
        "data": "2026-11-14",
        "horario": "11:00",
        "duracao_minutos": "60",
        "tipo": "gratuito",
    }
    base.update(extra)
    return base


@override_settings(SECURE_SSL_REDIRECT=False, PERIODOS_ATENDIMENTO="")
class BaseAgenda(TestCase):
    """Cliente já autenticado e sem períodos de atendimento configurados."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def setUp(self):
        self.client.force_login(self.usuario)
"""Cria agendamentos fictícios para medir o desempenho.


Os registros fictícios têm nomes que começam com "Teste Desempenho" e misturam
status e tipos. Os concluídos gratuitos inflariam a contagem de um banco real, por
isso o comando recusa rodar no arquivo db.sqlite3 sem um aviso explícito.
"""
from datetime import date, time, timedelta
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from agenda.models import Agendamento, StatusAgendamento, TipoCorte

PREFIXO = "Teste Desempenho"

# Ciclo de 4 registros: agendado, concluído, cancelado, concluído.
STATUS_EM_CICLO = [
    StatusAgendamento.AGENDADO,
    StatusAgendamento.CONCLUIDO,
    StatusAgendamento.CANCELADO,
    StatusAgendamento.CONCLUIDO,
]


def banco_e_o_principal(nome_do_banco):
    """True se o caminho aponta para o arquivo padrão do projeto (db.sqlite3)."""
    return Path(str(nome_do_banco)).name == "db.sqlite3"


class Command(BaseCommand):
    help = "Cria agendamentos fictícios (padrão: 200) em um banco de teste, para medir desempenho."

    def add_arguments(self, parser):
        parser.add_argument("--quantidade", type=int, default=200)
        parser.add_argument(
            "--por-dia",
            type=int,
            default=10,
            dest="por_dia",
            help="Quantos agendamentos por dia (use 200 para concentrar tudo em um dia).",
        )
        parser.add_argument(
            "--data-inicial",
            default="2030-01-01",
            dest="data_inicial",
            help="Primeiro dia dos dados fictícios, no formato AAAA-MM-DD.",
        )
        parser.add_argument(
            "--permitir-banco-principal",
            action="store_true",
            dest="permitir_principal",
            help="Autoriza rodar no db.sqlite3. Não recomendado.",
        )

    def handle(self, *args, **opcoes):
        quantidade = opcoes["quantidade"]
        por_dia = opcoes["por_dia"]

        if not 1 <= quantidade <= 1000:
            raise CommandError("A quantidade precisa estar entre 1 e 1000.")
        if not 1 <= por_dia <= 200:
            raise CommandError("O valor de --por-dia precisa estar entre 1 e 200.")
        try:
            primeiro_dia = date.fromisoformat(opcoes["data_inicial"])
            primeiro_dia + timedelta(days=(quantidade - 1) // por_dia)
        except (ValueError, OverflowError):
            raise CommandError("Use uma --data-inicial válida no formato AAAA-MM-DD.")

        nome_do_banco = connection.settings_dict["NAME"]
        if banco_e_o_principal(nome_do_banco) and not opcoes["permitir_principal"]:
            raise CommandError(
                "Este comando recusa rodar no banco principal (db.sqlite3), para não "
                "misturar dados fictícios com dados reais. Defina outro arquivo em "
                "DJANGO_DB_PATH, rode 'migrate' nele e tente de novo."
            )

        if Agendamento.objects.filter(nome_cliente__startswith=PREFIXO).exists():
            raise CommandError(
                "Já existem registros de teste neste banco. Apague o arquivo do banco "
                "de teste, rode 'migrate' de novo e repita o comando."
            )

        # Durações pequenas para caber muitos agendamentos no mesmo dia.
        duracao = max(1, min(30, 1200 // por_dia))
        inicio_do_dia = 8 * 60 if 8 * 60 + por_dia * duracao <= 24 * 60 else 0

        try:
            with transaction.atomic():
                for i in range(quantidade):
                    dia = primeiro_dia + timedelta(days=i // por_dia)
                    minutos = inicio_do_dia + (i % por_dia) * duracao
                    Agendamento(
                        nome_cliente=f"{PREFIXO} {i + 1:03d}",
                        data=dia,
                        horario=time(minutos // 60, minutos % 60),
                        duracao_minutos=duracao,
                        tipo=TipoCorte.PAGO if (i // 2) % 2 == 0 else TipoCorte.GRATUITO,
                        status=STATUS_EM_CICLO[i % 4],
                    ).save()
        except ValidationError as erro:
            raise CommandError(
                "Os dados de teste conflitam com agendamentos já existentes: "
                + " ".join(erro.messages)
            )

        total = Agendamento.objects.count()
        self.stdout.write(f"Banco usado: {nome_do_banco}")
        self.stdout.write(f"Criados {quantidade} agendamentos fictícios ({por_dia} por dia).")
        self.stdout.write(f"Total de agendamentos no banco agora: {total}.")
        for status in StatusAgendamento:
            quantos = Agendamento.objects.filter(
                nome_cliente__startswith=PREFIXO, status=status
            ).count()
            self.stdout.write(f"  {status.label}: {quantos}")
        self.stdout.write(
            "Gratuitos concluídos: "
            f"{Agendamento.objects.gratuitos_concluidos().count()}"
        )
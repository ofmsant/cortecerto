"""Prepara um banco de DEMONSTRAÇÃO com dados fictícios para a validação.

Cria o cenário usado nas três tarefas do roteiro (docs/validacao/roteiro.md):

  - Cliente C e Cliente D: cortes gratuitos já concluídos (a contagem começa em 2);
  - Cliente A (09:00) e Cliente B (10:00): agendados no dia da demonstração.

Todos têm duração de 60 minutos. Os nomes e os dados são fictícios e não
representam clientes reais. Use SEMPRE um banco separado e vazio, por exemplo:

    $env:DJANGO_DB_PATH="$PWD\\validacao-rodada1.sqlite3"

Para repetir o cenário (segunda rodada), apague o arquivo do banco, rode
"migrate" e crie o usuário de teste de novo.
"""
from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from agenda.management.commands.popular_desempenho import banco_e_o_principal
from agenda.models import Agendamento, StatusAgendamento, TipoCorte

DURACAO_MINUTOS = 60


def cenario(dia):
    """Lista de (nome, data, horário, tipo, status) do cenário de demonstração."""
    return [
        ("Cliente C", dia - timedelta(days=4), time(9, 0), TipoCorte.GRATUITO, StatusAgendamento.CONCLUIDO),
        ("Cliente D", dia - timedelta(days=3), time(9, 0), TipoCorte.GRATUITO, StatusAgendamento.CONCLUIDO),
        ("Cliente A", dia, time(9, 0), TipoCorte.PAGO, StatusAgendamento.AGENDADO),
        ("Cliente B", dia, time(10, 0), TipoCorte.GRATUITO, StatusAgendamento.AGENDADO),
    ]


class Command(BaseCommand):
    help = "Cria os dados fictícios do cenário de validação em um banco de demonstração vazio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-demonstracao",
            default="2026-11-14",
            dest="data_demonstracao",
            help="Dia dos agendamentos das 9h e das 10h, no formato AAAA-MM-DD.",
        )
        parser.add_argument(
            "--permitir-banco-principal",
            action="store_true",
            dest="permitir_principal",
            help="Autoriza rodar no db.sqlite3. Não recomendado.",
        )

    def handle(self, *args, **opcoes):
        try:
            dia = date.fromisoformat(opcoes["data_demonstracao"])
            dia - timedelta(days=4)
        except (ValueError, OverflowError):
            raise CommandError("Use uma --data-demonstracao válida no formato AAAA-MM-DD.")

        nome_do_banco = connection.settings_dict["NAME"]
        if banco_e_o_principal(nome_do_banco) and not opcoes["permitir_principal"]:
            raise CommandError(
                "Este comando recusa rodar no banco principal (db.sqlite3). Defina outro "
                "arquivo em DJANGO_DB_PATH, rode 'migrate' nele e tente de novo."
            )

        if Agendamento.objects.exists():
            raise CommandError(
                "O banco de demonstração precisa estar vazio. Apague o arquivo do banco "
                "de teste, rode 'migrate' de novo e repita o comando."
            )

        try:
            with transaction.atomic():
                for nome, data, horario, tipo, status in cenario(dia):
                    Agendamento(
                        nome_cliente=nome,
                        data=data,
                        horario=horario,
                        duracao_minutos=DURACAO_MINUTOS,
                        tipo=tipo,
                        status=status,
                    ).save()
        except ValidationError as erro:
            raise CommandError("Não foi possível criar o cenário: " + " ".join(erro.messages))

        self.stdout.write(f"Banco usado: {nome_do_banco}")
        self.stdout.write("Cenário de demonstração criado com dados fictícios:")
        for nome, data, horario, tipo, status in cenario(dia):
            self.stdout.write(
                f"  {nome}: {data:%d/%m/%Y} {horario:%H:%M}, {DURACAO_MINUTOS} min, "
                f"{tipo.label}, {status.label}"
            )
        self.stdout.write(
            "Cortes gratuitos concluídos no início: "
            f"{Agendamento.objects.gratuitos_concluidos().count()}"
        )
        self.stdout.write(
            "Lembrete: configure CORTECERTO_PERIODOS_ATENDIMENTO antes de iniciar o "
            "servidor, senão a agenda não mostra horários livres."
        )
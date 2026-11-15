"""Períodos de atendimento e intervalos livres da agenda.

Os períodos NÃO têm valor padrão. Eles vêm da variável de ambiente
CORTECERTO_PERIODOS_ATENDIMENTO (settings.PERIODOS_ATENDIMENTO), no formato
"HH:MM-HH:MM", separados por vírgula. Enquanto estiver vazia, nenhum horário
livre é calculado.

Os valores são minutos desde 00:00 (ex.: 09:30 = 570).
"""

import re
from collections import namedtuple

from django.conf import settings

from .models import Agendamento

Intervalo = namedtuple("Intervalo", ["inicio", "fim"])

_PADRAO = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


def formatar_minutos(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def interpretar_periodos(texto):
    """Converte o texto de configuração em uma lista ordenada de Intervalo.

    Levanta ValueError se o formato for inválido, se um período terminar antes
    de começar ou se houver períodos sobrepostos.
    """
    periodos = []
    for trecho in (texto or "").split(","):
        trecho = trecho.strip()
        if not trecho:
            continue

        correspondencia = _PADRAO.match(trecho)
        if not correspondencia:
            raise ValueError(
                f"Período inválido: '{trecho}'. Use o formato HH:MM-HH:MM."
            )

        h1, m1, h2, m2 = (
            int(valor) for valor in correspondencia.groups()
        )

        if (
            h1 > 23
            or m1 > 59
            or h2 > 24
            or m2 > 59
            or (h2 == 24 and m2 != 0)
        ):
            raise ValueError(f"Horário inexistente em '{trecho}'.")

        inicio = h1 * 60 + m1
        fim = h2 * 60 + m2

        if fim <= inicio:
            raise ValueError(
                f"O período '{trecho}' precisa terminar depois de começar."
            )

        periodos.append(Intervalo(inicio, fim))

    periodos.sort()

    for anterior, atual in zip(periodos, periodos[1:]):
        if atual.inicio < anterior.fim:
            raise ValueError(
                "Os períodos de atendimento não podem se sobrepor."
            )

    return periodos


def periodos_configurados():
    return interpretar_periodos(
        getattr(settings, "PERIODOS_ATENDIMENTO", "")
    )


def intervalos_livres(data):
    """Calcula intervalos livres nos períodos configurados para a data.

    Agendados e concluídos ocupam horário. Cancelados não são descontados.
    """
    ocupados = sorted(
        (
            agendamento.inicio_minutos,
            agendamento.fim_minutos,
        )
        for agendamento in (
            Agendamento.objects.ocupando_horario().filter(data=data)
        )
    )

    livres = []

    for periodo in periodos_configurados():
        cursor = periodo.inicio

        for inicio, fim in ocupados:
            if fim <= cursor:
                continue

            if inicio >= periodo.fim:
                break

            if inicio > cursor:
                livres.append(Intervalo(cursor, inicio))

            cursor = max(cursor, fim)

            if cursor >= periodo.fim:
                break

        if cursor < periodo.fim:
            livres.append(Intervalo(cursor, periodo.fim))

    return livres
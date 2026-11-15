from datetime import date, time, timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .disponibilidade import formatar_minutos, intervalos_livres, periodos_configurados
from .forms import AgendamentoForm
from .models import Agendamento, StatusAgendamento

ITENS_POR_PAGINA = 25

# Todas as views deste módulo são privadas: o LoginRequiredMiddleware exige
# login em qualquer view que não seja marcada com login_not_required.


def _url_agenda(dia):
    return f"{reverse('agenda:inicio')}?data={dia.isoformat()}"


def _ler_data(request):
    """Lê ?data=AAAA-MM-DD. Sem o parâmetro, usa hoje. Devolve (data, invalida)."""
    texto = request.GET.get("data", "").strip()
    if not texto:
        return timezone.localdate(), False
    try:
        return date.fromisoformat(texto), False
    except ValueError:
        return timezone.localdate(), True


def _ler_horario(request):
    """Lê ?horario=HH:MM (usado pelo link 'Agendar às ...'). Devolve time ou None."""
    texto = request.GET.get("horario", "").strip()
    if not texto:
        return None
    try:
        return time.fromisoformat(texto).replace(second=0, microsecond=0)
    except ValueError:
        return None


def _vizinho(dia, deslocamento):
    try:
        return dia + timedelta(days=deslocamento)
    except OverflowError:
        return None


@require_http_methods(["GET", "HEAD", "POST"])
def agenda(request):
    dia, data_invalida = _ler_data(request)
    if data_invalida:
        messages.warning(request, "Data inválida. Mostrando a agenda de hoje.")

    if request.method == "POST":
        formulario = AgendamentoForm(request.POST)
        if formulario.is_valid():
            try:
                agendamento = formulario.save()
            except ValidationError as erro:
                # Conflito detectado no momento de gravar (por exemplo, envio duplicado).
                formulario.add_error(None, erro)
            except IntegrityError:
                formulario.add_error(
                    None, "Este horário acabou de ser ocupado. Escolha outro horário."
                )
            else:
                messages.success(
                    request,
                    f"Agendamento de {agendamento.nome_cliente} registrado para "
                    f"{agendamento.data:%d/%m/%Y} às {agendamento.horario:%H:%M}.",
                )
                return redirect(_url_agenda(agendamento.data))
    else:
        inicial = {"data": dia}
        horario = _ler_horario(request)
        if horario is not None:
            inicial["horario"] = horario
        formulario = AgendamentoForm(initial=inicial)

    itens = [
        {"ag": agendamento, "fim": formatar_minutos(agendamento.fim_minutos)}
        for agendamento in Agendamento.objects.do_dia(dia)
    ]

    try:
        periodos_definidos = bool(periodos_configurados())
        periodos_invalidos = False
        livres = [
            {
                "inicio": formatar_minutos(intervalo.inicio),
                "fim": formatar_minutos(intervalo.fim),
                "minutos": intervalo.fim - intervalo.inicio,
            }
            for intervalo in intervalos_livres(dia)
        ]
    except ValueError:
        periodos_definidos = False
        periodos_invalidos = True
        livres = []

    contexto = {
        "dia": dia,
        "eh_hoje": dia == timezone.localdate(),
        "anterior": _vizinho(dia, -1),
        "proximo": _vizinho(dia, 1),
        "itens": itens,
        "livres": livres,
        "periodos_definidos": periodos_definidos,
        "periodos_invalidos": periodos_invalidos,
        "formulario": formulario,
        "url_formulario": _url_agenda(dia),
    }
    return render(request, "agenda/inicio.html", contexto)


@require_POST
def concluir(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    try:
        concluido_agora = agendamento.concluir()
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    else:
        if concluido_agora:
            messages.success(
                request, f"Atendimento de {agendamento.nome_cliente} concluído."
            )
        else:
            messages.info(
                request,
                f"O atendimento de {agendamento.nome_cliente} já estava concluído.",
            )
    return redirect(_url_agenda(agendamento.data))


@require_http_methods(["GET", "HEAD", "POST"])
def cancelar(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if request.method == "POST":
        try:
            cancelado_agora = agendamento.cancelar()
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
        else:
            if cancelado_agora:
                messages.success(
                    request,
                    f"Agendamento de {agendamento.nome_cliente} cancelado. "
                    "O registro foi mantido no histórico.",
                )
            else:
                messages.info(
                    request,
                    f"O agendamento de {agendamento.nome_cliente} já estava cancelado.",
                )
        return redirect(_url_agenda(agendamento.data))

    # GET: página de confirmação (só faz sentido para agendamentos ativos).
    if agendamento.status == StatusAgendamento.CONCLUIDO:
        messages.info(
            request,
            "Atendimentos concluídos permanecem no histórico e não podem ser cancelados.",
        )
        return redirect(_url_agenda(agendamento.data))
    if agendamento.status == StatusAgendamento.CANCELADO:
        messages.info(request, "Este agendamento já está cancelado.")
        return redirect(_url_agenda(agendamento.data))

    return render(
        request,
        "agenda/cancelar.html",
        {
            "agendamento": agendamento,
            "fim": formatar_minutos(agendamento.fim_minutos),
            "url_voltar": _url_agenda(agendamento.data),
        },
    )


@require_safe
def historico(request):
    registros = Agendamento.objects.historico().order_by("-data", "-horario", "-pk")
    pagina = Paginator(registros, ITENS_POR_PAGINA).get_page(request.GET.get("pagina"))
    return render(
        request,
        "agenda/historico.html",
        {
            "pagina": pagina,
            # A contagem vem sempre do banco: gratuitos com status concluído.
            "total_gratuitos": Agendamento.objects.gratuitos_concluidos().count(),
        },
    )
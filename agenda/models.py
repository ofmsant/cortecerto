from datetime import date, time

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone

MINUTOS_NO_DIA = 24 * 60


class TipoCorte(models.TextChoices):
    PAGO = "pago", "Pago"
    GRATUITO = "gratuito", "Gratuito"


class StatusAgendamento(models.TextChoices):
    AGENDADO = "agendado", "Agendado"
    CONCLUIDO = "concluido", "Concluído"
    CANCELADO = "cancelado", "Cancelado"


# Agendado e concluído ocupam o horário. Somente o cancelado o libera.
STATUS_QUE_OCUPAM_HORARIO = [
    StatusAgendamento.AGENDADO.value,
    StatusAgendamento.CONCLUIDO.value,
]


class AgendamentoQuerySet(models.QuerySet):
    def do_dia(self, data):
        return self.filter(data=data)

    def ocupando_horario(self):
        return self.filter(status__in=STATUS_QUE_OCUPAM_HORARIO)

    def gratuitos_concluidos(self):
        """Base da contagem de cortes gratuitos realizados (sempre calculada no banco)."""
        return self.filter(
            tipo=TipoCorte.GRATUITO,
            status=StatusAgendamento.CONCLUIDO,
        )

    def historico(self):
        """Atendimentos concluídos e cancelados, do mais recente para o mais antigo."""
        return self.filter(
            status__in=[
                StatusAgendamento.CONCLUIDO,
                StatusAgendamento.CANCELADO,
            ]
        ).order_by("-data", "-horario")


class Agendamento(models.Model):
    nome_cliente = models.CharField("Nome do cliente", max_length=100)
    data = models.DateField("Data")
    horario = models.TimeField("Horário")
    duracao_minutos = models.PositiveSmallIntegerField(
        "Duração (minutos)",
        validators=[MinValueValidator(1), MaxValueValidator(MINUTOS_NO_DIA)],
    )
    tipo = models.CharField("Tipo de corte", max_length=10, choices=TipoCorte.choices)
    status = models.CharField(
        "Status",
        max_length=10,
        choices=StatusAgendamento.choices,
        default=StatusAgendamento.AGENDADO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = AgendamentoQuerySet.as_manager()

    class Meta:
        ordering = ["data", "horario"]
        verbose_name = "agendamento"
        verbose_name_plural = "agendamentos"
        constraints = [
            # Reforço no banco: dois agendamentos que ocupam horário não podem
            # começar no mesmo instante. A sobreposição parcial é checada em clean().
            models.UniqueConstraint(
                fields=["data", "horario"],
                condition=models.Q(status__in=STATUS_QUE_OCUPAM_HORARIO),
                name="agendamento_inicio_unico_se_ocupa_horario",
            ),
            models.CheckConstraint(
                condition=models.Q(duracao_minutos__gt=0),
                name="agendamento_duracao_positiva",
            ),
        ]

    def __str__(self):
        return f"{self.nome_cliente} em {self.data:%d/%m/%Y} às {self.horario:%H:%M}"

    @property
    def inicio_minutos(self):
        return self.horario.hour * 60 + self.horario.minute

    @property
    def fim_minutos(self):
        return self.inicio_minutos + self.duracao_minutos

    def clean(self):
        super().clean()

        if isinstance(self.nome_cliente, str):
            if self.nome_cliente and not self.nome_cliente.strip():
                raise ValidationError({"nome_cliente": "Informe o nome do cliente."})
            self.nome_cliente = self.nome_cliente.strip()

        # Se algum campo essencial está ausente ou inválido, o erro já foi
        # reportado pela validação do campo e as regras abaixo não se aplicam.
        if not isinstance(self.data, date) or not isinstance(self.horario, time):
            return
        if not isinstance(self.duracao_minutos, int):
            return
        if not 1 <= self.duracao_minutos <= MINUTOS_NO_DIA:
            return

        self.horario = self.horario.replace(second=0, microsecond=0)

        if self.fim_minutos > MINUTOS_NO_DIA:
            raise ValidationError(
                {"duracao_minutos": "O atendimento precisa terminar até 24:00 do mesmo dia."}
            )

        if self.status in STATUS_QUE_OCUPAM_HORARIO:
            outros = Agendamento.objects.ocupando_horario().filter(data=self.data)
            if self.pk:
                outros = outros.exclude(pk=self.pk)
            for outro in outros:
                if (
                    self.inicio_minutos < outro.fim_minutos
                    and outro.inicio_minutos < self.fim_minutos
                ):
                    raise ValidationError(
                        {
                            "horario": (
                                f"Este horário conflita com o agendamento de "
                                f"{outro.nome_cliente} às {outro.horario:%H:%M}."
                            )
                        }
                    )

    def validate_constraints(self, exclude=None):
        # A regra de conflito é verificada em clean(), com mensagem mais clara.
        # As restrições continuam valendo no banco de dados.
        return

    def save(self, *args, **kwargs):
        # A transação (IMMEDIATE no SQLite, ver settings) mantém a checagem de
        # conflito e a gravação juntas.
        with transaction.atomic():
            self.full_clean()
            super().save(*args, **kwargs)

    def _alterar_status(self, novo_status, mensagem_erro):
        """Muda de 'agendado' para o novo status em uma única atualização condicional.

        Devolve True se esta chamada fez a mudança e False se o agendamento já
        estava nesse status (clique repetido ou operação duplicada).
        """
        self.refresh_from_db(fields=["status"])
        if self.status == novo_status:
            return False
        if self.status != StatusAgendamento.AGENDADO:
            raise ValidationError(mensagem_erro)
        alterados = Agendamento.objects.filter(
            pk=self.pk, status=StatusAgendamento.AGENDADO
        ).update(status=novo_status, atualizado_em=timezone.now())
        self.refresh_from_db(fields=["status", "atualizado_em"])
        return alterados == 1

    def concluir(self):
        return self._alterar_status(
            StatusAgendamento.CONCLUIDO,
            "Somente agendamentos ativos podem ser concluídos.",
        )

    def cancelar(self):
        return self._alterar_status(
            StatusAgendamento.CANCELADO,
            "Somente agendamentos ativos podem ser cancelados. "
            "Atendimentos concluídos permanecem no histórico.",
        )
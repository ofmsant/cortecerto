from django.contrib import admin

from .models import Agendamento


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("data", "horario", "duracao_minutos", "nome_cliente", "tipo", "status")
    list_filter = ("status", "tipo", "data")
    search_fields = ("nome_cliente",)
    ordering = ("-data", "-horario")

    def has_delete_permission(self, request, obj=None):
        # Agendamentos não são apagados: o caminho correto é o cancelamento.
        return False
from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Agendamento, TipoCorte


class FormularioLogin(AuthenticationForm):
    """Formulário de login com mensagem genérica.

    A mesma mensagem vale para usuário inexistente, senha errada e usuário
    inativo, para não revelar qual das informações falhou.
    """

    error_messages = {
        "invalid_login": "Usuário ou senha incorretos.",
        "inactive": "Usuário ou senha incorretos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuário"
        self.fields["password"].label = "Senha"


class AgendamentoForm(forms.ModelForm):
    """Formulário de novo agendamento.

    A validação real (campos, limite do nome, conflito de horário) acontece no
    modelo, no servidor. O formulário só apresenta os campos e os erros.
    """

    tipo = forms.ChoiceField(
        label="Tipo de corte",
        choices=TipoCorte.choices,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        error_messages={"required": "Escolha se o corte é pago ou gratuito."},
    )

    class Meta:
        model = Agendamento
        fields = ["nome_cliente", "data", "horario", "duracao_minutos", "tipo"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "horario": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if nome == "tipo":
                continue
            campo.widget.attrs["class"] = "form-control form-control-lg"
            ids = [f"erro-{nome}"]
            if nome == "duracao_minutos":
                ids.insert(0, f"dica-{nome}")
            campo.widget.attrs["aria-describedby"] = " ".join(ids)

        self.fields["nome_cliente"].widget.attrs.update(
            {"autocomplete": "off", "autocapitalize": "words"}
        )
        self.fields["duracao_minutos"].widget.attrs.update(
            {"min": 1, "max": 1440, "inputmode": "numeric"}
        )

    def full_clean(self):
        super().full_clean()
        # Marca visualmente os campos com erro (o texto do erro aparece junto ao campo).
        for nome in self._errors or {}:
            if nome in self.fields and nome != "tipo":
                atributos = self.fields[nome].widget.attrs
                atributos["class"] = f'{atributos.get("class", "")} is-invalid'.strip()
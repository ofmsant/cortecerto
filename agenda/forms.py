from django.contrib.auth.forms import AuthenticationForm


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
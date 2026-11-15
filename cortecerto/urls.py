from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from agenda.forms import FormularioLogin

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Login e logout são as únicas views liberadas do LoginRequiredMiddleware.
    path(
        "entrar/",
        login_not_required(
            LoginView.as_view(
                template_name="registration/login.html",
                authentication_form=FormularioLogin,
                redirect_authenticated_user=True,
            )
        ),
        name="login",
    ),
    # O logout só aceita POST (com token CSRF).
    path("sair/", login_not_required(LogoutView.as_view()), name="logout"),
    path("", include("agenda.urls")),
]
from django.urls import path

from . import views

app_name = "agenda"

urlpatterns = [
    path("", views.agenda, name="inicio"),
    path("historico/", views.historico, name="historico"),
    path("agendamentos/<int:pk>/concluir/", views.concluir, name="concluir"),
    path("agendamentos/<int:pk>/cancelar/", views.cancelar, name="cancelar"),
]
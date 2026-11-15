from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from agenda.models import Agendamento, StatusAgendamento

from .auxiliares import SENHA, criar, dados, url_agenda


@override_settings(SECURE_SSL_REDIRECT=False, PERIODOS_ATENDIMENTO="")
class RotasPrivadasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )
        cls.agendamento = criar()

    def assertExigeLogin(self, resposta, url):
        self.assertRedirects(
            resposta,
            f"{reverse('login')}?next={url}",
            fetch_redirect_response=False,
        )

    def test_get_anonimo_e_redirecionado_ao_login(self):
        urls = [
            reverse("agenda:inicio"),
            reverse("agenda:historico"),
            reverse("agenda:cancelar", args=[self.agendamento.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertExigeLogin(self.client.get(url), url)

    def test_post_anonimo_e_redirecionado_ao_login_e_nao_altera_dados(self):
        alvos = [
            reverse("agenda:inicio"),
            reverse("agenda:concluir", args=[self.agendamento.pk]),
            reverse("agenda:cancelar", args=[self.agendamento.pk]),
        ]
        for url in alvos:
            with self.subTest(url=url):
                resposta = self.client.post(url, dados())
                self.assertExigeLogin(resposta, url)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, StatusAgendamento.AGENDADO)
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_usuario_autenticado_acessa_as_paginas(self):
        self.client.force_login(self.usuario)
        for url in [reverse("agenda:inicio"), reverse("agenda:historico")]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_menu_so_aparece_para_quem_entrou(self):
        anonimo = self.client.get(reverse("login"))
        self.assertNotContains(anonimo, reverse("agenda:historico"))
        self.client.force_login(self.usuario)
        autenticado = self.client.get(reverse("agenda:inicio"))
        self.assertContains(autenticado, reverse("agenda:historico"))
        self.assertContains(autenticado, 'aria-current="page"')


@override_settings(SECURE_SSL_REDIRECT=False, PERIODOS_ATENDIMENTO="")
class CsrfNasOperacoesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def setUp(self):
        self.cliente = Client(enforce_csrf_checks=True)
        self.cliente.force_login(self.usuario)

    def test_criar_sem_token_csrf_e_recusado(self):
        resposta = self.cliente.post(url_agenda(), dados())
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_concluir_sem_token_csrf_e_recusado(self):
        agendamento = criar()
        resposta = self.cliente.post(reverse("agenda:concluir", args=[agendamento.pk]))
        self.assertEqual(resposta.status_code, 403)
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_cancelar_sem_token_csrf_e_recusado(self):
        agendamento = criar()
        resposta = self.cliente.post(reverse("agenda:cancelar", args=[agendamento.pk]))
        self.assertEqual(resposta.status_code, 403)
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, StatusAgendamento.AGENDADO)

    def test_formularios_da_agenda_trazem_token_csrf(self):
        criar()
        resposta = self.cliente.get(url_agenda())
        self.assertContains(resposta, "csrfmiddlewaretoken")
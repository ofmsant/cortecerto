from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(SECURE_SSL_REDIRECT=False)
class EstruturaInicialTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="usuario_teste", password="SenhaDeTeste#2026"
        )
        self.client.force_login(usuario)

    def test_pagina_inicial_responde_com_sucesso(self):
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CorteCerto")

    def test_pagina_inicial_usa_template_base(self):
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertTemplateUsed(resposta, "base.html")
        self.assertContains(resposta, 'lang="pt-br"')
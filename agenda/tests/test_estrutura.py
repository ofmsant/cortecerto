from django.test import TestCase
from django.urls import reverse


class EstruturaInicialTests(TestCase):
    def test_pagina_inicial_responde_com_sucesso(self):
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CorteCerto")

    def test_pagina_inicial_usa_template_base(self):
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertTemplateUsed(resposta, "base.html")
        self.assertContains(resposta, 'lang="pt-br"')

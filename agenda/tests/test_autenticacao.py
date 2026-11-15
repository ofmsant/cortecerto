from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

SENHA = "SenhaDeTeste#2026"
MENSAGEM_GENERICA = "Usuário ou senha incorretos."


@override_settings(SECURE_SSL_REDIRECT=False)
class BaseAutenticacao(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def entrar(self, username="usuario_teste", password=SENHA, **extra):
        return self.client.post(
            reverse("login"),
            {"username": username, "password": password, **extra},
        )


class LoginTests(BaseAutenticacao):
    def test_pagina_de_login_abre_com_os_campos(self):
        resposta = self.client.get(reverse("login"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "registration/login.html")
        self.assertContains(resposta, "Usuário")
        self.assertContains(resposta, "Senha")
        self.assertContains(resposta, "Entrar")
        self.assertContains(resposta, "csrfmiddlewaretoken")

    def test_login_valido_autentica_e_redireciona(self):
        resposta = self.entrar()
        self.assertRedirects(resposta, reverse("agenda:inicio"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_cookie_de_sessao_tem_protecoes(self):
        resposta = self.entrar()
        cookie = resposta.cookies["sessionid"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_login_com_senha_errada_mostra_mensagem_generica(self):
        resposta = self.entrar(password="senha-errada-secreta")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, MENSAGEM_GENERICA)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_senha_digitada_nao_e_exibida_de_volta(self):
        resposta = self.entrar(password="senha-errada-secreta")
        self.assertNotContains(resposta, "senha-errada-secreta")

    def test_mensagem_igual_para_usuario_inexistente_e_senha_errada(self):
        inexistente = self.entrar(username="ninguem", password="qualquer-coisa")
        senha_errada = self.entrar(password="qualquer-coisa")
        self.assertContains(inexistente, MENSAGEM_GENERICA)
        self.assertContains(senha_errada, MENSAGEM_GENERICA)

    def test_usuario_inativo_nao_entra(self):
        get_user_model().objects.create_user(
            username="inativo_teste", password=SENHA, is_active=False
        )
        resposta = self.entrar(username="inativo_teste")
        self.assertContains(resposta, MENSAGEM_GENERICA)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_campos_vazios_mostram_erro_junto_ao_campo(self):
        resposta = self.client.post(reverse("login"), {"username": "", "password": ""})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Este campo é obrigatório.")
        self.assertContains(resposta, 'id="erro-username"')
        self.assertContains(resposta, 'id="erro-password"')

    def test_usuario_autenticado_nao_ve_a_tela_de_login(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("login"))
        self.assertRedirects(resposta, reverse("agenda:inicio"))

    def test_senha_e_armazenada_com_hash(self):
        self.assertNotEqual(self.usuario.password, SENHA)
        self.assertTrue(self.usuario.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(self.usuario.check_password(SENHA))

    def test_destino_interno_informado_em_next_e_respeitado(self):
        destino = reverse("admin:index")
        resposta = self.entrar(next=destino)
        self.assertRedirects(resposta, destino, fetch_redirect_response=False)

    def test_destino_externo_em_next_e_ignorado(self):
        resposta = self.entrar(next="https://site-externo.exemplo/")
        self.assertRedirects(resposta, reverse("agenda:inicio"))


class AcessoTests(BaseAutenticacao):
    def test_paginas_privadas_exigem_login(self):
        for url in [reverse("agenda:inicio")]:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertRedirects(
                    resposta,
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_post_anonimo_em_rota_privada_e_barrado(self):
        resposta = self.client.post(reverse("agenda:inicio"))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta["Location"].startswith(reverse("login")))

    def test_usuario_autenticado_acessa_a_pagina_inicial(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("agenda:inicio"))
        self.assertEqual(resposta.status_code, 200)

    def test_admin_nao_abre_sem_login(self):
        resposta = self.client.get(reverse("admin:index"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("login", resposta["Location"])

    def test_nao_existe_cadastro_publico(self):
        for caminho in ["/cadastro/", "/registrar/", "/register/", "/signup/"]:
            with self.subTest(caminho=caminho):
                self.assertEqual(self.client.get(caminho).status_code, 404)


class LogoutTests(BaseAutenticacao):
    def test_logout_encerra_a_sessao(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse("logout"))
        self.assertRedirects(resposta, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        acesso = self.client.get(reverse("agenda:inicio"))
        self.assertEqual(acesso.status_code, 302)

    def test_logout_nao_aceita_get(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse("logout"))
        self.assertEqual(resposta.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_sem_sessao_nao_quebra(self):
        resposta = self.client.post(reverse("logout"))
        self.assertEqual(resposta.status_code, 302)

    def test_pagina_mostra_botao_de_sair_somente_para_quem_entrou(self):
        anonimo = self.client.get(reverse("login"))
        self.assertNotContains(anonimo, reverse("logout"))
        self.client.force_login(self.usuario)
        autenticado = self.client.get(reverse("agenda:inicio"))
        self.assertContains(autenticado, reverse("logout"))


@override_settings(SECURE_SSL_REDIRECT=False)
class CsrfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="usuario_teste", password=SENHA
        )

    def test_login_sem_token_csrf_e_recusado(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(
            reverse("login"), {"username": "usuario_teste", "password": SENHA}
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertNotIn("_auth_user_id", cliente.session)

    def test_logout_sem_token_csrf_e_recusado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        resposta = cliente.post(reverse("logout"))
        self.assertEqual(resposta.status_code, 403)
        self.assertIn("_auth_user_id", cliente.session)

    def test_pagina_de_erro_csrf_e_amigavel(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(reverse("login"), {})
        self.assertContains(resposta, "Não foi possível concluir a ação", status_code=403)


@override_settings(SECURE_SSL_REDIRECT=False)
class PaginasDeErroTests(TestCase):
    def test_pagina_404_e_amigavel_e_sem_detalhes_tecnicos(self):
        resposta = self.client.get("/pagina-que-nao-existe/")
        self.assertContains(resposta, "Página não encontrada", status_code=404)
        self.assertNotContains(resposta, "Traceback", status_code=404)

    def test_pagina_500_renderiza_mensagem_generica(self):
        conteudo = render_to_string("500.html")
        self.assertIn("Erro interno", conteudo)
        self.assertNotIn("Traceback", conteudo)


class ConfiguracaoDeSegurancaTests(SimpleTestCase):
    def test_login_obrigatorio_por_padrao(self):
        self.assertIn(
            "django.contrib.auth.middleware.LoginRequiredMiddleware",
            settings.MIDDLEWARE,
        )

    def test_protecao_csrf_ativa(self):
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)

    def test_cookies_e_cabecalhos_de_protecao(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.X_FRAME_OPTIONS, "DENY")
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)

    def test_sessao_tem_duracao_limitada(self):
        self.assertGreater(settings.SESSION_COOKIE_AGE, 0)
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, 60 * 60 * 24 * 30)
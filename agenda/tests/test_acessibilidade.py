"""Verificações automáticas de estrutura HTML acessível.

Elas ajudam, mas não substituem a inspeção manual descrita em
docs/acessibilidade-responsividade.md.
"""
import re
from collections import Counter
from datetime import time
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from agenda.models import StatusAgendamento, TipoCorte

from .auxiliares import BaseAgenda, criar, dados, url_agenda


class Analisador(HTMLParser):
    TIPOS_SEM_ROTULO = {"hidden", "submit", "button", "reset", "image"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.viewport = ""
        self.ids = []
        self.rotulos_for = set()
        self.controles = []
        self.descricoes = []
        self.cabecalhos = []
        self.tabindex_positivos = []
        self.acionaveis = []
        self.formularios = []
        self._form = None
        self._coleta = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if "id" in a:
            self.ids.append(a["id"])
        tabindex = a.get("tabindex")
        if tabindex and tabindex.lstrip("-").isdigit() and int(tabindex) > 0:
            self.tabindex_positivos.append(tag)
        if a.get("aria-describedby"):
            self.descricoes.extend(a["aria-describedby"].split())

        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = a.get("content", "")
        elif re.fullmatch(r"h[1-6]", tag):
            self.cabecalhos.append(int(tag[1]))
        elif tag == "label" and a.get("for"):
            self.rotulos_for.add(a["for"])
        elif tag in {"input", "select", "textarea"}:
            tipo = a.get("type", "text") if tag == "input" else tag
            if (
                tipo == "hidden"
                and a.get("name") == "csrfmiddlewaretoken"
                and self._form is not None
            ):
                self._form["csrf"] = True
            if tipo not in self.TIPOS_SEM_ROTULO:
                self.controles.append(
                    {
                        "id": a.get("id"),
                        "tipo": tipo,
                        "aria_label": a.get("aria-label"),
                        "aria_labelledby": a.get("aria-labelledby"),
                    }
                )
        elif tag == "form":
            self._form = {"metodo": a.get("method", "get").lower(), "csrf": False}
        elif tag == "button" or (tag == "a" and "href" in a):
            self._coleta = {"tag": tag, "aria": a.get("aria-label", ""), "texto": ""}

    def handle_data(self, data):
        if self._coleta is not None:
            self._coleta["texto"] += data

    def handle_endtag(self, tag):
        if self._coleta is not None and tag == self._coleta["tag"]:
            self.acionaveis.append(self._coleta)
            self._coleta = None
        elif tag == "form" and self._form is not None:
            self.formularios.append(self._form)
            self._form = None


def verificar_pagina(teste, html):
    a = Analisador()
    a.feed(html)

    teste.assertEqual(a.lang, "pt-br", "A página precisa declarar lang=pt-br.")

    teste.assertEqual(a.cabecalhos.count(1), 1, "Deve haver exatamente um h1.")
    teste.assertEqual(a.cabecalhos[0], 1, "O primeiro título deve ser o h1.")
    for anterior, atual in zip(a.cabecalhos, a.cabecalhos[1:]):
        teste.assertLessEqual(atual, anterior + 1, "Não pule níveis de título.")

    duplicados = [i for i, n in Counter(a.ids).items() if n > 1]
    teste.assertEqual(duplicados, [], "Ids duplicados na página.")

    for controle in a.controles:
        tem_nome = (
            (controle["id"] and controle["id"] in a.rotulos_for)
            or controle["aria_label"]
            or controle["aria_labelledby"]
        )
        teste.assertTrue(tem_nome, f"Campo sem rótulo: {controle}")

    for referencia in a.descricoes:
        teste.assertIn(referencia, a.ids, f"aria-describedby aponta para id inexistente: {referencia}")

    for item in a.acionaveis:
        nome = item["aria"].strip() or item["texto"].strip()
        teste.assertTrue(nome, f"Botão ou link sem nome acessível: {item}")

    teste.assertIn("width=device-width", a.viewport)
    teste.assertNotIn("user-scalable", a.viewport)
    teste.assertNotIn("maximum-scale", a.viewport)

    teste.assertEqual(a.tabindex_positivos, [], "tabindex positivo atrapalha a ordem do foco.")

    for formulario in a.formularios:
        if formulario["metodo"] == "post":
            teste.assertTrue(formulario["csrf"], "Formulário POST sem token CSRF.")

    teste.assertIn("conteudo-principal", a.ids, "O destino do link 'Ir para o conteúdo' não existe.")


class EstruturaDasPaginasTests(BaseAgenda):
    @override_settings(PERIODOS_ATENDIMENTO="08:00-12:00")
    def test_paginas_internas_tem_estrutura_acessivel(self):
        agendamento = criar(nome="Cliente A", horario=time(9, 0), tipo=TipoCorte.PAGO)
        criar(
            nome="Cliente B", horario=time(10, 0), tipo=TipoCorte.GRATUITO,
            status=StatusAgendamento.CONCLUIDO,
        )
        criar(nome="Cliente C", horario=time(11, 0), status=StatusAgendamento.CANCELADO)

        respostas = {
            "agenda": self.client.get(url_agenda()),
            "agenda com campo vazio": self.client.post(url_agenda(), dados(nome_cliente="")),
            "agenda com conflito": self.client.post(url_agenda(), dados(horario="09:30")),
            "historico": self.client.get(reverse("agenda:historico")),
            "confirmacao de cancelamento": self.client.get(
                reverse("agenda:cancelar", args=[agendamento.pk])
            ),
        }
        for nome, resposta in respostas.items():
            with self.subTest(pagina=nome):
                self.assertEqual(resposta.status_code, 200)
                verificar_pagina(self, resposta.content.decode())

    def test_pagina_de_login_tem_estrutura_acessivel(self):
        self.client.logout()
        respostas = {
            "login": self.client.get(reverse("login")),
            "login com campos vazios": self.client.post(
                reverse("login"), {"username": "", "password": ""}
            ),
            "login com senha errada": self.client.post(
                reverse("login"), {"username": "x", "password": "y"}
            ),
        }
        for nome, resposta in respostas.items():
            with self.subTest(pagina=nome):
                self.assertEqual(resposta.status_code, 200)
                verificar_pagina(self, resposta.content.decode())


class RecursosDeAcessibilidadeTests(BaseAgenda):
    def test_campos_do_formulario_sao_marcados_como_obrigatorios(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, "Todos os campos são obrigatórios.")
        self.assertContains(resposta, 'aria-required="true"', count=5)  # 4 campos e o grupo de tipo
        self.assertContains(resposta, 'role="radiogroup"')

    def test_sem_erro_nao_ha_resumo_nem_aria_invalid(self):
        resposta = self.client.get(url_agenda())
        self.assertNotContains(resposta, 'id="resumo-erros"')
        self.assertNotContains(resposta, "aria-invalid")

    def test_erro_gera_resumo_focavel_e_marca_o_campo(self):
        resposta = self.client.post(url_agenda(), dados(nome_cliente=""))
        self.assertContains(resposta, 'id="resumo-erros"')
        self.assertContains(resposta, 'tabindex="-1"')
        self.assertContains(resposta, 'aria-invalid="true"')

    def test_erro_no_tipo_marca_o_grupo_de_opcoes(self):
        resposta = self.client.post(url_agenda(), dados(tipo=""))
        self.assertContains(resposta, "Escolha se o corte é pago ou gratuito.")
        self.assertContains(resposta, 'role="radiogroup" aria-required="true" aria-describedby="erro-tipo" aria-invalid="true"')

    def test_conteudo_principal_recebe_foco_pelo_link_de_atalho(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, 'id="conteudo-principal" class="container py-4" tabindex="-1"')

    def test_navegacao_principal_tem_nome(self):
        resposta = self.client.get(url_agenda())
        self.assertContains(resposta, 'aria-label="Principal"')
        self.assertContains(resposta, 'aria-label="Navegação entre datas"')

    def test_script_leva_o_foco_para_o_resumo_de_erros(self):
        caminho = Path(settings.BASE_DIR) / "static" / "js" / "cortecerto.js"
        conteudo = caminho.read_text(encoding="utf-8")
        self.assertIn("resumo-erros", conteudo)
        self.assertIn(".focus()", conteudo)
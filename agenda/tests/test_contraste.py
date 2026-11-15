"""Contraste calculado pela fórmula da WCAG, com as cores do CSS do projeto."""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


def _linear(canal):
    c = canal / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(cor):
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


BRANCO = "#ffffff"
FUNDO_PAGINA = "#f8f9fa"
FUNDO_CANCELADO = "#f1f3f5"

# (primeiro plano, fundo, mínimo, descrição). Texto comum: 4,5. Componentes: 3.
PARES = [
    ("#212529", BRANCO, 4.5, "texto padrão do Bootstrap sobre branco"),
    ("#212529", FUNDO_PAGINA, 4.5, "texto padrão do Bootstrap sobre o fundo da página"),
    ("#495057", BRANCO, 4.5, "texto de apoio sobre branco"),
    ("#495057", FUNDO_PAGINA, 4.5, "texto de apoio sobre o fundo da página"),
    ("#495057", FUNDO_CANCELADO, 4.5, "texto de apoio sobre item cancelado"),
    (BRANCO, "#1f2a37", 4.5, "cabeçalho e navegação"),
    (BRANCO, "#146c43", 4.5, "selo gratuito"),
    ("#1f2a37", BRANCO, 4.5, "selo pago"),
    ("#052c65", "#cfe2ff", 4.5, "status agendado"),
    ("#0a3622", "#d1e7dd", 4.5, "status concluído"),
    ("#58151c", "#f8d7da", 4.5, "status cancelado"),
    (BRANCO, "#0a58ca", 4.5, "botão primário"),
    (BRANCO, "#084298", 4.5, "botão primário em hover"),
    (BRANCO, "#146c43", 4.5, "botão de concluir"),
    (BRANCO, "#0f5132", 4.5, "botão de concluir em hover"),
    (BRANCO, "#b02a37", 4.5, "botão de cancelar"),
    (BRANCO, "#842029", 4.5, "botão de cancelar em hover"),
    ("#b02a37", BRANCO, 4.5, "contorno de cancelar sobre branco"),
    ("#b02a37", FUNDO_PAGINA, 4.5, "contorno de cancelar e erros sobre o fundo da página"),
    ("#0a58ca", BRANCO, 4.5, "links sobre branco"),
    ("#0a58ca", FUNDO_PAGINA, 4.5, "links sobre o fundo da página"),
    ("#0b5ed7", BRANCO, 3.0, "anel de foco sobre branco"),
    ("#0b5ed7", FUNDO_PAGINA, 3.0, "anel de foco sobre o fundo da página"),
    (BRANCO, "#1f2a37", 3.0, "anel de foco no cabeçalho"),
    ("#146c43", BRANCO, 3.0, "faixa lateral do corte gratuito"),
    ("#1f2a37", BRANCO, 3.0, "faixa lateral do corte pago"),
]

# Cores que o próprio CSS do projeto define (a #212529 vem do Bootstrap).
COR_DO_BOOTSTRAP = {"#212529"}


def ler_css():
    caminho = Path(settings.BASE_DIR) / "static" / "css" / "cortecerto.css"
    return caminho.read_text(encoding="utf-8").lower()


class ContrasteTests(SimpleTestCase):
    def test_formula_confere_com_valores_conhecidos(self):
        self.assertAlmostEqual(contraste("#000000", "#ffffff"), 21.0, places=1)
        self.assertAlmostEqual(contraste("#ffffff", "#ffffff"), 1.0, places=2)
        # O vermelho padrão do Bootstrap fica abaixo de 4,5 sobre o fundo da página.
        self.assertLess(contraste("#dc3545", FUNDO_PAGINA), 4.5)

    def test_todos_os_pares_atingem_o_minimo(self):
        for frente, fundo, minimo, descricao in PARES:
            with self.subTest(descricao=descricao):
                valor = contraste(frente, fundo)
                self.assertGreaterEqual(
                    valor, minimo, f"{descricao}: {frente} sobre {fundo} = {valor:.2f}:1"
                )

    def test_cores_testadas_existem_no_css(self):
        css = ler_css()
        usadas = {c for par in PARES for c in par[:2]} - COR_DO_BOOTSTRAP
        for cor in sorted(usadas):
            with self.subTest(cor=cor):
                self.assertIn(cor, css, f"{cor} não está em cortecerto.css; atualize o teste ou o CSS.")

    def test_css_nao_remove_o_foco_nem_reduz_a_area_de_toque(self):
        css = ler_css()
        self.assertIsNone(re.search(r"outline\s*:\s*(none|0)\b", css))
        self.assertIn("min-height: 44px", css)
        self.assertIn("min-width: 44px", css)
#!/usr/bin/env python
"""Mede o tempo de resposta do CorteCerto em um servidor já em execução.

Mede, com o servidor de teste e o banco de teste (veja docs/desempenho.md):
  1. carregamento da agenda de um dia (GET), já autenticado;
  2. carregamento do histórico (GET);
  3. envio de um novo agendamento (POST, sem seguir o redirecionamento).

Cada operação tem 1 aquecimento (descartado) e N medições (padrão: 5).
Critério: mediana de até 3 s e nenhuma medição acima de 5 s.

O tempo medido é o da resposta HTTP do servidor (HTML), até o último byte lido.
Não inclui renderização no navegador, o Bootstrap vindo da CDN, nem rede móvel.
Usa só a biblioteca padrão do Python.
"""
import argparse
import getpass
import os
import platform
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from http.cookiejar import CookieJar

LIMITE_MEDIANA = 3.0
LIMITE_MAXIMO = 5.0
PADRAO_CSRF = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')


class ErroDeMedicao(Exception):
    pass


class SemRedirecionamento(urllib.request.HTTPRedirectHandler):
    """Não segue redirecionamentos, para medir só a resposta da requisição enviada."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class Resultado:
    nome: str
    tempos: list

    @property
    def mediana(self):
        return statistics.median(self.tempos)

    @property
    def maximo(self):
        return max(self.tempos)

    @property
    def atende(self):
        return self.mediana <= LIMITE_MEDIANA and self.maximo <= LIMITE_MAXIMO


class Cliente:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.cookies = CookieJar()
        self.abridor = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies), SemRedirecionamento()
        )

    def requisitar(self, caminho, dados=None):
        """Devolve (status, corpo, segundos, destino_do_redirecionamento)."""
        url = self.base + caminho
        corpo = None
        if dados is not None:
            corpo = urllib.parse.urlencode(dados).encode()
        requisicao = urllib.request.Request(url, data=corpo)
        if dados is not None:
            requisicao.add_header("Referer", url)
        inicio = time.perf_counter()
        try:
            with self.abridor.open(requisicao, timeout=30) as resposta:
                texto = resposta.read().decode("utf-8", "replace")
                status = resposta.status
                destino = resposta.headers.get("Location")
        except urllib.error.HTTPError as erro:
            texto = erro.read().decode("utf-8", "replace")
            status = erro.code
            destino = erro.headers.get("Location")
        segundos = time.perf_counter() - inicio
        return status, texto, segundos, destino

    def extrair_token(self, texto):
        achado = PADRAO_CSRF.search(texto)
        if not achado:
            raise ErroDeMedicao("Não encontrei o token CSRF na página recebida.")
        return achado.group(1)

    def entrar(self, usuario, senha):
        status, texto, _, destino = self.requisitar("/entrar/")
        if status != 200:
            raise ErroDeMedicao(
                f"A tela de login respondeu {status}"
                + (f" e redirecionou para {destino}" if destino else "")
                + ". Para o teste local, use DJANGO_DEBUG=True e DJANGO_HTTPS=False."
            )
        token = self.extrair_token(texto)
        status, _, _, _ = self.requisitar(
            "/entrar/",
            {
                "username": usuario,
                "password": senha,
                "csrfmiddlewaretoken": token,
                "next": "",
            },
        )
        if status != 302:
            raise ErroDeMedicao(
                "O login foi recusado. Confira o usuário e a senha do banco de teste."
            )

    def carregar(self, caminho):
        status, _, segundos, destino = self.requisitar(caminho)
        if status != 200:
            raise ErroDeMedicao(
                f"GET {caminho} respondeu {status}"
                + (f" e redirecionou para {destino}" if destino else "")
                + "."
            )
        return segundos


class Envio:
    """Cada chamada envia um agendamento novo, em um horário livre do dia de envio."""

    def __init__(self, cliente, data_envio):
        self.cliente = cliente
        self.data_envio = data_envio
        self.indice = 0

    def __call__(self):
        caminho = f"/?data={self.data_envio}"
        _, pagina, _, _ = self.cliente.requisitar(caminho)
        token = self.cliente.extrair_token(pagina)
        minutos = 8 * 60 + self.indice * 10
        self.indice += 1
        dados = {
            "csrfmiddlewaretoken": token,
            "nome_cliente": f"Teste Desempenho Envio {self.indice}",
            "data": self.data_envio,
            "horario": f"{minutos // 60:02d}:{minutos % 60:02d}",
            "duracao_minutos": "5",
            "tipo": "pago",
        }
        status, _, segundos, _ = self.cliente.requisitar(caminho, dados)
        if status != 302:
            raise ErroDeMedicao(
                f"O envio não foi aceito (status {status}). Se você já rodou este "
                "script neste banco, use outra data com --data-envio."
            )
        return segundos


def medir(nome, funcao, repeticoes):
    funcao()  # aquecimento, descartado
    return Resultado(nome, [funcao() for _ in range(repeticoes)])


def imprimir_relatorio(resultados, argumentos):
    print("## Resultado da medição\n")
    print(f"- Data e hora: {datetime.now():%d/%m/%Y %H:%M}")
    print(f"- Sistema: {platform.platform()}")
    print(f"- Python: {platform.python_version()}")
    print(f"- Servidor medido: {argumentos.base}")
    print(f"- Dia consultado na agenda: {argumentos.data_agenda}")
    print(f"- Repetições por operação: {argumentos.repeticoes} (após 1 aquecimento)")
    print(
        f"- Critério: mediana até {LIMITE_MEDIANA:g} s e nenhuma medição acima de "
        f"{LIMITE_MAXIMO:g} s\n"
    )
    print("| Operação | Medições (s) | Mediana (s) | Máximo (s) | Critério |")
    print("|---|---|---|---|---|")
    for r in resultados:
        medicoes = "; ".join(f"{t:.3f}" for t in r.tempos)
        veredito = "atendido" if r.atende else "NÃO atendido"
        print(f"| {r.nome} | {medicoes} | {r.mediana:.3f} | {r.maximo:.3f} | {veredito} |")
    print(
        "\nObservação: tempo de resposta HTTP do servidor local, sem renderização no "
        "navegador, sem a CDN do Bootstrap e sem rede móvel."
    )


def ler_argumentos():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--senha", help="Se omitida, usa CORTECERTO_SENHA ou pergunta.")
    parser.add_argument("--data-agenda", default="2030-01-01", dest="data_agenda")
    parser.add_argument("--data-envio", default="2031-01-01", dest="data_envio")
    parser.add_argument("--repeticoes", type=int, default=5)
    return parser.parse_args()


def principal():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argumentos = ler_argumentos()
    senha = (
        argumentos.senha
        or os.environ.get("CORTECERTO_SENHA")
        or getpass.getpass("Senha do usuário de teste: ")
    )
    cliente = Cliente(argumentos.base)
    n = argumentos.repeticoes
    try:
        cliente.entrar(argumentos.usuario, senha)
        resultados = [
            medir(
                "Agenda do dia (GET)",
                lambda: cliente.carregar(f"/?data={argumentos.data_agenda}"),
                n,
            ),
            medir("Histórico (GET)", lambda: cliente.carregar("/historico/"), n),
            medir(
                "Envio de agendamento (POST)", Envio(cliente, argumentos.data_envio), n
            ),
        ]
    except ErroDeMedicao as erro:
        print(f"Medição interrompida: {erro}")
        return 2
    except OSError as erro:
        print(
            f"Não foi possível falar com {argumentos.base}: {erro}. "
            "O servidor (runserver) está em execução?"
        )
        return 2

    imprimir_relatorio(resultados, argumentos)
    return 0 if all(r.atende for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(principal())
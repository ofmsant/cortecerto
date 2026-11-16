# Integração contínua (GitHub Actions)

O workflow está em `.github/workflows/ci.yml`. Ele roda os testes automaticamente
no GitHub, em um computador limpo (Ubuntu), sem nada da máquina do desenvolvedor.

## O que ele faz

Em todo `push` na `main`, em todo pull request para a `main` e quando disparado
manualmente:

1. baixa o código;
2. instala o Python 3.12 e as dependências de `requirements.txt`;
3. roda `python manage.py check`;
4. roda `python manage.py makemigrations --check --dry-run` (falha se o modelo mudou
   sem migração);
5. roda `python manage.py migrate --noinput`;
6. roda `python manage.py test`.

Se qualquer passo falhar, o job termina com falha e o GitHub marca a execução com um
X vermelho.

## Configuração de teste

O workflow define variáveis de ambiente fictícias, só para o CI:

| Variável | Valor | Motivo |
|---|---|---|
| `DJANGO_SECRET_KEY` | chave fictícia | o projeto não inicia sem chave |
| `DJANGO_DEBUG` | `True` | evita as exigências de produção durante os testes |
| `DJANGO_HTTPS` | `False` | sem isso, o redirecionamento para HTTPS quebra o cliente de testes |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | hosts usados nos testes |

Nenhum segredo real é usado. A chave do workflow não protege nada e não deve ser
copiada para outro ambiente.

## Como consultar o resultado

1. Abra o repositório no GitHub.
2. Clique na aba **Actions**.
3. Clique na execução mais recente do workflow **Testes**.
4. Clique no job **Verificações e testes (Python 3.12)** para ver cada passo.
5. Um passo que falhou aparece em vermelho. Clique nele para ler a saída completa.

Também aparece uma marca ao lado de cada commit (verde, vermelho ou amarelo) na lista
de commits da branch.

## Como disparar manualmente

Aba **Actions**, workflow **Testes**, botão **Run workflow**, branch `main`.

## Como conferir que a falha é detectada (opcional, sem mexer na main)

1. `git switch -c teste-ci-falha`
2. Em `agenda/tests/test_ci_falha.py`, crie um teste que sempre falha:

       from django.test import SimpleTestCase

       class FalhaDeProposito(SimpleTestCase):
           def test_falha(self):
               self.fail("Falha proposital para conferir o CI.")

3. `git add agenda/tests/test_ci_falha.py`, `git commit -m "test: falha proposital para conferir o CI"` e `git push -u origin teste-ci-falha`
4. Na aba Actions, a execução dessa branch deve terminar em vermelho. (O workflow só
   roda em push na `main` e em pull requests, então abra um pull request dessa branch
   para a `main` para disparar. Não faça o merge.)
5. Feche o pull request sem fazer merge, volte para a `main` (`git switch main`) e
   apague a branch (`git branch -D teste-ci-falha` e
   `git push origin --delete teste-ci-falha`).

## Resultados registrados (preencher)

| Item | Valor |
|---|---|
| Hash do commit testado | |
| Data e hora da execução | |
| Resultado | |
| Duração aproximada | |
| Falha proposital detectada (se o teste opcional foi feito) | |

## Limitações

- O CI só prova que os testes passam no ambiente do GitHub (Ubuntu, Python 3.12).
  Não mede desempenho, não audita acessibilidade e não substitui a verificação manual.
- Não há proteção de branch configurada. Isso é uma configuração do repositório, não
  do código.
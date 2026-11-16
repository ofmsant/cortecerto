# Integração contínua (GitHub Actions)

O workflow está em `.github/workflows/ci.yml`. Ele executa as verificações e os testes automaticamente no GitHub, em um ambiente Ubuntu separado da máquina do desenvolvedor.

## O que o workflow faz

Em todo `push` na `main`, em todo pull request para a `main` e quando disparado manualmente:

1. baixa o código do repositório;
2. instala o Python 3.12 e as dependências de `requirements.txt`;
3. executa `python manage.py check`;
4. executa `python manage.py makemigrations --check --dry-run`;
5. aplica as migrações com `python manage.py migrate --noinput`;
6. executa os testes automatizados com `python manage.py test`.

Se uma etapa falhar, o job termina com falha e a execução é marcada como malsucedida no GitHub Actions.

## Configuração do ambiente de teste

O workflow define as seguintes variáveis de ambiente:

| Variável | Valor | Finalidade |
|---|---|---|
| `DJANGO_SECRET_KEY` | Chave fictícia | Permite inicializar o Django no ambiente de teste |
| `DJANGO_DEBUG` | `True` | Ativa o modo de depuração no CI |
| `DJANGO_HTTPS` | `False` | Evita redirecionamentos HTTPS durante os testes |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Define os hosts aceitos no ambiente de teste |

A chave é fictícia, não é um segredo real e não deve ser utilizada fora do CI. Nenhuma credencial de produção é necessária para executar o workflow.

## Como consultar o resultado

1. Abra o repositório no GitHub.
2. Acesse a aba **Actions**.
3. Abra a execução desejada do workflow **Testes**.
4. Selecione o job **Verificações e testes (Python 3.12)**.
5. Abra cada etapa para consultar a saída completa.

Uma execução verde indica que as etapas do workflow terminaram com sucesso. Uma execução vermelha indica que pelo menos uma etapa falhou. Consulte o log da etapa que falhou para identificar a causa.

## Como disparar manualmente

1. Acesse a aba **Actions** do repositório.
2. Selecione o workflow **Testes**.
3. Clique em **Run workflow**.
4. Escolha a branch `main` e confirme a execução.

## Como conferir se uma falha é detectada (opcional)

Esse teste é opcional e não deve ser realizado diretamente na branch `main`.

1. Crie uma branch separada com `git switch -c teste-ci-falha`.
2. Crie o arquivo `agenda/tests/test_ci_falha.py` com o seguinte conteúdo:

   ```python
   from django.test import SimpleTestCase


   class FalhaDeProposito(SimpleTestCase):
       def test_falha(self):
           self.fail("Falha proposital para conferir o CI.")
   ```

3. Adicione e envie o teste para a branch:

   ```powershell
   git add agenda/tests/test_ci_falha.py
   git commit -m "test: falha proposital para conferir o CI"
   git push -u origin teste-ci-falha
   ```

4. Abra um pull request da branch `teste-ci-falha` para `main`. O workflow está configurado para executar em pull requests direcionados à `main`. A execução deverá falhar por causa do teste proposital.
5. Feche o pull request sem fazer merge.
6. Volte para a branch principal e exclua a branch de teste:

   ```powershell
   git switch main
   git branch -D teste-ci-falha
   git push origin --delete teste-ci-falha
   ```

Esse procedimento não foi realizado nas execuções registradas abaixo.

## Resultados das execuções

### Primeira execução

| Item | Valor |
|---|---|
| Hash do commit testado | `07785d3` |
| Data | 15/11/2026 |
| Duração aproximada | 22 segundos |
| Resultado | Pendente de confirmação no histórico da execução |
| Avisos registrados | Depreciação do Node.js 20 e migração do `ubuntu-latest` |
| Falha proposital detectada | Não testada |

### Execução após a atualização do workflow

| Item | Valor |
|---|---|
| Hash do commit testado | `219fbb660e8cbed7ec9caba24be36d68e22aba1b` |
| Data | 15/11/2026 |
| Branch | `main` |
| Duração aproximada | 38 segundos |
| Resultado | Success |
| Falha proposital detectada | Não testada |

A segunda execução confirmou que o workflow atualizado foi executado com sucesso. O arquivo de workflow foi atualizado para utilizar `ubuntu-24.04`, `actions/checkout@v5` e `actions/setup-python@v6`.

Os avisos da primeira execução não comprovam que a execução falhou. Para confirmar se foram eliminados, é necessário consultar as anotações da execução posterior.

## Limitações

- O CI verifica o projeto no ambiente definido pelo workflow, com Ubuntu e Python 3.12. Não substitui as verificações manuais realizadas no Windows.
- O CI não mede desempenho, não executa auditorias Lighthouse e não substitui uma auditoria de acessibilidade.
- Nenhuma porcentagem de cobertura de testes é declarada, pois ela não foi medida.
- A execução do teste proposital de falha não foi realizada.
- A configuração do workflow não habilita, por si só, regras de proteção da branch. A proteção da branch é uma configuração separada do repositório.

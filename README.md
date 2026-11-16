# CorteCerto

Sistema web para organizar os agendamentos de um barbeiro autônomo, consultar horários livres e acompanhar os cortes pagos e gratuitos realizados.

## Sobre o projeto

O CorteCerto é um MVP desenvolvido na disciplina Projeto de Software para apoiar um barbeiro autônomo que organiza seus atendimentos pelo WhatsApp. A proposta centraliza a agenda e facilita o acompanhamento dos cortes gratuitos oferecidos à comunidade.

**Público-alvo:** o barbeiro autônomo, usuário direto, com uso prioritário pelo celular, e os clientes pagantes e as pessoas atendidas gratuitamente, que são os beneficiados.

O projeto se relaciona ao **ODS 8 (Trabalho Decente e Crescimento Econômico)**, especialmente à meta 8.3, por apoiar a organização de uma atividade produtiva autônoma. O impacto social ainda não foi medido.

## Funcionalidades

| Requisito | Descrição                                                                          | Situação             |
| --------- | ---------------------------------------------------------------------------------- | -------------------- |
| RF01      | Cadastrar agendamentos com nome, data, horário, duração e tipo de corte.           | Implementado         |
| RF02      | Consultar a agenda diária e os horários livres.                                    | Implementado         |
| RF03      | Concluir atendimentos, consultar o histórico e contar cortes gratuitos concluídos. | Implementado         |
| RF04      | Cancelar agendamentos sem excluir seus registros.                                  | Implementado         |
| RF05      | Cadastrar dias e horários de disponibilidade pela interface.                       | **Não implementado** |

Os horários livres dependem dos períodos configurados em variável de ambiente. Isso não implementa o RF05.

O MVP não possui agendamento público para clientes, integração com WhatsApp, pagamentos online nem limite de tentativas de login.

## Tecnologias e arquitetura

- Python 3.12 e Django 5.2
- SQLite
- HTML, CSS, templates Django e Bootstrap 5.3 via CDN
- Git e GitHub Actions

A aplicação utiliza uma arquitetura monolítica em camadas, seguindo o padrão Model-View-Template (MVT), com o projeto de configuração `cortecerto` e o aplicativo `agenda`. As regras de negócio e validações ficam no modelo `Agendamento`; os cálculos de disponibilidade ficam em `agenda/disponibilidade.py`.

## Instalação e execução

Pré-requisitos: Python 3.12, Git e acesso à internet para instalar dependências e carregar o Bootstrap.

Clone o repositório pelo endereço disponibilizado na página do projeto e entre na pasta `CorteCerto`.

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux e macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Para uso local, com `DJANGO_DEBUG=True`, os valores do `.env.example` já funcionam. Em outro ambiente, ajuste o `.env` conforme a seção "Configuração". Em seguida, nos dois sistemas, execute:

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. O servidor `runserver` é destinado ao desenvolvimento local.

A conta de acesso é criada pelo `createsuperuser`. Não há cadastro público: o sistema é usado por uma única conta.

## Configuração

O arquivo `.env.example` apresenta as variáveis disponíveis. Copie-o para `.env` e ajuste os valores necessários. **Não envie `.env` ao GitHub.**

| Variável                          | Finalidade                                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `DJANGO_SECRET_KEY`               | Chave secreta do Django. Com `DJANGO_DEBUG=False`, a chave de exemplo é recusada; utilize uma chave própria. |
| `DJANGO_DEBUG`                    | Ativa ou desativa o modo de depuração.                                                                       |
| `DJANGO_ALLOWED_HOSTS`            | Hosts permitidos, separados por vírgula.                                                                     |
| `DJANGO_CSRF_TRUSTED_ORIGINS`     | Origens confiáveis para CSRF, quando necessárias.                                                            |
| `DJANGO_DB_PATH`                  | Caminho opcional do banco SQLite.                                                                            |
| `DJANGO_HTTPS`                    | Controla as configurações de HTTPS e cookies seguros.                                                        |
| `DJANGO_ADMIN_URL`                | Endereço do administrador; padrão `admin/`.                                                                  |
| `CORTECERTO_PERIODOS_ATENDIMENTO` | Períodos utilizados no cálculo dos horários livres.                                                          |

Os períodos de atendimento usam o formato `HH:MM-HH:MM`, separados por vírgula. Exemplo:

```dotenv
CORTECERTO_PERIODOS_ATENDIMENTO=09:00-12:00,13:00-18:00
```

Ajuste os horários conforme a rotina desejada. Se a variável estiver vazia, nenhum horário livre será calculado.

## Regras da agenda

- Agendamentos ativos e concluídos ocupam o horário; cancelados não ocupam.
- A duração é informada em minutos, de 1 a 1440, e o atendimento deve terminar até 24:00 do mesmo dia.
- O sistema aceita datas passadas e horários fora dos períodos de atendimento.
- A conclusão e o cancelamento preservam o registro; atendimentos concluídos não podem ser cancelados.
- Conflitos de horário são verificados no servidor, com reforço de integridade no banco de dados.

## Testes e integração contínua

Execute os testes automatizados com:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

O GitHub Actions executa essas verificações, as migrações e a suíte de testes em pushes para `main`, pull requests destinados a `main` e execuções manuais.

## Segurança

O projeto exige autenticação por padrão, utiliza proteção CSRF, valida dados no servidor e preserva os registros cancelados. As senhas utilizam os mecanismos de hash do Django. Com `DJANGO_DEBUG=False`, HTTPS e cookies seguros são ativados por padrão e a chave secreta de exemplo é recusada. Em produção, use uma chave própria e configure corretamente os hosts.

Limitações: o sistema ainda não possui limite de tentativas de login. Este repositório não inclui configuração de hospedagem. Com a depuração desligada, o Django não entrega CSS e JavaScript sozinho, então é necessária configuração adicional para servir os arquivos estáticos.

## Resultados e documentação

Os procedimentos e resultados detalhados estão nos seguintes documentos:

- [Desempenho](docs/desempenho.md)
- [Acessibilidade e responsividade](docs/acessibilidade-responsividade.md)
- [Integração contínua](docs/integracao-continua.md)
- [Roteiro de validação](docs/validacao/roteiro.md)
- [Registro da primeira rodada](docs/validacao/registro-sessao-rodada1.md)
- [Registro da segunda rodada](docs/validacao/registro-sessao-rodada2.md)
- [Comparação das rodadas](docs/validacao/comparacao-rodadas.md)
- [Registro de problemas](docs/validacao/registro-problemas.md)

As medições de desempenho foram realizadas com o servidor local e dados fictícios. A avaliação de responsividade incluiu emulação de dispositivos no Edge; não houve auditoria Lighthouse nem avaliação documentada com leitor de tela. A validação de usabilidade envolveu um único participante, portanto os resultados não podem ser generalizados. As sessões de validação usaram uma versão hospedada em serviço externo, com ajustes de configuração que não estão neste repositório.

---

**Situação atual:** MVP funcional com testes automatizados e documentação técnica. O RF05 permanece não implementado.

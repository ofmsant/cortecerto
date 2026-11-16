# Roteiro de validação de usabilidade com o participante (Fase 9)

## 1. Finalidade e situação

Este roteiro define o procedimento para avaliar a usabilidade do CorteCerto com Renan, barbeiro autônomo e representante externo do público-alvo do projeto.

A avaliação pretende verificar se o participante consegue consultar a agenda, cadastrar um corte gratuito, concluir o atendimento e conferir o histórico.

**Situação atual:** o cenário técnico de demonstração foi preparado com sucesso. As duas rodadas de validação de usabilidade ainda precisam de seus resultados registrados após a realização.

O consentimento para participação foi autorizado por meio de assinatura em 07/11/2026. A assinatura do consentimento é registrada separadamente da execução das tarefas.

## 2. Participante e consentimento

- Participante previsto: Renan, barbeiro autônomo, representante do público-alvo.
- Participação voluntária, com possibilidade de interrupção a qualquer momento.
- Ambiente preparado com dados fictícios, sem dados reais de clientes.
- Consentimento: autorizado por assinatura em 07/11/2026.

### Registro do consentimento

| Campo | Registro |
|---|---|
| Consentimento autorizado | Sim, conforme informação fornecida |
| Forma | Assinatura |
| Data da assinatura | 07/11/2026 |
| Documento assinado arquivado | Confirmar localização do documento |
| Data de realização da sessão | A registrar após a sessão |

### Termo de consentimento

Eu concordo em participar voluntariamente da avaliação do sistema CorteCerto. Entendo que o objetivo é avaliar o sistema, e não a minha capacidade de utilização. Estou ciente de que poderão ser registrados os tempos das tarefas, as ações realizadas e os comentários que eu fornecer durante a avaliação. Entendo que serão utilizados dados fictícios e que posso interromper minha participação a qualquer momento, sem prejuízo.

**Registro informado:** autorização assinada em 07/11/2026.

## 3. Preparação do ambiente

Cada rodada deve começar em um banco de dados separado, para que as condições iniciais sejam reproduzíveis.

No PowerShell, na pasta do projeto, com o ambiente virtual ativado:

### Primeira rodada

```powershell
$env:DJANGO_DB_PATH="$PWD\validacao-rodada1.sqlite3"
$env:CORTECERTO_PERIODOS_ATENDIMENTO="08:00-12:00"
python manage.py migrate
python manage.py createsuperuser
python manage.py preparar_validacao
python manage.py runserver
```

### Segunda rodada

```powershell
$env:DJANGO_DB_PATH="$PWD\validacao-rodada2.sqlite3"
$env:CORTECERTO_PERIODOS_ATENDIMENTO="08:00-12:00"
python manage.py migrate
python manage.py createsuperuser
python manage.py preparar_validacao
python manage.py runserver
```

O período `08:00-12:00` é um exemplo de demonstração e não deve ser apresentado como horário real de atendimento de Renan sem confirmação. Se forem definidos períodos reais, registrar o valor utilizado na sessão.

O comando `preparar_validacao` foi executado com sucesso no banco de ensaio `ensaio-validacao.sqlite3`. O cenário preparado contém:

- Cliente C: 10/11/2026, às 09h, gratuito, concluído.
- Cliente D: 11/11/2026, às 09h, gratuito, concluído.
- Cliente A: 14/11/2026, às 09h, pago, agendado.
- Cliente B: 14/11/2026, às 10h, gratuito, agendado.

Os quatro agendamentos possuem duração de 60 minutos. O histórico começa com dois cortes gratuitos concluídos.

O banco de ensaio comprova a preparação técnica do cenário, mas não substitui o registro de cada rodada de usabilidade.

Ao terminar cada sessão, parar o servidor com `Ctrl+C` e limpar as variáveis de ambiente:

```powershell
Remove-Item Env:DJANGO_DB_PATH, Env:CORTECERTO_PERIODOS_ATENDIMENTO
```

Registrar o dispositivo, o navegador e a versão realmente utilizados. Não atribuir a uma sessão um dispositivo que não tenha sido utilizado.

## 4. Materiais

- Sistema aberto na tela de login.
- Usuário e senha exclusivos para o ambiente de teste.
- Cartões com as três tarefas.
- Cronômetro.
- Uma cópia do arquivo `registro-sessao.md` para cada sessão.
- Arquivo `registro-problemas.md` para registrar problemas efetivamente observados.
- Pergunta de satisfação apresentada ao final.

## 5. Condução da sessão

1. Explicar que a avaliação é do sistema, não do participante.
2. Confirmar que o participante compreende a finalidade e deseja prosseguir.
3. Entregar o cartão de acesso e o cartão da primeira tarefa.
4. Iniciar a contagem quando o participante terminar de ler a tarefa.
5. Observar sem interferir e registrar ações, dúvidas, hesitações e comentários reais.
6. Interromper o cronômetro quando a tarefa for concluída ou abandonada.
7. Repetir o procedimento para as tarefas seguintes.
8. Ao final, fazer a pergunta de satisfação e registrar a resposta exata.
9. Preencher o registro da sessão e documentar problemas observados.

## 6. Tarefas

### Tarefa 1 — consultar a agenda

Cartão apresentado:

> Entre no sistema com o usuário e a senha do cartão. Consulte a agenda do dia 14/11/2026. Diga quais horários estão ocupados e um horário que está livre.

Resultado esperado: identificar 09h e 10h como ocupados e 11h como livre.

Também registrar se o participante conseguiu entrar no sistema e navegar até a data sem ajuda.

### Tarefa 2 — marcar um corte gratuito

Cartão apresentado:

> Registre um corte gratuito para o cliente Cliente E, no dia 14/11/2026, às 11h, com duração de 60 minutos.

Resultado esperado: o agendamento é salvo com os dados corretos, aparece na agenda e está identificado como gratuito.

**Desvio em relação ao plano original:** a duração de 60 minutos foi acrescentada ao cartão porque o formulário atual exige esse campo.

### Tarefa 3 — concluir e verificar o histórico

Cartão apresentado:

> Marque o atendimento do Cliente E como concluído e consulte o histórico. Diga quantos cortes gratuitos concluídos aparecem.

Resultado esperado: o atendimento aparece como concluído e a contagem de cortes gratuitos concluídos passa de dois para três.

Esse resultado pressupõe que o cenário inicial foi preparado corretamente e que nenhum outro agendamento interfere na contagem.

## 7. Regras de ajuda

- Não fornecer ajuda durante os primeiros 90 segundos de bloqueio.
- Após 90 segundos, oferecer no máximo uma orientação neutra.
- Exemplos de orientação neutra: “Leia o cartão novamente” ou “Observe a tela com calma”.
- Se for necessário indicar um botão, campo ou caminho específico, registrar como ajuda direta.
- Uma tarefa concluída com ajuda direta não conta como sucesso independente.
- Registrar o momento e o tipo de cada ajuda fornecida.

## 8. Métricas e critérios de aprovação

| Métrica | Meta |
|---|---|
| Sucesso independente | 3 de 3 tarefas |
| Tempo da Tarefa 2 | Até 120 segundos |
| Satisfação | Nota mínima 4 de 5 |
| Falhas críticas | Zero |

Pergunta de satisfação:

> De modo geral, quão fácil ou difícil foi utilizar o CorteCerto para realizar as tarefas propostas?

Escala: 1 = muito difícil; 5 = muito fácil.

O critério de aprovação exige que as três tarefas sejam concluídas de forma independente, que a Tarefa 2 seja concluída em até 120 segundos, que a satisfação seja igual ou superior a 4 e que não ocorra nenhuma falha crítica.

Os resultados devem ser calculados com base nas observações da sessão. Se algum critério não for atingido, registrar os problemas e avaliar as correções antes de uma nova rodada.

## 9. Definições

- **Sucesso independente:** tarefa concluída com o resultado correto, sem ajuda direta.
- **Tarefa assistida:** tarefa concluída com ajuda direta; não conta como sucesso independente.
- **Tarefa não concluída:** participante desiste ou o resultado não corresponde ao esperado.
- **Falha crítica — definição proposta:** problema que impede a conclusão de uma tarefa, salva dados incorretos sem que isso seja percebido ou provoca uma ação irreversível não desejada. A definição deve ser confrontada com os critérios das atividades anteriores da disciplina.

O cancelamento de um agendamento é irreversível no fluxo atual. Se houver cancelamento acidental durante uma sessão, registrar o ocorrido e a consequência.

## 10. Depois da sessão

1. Preencher uma cópia do registro da sessão no mesmo dia.
2. Registrar os problemas efetivamente observados em `registro-problemas.md`.
3. Decidir se cada problema será corrigido, adiado, considerado fora do escopo ou ficará sem ação.
4. Se uma correção for implementada, criar um commit específico e registrar seu hash.
5. Preparar a segunda rodada em um banco separado, mantendo o cenário inicial equivalente.
6. Preencher `comparacao-rodadas.md` somente depois que existirem resultados das duas rodadas.

## 11. Limitações

- Um único participante não permite generalizar os resultados.
- Os dados utilizados são fictícios e o ambiente é controlado.
- O dispositivo e o navegador usados limitam as conclusões sobre outros ambientes.
- A familiaridade adquirida na primeira rodada pode influenciar o desempenho na segunda.
- A preparação técnica bem-sucedida não demonstra, por si só, que os critérios de usabilidade foram atingidos.

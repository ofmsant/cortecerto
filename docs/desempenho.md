# Desempenho: procedimento e resultados — Fase 6

## 1. Objetivo e critérios

Avaliar o tempo de resposta das principais operações do CorteCerto utilizando 200 agendamentos fictícios em um banco SQLite separado do banco principal.

Foram avaliadas três operações: carregamento da agenda diária, carregamento do histórico e envio de um novo agendamento.

Critérios de aceitação:

- Mediana de até 3 segundos por operação.
- Nenhuma medição individual acima de 5 segundos.
- Uma execução de aquecimento e cinco medições por operação.

## 2. Ambiente de teste

| Item | Valor |
|---|---|
| Data das medições | 15/11/2026, às 16:37 e às 17:22 |
| Versão do projeto (hash do commit) | Não registrada para as medições |
| Sistema operacional | Windows 11 — versão 10.0.22000 |
| Python | 3.12.10 |
| Django | 5.2.19 |
| Servidor | Django `runserver`, `http://127.0.0.1:8000` |
| Banco de dados | SQLite, em arquivos de teste separados |
| Massa de dados | 200 agendamentos fictícios por cenário |
| Cenário padrão | 10 agendamentos por dia, distribuídos em 20 dias |
| Cenário de pior caso | 200 agendamentos concentrados em um dia |
| Data consultada na agenda | 01/01/2030 |
| Repetições | 5 por operação, após 1 aquecimento |
| Rede | Local, via `127.0.0.1` |
| Processador e memória | Não registrados |

No cenário concentrado, a massa gerada incluiu 50 agendamentos agendados, 100 concluídos e 50 cancelados. Entre os concluídos, 50 foram classificados como gratuitos.

## 3. Resultados das medições

### 3.1 Cenário padrão — 10 agendamentos por dia

| Operação | Medições (s) | Mediana (s) | Máximo (s) | Resultado |
|---|---|---:|---:|---|
| Agenda diária (GET) | 0,035; 0,034; 0,034; 0,044; 0,034 | 0,034 | 0,044 | Aprovado |
| Histórico (GET) | 0,032; 0,032; 0,034; 0,032; 0,044 | 0,032 | 0,044 | Aprovado |
| Envio de agendamento (POST) | 0,203; 0,328; 0,433; 0,055; 0,055 | 0,203 | 0,433 | Aprovado |

As três operações atenderam aos critérios estabelecidos. A maior mediana foi de 0,203 segundos, no envio de agendamento, e a maior medição individual foi de 0,433 segundos.

### 3.2 Cenário de pior caso — 200 agendamentos em um dia

| Operação | Medições (s) | Mediana (s) | Máximo (s) | Resultado |
|---|---|---:|---:|---|
| Agenda diária (GET) | 0,344; 0,692; 1,286; 0,291; 0,201 | 0,344 | 1,286 | Aprovado |
| Histórico (GET) | 0,102; 0,093; 0,079; 0,127; 0,140 | 0,102 | 0,140 | Aprovado |
| Envio de agendamento (POST) | 0,173; 0,096; 0,049; 0,061; 0,178 | 0,096 | 0,178 | Aprovado |

As três operações também atenderam aos critérios no cenário concentrado. A agenda diária apresentou o maior tempo de resposta, com mediana de 0,344 segundos e máximo de 1,286 segundos, permanecendo abaixo dos limites estabelecidos.

## 4. Análise comparativa

| Operação | Mediana — cenário padrão | Mediana — 200 no mesmo dia | Máximo — cenário padrão | Máximo — 200 no mesmo dia |
|---|---:|---:|---:|---:|
| Agenda diária (GET) | 0,034 s | 0,344 s | 0,044 s | 1,286 s |
| Histórico (GET) | 0,032 s | 0,102 s | 0,044 s | 0,140 s |
| Envio de agendamento (POST) | 0,203 s | 0,096 s | 0,433 s | 0,178 s |

A concentração dos 200 registros aumentou o tempo de resposta da agenda diária em comparação com o cenário padrão. Mesmo assim, a mediana permaneceu abaixo de um segundo, e a maior medição individual foi de 1,286 segundos.

O histórico apresentou tempos abaixo de 0,15 segundo no cenário concentrado. O envio de agendamento também permaneceu dentro dos critérios definidos.

As diferenças entre os cenários devem ser interpretadas considerando que as medições foram realizadas em momentos distintos e que os resultados podem variar conforme as condições de execução.

Não foi identificada necessidade de otimização para os cenários avaliados.

## 5. Verificações complementares

Além das medições de desempenho, foram executadas verificações automatizadas na Fase 6.

| Verificação | Resultado |
|---|---|
| Testes de acessibilidade | 9 aprovados |
| Testes de contraste | 4 aprovados |
| Testes do comando de preparação dos dados de desempenho | 7 aprovados |
| Suíte completa do projeto | 210 aprovados |
| Verificação do Django (`manage.py check`) | Sem problemas identificados |
| Verificação de migrações | Nenhuma migração pendente |
| Verificação de diferenças (`git diff --check`) | Sem problemas de formatação |

Os testes automatizados verificam funcionalidades, regras e características do projeto. Seus resultados não representam medições adicionais de tempo de resposta.

## 6. Limitações

- As medições representam o tempo de resposta HTTP do servidor local, sem incluir renderização no navegador, carregamento do Bootstrap pela CDN ou condições de rede móvel.
- O servidor de desenvolvimento do Django não representa um ambiente de produção.
- Os dados são fictícios e não reproduzem necessariamente o volume ou o padrão de utilização real.
- O cenário concentrado avalia 200 registros em uma única data, mas não representa todos os possíveis volumes de utilização.
- O hardware utilizado não foi registrado, o que limita a reprodução exata das medições.
- Não foram registradas métricas de carregamento no navegador.
- Os resultados são válidos para o ambiente, a massa de dados e as condições de execução descritas neste documento.

## 7. Conclusão

Os dois cenários avaliados atenderam aos critérios de desempenho estabelecidos. No cenário padrão, as medianas variaram entre 0,032 e 0,203 segundos. No cenário com 200 agendamentos concentrados em um dia, as medianas variaram entre 0,096 e 0,344 segundos.

A maior medição individual entre todas as operações e cenários foi de 1,286 segundos, abaixo do limite de 5 segundos. Portanto, não foi identificada necessidade de otimização para as condições testadas.

Os resultados indicam que as principais operações do CorteCerto apresentaram tempos de resposta compatíveis com os critérios definidos para a avaliação local, sem constituir garantia de desempenho equivalente em produção ou sob cargas maiores.
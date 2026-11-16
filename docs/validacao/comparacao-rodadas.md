# Comparação entre a primeira e a segunda rodada

## 1. Condições

| Item | Rodada 1 | Rodada 2 |
|---|---|---|
| Data | 16/11/2026 | 16/11/2026 |
| Participante | Renan | Renan |
| Dispositivo e navegador | iPhone 11; Safari, versão não informada | iPhone 11; Safari, versão não informada |
| Sistema operacional | iOS; versão não informada | iOS; versão não informada |
| Versão do sistema (hash) | `7b404df6dce4390c7d7b388ec7b95820ed4fa703` — correspondência com a versão testada não confirmada | `7b404df6dce4390c7d7b388ec7b95820ed4fa703` — correspondência com a versão testada não confirmada |
| Períodos de atendimento configurados | Conforme ambiente de validação | Conforme ambiente de validação |
| Cenário de dados | Preparado para validação (`preparar_validacao`) | Preparado para validação (`preparar_validacao`) |

## 2. Métricas

| Métrica | Meta | Rodada 1 | Rodada 2 | Variação |
|---|---|---|---|---|
| Tarefa 1 concluída sem ajuda | Sim | Sim | Sim | Sem alteração |
| Tarefa 2 concluída sem ajuda | Sim | Sim | Sim | Sem alteração |
| Tarefa 3 concluída sem ajuda | Sim | Sim | Sim | Sem alteração |
| Sucesso independente (de 3) | 3 de 3 | 3 de 3 | 3 de 3 | Sem alteração |
| Tempo da Tarefa 2 (s) | Até 120 | Menos de 30 | Menos de 30 | Sem alteração observada |
| Satisfação (1 a 5) | Mínimo 4 | 5 | 5 | 0 |
| Falhas críticas | 0 | 0 | 0 | Sem alteração |
| Ajudas diretas dadas | 0 | 0 | 0 | Sem alteração |
| Critério de aprovação atingido | Sim | Sim | Sim | Mantido |

## 3. Problemas e correções

| Problema da rodada 1 (nº do registro) | Correção feita | Commit | A rodada 2 mostrou melhora? | Evidência |
|---|---|---|---|---|
| Nenhum problema identificado nos registros | Não foi necessária | Não se aplica | Não se aplica | Os registros indicam o mesmo resultado nas tarefas das duas rodadas. |

### Novos problemas surgidos na rodada 2

| Descrição | Gravidade |
|---|---|
| Nenhum problema identificado nos registros da sessão | Não se aplica |

## 4. Conclusão

- **As correções ajudaram?** Não houve registro de correções decorrentes da primeira rodada.
- **O critério de aprovação foi atingido?** Sim, conforme os resultados registrados para as duas rodadas.
- **O que continua pendente?** Confirmar a correspondência entre o hash registrado e a versão efetivamente utilizada nas sessões. Permanecem as limitações técnicas e de avaliação descritas nos documentos do projeto.

**Resultado geral:** os registros das duas rodadas apresentam resultados equivalentes. De acordo com as informações documentadas, o participante concluiu as três tarefas sem ajuda, com tempos inferiores a 30 segundos por tarefa e nota de satisfação 5/5. Não foram registradas falhas críticas ou dificuldades adicionais na segunda rodada. A comparação descreve os resultados informados e não demonstra que houve melhoria entre as rodadas.

## 5. Limitações

- A avaliação contou com um único participante; os resultados não podem ser generalizados.
- Pode haver efeito de aprendizado, pois o participante já conhecia as tarefas na segunda rodada.
- Os dados de demonstração do sistema são fictícios e o ambiente é controlado.
- Como não foram registradas correções entre as rodadas, não é possível atribuir os resultados da segunda rodada a melhorias específicas.
- A versão exata do iOS e do Safari não foi informada nem verificada diretamente.
- O hash registrado corresponde ao commit identificado no repositório, mas sua correspondência com a versão efetivamente executada durante cada sessão não foi confirmada.
- Os resultados se referem ao uso informado em um iPhone 11 e não são suficientes para afirmar o mesmo desempenho em todos os dispositivos e navegadores.

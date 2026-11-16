# Acessibilidade e responsividade: procedimento e registro (Fase 6)

Este documento descreve os procedimentos e registra os resultados das verificações de acessibilidade, responsividade e usabilidade do CorteCerto. Foram realizadas verificações automatizadas e manuais, sem identificação de problemas nas condições avaliadas. A auditoria do Lighthouse não foi executada.

## 1. Ambiente da verificação

| Item | Valor |
|---|---|
| Data da verificação | 15/11/2026 |
| Versão de referência do projeto | `05669bc`, último commit anterior às alterações da Fase 6 |
| Navegador | Microsoft Edge 157.0.0.0 |
| Sistema operacional | Windows 11 |
| Condições de verificação responsiva | Larguras correspondentes a dispositivos móveis, tablet e desktop |
| Dados utilizados | Dados fictícios |
| Framework de aplicação | Django 5.2.19 |
| Python | 3.12.10 |

**Observação:** a versão de referência corresponde ao código versionado antes das alterações da Fase 6. Essas alterações foram versionadas nos commits `ea0de32`, `c4f26c4`, `6b749dd`, `05723f4` e `9c6a2e4`.

## 2. Verificações automáticas

Foram executados os testes automatizados de acessibilidade e contraste:

```powershell
.venv\Scripts\python.exe manage.py test agenda.tests.test_acessibilidade agenda.tests.test_contraste
```

Os testes verificam o idioma da página, a hierarquia dos títulos, a ausência de IDs duplicados, os rótulos dos campos, as referências `aria-describedby`, os nomes acessíveis de botões e links, a configuração de `viewport`, a ausência de `tabindex` positivo, a proteção CSRF, a indicação de campos obrigatórios, o foco no resumo de erros e o contraste das cores definidas no CSS segundo a fórmula da WCAG.

| Verificação | Resultado |
|---|---|
| Quantidade de testes executados | 13 |
| Testes aprovados | 13 |
| Testes com falha | 0 |
| Resultado geral | Aprovado |

Também foram executados os testes gerais do projeto e as verificações estruturais do Django.

| Verificação complementar | Resultado |
|---|---|
| Suíte completa de testes | 210 testes aprovados |
| `manage.py check` | Nenhum problema identificado |
| `makemigrations --check --dry-run` | Nenhuma migração pendente |
| `git diff --check` | Nenhum problema de formatação identificado |

Os testes automatizados foram complementados por verificações manuais de apresentação, navegação, responsividade e utilização dos formulários.

## 3. Larguras verificadas

Foram verificadas as telas de login, agenda e novo agendamento, histórico e confirmação de cancelamento em larguras representativas de diferentes dispositivos.

| Largura | Representação | Login | Agenda e novo agendamento | Histórico | Confirmação de cancelamento |
|---|---|---|---|---|---|
| 320 px | Celular muito estreito | OK | OK | OK | OK |
| 360 px | Celular pequeno | OK | OK | OK | OK |
| 390 px | Celular comum | OK | OK | OK | OK |
| 768 px | Tablet | OK | OK | OK | OK |
| 1280 px | Notebook ou desktop | OK | OK | OK | OK |

**Resultado:** nenhuma falha de responsividade foi identificada nas larguras verificadas. Não foram observados textos cortados, botões sobrepostos, campos fora da tela ou problemas que impedissem o uso das funcionalidades.

## 4. Verificações manuais

As verificações manuais foram realizadas nas telas e condições previstas no roteiro. Não foram identificados problemas nos itens avaliados.

### 4.1 Alvos de toque

Foi verificada a área dos principais elementos interativos, considerando a referência de 44 × 44 pixels CSS para os alvos de toque, quando aplicável.

| Elemento | Resultado |
|---|---|
| Botão Sair | OK |
| Links Agenda e Histórico | OK |
| Botões Dia anterior, Próximo dia, Ir e Hoje | OK |
| Botões Concluir e Cancelar | OK |
| Botão Agendar às HH:MM | OK |
| Opções Pago e Gratuito, incluindo a área clicável | OK |
| Botão Salvar agendamento | OK |
| Botões Confirmar cancelamento e Voltar sem cancelar | OK |
| Botões Anterior e Próxima no histórico | OK |

**Resultado:** os elementos avaliados apresentaram condições adequadas de interação, sem problemas identificados durante a verificação.

### 4.2 Teclado e foco

A navegação foi verificada utilizando o teclado, com `Tab`, `Shift + Tab`, `Enter` e a barra de espaço, conforme o tipo de controle.

| Verificação | Resultado |
|---|---|
| O foco está sempre visível, inclusive no cabeçalho | OK |
| A ordem do foco acompanha a ordem visual e lógica | OK |
| O link "Ir para o conteúdo" aparece ao receber foco e leva ao conteúdo principal | OK |
| É possível criar, concluir e cancelar um agendamento sem usar o mouse | OK |
| As opções Pago e Gratuito podem ser selecionadas pelo teclado | OK |
| Nenhum elemento prende o foco | OK |

**Resultado:** a navegação por teclado funcionou conforme esperado, sem problemas identificados de foco ou de acesso às funcionalidades avaliadas.

### 4.3 Zoom de 200% e 400%

A interface foi verificada com ampliação de 200% e 400%, considerando a redução da largura efetiva disponível para apresentação do conteúdo.

| Verificação | Resultado |
|---|---|
| Nenhum conteúdo essencial fica cortado ou escondido | OK |
| Não há rolagem horizontal desnecessária | OK |
| Todas as funções continuam disponíveis | OK |
| Nomes de clientes extensos quebram a linha sem ultrapassar os limites da tela | OK |

**Resultado:** a ampliação não comprometeu o acesso às informações e às funcionalidades verificadas.

### 4.4 Cor, contraste e identificação

| Verificação | Resultado |
|---|---|
| Os estados Pago e Gratuito são identificados por texto, e não somente por cor | OK |
| Os estados Agendado, Concluído e Cancelado são identificados por texto | OK |
| Os agendamentos cancelados são visualmente diferenciados e não exibem ações indevidas | OK |
| A tela continua compreensível com a simulação de deficiência de visão cromática do Edge | OK |
| O contraste dos elementos avaliados foi conferido no navegador e comparado com os testes automáticos | OK |

**Resultado:** os estados e as informações relevantes permaneceram identificáveis durante as verificações, sem problemas de contraste ou dependência exclusiva de cores identificados.

### 4.5 Formulários e mensagens

| Verificação | Resultado |
|---|---|
| Todos os campos possuem rótulos visíveis e compreensíveis | OK |
| O aviso de preenchimento obrigatório aparece quando aplicável | OK |
| As mensagens de erro aparecem junto aos campos correspondentes | OK |
| Após um erro de validação, o foco vai para o resumo de erros | OK |
| Os dados válidos permanecem preenchidos após um erro | OK |
| As mensagens de sucesso e de aviso são legíveis | OK |
| Os estados vazios, sem agendamentos ou sem histórico, apresentam orientação clara | OK |
| O cancelamento exige confirmação em uma tela própria | OK |

**Resultado:** os formulários e as mensagens apresentaram comportamento adequado durante os cenários verificados.

### 4.6 Lighthouse

A auditoria de acessibilidade do Lighthouse não foi executada nesta fase. Nenhuma pontuação foi obtida, e este documento não atribui resultados à ferramenta.

| Tela | Pontuação | Situação |
|---|---|---|
| Login | Não disponível | Não executado |
| Agenda e novo agendamento | Não disponível | Não executado |
| Histórico | Não disponível | Não executado |

A auditoria poderá ser realizada posteriormente, utilizando a aba Lighthouse do Edge, a categoria Accessibility e o modo Mobile. Os resultados reais deverão ser registrados nesta seção caso a verificação seja realizada.

### 4.7 Leitor de tela

A avaliação com o Narrador do Windows é opcional. Não há resultado específico registrado nesta seção.

| Verificação | Resultado |
|---|---|
| Anúncio de títulos, campos, botões e mensagens | Sem registro específico |
| Eventuais dificuldades observadas | Sem registro específico |

## 5. Problemas encontrados e correções

Durante as verificações manuais registradas, não foram identificados problemas de acessibilidade, responsividade ou interação que exigissem correção adicional.

| Nº | Tela e largura | Problema | Gravidade | Correção | Commit |
|---|---|---|---|---|---|
| — | Telas e larguras avaliadas | Nenhum problema identificado nas condições verificadas | — | Não necessária para os itens avaliados | Não se aplica |

As alterações implementadas na Fase 6 incluem melhorias de contraste, foco, apresentação responsiva e interação, acompanhadas de testes automatizados específicos e documentação de apoio.

## 6. Limitações

- As verificações de responsividade cobriram as larguras definidas neste documento. Isso não comprova o comportamento em todos os modelos de celulares, navegadores ou versões de sistemas operacionais.
- Os testes automatizados não substituem a avaliação visual e funcional das páginas.
- O teste automatizado de contraste verifica as cores definidas no CSS, mas não substitui a inspeção de todos os estados visuais e elementos da interface.
- O Lighthouse não foi executado, portanto não há indicadores dessa ferramenta neste documento.
- A avaliação específica com leitor de tela não possui resultado registrado.
- Os resultados documentados são válidos para as versões, configurações e condições efetivamente avaliadas.
- Os tempos de resposta registrados no documento de desempenho referem-se ao servidor HTTP local, sem renderização no navegador, CDN do Bootstrap ou rede móvel.
- A avaliação realizada não equivale a uma auditoria externa nem a uma certificação formal de acessibilidade.

## 7. Conclusão

As verificações automatizadas e manuais registradas para a Fase 6 não identificaram problemas nos aspectos avaliados de acessibilidade, contraste, responsividade, navegação por teclado, foco e utilização dos formulários.

Os 13 testes automatizados específicos de acessibilidade e contraste foram aprovados, assim como os 210 testes da suíte completa do projeto. As verificações estruturais do Django também foram concluídas sem problemas ou migrações pendentes.

As larguras correspondentes a dispositivos móveis, tablet e desktop foram avaliadas sem identificação de falhas de responsividade nas condições verificadas. A auditoria do Lighthouse permanece não executada, e a avaliação específica com leitor de tela não possui resultado registrado.

Os resultados de desempenho documentados atenderam aos critérios definidos para o ambiente local de teste. Dessa forma, as verificações realizadas forneceram evidências favoráveis às melhorias implementadas, respeitando as limitações e os aspectos sem registro descritos neste documento.

# CorteCerto

Agenda simples para barbeiro autônomo organizar horários e acompanhar cortes pagos e gratuitos.

## Problema
O barbeiro parceiro atende a domicílio, sozinho e como segunda atividade. Atualmente, combina os horários pelo WhatsApp, sem controle centralizado, e tem dificuldade para acompanhar os cortes gratuitos oferecidos à comunidade.

## Público
- Usuário direto: barbeiro autônomo, com uso prioritário pelo celular.
- Beneficiados: clientes pagantes e pessoas que recebem cortes gratuitos.

## Funcionalidades do MVP
- RF01: marcar agendamentos com data, hora, nome do cliente e tipo de corte (pago ou gratuito).
- RF02: consultar a agenda diária e os horários livres.
- RF03: registrar atendimentos realizados, consultar o histórico e contar os cortes gratuitos concluídos.
- RF04: cancelar agendamentos sem apagar seus registros.
- RF05 (desejável): cadastrar dias e horários de disponibilidade, caso o tempo de desenvolvimento permita. Pode ficar fora da primeira versão.

## Tecnologias
Python 3.12, Django 5.2 LTS, SQLite e Bootstrap 5.3.

## Como executar
1. Criar e ativar um ambiente virtual: `python -m venv .venv`
2. Instalar as dependências: `pip install -r requirements.txt`
3. Configurar as variáveis de ambiente necessárias, incluindo chave secreta, modo de depuração e hosts permitidos. Os nomes e a configuração serão detalhados durante o desenvolvimento.
4. Aplicar as migrações: `python manage.py migrate`
5. Criar a conta inicial de acesso com `python manage.py createsuperuser`. O MVP será utilizado exclusivamente pelo barbeiro parceiro, com uma única conta de usuário e sem cadastro público.
6. Iniciar o servidor de desenvolvimento: `python manage.py runserver`

Observação: os comandos pressupõem que o projeto Django, o arquivo `requirements.txt` e as configurações necessárias já estejam implementados.

## Testes
Executar os testes automatizados com: `python manage.py test`

## Segurança e privacidade
O projeto prevê autenticação obrigatória, armazenamento de senhas com hash gerenciado pelo Django, validação dos dados no servidor e coleta mínima de informações, incluindo apenas o nome do cliente para identificação do agendamento. Segredos e configurações sensíveis devem permanecer em variáveis de ambiente, fora do repositório.

## Contexto acadêmico
Projeto desenvolvido na

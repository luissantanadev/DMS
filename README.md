# DMS - Controle de Docas

Sistema web para controle operacional de docas e boxes, desenvolvido com Django e preparado para integração com WMS.

## Objetivo

Registrar e acompanhar o fluxo de veículos e cargas dentro da operação:

```text
Transportadora -> Motorista -> Veículo -> Carga
    -> Portaria -> Box/Doca -> Operação -> Saída -> Histórico
```

O sistema separa a visualização operacional, o atendimento da portaria e a gestão dos cadastros.

## Áreas do sistema

### Painel TV

Tela de visualização para ficar em uma TV na operação. Exibe todos os boxes/docas, status, ocupação, veículo, carga, horários e alertas. Não é uma tela de cadastro.

### Portaria

Registra a entrada do veículo, transportadora, motorista, carga, tipo de operação, pesagem e eventual alocação de uma doca livre. Também registra a saída, o peso final e libera automaticamente a doca.

### Box

Central administrativa para usuários autorizados. Reúne cadastros, alterações, consultas e futuros relatórios.

## Fluxo operacional

1. O usuário acessa o sistema e faz login.
2. O Django apresenta as áreas permitidas para o perfil.
3. A Portaria registra a entrada do veículo.
4. Uma transportadora ativa e, opcionalmente, uma doca livre são selecionadas.
5. A movimentação recebe status `No pátio` ou `Em operação`.
6. O Painel TV mostra a situação atual de cada doca.
7. A Portaria registra o peso e o horário de saída.
8. A movimentação recebe status `Finalizada` e a doca volta para `Livre`.

## Estrutura

```text
apps/
├── dashboard/          # seleção de área, Painel TV e Portaria
├── docas/              # modelo e gerenciamento de docas
├── operacao/           # movimentações operacionais
├── transportadoras/    # cadastro e consulta de transportadoras
└── integracao_wms/     # base para integração futura

config/                 # configurações, URLs, WSGI e ASGI
templates/              # telas HTML do sistema
static/css/             # estilos das telas
```

## Principais rotas

| Rota | Função |
| --- | --- |
| `/login/` | Login |
| `/painel/acesso/` | Seleção de área |
| `/painel/` | Painel TV |
| `/painel/portaria/` | Entrada e saída de veículos |
| `/painel/box/` | Central de gestão |
| `/docas/gerenciar/` | Cadastro e alteração de docas |
| `/transportadoras/` | Cadastro e consulta de transportadoras |
| `/transportadoras/api/` | API de transportadoras ativas |
| `/admin/` | Administração Django |

## Permissões

Crie no Django Admin os grupos:

- `Portaria`: acesso à Portaria;
- `Box`: acesso ao Painel TV e à central Box;
- `Administradores`: acesso às duas áreas.

As permissões são verificadas nas telas e também diretamente nas views. Esconder um link não substitui a proteção do servidor.

## Capturas das telas

As principais telas disponíveis para visualização são:

- Painel TV: `/painel/`
- Seleção de área: `/painel/acesso/`
- Portaria: `/painel/portaria/`
- Central Box: `/painel/box/`
- Docas: `/docas/gerenciar/`
- Transportadoras: `/transportadoras/`

Para gerar capturas locais, abra cada rota no navegador e use a ferramenta de captura de tela do navegador. O Painel TV deve ser capturado em uma resolução de TV, preferencialmente 1920x1080.

## Tecnologias

- Python 3.14+
- Django 5.2
- PostgreSQL
- Django REST Framework
- Django Channels
- HTML e CSS

## Instalação

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

Configure as credenciais do PostgreSQL no arquivo `.env`. Esse arquivo não deve ser enviado ao GitHub.

## Testes

```bash
python manage.py test apps.dashboard.tests apps.operacao.tests apps.transportadoras.tests apps.docas.tests
python manage.py check
```

Os testes cobrem permissões, cadastros, entrada, alocação de doca, saída e liberação automática.

## Próximas etapas

- cadastro separado de motoristas;
- cadastro separado de veículos;
- histórico e auditoria;
- relatórios operacionais;
- atualização do Painel TV em tempo real;
- integração com WMS.

# DMS - Controle de Docas

Sistema web para controle operacional de docas e boxes, desenvolvido com Django e integrado a um WMS por webhook.

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

### Integração WMS

Recebe movimentações do WMS por webhook, converte os dados para o formato do DMS e registra cada sincronização para auditoria. O monitoramento das sincronizações fica disponível exclusivamente na tela de administração do Django, em `/admin/integracao_wms/sincronizacaowms/`.

O webhook requer uma assinatura HMAC-SHA256 no cabeçalho `X-WMS-Signature-256`, no formato `sha256=<hex>`. A assinatura deve ser calculada sobre o corpo bruto da requisição usando o segredo configurado em `WMS_WEBHOOK_SECRET` no arquivo `.env`.

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
└── integracao_wms/     # webhook, mapeamento e auditoria da integração WMS

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
| `/wms/webhook/` | Recebe eventos do WMS por POST |
| `/wms/api/sincronizacoes/` | Lista sincronizações registradas |
| `/wms/api/sincronizacoes/<shipment_id>/` | Consulta uma sincronização específica |
| `/admin/` | Administração Django |

O acompanhamento visual das sincronizações é feito pelo Django Admin. Os endpoints de API são destinados à integração e à consulta técnica.

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

Para receber webhooks do WMS, configure também um segredo longo e aleatório:

```text
WMS_WEBHOOK_SECRET=troque-por-um-segredo-forte
```

## Testes

```bash
python manage.py test apps.dashboard.tests apps.operacao.tests apps.transportadoras.tests apps.docas.tests
python manage.py test apps.integracao_wms.tests
python manage.py check
```

Os testes cobrem permissões, cadastros, entrada, alocação de doca, saída, liberação automática, mapeamento WMS, webhook e auditoria das sincronizações.

## Próximas etapas

- cadastro separado de motoristas;
- cadastro separado de veículos;
- atualização automática do Painel TV;
- notificações operacionais para alertas críticos;
- autenticação e assinatura dos webhooks do WMS;
- expansão dos relatórios operacionais.

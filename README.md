# Controle de Docas

Sistema web para controle operacional de docas, desenvolvido com Django e preparado para integração com WMS.

## Fase 1
- Dashboard web
- Mapa de docas
- Status das docas
- KPIs
- Alertas
- Estrutura inicial de integração WMS

## Próximas fases
1. Modelagem completa do banco
2. CRUD de docas
3. Cargas e veículos
4. Operações de doca
5. Autenticação e perfis
6. API REST
7. Integração WMS
8. WebSocket para tempo real
9. Histórico e auditoria
10. Relatórios e gestão

## Executar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse http://127.0.0.1:8000/

from django.urls import path
from .views import (
    webhook_wms,
    list_sincronizacoes,
    detail_sincronizacao,
)

urlpatterns = [
    path('webhook/', webhook_wms, name='webhook_wms'),
    path('api/sincronizacoes/', list_sincronizacoes, name='list_sincronizacoes'),
    path('api/sincronizacoes/<str:shipment_id>/', detail_sincronizacao, name='detail_sincronizacao'),
]

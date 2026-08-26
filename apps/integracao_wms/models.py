from django.db import models
from apps.operacao.models import Movimentacao


class SincronizacaoWMS(models.Model):
    """Registro de sincronização de dados vindos do WMS"""
    
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("sucesso", "Sucesso"),
        ("erro", "Erro"),
        ("rejeitado", "Rejeitado"),
    ]
    
    movimentacao = models.ForeignKey(
        Movimentacao,
        on_delete=models.CASCADE,
        related_name="sincronizacoes_wms",
        null=True,
        blank=True,
    )
    shipment_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    dados_wms = models.JSONField()
    dados_mapeados = models.JSONField(null=True, blank=True)
    mensagem_erro = models.TextField(blank=True)
    operador_wms = models.CharField(max_length=100, blank=True)
    localizacao_wms = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Sincronização WMS"
        verbose_name_plural = "Sincronizações WMS"
        indexes = [
            models.Index(fields=["shipment_id", "-criado_em"]),
            models.Index(fields=["status", "-criado_em"]),
        ]
    
    def __str__(self):
        return f"{self.shipment_id} - {self.get_status_display()}"

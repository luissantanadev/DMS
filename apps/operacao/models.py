from django.db import models

from apps.docas.models import Doca
from apps.transportadoras.models import Transportadora


class Movimentacao(models.Model):
    TIPO_OPERACAO_CHOICES = [
        ("recebimento", "Recebimento"),
        ("carregamento", "Carregamento"),
        ("transferencia", "Transferência"),
    ]
    STATUS_CHOICES = [
        ("aguardando", "Aguardando"),
        ("patio", "No pátio"),
        ("em_operacao", "Em operação"),
        ("finalizada", "Finalizada"),
        ("cancelada", "Cancelada"),
    ]

    transportadora = models.ForeignKey(
        Transportadora,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    doca = models.ForeignKey(
        Doca,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
        null=True,
        blank=True,
    )
    motorista_nome = models.CharField(max_length=200)
    motorista_cpf = models.CharField(max_length=14, blank=True)
    placa = models.CharField(max_length=8)
    carga = models.CharField(max_length=100, blank=True)
    tipo_operacao = models.CharField(max_length=20, choices=TIPO_OPERACAO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="aguardando")
    peso_entrada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peso_saida = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    entrada_em = models.DateTimeField(null=True, blank=True)
    saida_em = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Movimentação"
        verbose_name_plural = "Movimentações"

    def __str__(self):
        return f"{self.placa} - {self.get_tipo_operacao_display()}"

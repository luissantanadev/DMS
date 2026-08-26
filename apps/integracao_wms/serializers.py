from rest_framework import serializers
from apps.operacao.models import Movimentacao
from .models import SincronizacaoWMS


class WebhookWMSSerializer(serializers.Serializer):
    """Validação de dados do webhook WMS"""
    
    shipment_id = serializers.CharField(max_length=100, required=True)
    status_code = serializers.CharField(max_length=50, required=True)
    weight_kg = serializers.FloatField(required=False, allow_null=True)
    last_updated = serializers.DateTimeField(required=False, allow_null=True)
    warehouse_zone = serializers.CharField(max_length=100, required=False, allow_blank=True)
    operator_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    item_count = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_weight_kg(self, value):
        """Valida peso"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Peso não pode ser negativo")
        return value
    
    def validate_shipment_id(self, value):
        """Valida ID de remessa"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Shipment ID não pode estar vazio")
        return value.strip()
    
    def validate_status_code(self, value):
        """Valida status code"""
        valid_statuses = [
            'RECEIVED', 'RECEIVED_INSPECTION', 'STORED', 'PICKING',
            'PACKED', 'SHIPPED', 'DELIVERED', 'EXCEPTION', 'DAMAGED',
            'LOST', 'RETURNED'
        ]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status inválido. Opções: {', '.join(valid_statuses)}"
            )
        return value


class SincronizacaoWMSSerializer(serializers.ModelSerializer):
    """Serializer para modelo SincronizacaoWMS"""
    
    class Meta:
        model = SincronizacaoWMS
        fields = [
            'id', 'shipment_id', 'status', 'dados_wms', 'dados_mapeados',
            'mensagem_erro', 'operador_wms', 'localizacao_wms',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = [
            'id', 'dados_mapeados', 'mensagem_erro', 'criado_em', 'atualizado_em'
        ]

import hashlib
import hmac
import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.operacao.models import Movimentacao, HistoricoMovimentacao
from .models import SincronizacaoWMS
from .mappers import WMSMovimentacaoMapper
from .serializers import WebhookWMSSerializer, SincronizacaoWMSSerializer


def _webhook_signature_is_valid(request):
    secret = settings.WMS_WEBHOOK_SECRET
    signature = request.headers.get("X-WMS-Signature-256", "")
    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"), request.body, hashlib.sha256
    ).hexdigest()
    return bool(secret) and hmac.compare_digest(signature, expected_signature)


def _json_compatible_data(data):
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


@csrf_exempt
@require_http_methods(["POST"])
def webhook_wms(request):
    """
    Endpoint webhook para receber atualizações do WMS
    
    Esperado:
    {
        "shipment_id": "SHP-001234",
        "status_code": "STORED",
        "weight_kg": 8750,
        "last_updated": "2026-08-26T14:35:22Z",
        "warehouse_zone": "Z05",
        "operator_id": "OP-445",
        "item_count": 150,
        "notes": "Armazenado conforme previsto"
    }
    """
    if not _webhook_signature_is_valid(request):
        return JsonResponse({
            "success": False,
            "error": "Assinatura do webhook inválida",
        }, status=401)

    try:
        wms_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    
    # Validar dados com serializer
    serializer = WebhookWMSSerializer(data=wms_data)
    if not serializer.is_valid():
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos',
            'details': serializer.errors
        }, status=400)
    
    shipment_id = serializer.validated_data['shipment_id']
    
    try:
        with transaction.atomic():
            # Mapear dados WMS
            dados_mapeados = WMSMovimentacaoMapper.mapear(wms_data)
            
            # Procurar movimentação existente
            movimentacao = Movimentacao.objects.filter(carga=shipment_id).first()
            
            if not movimentacao:
                # Obter ou criar transportadora padrão para WMS
                from apps.transportadoras.models import Transportadora
                transportadora, _ = Transportadora.objects.get_or_create(
                    cnpj='00.000.000/0000-01',
                    defaults={
                        'razao_social': 'WMS Auto',
                        'nome_fantasia': 'WMS Auto',
                        'ativa': True
                    }
                )
                
                # Criar nova movimentação (pode ser de inbound que não passou por portaria ainda)
                movimentacao = Movimentacao.objects.create(
                    transportadora=transportadora,
                    motorista_nome=wms_data.get('driver_name', 'WMS Auto'),
                    placa=wms_data.get('license_plate', 'AUTO-WMS'),
                    carga=shipment_id,
                    tipo_operacao='recebimento',
                    status=dados_mapeados['status'],
                    peso_saida=dados_mapeados['peso_saida'],
                    saida_em=dados_mapeados['saida_em'],
                    observacoes=dados_mapeados['observacoes'],
                )
            else:
                # Atualizar movimentação existente
                movimentacao.status = dados_mapeados['status']
                movimentacao.peso_saida = dados_mapeados['peso_saida']
                movimentacao.saida_em = dados_mapeados['saida_em']
                
                # Append observações WMS
                obs_anterior = movimentacao.observacoes or ''
                movimentacao.observacoes = f"{obs_anterior} | WMS: {dados_mapeados['observacoes']}" if obs_anterior else dados_mapeados['observacoes']
                movimentacao.save(update_fields=[
                    'status', 'peso_saida', 'saida_em', 'observacoes', 'atualizado_em'
                ])
            
            # Registrar histórico
            HistoricoMovimentacao.objects.create(
                movimentacao=movimentacao,
                acao='atualizacao',
                descricao=f"Atualização WMS: {serializer.validated_data['status_code']}"
            )
            
            # Registrar sincronização
            SincronizacaoWMS.objects.create(
                movimentacao=movimentacao,
                shipment_id=shipment_id,
                status='sucesso',
                dados_wms=wms_data,
                dados_mapeados=_json_compatible_data(dados_mapeados),
                operador_wms=wms_data.get('operator_id', ''),
                localizacao_wms=wms_data.get('warehouse_zone', ''),
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Sincronização bem-sucedida',
                'shipment_id': shipment_id,
                'movimentacao_id': movimentacao.id
            }, status=200)
    
    except Exception as e:
        # Registrar erro de sincronização
        SincronizacaoWMS.objects.create(
            shipment_id=shipment_id,
            status='erro',
            dados_wms=wms_data,
            mensagem_erro=str(e),
            operador_wms=wms_data.get('operator_id', ''),
            localizacao_wms=wms_data.get('warehouse_zone', ''),
        )
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'shipment_id': shipment_id
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sincronizacoes(request):
    """Lista sincronizações WMS com filtros"""
    filtro_status = request.query_params.get('status')
    filtro_shipment = request.query_params.get('shipment_id')
    
    sincronizacoes = SincronizacaoWMS.objects.all()
    
    if filtro_status:
        sincronizacoes = sincronizacoes.filter(status=filtro_status)
    if filtro_shipment:
        sincronizacoes = sincronizacoes.filter(shipment_id__icontains=filtro_shipment)
    
    serializer = SincronizacaoWMSSerializer(sincronizacoes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_sincronizacao(request, shipment_id):
    """Detalhes de uma sincronização específica"""
    try:
        sincronizacao = SincronizacaoWMS.objects.get(shipment_id=shipment_id)
        serializer = SincronizacaoWMSSerializer(sincronizacao)
        return Response(serializer.data)
    except SincronizacaoWMS.DoesNotExist:
        return Response({
            'error': f'Sincronização não encontrada: {shipment_id}'
        }, status=404)

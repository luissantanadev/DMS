"""
Mapper para sincronização de dados WMS → DMS
Converte formato e campos do WMS para o modelo Movimentacao do DMS
"""
from datetime import datetime
from django.utils import timezone


class WMSMovimentacaoMapper:
    """Converte dados do WMS para Movimentacao do DMS"""
    
    # Mapeamento de campos WMS → campos DMS
    FIELD_MAPPING = {
        'shipment_id': 'carga',
        'weight_kg': 'peso_saida',
        'last_updated': 'saida_em',
        'warehouse_zone': 'localizacao_wms',
        'operator_id': 'operador_wms',
    }
    
    # Mapeamento de status WMS → status DMS
    STATUS_MAPPING = {
        'RECEIVED': 'em_operacao',
        'RECEIVED_INSPECTION': 'em_operacao',
        'STORED': 'finalizada',
        'PICKING': 'em_operacao',
        'PACKED': 'finalizada',
        'SHIPPED': 'finalizada',
        'DELIVERED': 'finalizada',
        'EXCEPTION': 'cancelada',
        'DAMAGED': 'cancelada',
        'LOST': 'cancelada',
        'RETURNED': 'cancelada',
    }
    
    @classmethod
    def mapear(cls, wms_data):
        """
        Converte um dado do WMS para formato DMS
        
        Args:
            wms_data (dict): Dados brutos do WMS
            
        Returns:
            dict: Dados mapeados para DMS
            
        Raises:
            ValueError: Se houver campos obrigatórios faltando
        """
        # Validação de campos obrigatórios
        campos_obrigatorios = ['shipment_id', 'status_code']
        for campo in campos_obrigatorios:
            if campo not in wms_data:
                raise ValueError(f"Campo obrigatório faltando: {campo}")
        
        # Converte timestamp
        saida_em = cls._converter_timestamp(wms_data.get('last_updated'))
        
        # Valida e converte peso
        peso = cls._converter_peso(wms_data.get('weight_kg'))
        
        return {
            'carga': wms_data.get('shipment_id'),
            'peso_saida': peso,
            'status': cls._converter_status(wms_data.get('status_code')),
            'saida_em': saida_em,
            'observacoes': cls._gerar_observacoes(wms_data),
            'localizacao_wms': wms_data.get('warehouse_zone', ''),
            'operador_wms': wms_data.get('operator_id', ''),
        }
    
    @classmethod
    def _converter_timestamp(cls, timestamp_str):
        """Converte timestamp do WMS para datetime aware"""
        if not timestamp_str:
            return timezone.now()
        
        try:
            if isinstance(timestamp_str, str):
                # Tenta vários formatos comuns de ISO 8601
                for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(timestamp_str, fmt)
                        return timezone.make_aware(dt) if not timezone.is_aware(dt) else dt
                    except ValueError:
                        continue
                raise ValueError(f"Formato de timestamp não reconhecido: {timestamp_str}")
            elif isinstance(timestamp_str, datetime):
                return timezone.make_aware(timestamp_str) if not timezone.is_aware(timestamp_str) else timestamp_str
        except Exception as e:
            raise ValueError(f"Erro ao converter timestamp: {e}")
        
        return timezone.now()
    
    @classmethod
    def _converter_peso(cls, peso):
        """Converte e valida peso"""
        if peso is None:
            return None
        
        try:
            peso_float = float(peso)
            if peso_float < 0:
                raise ValueError("Peso não pode ser negativo")
            return peso_float
        except (ValueError, TypeError) as e:
            raise ValueError(f"Peso inválido: {e}")
    
    @classmethod
    def _converter_status(cls, status_wms):
        """Converte status WMS para status DMS"""
        status_convertido = cls.STATUS_MAPPING.get(status_wms, 'aguardando')
        return status_convertido
    
    @classmethod
    def _gerar_observacoes(cls, wms_data):
        """Gera observações com informações adicionais do WMS"""
        obs = []
        
        if wms_data.get('warehouse_zone'):
            obs.append(f"Zona WMS: {wms_data['warehouse_zone']}")
        
        if wms_data.get('item_count'):
            obs.append(f"Itens: {wms_data['item_count']}")
        
        if wms_data.get('operator_id'):
            obs.append(f"Operador: {wms_data['operator_id']}")
        
        if wms_data.get('notes'):
            obs.append(f"Notas: {wms_data['notes']}")
        
        return ' | '.join(obs) if obs else ''
    
    @classmethod
    def validar(cls, wms_data):
        """
        Valida dados do WMS antes de processar
        
        Returns:
            tuple: (válido: bool, mensagem: str)
        """
        try:
            cls.mapear(wms_data)
            return True, "Dados válidos"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro inesperado na validação: {e}"

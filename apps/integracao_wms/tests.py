import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, Group

from apps.operacao.models import Movimentacao, Motorista, Veiculo, HistoricoMovimentacao
from apps.docas.models import Doca
from apps.transportadoras.models import Transportadora
from .models import SincronizacaoWMS
from .mappers import WMSMovimentacaoMapper


class WMSMapperTests(TestCase):
    """Testes para o mapper WMS → DMS"""
    
    def test_mapper_converte_dados_basicos(self):
        """Testa conversão básica de campos WMS para DMS"""
        wms_data = {
            'shipment_id': 'SHP-001234',
            'status_code': 'STORED',
            'weight_kg': 8750.50,
            'last_updated': '2026-08-26T14:35:22Z',
            'warehouse_zone': 'Z05',
            'operator_id': 'OP-445',
        }
        
        resultado = WMSMovimentacaoMapper.mapear(wms_data)
        
        self.assertEqual(resultado['carga'], 'SHP-001234')
        self.assertEqual(resultado['peso_saida'], 8750.50)
        self.assertEqual(resultado['status'], 'finalizada')
        self.assertEqual(resultado['operador_wms'], 'OP-445')
        self.assertEqual(resultado['localizacao_wms'], 'Z05')
    
    def test_mapper_converte_status_corretamente(self):
        """Testa conversão de diversos status WMS"""
        status_testes = [
            ('RECEIVED', 'em_operacao'),
            ('STORED', 'finalizada'),
            ('PICKING', 'em_operacao'),
            ('SHIPPED', 'finalizada'),
            ('EXCEPTION', 'cancelada'),
            ('DAMAGED', 'cancelada'),
        ]
        
        for status_wms, status_dms_esperado in status_testes:
            wms_data = {
                'shipment_id': f'SHP-{status_wms}',
                'status_code': status_wms,
            }
            resultado = WMSMovimentacaoMapper.mapear(wms_data)
            self.assertEqual(resultado['status'], status_dms_esperado, f"Status {status_wms} não convertido corretamente")
    
    def test_mapper_rejeita_dados_obrigatorios_faltando(self):
        """Testa rejeição quando faltam campos obrigatórios"""
        wms_data_incompleto = {
            'shipment_id': 'SHP-123'
            # Faltando status_code
        }
        
        with self.assertRaises(ValueError):
            WMSMovimentacaoMapper.mapear(wms_data_incompleto)
    
    def test_mapper_rejeita_peso_negativo(self):
        """Testa rejeição de peso negativo"""
        wms_data = {
            'shipment_id': 'SHP-123',
            'status_code': 'STORED',
            'weight_kg': -100
        }
        
        with self.assertRaises(ValueError):
            WMSMovimentacaoMapper.mapear(wms_data)
    
    def test_mapper_gera_observacoes(self):
        """Testa geração de observações com dados adicionais"""
        wms_data = {
            'shipment_id': 'SHP-001',
            'status_code': 'STORED',
            'warehouse_zone': 'Z05',
            'item_count': 150,
            'operator_id': 'OP-445',
            'notes': 'Conforme previsto',
        }
        
        resultado = WMSMovimentacaoMapper.mapear(wms_data)
        obs = resultado['observacoes']
        
        self.assertIn('Z05', obs)
        self.assertIn('150', obs)
        self.assertIn('OP-445', obs)
        self.assertIn('Conforme previsto', obs)
    
    def test_mapper_validacao_com_sucesso(self):
        """Testa validação bem-sucedida"""
        wms_data = {
            'shipment_id': 'SHP-001',
            'status_code': 'STORED',
        }
        
        valido, mensagem = WMSMovimentacaoMapper.validar(wms_data)
        self.assertTrue(valido)
    
    def test_mapper_validacao_com_erro(self):
        """Testa validação com erro"""
        wms_data = {
            'shipment_id': 'SHP-001',
            # Faltando status_code
        }
        
        valido, mensagem = WMSMovimentacaoMapper.validar(wms_data)
        self.assertFalse(valido)


class WebhookWMSTests(TestCase):
    """Testes para o endpoint webhook WMS"""
    
    def setUp(self):
        self.client = Client()
    
    def test_webhook_rejeita_json_invalido(self):
        """Testa rejeição de JSON inválido"""
        response = self.client.post(
            '/wms/webhook/',
            data='json inválido',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
    
    def test_webhook_rejeita_dados_incompletos(self):
        """Testa rejeição de dados incompletos"""
        wms_payload = {
            'shipment_id': 'SHP-TEST'
            # Faltando status_code
        }
        
        response = self.client.post(
            '/wms/webhook/',
            data=json.dumps(wms_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])


class SincronizacaoWMSModelTests(TestCase):
    """Testes para o modelo SincronizacaoWMS"""
    
    def test_cria_sincronizacao(self):
        """Testa criação de registro de sincronização"""
        dados_wms = {'shipment_id': 'SHP-001', 'status_code': 'STORED'}
        
        sincronizacao = SincronizacaoWMS.objects.create(
            shipment_id='SHP-001',
            status='sucesso',
            dados_wms=dados_wms,
            operador_wms='OP-100',
            localizacao_wms='Z01',
        )
        
        self.assertEqual(sincronizacao.shipment_id, 'SHP-001')
        self.assertEqual(sincronizacao.status, 'sucesso')
        self.assertIsNotNone(sincronizacao.criado_em)
    
    def test_shipment_id_unico(self):
        """Testa que shipment_id é único"""
        SincronizacaoWMS.objects.create(
            shipment_id='SHP-DUP',
            status='sucesso',
            dados_wms={}
        )
        
        with self.assertRaises(Exception):
            SincronizacaoWMS.objects.create(
                shipment_id='SHP-DUP',
                status='sucesso',
                dados_wms={}
            )

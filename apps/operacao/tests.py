from django.db.models import ProtectedError
from django.test import TestCase

from apps.docas.models import Doca
from apps.operacao.models import Movimentacao
from apps.transportadoras.models import Transportadora


class MovimentacaoTests(TestCase):
    def setUp(self):
        self.transportadora = Transportadora.objects.create(
            razao_social="Logistica Central Ltda",
            nome_fantasia="Central Log",
            cnpj="12.345.678/0001-99",
        )
        self.doca = Doca.objects.create(codigo="D20")

    def test_movimentacao_conecta_transportadora_doca_e_veiculo(self):
        movimentacao = Movimentacao.objects.create(
            transportadora=self.transportadora,
            doca=self.doca,
            motorista_nome="Joao da Silva",
            placa="ABC1D23",
            carga="NF-1001",
            tipo_operacao="recebimento",
        )

        self.assertEqual(movimentacao.status, "aguardando")
        self.assertEqual(movimentacao.transportadora, self.transportadora)
        self.assertEqual(movimentacao.doca, self.doca)

    def test_cadastros_usados_nao_podem_ser_excluidos(self):
        Movimentacao.objects.create(
            transportadora=self.transportadora,
            motorista_nome="Joao da Silva",
            placa="ABC1D23",
            tipo_operacao="carregamento",
        )

        with self.assertRaises(ProtectedError):
            self.transportadora.delete()

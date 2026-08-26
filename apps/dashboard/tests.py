from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.dashboard.views import (
    box,
    finalizar_movimentacao,
    gerenciar_historico,
    gerenciar_motoristas,
    gerenciar_relatorios,
    gerenciar_veiculos,
    painel,
    portaria,
    selecionar_area,
)
from apps.docas.models import Doca
from apps.operacao.models import Movimentacao, Motorista, Veiculo
from apps.transportadoras.models import Transportadora


class AreaAccessTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_box_user_sees_only_box_area(self):
        user = User.objects.create_user(username="box_user", password="123")
        Group.objects.get_or_create(name="Box")
        user.groups.add(Group.objects.get(name="Box"))

        request = self.factory.get("/acesso/")
        request.user = user

        response = selecionar_area(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Box")
        self.assertNotContains(response, "Portaria")

    def test_user_without_area_access_is_blocked(self):
        user = User.objects.create_user(username="sem_acesso", password="123")

        request = self.factory.get("/acesso/")
        request.user = user

        with self.assertRaises(PermissionDenied):
            selecionar_area(request)

    def test_painel_uses_real_docas_from_database(self):
        user = User.objects.create_user(username="box_dashboard", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        Doca.objects.create(codigo="D99", status="livre", ativo=True)

        request = self.factory.get("/painel/")
        request.user = user

        response = painel(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "D99")

    def test_box_exibe_central_de_gestao(self):
        user = User.objects.create_user(username="box_gestao", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        request = self.factory.get("/box/")
        request.user = user

        response = box(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastros, alterações e relatórios")
        self.assertContains(response, "Transportadoras")

    def test_portaria_registra_entrada_no_patio(self):
        user = User.objects.create_user(username="portaria_user", password="123")
        group, _ = Group.objects.get_or_create(name="Portaria")
        user.groups.add(group)
        transportadora = Transportadora.objects.create(
            razao_social="Logistica Central Ltda",
            nome_fantasia="Central Log",
            cnpj="12.345.678/0001-99",
        )
        doca = Doca.objects.create(codigo="D21")

        request = self.factory.post("/portaria/", {
            "transportadora": transportadora.id,
            "doca": doca.id,
            "motorista_nome": "Joao da Silva",
            "placa": "ABC1D23",
            "tipo_operacao": "recebimento",
            "carga": "NF-1001",
        })
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = portaria(request)

        self.assertEqual(response.status_code, 302)
        movimentacao = Movimentacao.objects.get(placa="ABC1D23")
        self.assertEqual(movimentacao.status, "em_operacao")
        self.assertEqual(movimentacao.transportadora, transportadora)
        self.assertEqual(movimentacao.doca, doca)
        doca.refresh_from_db()
        self.assertEqual(doca.status, "recebimento")

    def test_box_referencia_motoristas_e_veiculos(self):
        user = User.objects.create_user(username="box_cadastros", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        request = self.factory.get("/box/")
        request.user = user

        response = box(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Motoristas")
        self.assertContains(response, "Veículos")

    def test_gerenciar_relatorios_exibe_filtros_e_indicadores(self):
        user = User.objects.create_user(username="box_relatorios", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        transportadora = Transportadora.objects.create(
            razao_social="Operacao Norte Ltda",
            nome_fantasia="Norte Log",
            cnpj="88.123.456/0001-01",
        )
        motorista = Motorista.objects.create(nome="Carlos Nunes", cpf="33344455566")
        veiculo = Veiculo.objects.create(placa="QWE7T89", modelo="Volvo FM")
        doca = Doca.objects.create(codigo="D30", status="recebimento", ativo=True)
        Movimentacao.objects.create(
            transportadora=transportadora,
            doca=doca,
            motorista=motorista,
            veiculo=veiculo,
            motorista_nome="Carlos Nunes",
            motorista_cpf="33344455566",
            placa="QWE7T89",
            carga="NF-9001",
            tipo_operacao="recebimento",
            status="em_operacao",
        )

        request = self.factory.get("/box/relatorios/?status=em_operacao&tipo_operacao=recebimento")
        request.user = user

        response = gerenciar_relatorios(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Relatórios operacionais")
        self.assertContains(response, "Filtro de operação")
        self.assertContains(response, "Indicadores")
        self.assertContains(response, "QWE7T89")

    def test_historico_registra_entrada_e_saida_da_movimentacao(self):
        user = User.objects.create_user(username="portaria_historico", password="123")
        group, _ = Group.objects.get_or_create(name="Portaria")
        user.groups.add(group)
        transportadora = Transportadora.objects.create(
            razao_social="Logistica Central Ltda",
            nome_fantasia="Central Log",
            cnpj="04.000.111/0001-22",
        )
        motorista = Motorista.objects.create(nome="Ana Souza", cpf="22233344455")
        veiculo = Veiculo.objects.create(placa="LMN4F56", modelo="Mercedes Axor")
        doca = Doca.objects.create(codigo="D24", status="livre")

        request = self.factory.post("/painel/portaria/", {
            "transportadora": transportadora.id,
            "motorista": motorista.id,
            "veiculo": veiculo.id,
            "doca": doca.id,
            "tipo_operacao": "recebimento",
            "carga": "NF-7001",
        })
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))
        portaria(request)

        movimentacao = Movimentacao.objects.get(veiculo=veiculo)
        request = self.factory.post(f"/painel/portaria/finalizar/{movimentacao.id}/", {"peso_saida": "9800.00"})
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))
        finalizar_movimentacao(request, movimentacao.id)

        request = self.factory.get("/painel/box/historico/")
        request.user = User.objects.create_user(username="box_historico", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        request.user.groups.add(group)

        response = gerenciar_historico(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LMN4F56")
        self.assertContains(response, "Entrada registrada")
        self.assertContains(response, "Saída registrada")

    def test_painel_exibe_timers_e_alertas_inteligentes(self):
        user = User.objects.create_user(username="box_painel", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)
        transportadora = Transportadora.objects.create(
            razao_social="Logistica Rapida Ltda",
            nome_fantasia="Rapida Log",
            cnpj="11.222.333/0001-44",
        )
        motorista = Motorista.objects.create(nome="Pedro Costa", cpf="44455566677")
        veiculo = Veiculo.objects.create(placa="ABC9Z99", modelo="Scania P")
        doca = Doca.objects.create(codigo="D50", status="patio", ativo=True)

        entrada_tempo_atraso = timezone.now() - timedelta(minutes=35)
        Movimentacao.objects.create(
            transportadora=transportadora,
            doca=doca,
            motorista=motorista,
            veiculo=veiculo,
            motorista_nome="Pedro Costa",
            motorista_cpf="44455566677",
            placa="ABC9Z99",
            carga="NF-8001",
            tipo_operacao="recebimento",
            status="patio",
            entrada_em=entrada_tempo_atraso,
        )

        request = self.factory.get("/painel/")
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = painel(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ABC9Z99")
        self.assertContains(response, "Aguardando")

    def test_portaria_registra_entrada_com_motorista_e_veiculo_cadastrados(self):
        user = User.objects.create_user(username="portaria_cadastros", password="123")
        group, _ = Group.objects.get_or_create(name="Portaria")
        user.groups.add(group)
        transportadora = Transportadora.objects.create(
            razao_social="Logistica Central Ltda",
            nome_fantasia="Central Log",
            cnpj="77.888.999/0001-66",
        )
        motorista = Motorista.objects.create(nome="Joao da Silva", cpf="12345678909")
        veiculo = Veiculo.objects.create(placa="XYZ1A23", modelo="Scania P/G", ano=2023)
        doca = Doca.objects.create(codigo="D23", status="livre")

        request = self.factory.post("/portaria/", {
            "transportadora": transportadora.id,
            "motorista": motorista.id,
            "veiculo": veiculo.id,
            "doca": doca.id,
            "tipo_operacao": "carregamento",
            "carga": "NF-3001",
        })
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = portaria(request)

        self.assertEqual(response.status_code, 302)
        doca.refresh_from_db()
        movimentacao = Movimentacao.objects.get(veiculo=veiculo)
        self.assertEqual(movimentacao.motorista, motorista)
        self.assertEqual(movimentacao.veiculo, veiculo)
        self.assertEqual(movimentacao.status, "em_operacao")
        self.assertEqual(doca.status, "carregamento")

    def test_gerenciar_motoristas_persiste_no_banco(self):
        user = User.objects.create_user(username="box_motoristas", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        request = self.factory.post("/box/motoristas/", {
            "nome": "Maria da Silva",
            "cpf": "11122233344",
            "telefone": "11999998888",
            "ativo": "on",
        })
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = gerenciar_motoristas(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Motorista.objects.filter(nome="Maria da Silva", cpf="11122233344").exists())

    def test_gerenciar_veiculos_persiste_no_banco(self):
        user = User.objects.create_user(username="box_veiculos", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        user.groups.add(group)

        request = self.factory.post("/box/veiculos/", {
            "placa": "DEF4E56",
            "modelo": "Mercedes Actros",
            "ano": "2024",
            "ativo": "on",
        })
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = gerenciar_veiculos(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Veiculo.objects.filter(placa="DEF4E56", modelo="Mercedes Actros").exists())

    def test_portaria_finaliza_movimentacao_e_libera_doca(self):
        user = User.objects.create_user(username="portaria_saida", password="123")
        group, _ = Group.objects.get_or_create(name="Portaria")
        user.groups.add(group)
        transportadora = Transportadora.objects.create(
            razao_social="Logistica Central Ltda",
            nome_fantasia="Central Log",
            cnpj="98.765.432/0001-11",
        )
        motorista = Motorista.objects.create(nome="Joao da Silva", cpf="11122233344")
        veiculo = Veiculo.objects.create(placa="ABC1D23", modelo="Volvo FH", ano=2022)
        doca = Doca.objects.create(codigo="D22", status="recebimento")
        movimentacao = Movimentacao.objects.create(
            transportadora=transportadora,
            doca=doca,
            motorista=motorista,
            veiculo=veiculo,
            tipo_operacao="recebimento",
            status="em_operacao",
        )

        request = self.factory.post(f"/portaria/finalizar/{movimentacao.id}/", {"peso_saida": "12500.50"})
        request.user = user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = finalizar_movimentacao(request, movimentacao.id)

        self.assertEqual(response.status_code, 302)
        movimentacao.refresh_from_db()
        doca.refresh_from_db()
        self.assertEqual(movimentacao.status, "finalizada")
        self.assertEqual(movimentacao.peso_saida, 12500.50)
        self.assertIsNotNone(movimentacao.saida_em)
        self.assertEqual(doca.status, "livre")

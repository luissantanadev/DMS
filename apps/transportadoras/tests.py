from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from apps.transportadoras.models import Transportadora
from apps.transportadoras.views import lista_transportadoras


class TransportadoraTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="box_transportadora", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        self.user.groups.add(group)

    def test_lista_transportadoras_requer_box(self):
        user = User.objects.create_user(username="sem_perm", password="123")

        request = self.factory.get("/transportadoras/")
        request.user = user

        with self.assertRaises(PermissionDenied):
            lista_transportadoras(request)

    def test_cadastro_de_transportadora_persiste(self):
        data = {
            "razao_social": "Logistica Central Ltda",
            "nome_fantasia": "Central Log",
            "cnpj": "12.345.678/0001-99",
            "telefone": "(11) 99999-0000",
            "ativa": True,
        }

        transportadora = Transportadora.objects.create(**data)

        self.assertEqual(transportadora.nome_fantasia, "Central Log")
        self.assertTrue(transportadora.ativa)

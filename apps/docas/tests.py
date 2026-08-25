from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from apps.docas.models import Doca
from apps.docas.views import gerenciar_docas, lista_docas


class DocaManagementTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="box_operador", password="123")
        group, _ = Group.objects.get_or_create(name="Box")
        self.user.groups.add(group)

    def test_lista_docas_requer_permissao_box(self):
        user = User.objects.create_user(username="sem_permissao", password="123")
        request = self.factory.get("/docas/")
        request.user = user

        with self.assertRaises(PermissionDenied):
            lista_docas(request)

    def test_cadastro_doca_persiste_no_banco(self):
        request = self.factory.post("/docas/gerenciar/", {"codigo": "D20", "status": "livre", "ativo": "on"})
        request.user = self.user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = gerenciar_docas(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Doca.objects.filter(codigo="D20").exists())

    def test_lista_docas_exibe_docas_cadastradas(self):
        Doca.objects.create(codigo="D30", status="recebimento", ativo=True)

        request = self.factory.get("/docas/")
        request.user = self.user

        response = lista_docas(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "D30")

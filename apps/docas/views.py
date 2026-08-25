from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from .models import Doca


@login_required
def lista_docas(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=("Box", "Administradores")).exists()):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    data = list(Doca.objects.values("id", "codigo", "status", "ativo"))
    return JsonResponse({"docas": data})

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .models import Transportadora


def _has_box_access(user):
    return user.is_superuser or user.groups.filter(name__in=("Box", "Administradores")).exists()


@login_required
def lista_transportadoras(request):
    if not _has_box_access(request.user):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    if request.method == "POST":
        Transportadora.objects.create(
            razao_social=(request.POST.get("razao_social") or "").strip(),
            nome_fantasia=(request.POST.get("nome_fantasia") or "").strip(),
            cnpj=(request.POST.get("cnpj") or "").strip(),
            telefone=(request.POST.get("telefone") or "").strip(),
            ativa=request.POST.get("ativa") == "on",
        )
        return redirect("lista_transportadoras")

    transportadoras = Transportadora.objects.order_by("nome_fantasia")
    return render(request, "transportadoras/gerenciar.html", {
        "transportadoras": transportadoras,
    })


@login_required
def api_transportadoras(request):
    if not _has_box_access(request.user):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    data = list(Transportadora.objects.filter(ativa=True).values("id", "nome_fantasia", "cnpj", "telefone"))
    return JsonResponse({"transportadoras": data})

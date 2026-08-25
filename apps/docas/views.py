from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import Doca


def _has_box_access(user):
    return user.is_superuser or user.groups.filter(name__in=("Box", "Administradores")).exists()


@login_required
def lista_docas(request):
    if not _has_box_access(request.user):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    data = list(Doca.objects.values("id", "codigo", "status", "ativo"))
    return JsonResponse({"docas": data})


@login_required
def gerenciar_docas(request):
    if not _has_box_access(request.user):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    if request.method == "POST":
        codigo = (request.POST.get("codigo") or "").strip().upper()
        status = request.POST.get("status") or "livre"
        ativo = request.POST.get("ativo") in ("on", "true", "1", "True", "yes")

        if not codigo:
            messages.error(request, "Informe o código da doca.")
            return redirect("gerenciar_docas")

        Doca.objects.update_or_create(
            codigo=codigo,
            defaults={"status": status, "ativo": ativo},
        )
        messages.success(request, f"Doca {codigo} salva com sucesso.")
        return redirect("gerenciar_docas")

    docas = Doca.objects.order_by("codigo")
    return render(request, "docas/gerenciar.html", {"docas": docas})

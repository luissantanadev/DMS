from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.docas.models import Doca
from apps.operacao.models import Movimentacao
from apps.transportadoras.models import Transportadora


def _has_area_access(user, area):
    return user.is_superuser or user.groups.filter(name__in=(area, "Administradores")).exists()


@login_required
def selecionar_area(request):
    areas = []
    if _has_area_access(request.user, "Portaria"):
        areas.append({"nome": "Portaria", "url": "portaria"})
    if _has_area_access(request.user, "Box"):
        areas.extend([
            {"nome": "Dashboard", "url": "painel"},
            {"nome": "Box", "url": "box"},
        ])

    if not areas:
        raise PermissionDenied("Usuário sem área de acesso configurada.")

    return render(request, "dashboard/selecionar_area.html", {"areas": areas})


@login_required
def painel(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    docas = list(
        Doca.objects.filter(ativo=True).order_by("codigo").values("codigo", "status")
    )

    movimentacoes_ativas = {
        movimentacao.doca.codigo: movimentacao
        for movimentacao in Movimentacao.objects.select_related("doca").filter(
            doca__isnull=False,
            status__in=("em_operacao", "patio"),
        )
    }

    if not docas:
        docas = [
            {"codigo": "D01", "status": "livre"},
            {"codigo": "D02", "status": "carregamento"},
            {"codigo": "D03", "status": "recebimento"},
            {"codigo": "D04", "status": "bloqueada"},
            {"codigo": "D05", "status": "recebimento"},
            {"codigo": "D06", "status": "recebimento"},
            {"codigo": "D07", "status": "livre"},
            {"codigo": "D08", "status": "carregamento"},
            {"codigo": "D09", "status": "recebimento"},
            {"codigo": "D10", "status": "carregamento"},
            {"codigo": "D11", "status": "manual"},
            {"codigo": "D12", "status": "livre"},
            {"codigo": "D13", "status": "separacao"},
            {"codigo": "D14", "status": "separacao"},
            {"codigo": "D15", "status": "livre"},
        ]

    for doca in docas:
        doca.setdefault("carga", "")
        doca.setdefault("hora", "")
        movimentacao = movimentacoes_ativas.get(doca["codigo"])
        if movimentacao:
            doca["carga"] = f"{movimentacao.placa}"
            if movimentacao.carga:
                doca["carga"] += f" • {movimentacao.carga}"
            doca["hora"] = movimentacao.entrada_em.strftime("%H:%M") if movimentacao.entrada_em else "Em operação"

    return render(request, "dashboard/painel.html", {
        "docas": docas,
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def box(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    return render(request, "dashboard/box.html", {
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def portaria(request):
    if not _has_area_access(request.user, "Portaria"):
        raise PermissionDenied("Usuário sem acesso à Portaria.")

    if request.method == "POST":
        transportadora_id = request.POST.get("transportadora")
        doca_id = request.POST.get("doca")
        motorista_nome = (request.POST.get("motorista_nome") or "").strip()
        placa = (request.POST.get("placa") or "").strip().upper()
        tipo_operacao = request.POST.get("tipo_operacao") or "recebimento"

        if not transportadora_id or not motorista_nome or not placa:
            messages.error(request, "Informe transportadora, motorista e placa.")
            return redirect("portaria")

        try:
            transportadora = Transportadora.objects.get(id=transportadora_id, ativa=True)
        except Transportadora.DoesNotExist:
            messages.error(request, "Selecione uma transportadora ativa.")
            return redirect("portaria")

        doca = None
        if doca_id:
            try:
                doca = Doca.objects.get(id=doca_id, ativo=True, status="livre")
            except Doca.DoesNotExist:
                messages.error(request, "Selecione uma doca livre.")
                return redirect("portaria")

        entrada_em = timezone.now()
        data_entrada = request.POST.get("entrada_em")
        if data_entrada:
            try:
                entrada_em = timezone.make_aware(datetime.fromisoformat(data_entrada))
            except ValueError:
                messages.error(request, "Informe uma data e hora de entrada válida.")
                return redirect("portaria")

        movimentacao = Movimentacao.objects.create(
            transportadora=transportadora,
            doca=doca,
            motorista_nome=motorista_nome,
            motorista_cpf=(request.POST.get("motorista_cpf") or "").strip(),
            placa=placa,
            carga=(request.POST.get("carga") or "").strip(),
            tipo_operacao=tipo_operacao,
            peso_entrada=request.POST.get("peso_entrada") or None,
            entrada_em=entrada_em,
            observacoes=(request.POST.get("observacoes") or "").strip(),
            status="em_operacao" if doca else "patio",
        )
        if doca:
            doca.status = tipo_operacao
            doca.save(update_fields=("status",))
        messages.success(request, f"Entrada do veículo {placa} registrada com sucesso.")
        return redirect("portaria")

    movimentacoes = Movimentacao.objects.select_related("transportadora", "doca")[:8]
    return render(request, "dashboard/portaria.html", {
        "transportadoras": Transportadora.objects.filter(ativa=True).order_by("nome_fantasia"),
        "docas_livres": Doca.objects.filter(ativo=True, status="livre").order_by("codigo"),
        "movimentacoes": movimentacoes,
        "tem_box": _has_area_access(request.user, "Box"),
    })


@login_required
def finalizar_movimentacao(request, movimentacao_id):
    if not _has_area_access(request.user, "Portaria"):
        raise PermissionDenied("Usuário sem acesso à Portaria.")
    if request.method != "POST":
        raise PermissionDenied("A finalização deve ser enviada por POST.")

    try:
        movimentacao = Movimentacao.objects.select_related("doca").get(
            id=movimentacao_id,
            status__in=("patio", "em_operacao"),
        )
    except Movimentacao.DoesNotExist:
        messages.error(request, "Movimentação não encontrada ou já finalizada.")
        return redirect("portaria")

    peso_saida = request.POST.get("peso_saida") or None
    with transaction.atomic():
        movimentacao.peso_saida = peso_saida
        movimentacao.saida_em = timezone.now()
        movimentacao.status = "finalizada"
        movimentacao.save(update_fields=("peso_saida", "saida_em", "status", "atualizado_em"))
        if movimentacao.doca_id:
            movimentacao.doca.status = "livre"
            movimentacao.doca.save(update_fields=("status",))

    messages.success(request, f"Saída do veículo {movimentacao.placa} registrada com sucesso.")
    return redirect("portaria")

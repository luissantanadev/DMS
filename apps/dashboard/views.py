from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.docas.models import Doca
from apps.operacao.models import HistoricoMovimentacao, Motorista, Movimentacao, Veiculo
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
        Doca.objects.filter(ativo=True).order_by("codigo").values("id", "codigo", "status")
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
            {"id": 1, "codigo": "D01", "status": "livre"},
            {"id": 2, "codigo": "D02", "status": "carregamento"},
            {"id": 3, "codigo": "D03", "status": "recebimento"},
            {"id": 4, "codigo": "D04", "status": "bloqueada"},
            {"id": 5, "codigo": "D05", "status": "recebimento"},
            {"id": 6, "codigo": "D06", "status": "recebimento"},
            {"id": 7, "codigo": "D07", "status": "livre"},
            {"id": 8, "codigo": "D08", "status": "carregamento"},
            {"id": 9, "codigo": "D09", "status": "recebimento"},
            {"id": 10, "codigo": "D10", "status": "carregamento"},
            {"id": 11, "codigo": "D11", "status": "manual"},
            {"id": 12, "codigo": "D12", "status": "livre"},
            {"id": 13, "codigo": "D13", "status": "separacao"},
            {"id": 14, "codigo": "D14", "status": "separacao"},
            {"id": 15, "codigo": "D15", "status": "livre"},
        ]

    alertas = []
    now = timezone.now()
    for doca in docas:
        doca.setdefault("carga", "")
        doca.setdefault("hora", "")
        doca.setdefault("duracao_minutos", 0)
        doca.setdefault("alerta", "")
        movimentacao = movimentacoes_ativas.get(doca["codigo"])
        if movimentacao:
            doca["carga"] = f"{movimentacao.placa}"
            if movimentacao.carga:
                doca["carga"] += f" • {movimentacao.carga}"
            if movimentacao.entrada_em:
                duracao = (now - movimentacao.entrada_em).total_seconds() / 60
                doca["duracao_minutos"] = int(duracao)
                doca["hora"] = movimentacao.entrada_em.strftime("%H:%M")
                if doca["status"] == "patio" and duracao > 20:
                    doca["alerta"] = "Aguardando ação"
                    alertas.append(f"{doca['codigo']} aguardando há {doca['duracao_minutos']} min")
                elif doca["status"] == "em_operacao" and duracao > 60:
                    doca["alerta"] = "Operação prolongada"
                    alertas.append(f"{doca['codigo']} em operação há {doca['duracao_minutos']} min")
            else:
                doca["hora"] = "Em operação"

    docas_livres = sum(1 for d in docas if d["status"] == "livre")
    docas_ocupadas = sum(1 for d in docas if d["status"] != "livre" and d["status"] != "bloqueada")

    # Estatísticas de integração WMS
    from apps.integracao_wms.models import SincronizacaoWMS
    total_sincronizacoes = SincronizacaoWMS.objects.count()
    sincronizacoes_sucesso = SincronizacaoWMS.objects.filter(status="sucesso").count()
    sincronizacoes_erro = SincronizacaoWMS.objects.filter(status="erro").count()

    return render(request, "dashboard/painel.html", {
        "docas": docas,
        "docas_livres": docas_livres,
        "docas_ocupadas": docas_ocupadas,
        "alertas": alertas[:5],
        "tem_portaria": _has_area_access(request.user, "Portaria"),
        "wms_total": total_sincronizacoes,
        "wms_sucesso": sincronizacoes_sucesso,
        "wms_erro": sincronizacoes_erro,
    })


@login_required
def box(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    return render(request, "dashboard/box.html", {
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def gerenciar_historico(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    historico = HistoricoMovimentacao.objects.select_related("movimentacao__veiculo", "movimentacao__doca", "movimentacao__transportadora").order_by("-criado_em")
    return render(request, "dashboard/historico.html", {
        "historico": historico,
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def gerenciar_relatorios(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    filtro_status = request.GET.get("status")
    filtro_tipo = request.GET.get("tipo_operacao")
    filtro_doca = request.GET.get("doca")
    filtro_placa = request.GET.get("placa")

    movimentacoes = Movimentacao.objects.select_related("transportadora", "doca", "motorista", "veiculo").order_by("-criado_em")
    if filtro_status:
        movimentacoes = movimentacoes.filter(status=filtro_status)
    if filtro_tipo:
        movimentacoes = movimentacoes.filter(tipo_operacao=filtro_tipo)
    if filtro_doca:
        movimentacoes = movimentacoes.filter(doca__codigo__icontains=filtro_doca)
    if filtro_placa:
        movimentacoes = movimentacoes.filter(placa__icontains=filtro_placa)

    total_movimentacoes = movimentacoes.count()
    em_operacao = movimentacoes.filter(status="em_operacao").count()
    finalizadas = movimentacoes.filter(status="finalizada").count()
    aguardando = movimentacoes.filter(status="aguardando").count()
    recebimentos = movimentacoes.filter(tipo_operacao="recebimento").count()
    carregamentos = movimentacoes.filter(tipo_operacao="carregamento").count()

    return render(request, "dashboard/relatorios.html", {
        "movimentacoes": movimentacoes[:30],
        "total_movimentacoes": total_movimentacoes,
        "em_operacao": em_operacao,
        "finalizadas": finalizadas,
        "aguardando": aguardando,
        "recebimentos": recebimentos,
        "carregamentos": carregamentos,
        "filtro_status": filtro_status,
        "filtro_tipo": filtro_tipo,
        "filtro_doca": filtro_doca,
        "filtro_placa": filtro_placa,
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def gerenciar_motoristas(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    if request.method == "POST":
        Motorista.objects.update_or_create(
            cpf=(request.POST.get("cpf") or "").strip() or None,
            defaults={
                "nome": (request.POST.get("nome") or "").strip(),
                "telefone": (request.POST.get("telefone") or "").strip(),
                "ativo": request.POST.get("ativo") == "on",
            },
        )
        return redirect("gerenciar_motoristas")

    motoristas = Motorista.objects.order_by("nome")
    return render(request, "dashboard/motoristas.html", {
        "motoristas": motoristas,
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def gerenciar_veiculos(request):
    if not _has_area_access(request.user, "Box"):
        raise PermissionDenied("Usuário sem acesso ao Box.")

    if request.method == "POST":
        Veiculo.objects.update_or_create(
            placa=(request.POST.get("placa") or "").strip().upper(),
            defaults={
                "modelo": (request.POST.get("modelo") or "").strip(),
                "ano": int(request.POST.get("ano") or 0) or None,
                "ativo": request.POST.get("ativo") == "on",
            },
        )
        return redirect("gerenciar_veiculos")

    veiculos = Veiculo.objects.order_by("placa")
    return render(request, "dashboard/veiculos.html", {
        "veiculos": veiculos,
        "tem_portaria": _has_area_access(request.user, "Portaria"),
    })


@login_required
def portaria(request):
    if not _has_area_access(request.user, "Portaria"):
        raise PermissionDenied("Usuário sem acesso à Portaria.")

    if request.method == "POST":
        transportadora_id = request.POST.get("transportadora")
        doca_id = request.POST.get("doca")
        motorista_id = request.POST.get("motorista")
        veiculo_id = request.POST.get("veiculo")
        motorista_nome = (request.POST.get("motorista_nome") or "").strip()
        motorista_cpf = (request.POST.get("motorista_cpf") or "").strip()
        placa = (request.POST.get("placa") or "").strip().upper()
        tipo_operacao = request.POST.get("tipo_operacao") or "recebimento"

        if not transportadora_id or (not motorista_id and not motorista_nome) or (not veiculo_id and not placa):
            messages.error(request, "Informe transportadora, motorista e placa.")
            return redirect("portaria")

        try:
            transportadora = Transportadora.objects.get(id=transportadora_id, ativa=True)
        except Transportadora.DoesNotExist:
            messages.error(request, "Selecione uma transportadora ativa.")
            return redirect("portaria")

        if motorista_id:
            try:
                motorista = Motorista.objects.get(id=motorista_id, ativo=True)
            except Motorista.DoesNotExist:
                messages.error(request, "Selecione um motorista ativo.")
                return redirect("portaria")
        else:
            motorista = Motorista.objects.filter(nome__iexact=motorista_nome).first()
            if not motorista:
                motorista = Motorista.objects.create(nome=motorista_nome, cpf=motorista_cpf)
            elif motorista_cpf and not motorista.cpf:
                motorista.cpf = motorista_cpf
                motorista.save(update_fields=("cpf",))

        if veiculo_id:
            try:
                veiculo = Veiculo.objects.get(id=veiculo_id, ativo=True)
            except Veiculo.DoesNotExist:
                messages.error(request, "Selecione um veículo ativo.")
                return redirect("portaria")
        else:
            veiculo = Veiculo.objects.filter(placa__iexact=placa).first()
            if not veiculo:
                veiculo = Veiculo.objects.create(placa=placa, modelo=request.POST.get("veiculo_modelo", "").strip())

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
            motorista=motorista,
            veiculo=veiculo,
            motorista_nome=motorista.nome,
            motorista_cpf=motorista.cpf,
            placa=veiculo.placa,
            carga=(request.POST.get("carga") or "").strip(),
            tipo_operacao=tipo_operacao,
            peso_entrada=request.POST.get("peso_entrada") or None,
            entrada_em=entrada_em,
            observacoes=(request.POST.get("observacoes") or "").strip(),
            status="em_operacao" if doca else "patio",
        )
        HistoricoMovimentacao.objects.create(
            movimentacao=movimentacao,
            acao="entrada",
            descricao="Entrada registrada",
        )
        if doca:
            doca.status = tipo_operacao
            doca.save(update_fields=("status",))
        messages.success(request, f"Entrada do veículo {veiculo.placa} registrada com sucesso.")
        return redirect("portaria")

    movimentacoes = Movimentacao.objects.select_related("transportadora", "doca", "motorista", "veiculo")[:8]
    return render(request, "dashboard/portaria.html", {
        "transportadoras": Transportadora.objects.filter(ativa=True).order_by("nome_fantasia"),
        "motoristas": Motorista.objects.filter(ativo=True).order_by("nome"),
        "veiculos": Veiculo.objects.filter(ativo=True).order_by("placa"),
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
        HistoricoMovimentacao.objects.create(
            movimentacao=movimentacao,
            acao="saida",
            descricao="Saída registrada",
        )
        if movimentacao.doca_id:
            movimentacao.doca.status = "livre"
            movimentacao.doca.save(update_fields=("status",))

    messages.success(request, f"Saída do veículo {movimentacao.placa} registrada com sucesso.")
    return redirect("portaria")

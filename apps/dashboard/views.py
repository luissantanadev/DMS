from django.shortcuts import render

def painel(request):
    docas = [
        {"codigo": "D01", "status": "livre", "carga": "", "hora": ""},
        {"codigo": "D02", "status": "carregamento", "carga": "9700418516", "hora": "17:00"},
        {"codigo": "D03", "status": "recebimento", "carga": "9700418523", "hora": "18:00"},
        {"codigo": "D04", "status": "bloqueada", "carga": "", "hora": ""},
        {"codigo": "D05", "status": "recebimento", "carga": "9700418515", "hora": "09:00"},
        {"codigo": "D06", "status": "recebimento", "carga": "9700418213", "hora": "06:00"},
        {"codigo": "D07", "status": "livre", "carga": "", "hora": ""},
        {"codigo": "D08", "status": "carregamento", "carga": "9700418498", "hora": "13:00"},
        {"codigo": "D09", "status": "recebimento", "carga": "9700418300", "hora": "02:00"},
        {"codigo": "D10", "status": "carregamento", "carga": "9700418653", "hora": "16:00"},
        {"codigo": "D11", "status": "manual", "carga": "", "hora": ""},
        {"codigo": "D12", "status": "livre", "carga": "", "hora": ""},
        {"codigo": "D13", "status": "separacao", "carga": "9700418455", "hora": "10:00"},
        {"codigo": "D14", "status": "separacao", "carga": "9700418450", "hora": "08:00"},
        {"codigo": "D15", "status": "livre", "carga": "", "hora": ""},
    ]
    return render(request, "dashboard/painel.html", {"docas": docas})

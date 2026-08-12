from django.http import JsonResponse
from .models import Doca

def lista_docas(request):
    data = list(Doca.objects.values("id", "codigo", "status", "ativo"))
    return JsonResponse({"docas": data})

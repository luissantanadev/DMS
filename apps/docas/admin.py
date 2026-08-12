from django.contrib import admin
from .models import Doca

@admin.register(Doca)
class DocaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "status", "ativo")
    list_filter = ("status", "ativo")
    search_fields = ("codigo",)

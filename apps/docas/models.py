from django.db import models

class Doca(models.Model):
    STATUS_CHOICES = [
        ("livre", "Livre"),
        ("recebimento", "Recebimento"),
        ("carregamento", "Carregamento"),
        ("separacao", "Em Separação"),
        ("aguardando", "Aguardando"),
        ("atrasada", "Atrasada"),
        ("bloqueada", "Bloqueada"),
        ("manual", "Manual"),
    ]

    codigo = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="livre")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.codigo

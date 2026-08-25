from django.db import models


class Transportadora(models.Model):
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Transportadora"
        verbose_name_plural = "Transportadoras"

    def __str__(self):
        return self.nome_fantasia or self.razao_social

from django.db import models
from django.contrib.auth.models import User


class Fornecedor(models.Model):
    cnpj = models.CharField(max_length=18, unique=True)  # formato 00.000.000/0000-00
    nome = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} — {self.cnpj}"


class NotaFiscal(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente (estoquista)"),
        ("em_analise", "Em análise (fiscal)"),
        ("lancada", "Lançada"),
    ]

    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.PROTECT, related_name="notas"
    )
    numero_nota = models.CharField(max_length=50)
    chave_acesso = models.CharField(max_length=44, unique=True)
    pdf_nota = models.FileField(upload_to="notas/%Y/%m/")
    observacao = models.TextField(max_length=1000, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")

    criado_por = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="notas_criadas"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    data_envio_fiscal = models.DateTimeField(null=True, blank=True)
    data_lancamento = models.DateTimeField(null=True, blank=True)
    lancada_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notas_lancadas",
    )

    class Meta:
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"NF {self.numero_nota} — {self.fornecedor.nome}"


class HistoricoNotaFiscal(models.Model):
    nota = models.ForeignKey(
        NotaFiscal, on_delete=models.CASCADE, related_name="historico"
    )
    acao = models.CharField(
        max_length=100
    )  # ex: "criada", "enviada ao fiscal", "lançada"
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_hora = models.DateTimeField(auto_now_add=True)
    detalhes = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_hora"]

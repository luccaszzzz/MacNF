from django.contrib import admin
from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal

admin.site.register(Fornecedor)
admin.site.register(NotaFiscal)
admin.site.register(HistoricoNotaFiscal)
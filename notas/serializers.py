from rest_framework import serializers
from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ["id", "cnpj", "nome", "criado_em"]


class HistoricoSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = HistoricoNotaFiscal
        fields = ["id", "acao", "usuario", "data_hora", "detalhes"]


class NotaFiscalSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source="fornecedor.nome", read_only=True)
    criado_por = serializers.StringRelatedField(read_only=True)
    lancada_por = serializers.StringRelatedField(read_only=True)
    historico = HistoricoSerializer(many=True, read_only=True)

    class Meta:
        model = NotaFiscal
        fields = [
            "id",
            "fornecedor",
            "fornecedor_nome",
            "numero_nota",
            "chave_acesso",
            "pdf_nota",
            "observacao",
            "status",
            "criado_por",
            "data_criacao",
            "data_envio_fiscal",
            "data_lancamento",
            "lancada_por",
            "historico",
        ]
        read_only_fields = [
            "status",
            "criado_por",
            "data_criacao",
            "data_envio_fiscal",
            "data_lancamento",
            "lancada_por",
        ]

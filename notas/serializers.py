import re
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import serializers
from validate_docbr import CNPJ
from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal, AnexoNotaFiscal


def validar_cnpj(value):
    """Valida CNPJ com cálculo de dígito verificador."""
    cnpj_limpo = re.sub(r"\D", "", value or "")

    if len(cnpj_limpo) != 14:
        raise serializers.ValidationError("CNPJ deve ter 14 dígitos.")

    if not CNPJ().validate(cnpj_limpo):
        raise serializers.ValidationError("CNPJ inválido. Verifique os números.")

    # Formata pro padrão 00.000.000/0000-00
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"


def validar_chave_acesso(value):
    """Valida chave de acesso da NFe (44 dígitos + DV módulo 11)."""
    chave_limpa = re.sub(r"\D", "", value or "")

    if len(chave_limpa) != 44:
        raise serializers.ValidationError(
            "Chave de acesso deve ter exatamente 44 dígitos numéricos."
        )

    # Cálculo do dígito verificador (módulo 11)
    pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6  # 48 valores
    soma = sum(int(chave_limpa[i]) * pesos[42 - i] for i in range(43))
    resto = soma % 11
    dv_calculado = 0 if resto < 2 else 11 - resto

    if int(chave_limpa[43]) != dv_calculado:
        raise serializers.ValidationError(
            "Chave de acesso com dígito verificador inválido. "
            "Confira a chave no PDF da nota."
        )

    return chave_limpa


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ["id", "cnpj", "nome", "criado_em"]

    def validate_cnpj(self, value):
        return validar_cnpj(value)


class HistoricoSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = HistoricoNotaFiscal
        fields = ["id", "acao", "usuario", "data_hora", "detalhes"]


class AnexoNotaFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnexoNotaFiscal
        fields = ["id", "arquivo", "criado_em"]


class NotaFiscalSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source="fornecedor.nome", read_only=True)
    criado_por = serializers.StringRelatedField(read_only=True)
    lancada_por = serializers.StringRelatedField(read_only=True)
    observacao_resposta_por = serializers.StringRelatedField(read_only=True)
    historico = HistoricoSerializer(many=True, read_only=True)
    anexos = serializers.SerializerMethodField()

    class Meta:
        model = NotaFiscal
        fields = [
            "id",
            "fornecedor",
            "fornecedor_nome",
            "numero_nota",
            "chave_acesso",
            "observacao_resposta",
            "observacao_resposta_por",
            "observacao_resposta_data",
            "loja",
            "pdf_nota",
            "observacao",
            "status",
            "criado_por",
            "data_criacao",
            "data_envio_fiscal",
            "data_lancamento",
            "lancada_por",
            "historico",
            "anexos",
        ]
        read_only_fields = [
            "status",
            "criado_por",
            "data_criacao",
            "data_envio_fiscal",
            "data_lancamento",
            "lancada_por",
            "observacao_resposta_por",
            "observacao_resposta_data",
        ]

    def get_anexos(self, obj):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'notas_anexonotafiscal'")
                exists = cursor.fetchone() is not None
        except Exception:
            exists = False

        if not exists:
            return []

        try:
            queryset = obj.anexos.all()
        except (ProgrammingError, OperationalError):
            return []
        return AnexoNotaFiscalSerializer(queryset, many=True, context=self.context).data

    def validate_chave_acesso(self, value):
        return validar_chave_acesso(value)

    def validate_pdf_nota(self, value):
        """Aceita PDF ou imagens comuns."""
        extensoes_validas = [".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"]
        nome = value.name.lower()

        if not any(nome.endswith(ext) for ext in extensoes_validas):
            raise serializers.ValidationError(
                "Arquivo deve ser PDF, JPG, PNG, HEIC ou WEBP."
            )

        # Limite de 10 MB no upload (antes da compressão)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Arquivo muito grande. Máximo: 10 MB.")

        return value

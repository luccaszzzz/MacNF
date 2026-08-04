import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal
from .serializers import NotaFiscalSerializer


class NotaFiscalApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="estoquista", password="123456"
        )
        self.group = Group.objects.create(name="estoquista")
        self.user.groups.add(self.group)
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.fornecedor = Fornecedor.objects.create(
            cnpj="11.111.111/1111-11",
            nome="Fornecedor Teste",
        )

    def _chave_acesso_valida(self):
        base = "1234567890123456789012345678901234567890123"
        pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6
        soma = sum(int(base[i]) * pesos[42 - i] for i in range(43))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        return base + str(dv)

    def _make_nota(self, **overrides):
        defaults = {
            "fornecedor": self.fornecedor,
            "numero_nota": "100",
            "chave_acesso": self._chave_acesso_valida() + str(uuid.uuid4().int % 10),
            "loja": "canguaretama",
            "observacao": "nota para teste",
            "status": "em_analise",
            "criado_por": self.user,
        }
        defaults.update(overrides)
        return NotaFiscal.objects.create(**defaults)

    def test_filtro_por_busca_fornecedor_e_data(self):
        nota = self._make_nota(
            numero_nota="123",
            observacao="observacao relevante",
        )
        self._make_nota(
            numero_nota="999",
            observacao="outra nota",
        )

        response = self.client.get(
            "/api/notas/",
            {
                "search": "relevante",
                "fornecedor": str(self.fornecedor.id),
                "data_criacao": str(nota.data_criacao.date()),
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], nota.id)

    def test_envio_multiplo_de_arquivos_cria_anexo(self):
        arquivo1 = SimpleUploadedFile(
            "nota1.pdf",
            b"conteudo pdf 1",
            content_type="application/pdf",
        )
        arquivo2 = SimpleUploadedFile(
            "nota2.jpg",
            b"conteudo imagem 2",
            content_type="image/jpeg",
        )

        response = self.client.post(
            "/api/notas/",
            {
                "fornecedor": str(self.fornecedor.id),
                "numero_nota": "250",
                "chave_acesso": self._chave_acesso_valida(),
                "loja": "pipa",
                "observacao": "múltiplos arquivos",
                "pdf_nota": [arquivo1, arquivo2],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        nota = NotaFiscal.objects.get(numero_nota="250")
        self.assertTrue(nota.pdf_nota)
        self.assertEqual(nota.anexos.count(), 1)
        self.assertIn("nota2", nota.anexos.first().arquivo.name)

    def test_excluir_nota_remove_arquivo_do_storage(self):
        arquivo = SimpleUploadedFile(
            "nota.pdf",
            b"conteudo pdf",
            content_type="application/pdf",
        )
        nota = NotaFiscal.objects.create(
            fornecedor=self.fornecedor,
            numero_nota="300",
            chave_acesso=self._chave_acesso_valida(),
            loja="canguaretama",
            observacao="nota para teste de exclusão",
            status="em_analise",
            criado_por=self.user,
            pdf_nota=arquivo,
        )

        caminho_arquivo = nota.pdf_nota.name
        nota.delete()

        self.assertTrue(caminho_arquivo)
        self.assertFalse(nota.pdf_nota.storage.exists(caminho_arquivo))

    def test_serializer_nao_quebra_quando_tabela_de_anexos_nao_existe(self):
        with connection.schema_editor() as editor:
            editor.execute("DROP TABLE IF EXISTS notas_anexonotafiscal")

        nota = self._make_nota(numero_nota="400")
        serializer = NotaFiscalSerializer(nota)

        self.assertEqual(serializer.data["anexos"], [])

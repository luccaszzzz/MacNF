from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from PIL import Image
from io import BytesIO

from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal, AnexoNotaFiscal
from .serializers import FornecedorSerializer, NotaFiscalSerializer
from .permissions import (
    FornecedorPermission,
    NotaFiscalPermission,
    is_fiscal,
    is_estoquista,
    is_compras,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "is_fiscal": is_fiscal(user),
                "is_estoquista": is_estoquista(user),
                "is_compras": is_compras(user),
            }
        )


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    permission_classes = [FornecedorPermission]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            count = instance.notas.count()
            return Response(
                {
                    "erro": f'Não é possível excluir "{instance.nome}": existem {count} nota(s) fiscal(is) vinculada(s) a este fornecedor.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotaFiscalViewSet(viewsets.ModelViewSet):
    serializer_class = NotaFiscalSerializer
    permission_classes = [NotaFiscalPermission]

    def get_queryset(self):
        qs = NotaFiscal.objects.all().select_related(
            "fornecedor", "criado_por", "lancada_por", "observacao_resposta_por"
        )
        # Estoquista (não-admin) só vê suas próprias notas
        if is_estoquista(self.request.user) and not self.request.user.is_superuser:
            qs = qs.filter(criado_por=self.request.user)

        search = (self.request.query_params.get("search") or "").strip()
        fornecedor_id = self.request.query_params.get("fornecedor")
        data_criacao = self.request.query_params.get("data_criacao")

        if search:
            qs = qs.filter(
                Q(numero_nota__icontains=search)
                | Q(chave_acesso__icontains=search)
                | Q(observacao__icontains=search)
                | Q(fornecedor__nome__icontains=search)
            )
        if fornecedor_id:
            qs = qs.filter(fornecedor_id=fornecedor_id)
        if data_criacao:
            qs = qs.filter(data_criacao__date=data_criacao)

        return qs

    def _processar_arquivo(self, arquivo):
        if not arquivo:
            return arquivo

        if arquivo.content_type and arquivo.content_type.startswith("image/"):
            try:
                img = Image.open(arquivo)

                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                nome_novo = arquivo.name.rsplit(".", 1)[0] + ".jpg"
                return ContentFile(buffer.read(), name=nome_novo)
            except Exception:
                return arquivo

        return arquivo

    def perform_create(self, serializer):
        """Cria nota — comprime imagens automaticamente antes de salvar."""
        arquivos = list(self.request.FILES.getlist("pdf_nota"))
        if not arquivos:
            arquivo = self.request.FILES.get("pdf_nota")
            if arquivo:
                arquivos = [arquivo]

        arquivo_principal = self._processar_arquivo(arquivos[0]) if arquivos else None
        if arquivo_principal:
            serializer.validated_data["pdf_nota"] = arquivo_principal

        nota = serializer.save(
            criado_por=self.request.user,
            status="em_analise",
            data_envio_fiscal=timezone.now(),
        )

        for arquivo_extra in arquivos[1:]:
            arquivo_processado = self._processar_arquivo(arquivo_extra)
            AnexoNotaFiscal.objects.create(nota=nota, arquivo=arquivo_processado)

        HistoricoNotaFiscal.objects.create(
            nota=nota,
            acao="criada e enviada ao fiscal",
            usuario=self.request.user,
        )

    def perform_update(self, serializer):
        """Edita nota — só permite enquanto status='em_analise'."""
        nota = self.get_object()
        if nota.status == "lancada":
            raise PermissionDenied("Nota lançada não pode ser editada.")
        nota_atualizada = serializer.save()

        # Se o fiscal respondeu à observação, registra autor e data e cria histórico específico
        resposta = (
            serializer.validated_data.get("observacao_resposta")
            if hasattr(serializer, "validated_data")
            else None
        )
        if resposta and (is_fiscal(self.request.user) or is_compras(self.request.user)):
            nota_atualizada.observacao_resposta_por = self.request.user
            nota_atualizada.observacao_resposta_data = timezone.now()
            nota_atualizada.save()
            HistoricoNotaFiscal.objects.create(
                nota=nota_atualizada,
                acao="resposta à observação",
                usuario=self.request.user,
                detalhes=resposta,
            )
        else:
            HistoricoNotaFiscal.objects.create(
                nota=nota_atualizada,
                acao="editada",
                usuario=self.request.user,
                detalhes="Dados da nota foram alterados pelo estoquista.",
            )

    def perform_destroy(self, instance):
        """Exclui nota — só permite enquanto status='em_analise'."""
        if instance.status == "lancada":
            raise PermissionDenied("Nota lançada não pode ser excluída.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def lancar(self, request, pk=None):
        nota = self.get_object()
        if nota.status == "lancada":
            return Response({"erro": "Nota já está lançada."}, status=400)
        nota.status = "lancada"
        nota.data_lancamento = timezone.now()
        nota.lancada_por = request.user
        nota.save()
        HistoricoNotaFiscal.objects.create(
            nota=nota,
            acao="lançada",
            usuario=request.user,
            detalhes=request.data.get("observacao", ""),
        )
        return Response(NotaFiscalSerializer(nota).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        now = timezone.now()
        return Response(
            {
                "total": qs.count(),
                "em_analise": qs.filter(status="em_analise").count(),
                "lancadas_mes": qs.filter(
                    status="lancada",
                    data_lancamento__year=now.year,
                    data_lancamento__month=now.month,
                ).count(),
                "lancadas_total": qs.filter(status="lancada").count(),
            }
        )

    @action(detail=False, methods=["get"])
    def relatorio(self, request):
        ano = int(request.query_params.get("ano", timezone.now().year))
        mes = request.query_params.get("mes")
        qs = NotaFiscal.objects.filter(status="lancada", data_lancamento__year=ano)
        if mes:
            qs = qs.filter(data_lancamento__month=int(mes))
        return Response(
            {
                "ano": ano,
                "mes": mes,
                "total_lancadas": qs.count(),
                "por_fornecedor": list(
                    qs.values("fornecedor__nome")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
                "notas": NotaFiscalSerializer(qs, many=True).data,
            }
        )

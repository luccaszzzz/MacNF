from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from .models import Fornecedor, NotaFiscal, HistoricoNotaFiscal
from .serializers import FornecedorSerializer, NotaFiscalSerializer
from .permissions import (
    FornecedorPermission, NotaFiscalPermission, is_fiscal, is_estoquista,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username,
            'is_fiscal': is_fiscal(user),
            'is_estoquista': is_estoquista(user),
        })


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    permission_classes = [FornecedorPermission]


class NotaFiscalViewSet(viewsets.ModelViewSet):
    serializer_class = NotaFiscalSerializer
    permission_classes = [NotaFiscalPermission]

    def get_queryset(self):
        qs = NotaFiscal.objects.all().select_related(
            'fornecedor', 'criado_por', 'lancada_por'
        )
        # Estoquista (não-admin) só vê suas próprias notas
        if is_estoquista(self.request.user) and not self.request.user.is_superuser:
            qs = qs.filter(criado_por=self.request.user)
        return qs

    def perform_create(self, serializer):
        nota = serializer.save(
            criado_por=self.request.user,
            status='em_analise',
            data_envio_fiscal=timezone.now(),
        )
        HistoricoNotaFiscal.objects.create(
            nota=nota, acao='criada e enviada ao fiscal', usuario=self.request.user
        )

    @action(detail=True, methods=['post'])
    def lancar(self, request, pk=None):
        nota = self.get_object()
        if nota.status == 'lancada':
            return Response({'erro': 'Nota já está lançada.'}, status=400)
        nota.status = 'lancada'
        nota.data_lancamento = timezone.now()
        nota.lancada_por = request.user
        nota.save()
        HistoricoNotaFiscal.objects.create(
            nota=nota, acao='lançada', usuario=request.user,
            detalhes=request.data.get('observacao', '')
        )
        return Response(NotaFiscalSerializer(nota).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        now = timezone.now()
        return Response({
            'total': qs.count(),
            'em_analise': qs.filter(status='em_analise').count(),
            'lancadas_mes': qs.filter(
                status='lancada',
                data_lancamento__year=now.year,
                data_lancamento__month=now.month,
            ).count(),
            'lancadas_total': qs.filter(status='lancada').count(),
        })

    @action(detail=False, methods=['get'])
    def relatorio(self, request):
        ano = int(request.query_params.get('ano', timezone.now().year))
        mes = request.query_params.get('mes')
        qs = NotaFiscal.objects.filter(status='lancada', data_lancamento__year=ano)
        if mes:
            qs = qs.filter(data_lancamento__month=int(mes))
        return Response({
            'ano': ano,
            'mes': mes,
            'total_lancadas': qs.count(),
            'por_fornecedor': list(
                qs.values('fornecedor__nome').annotate(total=Count('id')).order_by('-total')
            ),
            'notas': NotaFiscalSerializer(qs, many=True).data,
        })
from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_fiscal(user):
    return user.is_authenticated and (
        user.groups.filter(name="setor_fiscal").exists() or user.is_superuser
    )


def is_estoquista(user):
    return user.is_authenticated and (
        user.groups.filter(name="estoquista").exists() or user.is_superuser
    )


class FornecedorPermission(BasePermission):
    """Ambos os perfis podem criar, listar e excluir fornecedores."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return is_estoquista(request.user) or is_fiscal(request.user)


class NotaFiscalPermission(BasePermission):
    """
    Estoquista:
      - cria notas
      - vê e edita apenas as próprias notas (e só enquanto não lançadas)
    Setor fiscal:
      - vê todas as notas
      - lança notas
      - acessa relatório e estatísticas
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Ações exclusivas do fiscal
        if view.action in ("lancar", "relatorio"):
            return is_fiscal(request.user)

        # Criar nota: apenas estoquista (ou admin)
        if view.action == "create":
            return is_estoquista(request.user)

        # Leitura, edição, exclusão: ambos autenticados — verifica nota a nota
        return True

    def has_object_permission(self, request, view, obj):
        # Fiscal pode tudo nos objetos
        if is_fiscal(request.user):
            return True

        # Estoquista: só mexe nas próprias notas
        if obj.criado_por != request.user:
            return False

        # Estoquista não pode editar/excluir nota lançada
        if request.method not in SAFE_METHODS and obj.status == "lancada":
            return False

        return True

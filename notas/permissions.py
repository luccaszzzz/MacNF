from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_fiscal(user):
    return user.is_authenticated and (
        user.groups.filter(name="setor_fiscal").exists() or user.is_superuser
    )


def is_estoquista(user):
    return user.is_authenticated and (
        user.groups.filter(name="estoquista").exists() or user.is_superuser
    )


def is_compras(user):
    return user.is_authenticated and (
        user.groups.filter(name="setor_compras").exists() or user.is_superuser
    )


class FornecedorPermission(BasePermission):
    """Estoquista, fiscal ou compras podem criar, listar e excluir fornecedores."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (
            is_estoquista(request.user)
            or is_fiscal(request.user)
            or is_compras(request.user)
        )


class NotaFiscalPermission(BasePermission):
    """
    Estoquista e compras:
      - criam notas
      - veem e editam apenas as próprias notas (e só enquanto não lançadas)
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

        # Criar nota: estoquista ou compras (ou admin)
        if view.action == "create":
            return is_estoquista(request.user) or is_compras(request.user)

        # Leitura, edição, exclusão: ambos autenticados — verifica nota a nota
        return True

    def has_object_permission(self, request, view, obj):
        # Fiscal pode tudo nos objetos
        if is_fiscal(request.user):
            return True

        # Compras pode ver todas as notas, e editar/excluir apenas suas próprias não lançadas
        if is_compras(request.user):
            if request.method in SAFE_METHODS:
                return True
            if obj.criado_por != request.user:
                return False
            if request.method not in SAFE_METHODS and obj.status == "lancada":
                return False
            return True

        # Estoquista: só mexe nas próprias notas
        if obj.criado_por != request.user:
            return False

        # Estoquista não pode editar/excluir nota lançada
        if request.method not in SAFE_METHODS and obj.status == "lancada":
            return False

        return True

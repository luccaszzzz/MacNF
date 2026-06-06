from rest_framework.routers import DefaultRouter
from .views import FornecedorViewSet, NotaFiscalViewSet

router = DefaultRouter()
router.register('fornecedores', FornecedorViewSet)
router.register('notas', NotaFiscalViewSet, basename='nota')
urlpatterns = router.urls

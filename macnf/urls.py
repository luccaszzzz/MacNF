import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from notas.views import CustomAuthToken

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("api/", include("notas.urls")),
    path("api/login/", CustomAuthToken.as_view()),
]

# Admin só existe como rota se ENABLE_ADMIN=true estiver setado no ambiente (Railway).
# ADMIN_PATH é OBRIGATÓRIO via variável de ambiente - repositório é público,
# nenhum valor real de caminho pode aparecer aqui no código.
if os.environ.get("ENABLE_ADMIN") == "true":
    ADMIN_PATH = os.environ["ADMIN_PATH"]
    urlpatterns.append(path(ADMIN_PATH, admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
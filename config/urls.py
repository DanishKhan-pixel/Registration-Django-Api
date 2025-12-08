from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from authentication.views import HealthCheckView
from .api_docs import urlpatterns as api_docs_urls
from django.views.generic import RedirectView


API_VERSION = 'api/v1'


urlpatterns = [
   path('admin/', admin.site.urls),  
   path('', RedirectView.as_view(url='/api-docs/', permanent=False)),
   path('health', HealthCheckView.as_view(), name='health-check'),
   path(f'{API_VERSION}/auth/', include('authentication.urls')),
   path(f'{API_VERSION}/login-history', include('authentication.login_history_urls')),
   path(f'{API_VERSION}/roles', include('role.urls')),

   *api_docs_urls,
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

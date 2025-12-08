"""
URL configuration for config project.


The `urlpatterns` list routes URLs to views. For more information please see:
   https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
   1. Add an import:  from my_app import views
   2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
   1. Add an import:  from other_app.views import Home
   2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
   1. Import the include() function: from django.urls import include, path
   2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
   path(f'{API_VERSION}/organizations/external', include('organization.external_apis_urls')),
   path(f'{API_VERSION}/organizations', include('organization.urls')),
   path(f'{API_VERSION}/dashboard/', include('dashboard.urls')),
   *api_docs_urls,
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

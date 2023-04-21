from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordResetConfirmView,
    PasswordResetView, UserDetailsView,
)

from . import views, whitelistViews, sslCertViews, purgeCdnCacheViews

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('dj-rest-auth/login/', LoginView.as_view(), name='rest_login'),
    path('dj-rest-auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('jwt/verify/', views.verify, name='token_verify'),
    path('refresh/', views.refresh, name='api'),
    path('getData/', views.getData, name='api'),
    path('modifyTag/', views.modifyTag, name='api'),
    path('getOrphanData/', views.getOrphanData, name='api'),
    path('getLogData/', views.getLogData, name='api'),
    path('getIcpData/', views.getIcpData, name='api'),
    path('icpDescription/', views.icpDescription, name='api'),
    path('getSupportedDomainList/', whitelistViews.getSupportedDomainList, name='api'),
    path('cdnWhitelist/', whitelistViews.cdnWhitelist, name='api'),
    path('whitelistCsv/', whitelistViews.whitelistCsv, name='api'),
    path('certPurchase/', sslCertViews.certPurchase, name='api'),
    path('getPurgeDomainList/', purgeCdnCacheViews.getPurgeDomainList, name='api'),
    path('purgeCdnCache/', purgeCdnCacheViews.purgeCache, name='api'),
    path('getH5DomainList/', purgeCdnCacheViews.getH5DomainList, name='api'),
    path('purgeH5CdnCache/', purgeCdnCacheViews.purgeH5Cache, name='api'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from monitor.views import ServiceViewSet, TeamViewSet

router = DefaultRouter()
router.register('teams', TeamViewSet)
router.register('services', ServiceViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]

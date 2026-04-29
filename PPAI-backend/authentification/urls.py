from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentification.views import AuthenticationViewSet

router = DefaultRouter()
router.register(r"auth", AuthenticationViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]

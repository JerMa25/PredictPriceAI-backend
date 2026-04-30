from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentification.views import AuthentificationViewSet

router = DefaultRouter()
router.register(r"auth", AuthentificationViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]

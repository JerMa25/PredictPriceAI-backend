from django.urls import path, include
from rest_framework.routers import DefaultRouter
from model.views import PredictionViewSet

router = DefaultRouter()
router.register(r"prediction", PredictionViewSet, basename="prediction")

urlpatterns = [
    path("", include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from product.views import ProductViewSet

router = DefaultRouter()
router.register(r"product", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from product.services import (
    get_all_products,
    get_product_by_id,
    get_products_by_market,
)


class ProductViewSet(viewsets.ViewSet):
    """
    API endpoints pour la récupération des produits depuis le modèle ML.
    """

    @extend_schema(
        description="Retourne la liste de tous les produits disponibles dans le modèle ML",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "example": 1},
                                "name": {"type": "string", "example": "Tomate"},
                                "market_id": {"type": "integer", "example": 3},
                            },
                        },
                    },
                    "count": {"type": "integer"},
                },
            },
            500: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
        },
    )
    def list(self, request: Request):
        """Retourne tous les produits avec leur id et leur market_id."""
        products = get_all_products()

        if products is None:
            return Response(
                {
                    "success": False,
                    "message": "Erreur lors du chargement des produits.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "count": len(products),
                "data": products,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description="Retourne un produit par son identifiant",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Identifiant du produit",
            )
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "example": 1},
                            "name": {"type": "string", "example": "Tomate"},
                            "market_id": {"type": "integer", "example": 3},
                        },
                    },
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
            404: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
        },
    )
    def retrieve(self, request: Request, pk=None):
        """Retourne un produit par son id."""
        try:
            product_id = int(pk)
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "L'identifiant doit être un entier.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_product_by_id(product_id)

        if product is None:
            return Response(
                {
                    "success": False,
                    "message": f"Produit avec l'id {product_id} introuvable.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "data": product,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description="Retourne tous les produits disponibles dans un marché donné",
        parameters=[
            OpenApiParameter(
                name="market_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Identifiant du marché",
            )
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "market_id": {"type": "integer"},
                    "count": {"type": "integer"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "example": 1},
                                "name": {"type": "string", "example": "Tomate"},
                                "market_id": {"type": "integer", "example": 3},
                            },
                        },
                    },
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
        },
    )
    @action(detail=False, methods=["get"], url_path=r"market/(?P<market_id>[0-9]+)")
    def by_market(self, request: Request, market_id=None):
        """Retourne tous les produits d'un marché donné."""
        try:
            market_id_int = int(market_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "Le market_id doit être un entier.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = get_products_by_market(market_id_int)

        return Response(
            {
                "success": True,
                "market_id": market_id_int,
                "count": len(products),
                "data": products,
            },
            status=status.HTTP_200_OK,
        )
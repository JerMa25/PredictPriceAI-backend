from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from product.services import (
    get_all_products,
    get_product_by_id,
    get_products_by_market,
    products_count,
    products_count_by_market,
)

# ── Réponses réutilisables ────────────────────────────────────────────────────
_PRODUCT_OBJECT = {
    "type": "object",
    "properties": {
        "id":        {"type": "integer", "example": 1},
        "name":      {"type": "string",  "example": "Maize (white)"},
        "market_id": {"type": "integer", "example": 3},
    },
}
_RESPONSE_ERROR = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": False},
        "message": {"type": "string"},
    },
}


class ProductViewSet(viewsets.ViewSet):
    """
    API endpoints pour la récupération des produits depuis le dataset WFP.
    """

    @extend_schema(
        tags=["Produits"],
        summary="Liste de tous les produits",
        description=(
            "Retourne la liste complète des produits agricoles disponibles dans le dataset WFP. "
            "Chaque produit est identifié par un `id`, un `name` et le `market_id` du marché associé."
        ),
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "count":   {"type": "integer", "example": 55},
                    "data":    {"type": "array", "items": _PRODUCT_OBJECT},
                },
            },
            500: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={
                    "success": True,
                    "count": 2,
                    "data": [
                        {"id": 1, "name": "Maize (white)", "market_id": 3},
                        {"id": 2, "name": "Rice (local)",  "market_id": 5},
                    ],
                },
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "Erreur serveur",
                value={"success": False, "message": "Erreur lors du chargement des produits."},
                response_only=True, status_codes=["500"],
            ),
        ],
    )
    def list(self, request: Request):
        """GET /products/ — Retourne tous les produits."""
        products = get_all_products()

        if products is None:
            return Response(
                {"success": False, "message": "Erreur lors du chargement des produits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"success": True, "count": len(products), "data": products},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Produits"],
        summary="Récupérer un produit par ID",
        description="Retourne les détails d'un produit spécifique à partir de son identifiant.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Identifiant unique du produit",
            )
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "data":    _PRODUCT_OBJECT,
                },
            },
            400: _RESPONSE_ERROR,
            404: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={"success": True, "data": {"id": 1, "name": "Maize (white)", "market_id": 3}},
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "ID invalide",
                value={"success": False, "message": "L'identifiant doit être un entier."},
                response_only=True, status_codes=["400"],
            ),
            OpenApiExample(
                "Produit introuvable",
                value={"success": False, "message": "Produit avec l'id 99 introuvable."},
                response_only=True, status_codes=["404"],
            ),
        ],
    )
    def retrieve(self, request: Request, pk=None):
        """GET /products/{id}/ — Retourne un produit par son ID."""
        try:
            product_id = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"success": False, "message": "L'identifiant doit être un entier."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_product_by_id(product_id)

        if product is None:
            return Response(
                {"success": False, "message": f"Produit avec l'id {product_id} introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"success": True, "data": product},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Produits"],
        summary="Produits d'un marché",
        description=(
            "Retourne la liste de tous les produits disponibles dans un marché donné, "
            "identifié par son `market_id`."
        ),
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
                    "success":   {"type": "boolean", "example": True},
                    "market_id": {"type": "integer", "example": 3},
                    "count":     {"type": "integer", "example": 12},
                    "data":      {"type": "array", "items": _PRODUCT_OBJECT},
                },
            },
            400: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={
                    "success":   True,
                    "market_id": 3,
                    "count":     2,
                    "data": [
                        {"id": 1, "name": "Maize (white)", "market_id": 3},
                        {"id": 4, "name": "Tomatoes",      "market_id": 3},
                    ],
                },
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "market_id invalide",
                value={"success": False, "message": "Le market_id doit être un entier."},
                response_only=True, status_codes=["400"],
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path=r"market/(?P<market_id>[0-9]+)")
    def by_market(self, request: Request, market_id=None):
        """GET /products/market/{market_id}/ — Produits d'un marché."""
        try:
            market_id_int = int(market_id)
        except (TypeError, ValueError):
            return Response(
                {"success": False, "message": "Le market_id doit être un entier."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = get_products_by_market(market_id_int)

        return Response(
            {"success": True, "market_id": market_id_int, "count": len(products), "data": products},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Produits"],
        summary="Nombre total de produits",
        description="Retourne le nombre total de produits uniques présents dans le dataset.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "count":   {"type": "integer", "example": 55},
                },
            },
            500: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={"success": True, "count": 55},
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "Erreur serveur",
                value={"success": False, "message": "Erreur lors du calcul du nombre de produits."},
                response_only=True, status_codes=["500"],
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="count")
    def count(self, request: Request):
        """GET /products/count/ — Nombre total de produits uniques."""
        count = products_count()

        if count == 0:
            return Response(
                {"success": False, "message": "Erreur lors du calcul du nombre de produits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"success": True, "count": count},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Produits"],
        summary="Nombre de produits dans un marché",
        description="Retourne le nombre de produits uniques disponibles dans un marché donné.",
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
                    "success":   {"type": "boolean", "example": True},
                    "market_id": {"type": "integer", "example": 3},
                    "count":     {"type": "integer", "example": 12},
                },
            },
            400: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={"success": True, "market_id": 3, "count": 12},
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "market_id invalide",
                value={"success": False, "message": "Le market_id doit être un entier."},
                response_only=True, status_codes=["400"],
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path=r"market/(?P<market_id>[0-9]+)/count")
    def count_by_market(self, request: Request, market_id=None):
        """GET /products/market/{market_id}/count/ — Nombre de produits dans un marché."""
        try:
            market_id_int = int(market_id)
        except (TypeError, ValueError):
            return Response(
                {"success": False, "message": "Le market_id doit être un entier."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = products_count_by_market(market_id_int)

        return Response(
            {"success": True, "market_id": market_id_int, "count": count},
            status=status.HTTP_200_OK,
        )
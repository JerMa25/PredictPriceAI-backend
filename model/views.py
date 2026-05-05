from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from model.services import predictprice, get_metrics_by_product


# ── Réponses réutilisables ────────────────────────────────────────────────────
_RESPONSE_ERROR = {
    "type": "object",
    "properties": {
        "status":  {"type": "string", "example": "error"},
        "message": {"type": "string"},
    },
}


class PredictionViewSet(viewsets.ViewSet):
    """
    API endpoints pour les prédictions de prix et les métriques du modèle ML.
    """

    @extend_schema(
        tags=["Prédiction ML"],
        summary="Prédire le prix d'un produit",
        description=(
            "Prédit le prix d'un produit agricole pour une date et un marché donnés. "
            "Le modèle Random Forest effectue une prédiction itérative mois par mois "
            "jusqu'à la date cible, en se basant sur l'historique du couple (produit, marché). "
            "\n\n**Minimum requis :** 15 observations historiques pour le couple (produit, marché)."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "product_name":    {"type": "string",  "example": "Maize (yellow)"},
                    "prediction_date": {"type": "string",  "example": "2026-06-15", "format": "date"},
                    "market":          {"type": "string",  "example": "Yaoundé-Mfoundi"},
                },
                "required": ["product_name", "prediction_date", "market"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "product_name":    {"type": "string"},
                            "date":            {"type": "string", "format": "date"},
                            "market":          {"type": "string"},
                            "predicted_price": {"type": "number", "format": "float"},
                        },
                    },
                },
            },
            400: _RESPONSE_ERROR,
            500: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={
                    "status": "success",
                    "data": {
                        "product_name":    "Maize (yellow)",
                        "date":            "2026-06-15",
                        "market":          "Yaoundé-Mfoundi",
                        "predicted_price": 312.45,
                    },
                },
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "Paramètres manquants",
                value={"status": "error", "message": "Les paramètres 'product_name', 'prediction_date' et 'market' sont requis"},
                response_only=True, status_codes=["400"],
            ),
            OpenApiExample(
                "Données insuffisantes",
                value={"status": "error", "message": "Pas assez de données pour \"Maize (yellow)\" @ \"Yaoundé-Mfoundi\""},
                response_only=True, status_codes=["500"],
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="predictprice")
    def predict_price(self, request: Request):
        """
        POST /predictions/predictprice/
        Body: { product_name, prediction_date, market }
        """
        try:
            product_name    = request.data.get("product_name")
            prediction_date = request.data.get("prediction_date")
            market          = request.data.get("market")

            if not all([product_name, prediction_date, market]):
                return Response(
                    {"status": "error", "message": "Les paramètres 'product_name', 'prediction_date' et 'market' sont requis"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = predictprice(product_name, prediction_date, market)

            if result is None or result.get("status") == "error":
                return Response(
                    {"status": "error", "message": result.get("message", "Erreur lors de la prédiction")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "status": "success",
                    "data": {
                        "product_name":    result.get("product_name"),
                        "date":            result.get("date"),
                        "market":          result.get("market"),
                        "predicted_price": result.get("predicted_price"),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"Erreur serveur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        tags=["Prédiction ML"],
        summary="Métriques d'un produit sur un marché",
        description=(
            "Retourne les métriques de performance du modèle (RMSE, MAE, MAPE) "
            "pour un couple **(produit, marché)** spécifique. "
            "\n\n- **RMSE** : erreur quadratique moyenne (XAF/kg)"
            "\n- **MAE** : erreur absolue moyenne (XAF/kg)"
            "\n- **MAPE** : erreur en pourcentage — ex: 12.5% signifie que le modèle se trompe en moyenne de 12.5%"
        ),
        parameters=[
            OpenApiParameter(
                "commodity", OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Nom exact du produit ex: "Maize (white)"',
                required=True,
            ),
            OpenApiParameter(
                "market", OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Nom exact du marché ex: "Yaoundé-Mfoundi"',
                required=True,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "product_name": {"type": "string"},
                            "market":       {"type": "string"},
                            "rmse":         {"type": "number", "format": "float"},
                            "mae":          {"type": "number", "format": "float"},
                            "mape":         {"type": "number", "format": "float"},
                            "num_samples":  {"type": "integer"},
                        },
                    },
                },
            },
            400: _RESPONSE_ERROR,
            404: _RESPONSE_ERROR,
            500: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample(
                "Succès",
                value={
                    "status": "success",
                    "data": {
                        "product_name": "Maize (white)",
                        "market":       "Yaoundé-Mfoundi",
                        "rmse":         28.5,
                        "mae":          21.3,
                        "mape":         9.7,
                        "num_samples":  187,
                    },
                },
                response_only=True, status_codes=["200"],
            ),
            OpenApiExample(
                "Paramètres manquants",
                value={"status": "error", "message": "Les paramètres 'commodity' et 'market' sont requis"},
                response_only=True, status_codes=["400"],
            ),
            OpenApiExample(
                "Couple introuvable",
                value={"status": "error", "message": "Pas de données pour \"Maize (white)\" @ \"Yaoundé-Mfoundi\""},
                response_only=True, status_codes=["404"],
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="metrics/product")
    def get_product_metrics(self, request: Request):
        """
        GET /predictions/metrics/product/?commodity=Maize (white)&market=Yaoundé-Mfoundi
        """
        commodity = request.query_params.get("commodity")
        market    = request.query_params.get("market")

        if not commodity or not market:
            return Response(
                {"status": "error", "message": "Les paramètres 'commodity' et 'market' sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        metrics = get_metrics_by_product(commodity, market)

        if metrics is None or metrics.get("status") == "error":
            return Response(
                {"status": "error", "message": metrics.get("message")},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "status": "success",
                "data": {
                    "product_name": metrics.get("commodity"),
                    "market":       metrics.get("market"),
                    "rmse":         metrics.get("rmse"),
                    "mae":          metrics.get("mae"),
                    "mape":         metrics.get("mape"),
                    "num_samples":  metrics.get("num_samples"),
                },
            },
            status=status.HTTP_200_OK,
        )
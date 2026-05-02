from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from model.services import predictprice, get_metrics_by_product


class PredictionViewSet(viewsets.ViewSet):
    """
    API endpoints pour les prédictions de prix et les métriques du modèle ML.
    """

    @extend_schema(
        description="Prédit le prix d'une commodité pour une date et un marché donnés",
        request={
            "type": "object",
            "properties": {
                "product_name":    {"type": "string", "example": "Maize (yellow)"},
                "prediction_date": {"type": "string", "example": "2026-06-15", "format": "date"},
                "market":          {"type": "string", "example": "Yaoundé-Mfoundi"},
            },
            "required": ["product_name", "prediction_date", "market"],
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
            400: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            500: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
        },
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
    parameters=[
        OpenApiParameter("commodity", OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter("market",    OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True),
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
                            "rmse":         {"type": "number", "format": "float"},
                            "mae":          {"type": "number", "format": "float"},
                            "mape":         {"type": "number", "format": "float"},
                            "num_samples":  {"type": "integer"},
                        },
                    },
                },
            },
            400: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            404: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            500: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
        },
    )
    @action(detail=False, methods=["get"], url_path="metrics/product")
    def get_product_metrics(self, request: Request):
        """
        GET /predictions/metrics/product/?commodity=Maize (white)&market=Yaoundé-Mfoundi
        """
        commodity = request.query_params.get("commodity")
        market    = request.query_params.get("market")

        print(f"DEBUG commodity='{commodity}' | market='{market}'")

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
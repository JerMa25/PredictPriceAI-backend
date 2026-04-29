from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from authentification.services import (
    verify_admin_credentials,
    update_admin_credentials,
    admin_login_session,
    admin_logout_session,
    verify_admin_password,
)


class AuthenticationViewSet(viewsets.ViewSet):
    """
    API endpoints pour l'authentification de l'administrateur.
    """

    @extend_schema(
        description="Connecte l'administrateur",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "example": "admin@predictprice.cm"},
                    "password": {"type": "string", "example": "PredictPrice2026!"},
                },
                "required": ["email", "password"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    @action(detail=False, methods=["post"])
    def login(self, request: Request):
        """Connecte l'administrateur avec ses identifiants."""
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "success": False,
                    "message": "Email et mot de passe sont requis.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verify_admin_credentials(email, password):
            admin_login_session(request)
            return Response(
                {
                    "success": True,
                    "message": "Connexion réussie.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "success": False,
                    "message": "Email ou mot de passe incorrect.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @extend_schema(
        description="Déconnecte l'administrateur",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    @action(detail=False, methods=["post"])
    def logout(self, request: Request):
        """Déconnecte l'administrateur."""
        admin_logout_session(request)
        return Response(
            {
                "success": True,
                "message": "Déconnexion réussie.",
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description="Change les identifiants de l'administrateur",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "example": "admin@predictprice.cm"},
                    "password": {"type": "string", "example": "NewPassword123!"},
                    "current_password": {
                        "type": "string",
                        "example": "PredictPrice2026!",
                    },
                },
                "required": ["email", "password", "current_password"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    @action(detail=False, methods=["post"])
    def change_credentials(self, request: Request):
        """Change les identifiants de l'administrateur."""
        email = request.data.get("email")
        password = request.data.get("password")
        current_password = request.data.get("current_password")

        if not email or not password or not current_password:
            return Response(
                {
                    "success": False,
                    "message": "Tous les champs sont requis.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not verify_admin_password(current_password):
            return Response(
                {
                    "success": False,
                    "message": "Mot de passe actuel incorrect.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if update_admin_credentials(email, password):
            return Response(
                {
                    "success": True,
                    "message": "Identifiants mis à jour avec succès.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "success": False,
                    "message": "Erreur lors de la mise à jour des identifiants.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

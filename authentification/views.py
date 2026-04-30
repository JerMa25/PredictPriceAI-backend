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


class AuthentificationViewSet(viewsets.ViewSet):
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

    @extend_schema(
        description="Envoie un email de réinitialisation du mot de passe à l'administrateur",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "example": "admin@predictprice.cm"
                    }
                },
                "required": ["email"]
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Email de réinitialisation envoyé."
                    }
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {"type": "string"}
                }
            },
            404: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {"type": "string", "example": "Email non trouvé."}
                }
            }
        }
    )
    @action(detail=False, methods=["post"])
    def forgotten_password(self, request: Request):
        """Gère la réinitialisation du mot de passe de l'administrateur."""
        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "success": False,
                    "message": "Email est requis.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        from authentification.services import generate_reset_token, send_password_reset_email, load_admin_data

        admin = load_admin_data()
        if email != admin.get("email"):
            return Response(
                {
                    "success": False,
                    "message": "Email non trouvé.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        
        token = generate_reset_token(email)
        send_password_reset_email(email, token)

        return Response({"message": "Email de réinitialisation envoyé."}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description="Réinitialise le mot de passe de l'administrateur à partir d'un token valide",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "example": "eyJhbGciOi..."
                    },
                    "new_password": {
                        "type": "string",
                        "example": "NewSecurePassword123!"
                    }
                },
                "required": ["token", "new_password"]
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Mot de passe réinitialisé avec succès."
                    }
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {"type": "string"}
                }
            }
        }
    )
    @action(detail=False, methods=["post"])
    def reset_password(self, request: Request):
        """Gère la réinitialisation du mot de passe de l'administrateur à partir du token."""
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {
                    "success": False,
                    "message": "Token et nouveau mot de passe sont requis.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        from authentification.services import verify_reset_token, update_admin_credentials

        email = verify_reset_token(token)
        if not email:
            return Response(
                {
                    "success": False,
                    "message": "Token invalide ou expiré.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        update_admin_credentials(email, new_password)
        return Response(
            {
                "success": True,
                "message": "Mot de passe réinitialisé avec succès.",
            },
            status=status.HTTP_200_OK,
        )
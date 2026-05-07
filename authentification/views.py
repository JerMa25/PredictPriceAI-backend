import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from authentification.services import (
    verify_admin_credentials,
    update_admin_credentials,
    admin_login_session,
    admin_logout_session,
    verify_admin_password,
    generate_jwt_tokens,
)

logger = logging.getLogger(__name__)

# ── Réponses réutilisables ────────────────────────────────────────────────────
_RESPONSE_SUCCESS = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": True},
        "message": {"type": "string"},
    },
}
_RESPONSE_ERROR = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": False},
        "message": {"type": "string"},
    },
}


class AuthentificationViewSet(viewsets.ViewSet):
    """
    API endpoints pour l'authentification de l'administrateur PredictPrice AI.
    """

    @extend_schema(
        tags=["Authentification"],
        summary="Connexion administrateur",
        description=(
            "Authentifie l'administrateur avec son email et son mot de passe. "
            "Les credentials sont stockés dans `core/config/admin.json`. "
            "En cas de succès, une session est créée côté serveur."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email":    {"type": "string",  "example": "admin@predictprice.cm"},
                    "password": {"type": "string",  "example": "PredictPrice2026!"},
                },
                "required": ["email", "password"],
            }
        },
        responses={
            200: _RESPONSE_SUCCESS,
            400: _RESPONSE_ERROR,
            401: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample("Succès",             value={"success": True,  "message": "Connexion réussie."},                response_only=True, status_codes=["200"]),
            OpenApiExample("Champs manquants",   value={"success": False, "message": "Email et mot de passe sont requis."}, response_only=True, status_codes=["400"]),
            OpenApiExample("Mauvais credentials",value={"success": False, "message": "Email ou mot de passe incorrect."},   response_only=True, status_codes=["401"]),
        ],
    )
    @action(detail=False, methods=["post"])
    def login(self, request: Request):
        """Connecte l'administrateur avec ses identifiants."""
        email    = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"success": False, "message": "Email et mot de passe sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verify_admin_credentials(email, password):
            admin_login_session(request)
            return Response(
                {"success": True, "message": "Connexion réussie."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "message": "Email ou mot de passe incorrect."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @extend_schema(
        tags=["Authentification"],
        summary="Déconnexion administrateur",
        description="Stateless logout - le JWT token devient invalide après son expiration.",
        responses={
            200: _RESPONSE_SUCCESS,
        },
        examples=[
            OpenApiExample("Succès", value={"success": True, "message": "Déconnexion réussie."}, response_only=True, status_codes=["200"]),
        ],
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def logout(self, request: Request):
        """Déconnecte l'administrateur (stateless - JWT logout)."""
        return Response(
            {"success": True, "message": "Déconnexion réussie."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Authentification"],
        summary="Modifier les identifiants admin",
        description=(
            "Permet à l'administrateur de changer son email et/ou son mot de passe. "
            "Le mot de passe actuel est requis pour valider l'opération. "
            "Les nouvelles valeurs sont sauvegardées dans `core/config/admin.json`."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email":            {"type": "string", "example": "nouveau@predictprice.cm"},
                    "password":         {"type": "string", "example": "NouveauMotDePasse123!"},
                    "current_password": {"type": "string", "example": "PredictPrice2026!"},
                },
                "required": ["email", "password", "current_password"],
            }
        },
        responses={
            200: _RESPONSE_SUCCESS,
            400: _RESPONSE_ERROR,
            401: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample("Succès",                  value={"success": True,  "message": "Identifiants mis à jour avec succès."},        response_only=True, status_codes=["200"]),
            OpenApiExample("Champs manquants",         value={"success": False, "message": "Tous les champs sont requis."},                response_only=True, status_codes=["400"]),
            OpenApiExample("Mauvais mot de passe",     value={"success": False, "message": "Mot de passe actuel incorrect."},             response_only=True, status_codes=["401"]),
            OpenApiExample("Erreur mise à jour",       value={"success": False, "message": "Erreur lors de la mise à jour des identifiants."}, response_only=True, status_codes=["400"]),
        ],
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def change_credentials(self, request: Request):
        """Change les identifiants de l'administrateur."""
        email            = request.data.get("email")
        password         = request.data.get("password")
        current_password = request.data.get("current_password")

        if not email or not password or not current_password:
            return Response(
                {"success": False, "message": "Tous les champs sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_admin_password(current_password):
            return Response(
                {"success": False, "message": "Mot de passe actuel incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if update_admin_credentials(email, password):
            return Response(
                {"success": True, "message": "Identifiants mis à jour avec succès."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "message": "Erreur lors de la mise à jour des identifiants."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Authentification"],
        summary="Mot de passe oublié",
        description=(
            "Envoie un email contenant un lien de réinitialisation du mot de passe "
            "à l'adresse email de l'administrateur. "
            "Le lien contient un token JWT valable 1 heure."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "example": "admin@predictprice.cm"},
                },
                "required": ["email"],
            }
        },
        responses={
            200: _RESPONSE_SUCCESS,
            400: _RESPONSE_ERROR,
            404: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample("Succès",          value={"success": True,  "message": "Email de réinitialisation envoyé."}, response_only=True, status_codes=["200"]),
            OpenApiExample("Email manquant",  value={"success": False, "message": "Email est requis."},                 response_only=True, status_codes=["400"]),
            OpenApiExample("Email introuvable",value={"success": False, "message": "Email non trouvé."},               response_only=True, status_codes=["404"]),
        ],
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def forgotten_password(self, request: Request):
        """Envoie un email de réinitialisation du mot de passe."""
        email = request.data.get("email")

        if not email:
            return Response(
                {"success": False, "message": "Email est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from authentification.services import generate_reset_token, send_password_reset_email, load_admin_data

        admin = load_admin_data()
        if email != admin.get("email"):
            return Response(
                {"success": False, "message": "Email non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = generate_reset_token(email)
        send_password_reset_email(email, token)

        return Response(
            {"success": True, "message": "Email de réinitialisation envoyé."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Authentification"],
        summary="Réinitialiser le mot de passe",
        description=(
            "Réinitialise le mot de passe de l'administrateur à partir d'un token valide "
            "reçu par email via l'endpoint `forgotten_password`. "
            "Le token est valable **1 heure** après sa génération."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token":        {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                    "new_password": {"type": "string", "example": "NouveauMotDePasse123!"},
                },
                "required": ["token", "new_password"],
            }
        },
        responses={
            200: _RESPONSE_SUCCESS,
            400: _RESPONSE_ERROR,
        },
        examples=[
            OpenApiExample("Succès",           value={"success": True,  "message": "Mot de passe réinitialisé avec succès."}, response_only=True, status_codes=["200"]),
            OpenApiExample("Champs manquants", value={"success": False, "message": "Token et nouveau mot de passe sont requis."}, response_only=True, status_codes=["400"]),
            OpenApiExample("Token invalide",   value={"success": False, "message": "Token invalide ou expiré."},              response_only=True, status_codes=["400"]),
        ],
    )
    @action(detail=False, methods=["post"])
    def reset_password(self, request: Request):
        """Réinitialise le mot de passe à partir d'un token valide."""
        token        = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"success": False, "message": "Token et nouveau mot de passe sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from authentification.services import verify_reset_token

        email = verify_reset_token(token)
        if not email:
            return Response(
                {"success": False, "message": "Token invalide ou expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_admin_credentials(email, new_password)
        return Response(
            {"success": True, "message": "Mot de passe réinitialisé avec succès."},
            status=status.HTTP_200_OK,
        )
from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Grants access only to the user who owns the quiz."""

    def has_object_permission(self, request, view, obj):
        """Denies every user except the owner, which results in a 403."""
        return obj.owner == request.user

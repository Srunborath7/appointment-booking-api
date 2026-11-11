"""Translation and localization helper."""

TRANSLATIONS = {
    "en": {
        "success": "Success",
        "created": "Resource created successfully",
        "updated": "Resource updated successfully",
        "deleted": "Resource deleted successfully",
        "not_found": "Resource not found",
        "unauthorized": "Unauthorized access",
        "forbidden": "Permission denied",
        "invalid_parameters": "Invalid parameters",
        "field_cannot_empty": "Field cannot be empty",
        "internal_server_error": "An internal server error occurred",
        "conflict": "Resource already exists",
    }
}


def get_translation(key: str, locale: str = "en") -> str:
    """Get localized translation string, defaulting to English, or returning key itself."""
    return TRANSLATIONS.get(locale, TRANSLATIONS["en"]).get(key, key)

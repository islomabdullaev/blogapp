"""XSS protection through input sanitization"""

from typing import Any, Dict

import bleach
from pydantic import BaseModel

# Allowed HTML tags and attributes (very restrictive for security)
ALLOWED_TAGS = []  # No HTML tags allowed by default
ALLOWED_ATTRIBUTES = {}


def sanitize_string(value: str) -> str:
    """
    Sanitize string input to prevent XSS attacks
    Removes all HTML tags and dangerous characters
    """
    if not isinstance(value, str):
        return value

    # Remove HTML tags
    cleaned = bleach.clean(
        value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "\x00"]
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, "")

    return cleaned.strip()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize dictionary values"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def sanitize_pydantic_model(model: BaseModel) -> BaseModel:
    """Sanitize Pydantic model fields"""
    data = model.model_dump()
    sanitized_data = sanitize_dict(data)
    return model.__class__(**sanitized_data)

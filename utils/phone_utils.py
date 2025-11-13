"""
Phone number normalization utilities
"""
import re
from typing import Optional


def normalize_phone(phone: str) -> Optional[str]:
    """
    Normalize phone number to 10 digits by removing all special characters.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        10-digit phone number string, or None if invalid
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    if not digits:
        return None
    
    # Take last 10 digits (handles country codes)
    if len(digits) >= 10:
        digits = digits[-10:]
    
    # Validate it's exactly 10 digits
    if len(digits) != 10:
        return None
    
    return digits


def generate_user_id(phone: str) -> Optional[str]:
    """
    Generate UserID in format: 91 + 10-digit phone number.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        12-digit UserID string (91 + 10 digits), or None if invalid
        
    Example:
        >>> generate_user_id("9876543210")
        "919876543210"
        >>> generate_user_id("+91-98765-43210")
        "919876543210"
    """
    normalized = normalize_phone(phone)
    
    if not normalized:
        return None
    
    return f"91{normalized}"


def validate_user_id(user_id: str) -> bool:
    """
    Validate that UserID is in correct format (91 + 10 digits).
    
    Args:
        user_id: UserID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not user_id or not isinstance(user_id, str):
        return False
    
    # Must be exactly 12 digits starting with 91
    if len(user_id) != 12:
        return False
    
    if not user_id.startswith('91'):
        return False
    
    if not user_id.isdigit():
        return False
    
    return True

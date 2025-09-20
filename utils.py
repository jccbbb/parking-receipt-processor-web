import re
from typing import Optional, Tuple


def format_swedish_currency(amount: float) -> str:
    """Format amount as Swedish currency"""
    return f"{amount:.2f} kr"


def parse_brutto_amount(text: str) -> Optional[float]:
    """Parse Brutto amount from various formats"""
    if not text:
        return None

    # Remove all whitespace and convert to lowercase
    text = text.strip().lower()

    # Common patterns for Swedish currency
    patterns = [
        r'brutto[:\s]*([0-9]+[,.]?[0-9]*)\s*kr?',
        r'([0-9]+[,.]?[0-9]*)\s*kr',
        r'([0-9]+[,.]?[0-9]*)\s*sek',
        r'brutto[:\s]*([0-9]+[,.]?[0-9]*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1)
            # Replace comma with dot for decimal
            amount_str = amount_str.replace(',', '.')
            try:
                return float(amount_str)
            except ValueError:
                continue

    return None


def extract_ticket_number(text: str) -> Optional[str]:
    """Extract 9-digit ticket number from text"""
    if not text:
        return None

    # Common patterns for ticket numbers
    patterns = [
        r'biljettnummer[:\s]*([0-9]{9})',
        r'biljett[:\s]*([0-9]{9})',
        r'nummer[:\s]*([0-9]{9})',
        r'\b([0-9]{9})\b',  # Any standalone 9-digit number
    ]

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1)

    return None


def validate_pdf_file(path: str) -> Tuple[bool, str]:
    """Validate PDF file path and permissions"""
    import os

    if not path:
        return False, "No file selected"

    if not os.path.exists(path):
        return False, "File does not exist"

    if not path.lower().endswith('.pdf'):
        return False, "File must be a PDF"

    if not os.access(path, os.R_OK):
        return False, "Cannot read file (permission denied)"

    # Check file size (warn if over 100MB)
    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb > 100:
        return True, f"Warning: Large file ({file_size_mb:.1f} MB) may take time to process"

    return True, "Valid PDF file"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safety"""
    import os
    # Remove directory traversal attempts
    filename = os.path.basename(filename)
    # Remove potentially dangerous characters
    invalid_chars = '<>:"|?*\\/.'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename
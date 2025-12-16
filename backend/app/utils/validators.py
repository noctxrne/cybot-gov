import os
import re
from typing import Dict, Any
from fastapi import UploadFile

def validate_file(file: UploadFile, max_size: int, allowed_extensions: list) -> Dict[str, Any]:
    """
    Validate uploaded file
    """
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return {
            "valid": False,
            "message": f"File too large. Maximum size is {max_size/(1024*1024):.1f}MB"
        }
    
    # Check extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        return {
            "valid": False,
            "message": f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
        }
    
    # Check filename for security
    if not re.match(r'^[\w\-. ]+$', file.filename):
        return {
            "valid": False,
            "message": "Invalid filename"
        }
    
    return {"valid": True, "message": "File valid"}

def validate_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate document metadata
    """
    errors = []
    
    # Check required fields
    required_fields = ["title", "document_type", "source"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate document type
    allowed_types = ["cyber_law", "amendment", "guideline", "circular", "notification"]
    if data.get("document_type") not in allowed_types:
        errors.append(f"Invalid document type. Allowed: {', '.join(allowed_types)}")
    
    # Validate dates if provided
    date_fields = ["effective_date", "amendment_date"]
    for field in date_fields:
        if field in data and data[field]:
            try:
                # You might want to use dateutil.parser for flexible date parsing
                pass
            except:
                errors.append(f"Invalid date format for {field}")
    
    if errors:
        return {"valid": False, "errors": errors}
    
    return {"valid": True, "errors": []}

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal
    """
    # Remove directory components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\-. ]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename
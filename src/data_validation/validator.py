"""
Main data validation logic for CFPB complaint data.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .utils import clean_whitespace, is_valid_date_format, safe_get, is_empty_or_none


@dataclass
class ValidationResult:
    """
    Result of data validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of validation error messages
        cleaned_data: Cleaned version of input data
    """
    is_valid: bool
    errors: List[str]
    cleaned_data: Dict[str, Any]


class DataValidator:
    """
    Data validator for CFPB complaint records.
    
    Validates text fields, required fields, and data formats according to
    CFPB complaint data standards.
    """
    
    REQUIRED_FIELDS = ['complaint_text', 'product', 'company', 'date_received']
    MIN_TEXT_LENGTH = 10
    
    def __init__(self):
        """Initialize the data validator."""
        self._last_errors: List[str] = []
    
    def validate_text(self, text: str, min_length: int = None) -> bool:
        """
        Validate text meets minimum requirements.
        
        Args:
            text: Text to validate
            min_length: Minimum required length (default: class minimum)
            
        Returns:
            True if text is valid, False otherwise
        """
        if min_length is None:
            min_length = self.MIN_TEXT_LENGTH
        
        if is_empty_or_none(text):
            return False
        
        if not isinstance(text, str):
            return False
        
        # Check minimum length after cleaning whitespace
        cleaned_text = clean_whitespace(text)
        return len(cleaned_text) >= min_length
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text data.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text with normalized whitespace
        """
        if is_empty_or_none(text):
            return ""
        
        return clean_whitespace(str(text))
    
    def validate_record(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete data record.
        
        Args:
            record: Dictionary containing record data
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        cleaned_data = {}
        
        if not isinstance(record, dict):
            errors.append("Record must be a dictionary")
            return ValidationResult(False, errors, {})
        
        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            value = safe_get(record, field)
            
            if is_empty_or_none(value):
                errors.append(f"Required field '{field}' is missing or empty")
                cleaned_data[field] = ""
            else:
                cleaned_value = str(value)
                
                # Special validation for specific fields
                if field == 'complaint_text':
                    if not self.validate_text(cleaned_value):
                        errors.append(f"Complaint text must be at least {self.MIN_TEXT_LENGTH} characters")
                    cleaned_data[field] = self.clean_text(cleaned_value)
                
                elif field == 'date_received':
                    if not is_valid_date_format(cleaned_value):
                        errors.append("Date must be in YYYY-MM-DD format")
                    cleaned_data[field] = cleaned_value.strip()
                
                else:
                    # For product and company, just clean whitespace
                    cleaned_data[field] = self.clean_text(cleaned_value)
        
        # Include any additional fields from the record
        for key, value in record.items():
            if key not in self.REQUIRED_FIELDS:
                cleaned_data[key] = self.clean_text(str(value)) if value is not None else ""
        
        self._last_errors = errors.copy()
        is_valid = len(errors) == 0
        
        return ValidationResult(is_valid, errors, cleaned_data)
    
    def get_validation_errors(self) -> List[str]:
        """
        Return list of validation errors from last validation.
        
        Returns:
            List of error messages from the most recent validation
        """
        return self._last_errors.copy()
"""
Tests for the data validation module.
"""

import pytest
from src.data_validation import DataValidator, ValidationResult
from src.data_validation.utils import (
    clean_whitespace, 
    is_valid_date_format, 
    safe_get, 
    is_empty_or_none
)


class TestUtils:
    """Test utility functions."""
    
    def test_clean_whitespace(self):
        """Test whitespace cleaning functionality."""
        assert clean_whitespace("  hello   world  ") == "hello world"
        assert clean_whitespace("text") == "text"
        assert clean_whitespace("") == ""
        assert clean_whitespace("   ") == ""
        assert clean_whitespace("line1\n\nline2") == "line1 line2"
        assert clean_whitespace(123) == "123"
        assert clean_whitespace(None) == ""
    
    def test_is_valid_date_format(self):
        """Test date format validation."""
        # Valid dates
        assert is_valid_date_format("2024-01-15") == True
        assert is_valid_date_format("2023-12-31") == True
        assert is_valid_date_format("2000-01-01") == True
        
        # Invalid dates
        assert is_valid_date_format("24-01-15") == False
        assert is_valid_date_format("2024-1-15") == False
        assert is_valid_date_format("2024-01-5") == False
        assert is_valid_date_format("invalid") == False
        assert is_valid_date_format("") == False
        assert is_valid_date_format(None) == False
    
    def test_safe_get(self):
        """Test safe dictionary value retrieval."""
        data = {"key1": "value1", "key2": None}
        
        assert safe_get(data, "key1") == "value1"
        assert safe_get(data, "key2") is None
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"
        assert safe_get(None, "key") is None
        assert safe_get("not_dict", "key") is None
    
    def test_is_empty_or_none(self):
        """Test empty value detection."""
        assert is_empty_or_none(None) == True
        assert is_empty_or_none("") == True
        assert is_empty_or_none("   ") == True
        assert is_empty_or_none("text") == False
        assert is_empty_or_none(0) == False
        assert is_empty_or_none([]) == False


class TestDataValidator:
    """Test DataValidator class."""
    
    def setup_method(self):
        """Set up test fixture."""
        self.validator = DataValidator()
    
    def test_validate_text_valid_cases(self):
        """Test text validation with valid inputs."""
        assert self.validator.validate_text("This is a valid complaint text") == True
        assert self.validator.validate_text("Short but valid enough text") == True
        assert self.validator.validate_text("a" * 50) == True
    
    def test_validate_text_invalid_cases(self):
        """Test text validation with invalid inputs."""
        assert self.validator.validate_text("") == False
        assert self.validator.validate_text("   ") == False
        assert self.validator.validate_text("short") == False  # Less than 10 chars
        assert self.validator.validate_text(None) == False
        assert self.validator.validate_text(123) == False
    
    def test_validate_text_custom_length(self):
        """Test text validation with custom minimum length."""
        assert self.validator.validate_text("hello", min_length=3) == True
        assert self.validator.validate_text("hi", min_length=3) == False
        assert self.validator.validate_text("exactly", min_length=7) == True
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        assert self.validator.clean_text("  messy   text  ") == "messy text"
        assert self.validator.clean_text("clean") == "clean"
        assert self.validator.clean_text("") == ""
        assert self.validator.clean_text(None) == ""
        assert self.validator.clean_text(42) == "42"
    
    def test_validate_record_valid(self):
        """Test record validation with valid data."""
        valid_record = {
            "complaint_text": "I have an issue with unauthorized charges on my account",
            "product": "Credit card",
            "company": "Big Bank Corp",
            "date_received": "2024-01-15"
        }
        
        result = self.validator.validate_record(valid_record)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.cleaned_data["complaint_text"] == "I have an issue with unauthorized charges on my account"
        assert result.cleaned_data["product"] == "Credit card"
    
    def test_validate_record_missing_fields(self):
        """Test record validation with missing required fields."""
        incomplete_record = {
            "complaint_text": "Valid complaint text",
            "product": "Credit card"
            # Missing company and date_received
        }
        
        result = self.validator.validate_record(incomplete_record)
        
        assert result.is_valid == False
        assert len(result.errors) == 2
        assert "Required field 'company' is missing or empty" in result.errors
        assert "Required field 'date_received' is missing or empty" in result.errors
    
    def test_validate_record_invalid_text_length(self):
        """Test record validation with invalid text length."""
        record_with_short_text = {
            "complaint_text": "short",  # Less than 10 characters
            "product": "Credit card",
            "company": "Big Bank Corp",
            "date_received": "2024-01-15"
        }
        
        result = self.validator.validate_record(record_with_short_text)
        
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Complaint text must be at least 10 characters" in result.errors[0]
    
    def test_validate_record_invalid_date_format(self):
        """Test record validation with invalid date format."""
        record_with_bad_date = {
            "complaint_text": "Valid complaint text here",
            "product": "Credit card",
            "company": "Big Bank Corp",
            "date_received": "01/15/2024"  # Wrong format
        }
        
        result = self.validator.validate_record(record_with_bad_date)
        
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Date must be in YYYY-MM-DD format" in result.errors[0]
    
    def test_validate_record_empty_values(self):
        """Test record validation with empty string values."""
        empty_record = {
            "complaint_text": "",
            "product": "   ",  # Only whitespace
            "company": None,
            "date_received": ""
        }
        
        result = self.validator.validate_record(empty_record)
        
        assert result.is_valid == False
        assert len(result.errors) == 4  # All required fields are empty
    
    def test_validate_record_extra_fields(self):
        """Test record validation preserves extra fields."""
        record_with_extras = {
            "complaint_text": "Valid complaint text here",
            "product": "Credit card", 
            "company": "Big Bank Corp",
            "date_received": "2024-01-15",
            "extra_field": "extra value",
            "another_field": 123
        }
        
        result = self.validator.validate_record(record_with_extras)
        
        assert result.is_valid == True
        assert "extra_field" in result.cleaned_data
        assert "another_field" in result.cleaned_data
        assert result.cleaned_data["extra_field"] == "extra value"
        assert result.cleaned_data["another_field"] == "123"
    
    def test_validate_record_invalid_input(self):
        """Test record validation with invalid input type."""
        result = self.validator.validate_record("not a dict")
        
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Record must be a dictionary" in result.errors[0]
        assert result.cleaned_data == {}
    
    def test_get_validation_errors(self):
        """Test error retrieval functionality."""
        # Start with no errors
        assert self.validator.get_validation_errors() == []
        
        # Validate invalid record
        invalid_record = {"complaint_text": "short"}
        self.validator.validate_record(invalid_record)
        
        errors = self.validator.get_validation_errors()
        assert len(errors) > 0
        assert isinstance(errors, list)
        
        # Validate valid record
        valid_record = {
            "complaint_text": "This is a valid complaint text",
            "product": "Credit card",
            "company": "Big Bank Corp", 
            "date_received": "2024-01-15"
        }
        self.validator.validate_record(valid_record)
        
        # Errors should be empty now
        assert self.validator.get_validation_errors() == []


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult can be created properly."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            cleaned_data={"test": "data"}
        )
        
        assert result.is_valid == True
        assert result.errors == []
        assert result.cleaned_data == {"test": "data"}
    
    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            cleaned_data={}
        )
        
        assert result.is_valid == False
        assert result.errors == errors
        assert result.cleaned_data == {}


# Integration tests
class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_realistic_cfpb_record(self):
        """Test with realistic CFPB complaint record."""
        validator = DataValidator()
        
        realistic_record = {
            "complaint_text": "I noticed several unauthorized charges on my credit card statement from a company I've never done business with. When I called my bank, they said I need to file a complaint. The charges totaled $245.67 and appeared on 3 different dates last month.",
            "product": "Credit card or prepaid card", 
            "company": "BANK OF AMERICA, NATIONAL ASSOCIATION",
            "date_received": "2024-01-15",
            "issue": "Billing disputes",
            "sub_issue": "Charged fees or interest I didn't expect",
            "state": "CA",
            "zip_code": "90210"
        }
        
        result = validator.validate_record(realistic_record)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert len(result.cleaned_data) == 8  # All fields preserved
        assert "issue" in result.cleaned_data
        assert "zip_code" in result.cleaned_data
    
    def test_batch_processing_simulation(self):
        """Test processing multiple records like batch processing."""
        validator = DataValidator()
        
        records = [
            {
                "complaint_text": "Valid complaint about bank fees",
                "product": "Checking account",
                "company": "Test Bank",
                "date_received": "2024-01-01"
            },
            {
                "complaint_text": "short",  # Invalid
                "product": "",  # Invalid 
                "company": "Another Bank",
                "date_received": "2024-01-02"
            },
            {
                "complaint_text": "Another valid complaint about service issues",
                "product": "Savings account",
                "company": "Third Bank",
                "date_received": "invalid-date"  # Invalid
            }
        ]
        
        results = [validator.validate_record(record) for record in records]
        
        # First record should be valid
        assert results[0].is_valid == True
        
        # Second record should have errors
        assert results[1].is_valid == False
        assert len(results[1].errors) >= 2
        
        # Third record should have date error
        assert results[2].is_valid == False
        assert any("Date must be in YYYY-MM-DD format" in error for error in results[2].errors)
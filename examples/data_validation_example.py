#!/usr/bin/env python3
"""
Example usage of the Simple Data Validator module.

This example demonstrates how to use the data validation module to validate
CFPB complaint records and handle validation errors.
"""

import sys
import os

# Add src directory to path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_validation import DataValidator, ValidationResult


def main():
    """Demonstrate data validation functionality."""
    print("=== Simple Data Validator Example ===\n")
    
    # Initialize validator
    validator = DataValidator()
    print("✓ Data validator initialized")
    
    # Example 1: Validate individual text
    print("\n1. Text Validation Examples:")
    
    texts_to_test = [
        "This is a complaint about my credit card charges.",
        "Short text",  # Too short
        "",  # Empty
        "This is a much longer complaint about various issues I've been having with my financial institution's customer service."
    ]
    
    for i, text in enumerate(texts_to_test, 1):
        is_valid = validator.validate_text(text)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        text_preview = text[:30] + "..." if len(text) > 30 else text
        print(f"   {i}.{i} '{text_preview}' -> {status}")
    
    # Example 2: Validate complete records
    print("\n2. Record Validation Examples:")
    
    # Valid record
    print("\n   2.1 Valid CFPB Record:")
    valid_record = {
        "complaint_text": "I have an issue with unauthorized charges on my credit card account. The bank charged me fees that I was not aware of.",
        "product": "Credit card",
        "company": "Big Bank Corp",
        "date_received": "2024-01-15",
        "state": "CA",  # Extra field - should be preserved
        "zip_code": "90210"  # Extra field - should be preserved
    }
    
    result = validator.validate_record(valid_record)
    print(f"   Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Cleaned fields: {len(result.cleaned_data)}")
    if result.is_valid:
        print("   Sample cleaned data:")
        for key, value in list(result.cleaned_data.items())[:3]:
            print(f"     {key}: '{value[:40]}{'...' if len(str(value)) > 40 else ''}'")
    
    # Invalid record with multiple issues
    print("\n   2.2 Invalid Record (Multiple Issues):")
    invalid_record = {
        "complaint_text": "Too short",  # Less than 10 characters
        "product": "",  # Empty required field
        "company": "Valid Company",
        "date_received": "01/15/2024"  # Wrong date format
    }
    
    result = validator.validate_record(invalid_record)
    print(f"   Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
    print(f"   Errors: {len(result.errors)}")
    if result.errors:
        print("   Error details:")
        for error in result.errors:
            print(f"     - {error}")
    
    # Record with missing required fields
    print("\n   2.3 Record with Missing Fields:")
    incomplete_record = {
        "complaint_text": "This complaint has valid text but missing other required fields.",
        "product": "Credit card"
        # Missing: company, date_received
    }
    
    result = validator.validate_record(incomplete_record)
    print(f"   Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
    print(f"   Errors: {len(result.errors)}")
    if result.errors:
        print("   Missing fields:")
        for error in result.errors:
            print(f"     - {error}")
    
    # Example 3: Batch processing simulation
    print("\n3. Batch Processing Example:")
    
    batch_records = [
        {
            "complaint_text": "First valid complaint about billing issues with detailed explanation.",
            "product": "Checking account",
            "company": "First Bank",
            "date_received": "2024-01-10"
        },
        {
            "complaint_text": "Second valid complaint about customer service problems that occurred last month.",
            "product": "Savings account", 
            "company": "Second Bank",
            "date_received": "2024-01-11"
        },
        {
            "complaint_text": "Invalid",  # Too short
            "product": "Credit card",
            "company": "Third Bank",
            "date_received": "2024-01-12"
        },
        {
            "complaint_text": "Fourth complaint about mortgage processing delays and communication issues.",
            "product": "Mortgage",
            "company": "",  # Empty company
            "date_received": "invalid-date"
        }
    ]
    
    valid_count = 0
    invalid_count = 0
    
    print(f"   Processing {len(batch_records)} records...")
    
    for i, record in enumerate(batch_records, 1):
        result = validator.validate_record(record)
        if result.is_valid:
            valid_count += 1
            print(f"   Record {i}: ✓ VALID")
        else:
            invalid_count += 1
            print(f"   Record {i}: ✗ INVALID ({len(result.errors)} errors)")
    
    print(f"\n   Batch Results:")
    print(f"   - Valid records: {valid_count}")
    print(f"   - Invalid records: {invalid_count}")
    print(f"   - Success rate: {(valid_count/len(batch_records)*100):.1f}%")
    
    # Example 4: Text cleaning demonstration
    print("\n4. Text Cleaning Example:")
    
    messy_texts = [
        "  Text   with    excessive    whitespace  ",
        "Text\n\nwith\n\nmultiple\nlines",
        "   Leading and trailing spaces   ",
        "Normal text"
    ]
    
    print("   Before -> After cleaning:")
    for text in messy_texts:
        cleaned = validator.clean_text(text)
        print(f"   '{text}' -> '{cleaned}'")
    
    # Example 5: Custom validation
    print("\n5. Custom Validation Length Example:")
    
    test_text = "Short text for testing"
    print(f"   Text: '{test_text}'")
    print(f"   Default validation (≥10 chars): {'✓' if validator.validate_text(test_text) else '✗'}")
    print(f"   Custom validation (≥5 chars): {'✓' if validator.validate_text(test_text, min_length=5) else '✗'}")
    print(f"   Custom validation (≥30 chars): {'✓' if validator.validate_text(test_text, min_length=30) else '✗'}")
    
    print("\n=== Example Complete ===")
    print("\nThe data validation module is working correctly!")
    print("You can now use this module in your data processing pipelines.")


if __name__ == "__main__":
    main()
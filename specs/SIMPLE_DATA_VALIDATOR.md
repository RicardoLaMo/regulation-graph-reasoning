# Simple Data Validator

## Overview
A lightweight data validation module for processing and validating complaint text data from CFPB datasets.

## Technical Requirements

### Core Functionality
- Validate text fields for minimum length and content
- Clean and normalize text data
- Check for required fields in data records
- Handle missing or null values gracefully
- Provide detailed validation error messages

### Dependencies
- Python 3.9+
- Standard library only (no external dependencies for this simple example)

### Performance Criteria
- Process 1000+ records per second
- Memory efficient for large datasets
- Fast validation with early failure detection

## Implementation Details

### Module Structure
```
src/
├── data_validation/
│   ├── __init__.py
│   ├── validator.py      # Main validation logic
│   └── utils.py          # Helper utilities
```

### Key Classes and Functions

#### `DataValidator` class
- `validate_text(text: str, min_length: int = 10) -> bool`: Validate text meets minimum requirements
- `clean_text(text: str) -> str`: Clean and normalize text data
- `validate_record(record: dict) -> ValidationResult`: Validate complete data record
- `get_validation_errors() -> List[str]`: Return list of validation errors

#### `ValidationResult` class
- `is_valid: bool`: Whether validation passed
- `errors: List[str]`: List of validation error messages
- `cleaned_data: dict`: Cleaned version of input data

### Required Fields for CFPB Records
- `complaint_text`: Main complaint description (min 10 characters)
- `product`: Product category (must not be empty)
- `company`: Company name (must not be empty)
- `date_received`: Date in YYYY-MM-DD format

## Test Requirements

### Unit Tests
- Test text validation with various inputs (empty, short, normal, long)
- Test record validation with complete and incomplete records
- Test error message generation
- Test text cleaning functionality
- Test edge cases (None values, special characters, etc.)

### Test Data
- Valid CFPB complaint records
- Invalid records with missing fields
- Records with malformed data
- Empty and null data cases

## Examples

### Expected Usage Pattern
```python
from src.data_validation.validator import DataValidator

# Initialize validator
validator = DataValidator()

# Validate single text
is_valid = validator.validate_text("This is a complaint about my credit card.")
print(f"Text is valid: {is_valid}")

# Validate complete record
record = {
    "complaint_text": "I have an issue with unauthorized charges",
    "product": "Credit card",
    "company": "Big Bank Corp",
    "date_received": "2024-01-15"
}

result = validator.validate_record(record)
if result.is_valid:
    print("Record is valid!")
    print("Cleaned data:", result.cleaned_data)
else:
    print("Validation errors:", result.errors)
```

### Expected Output
```
Text is valid: True
Record is valid!
Cleaned data: {'complaint_text': 'I have an issue with unauthorized charges', 'product': 'Credit card', 'company': 'Big Bank Corp', 'date_received': '2024-01-15'}
```

## Integration Points
- Can be used as part of data preprocessing pipeline
- Compatible with pandas DataFrames for batch processing
- Easily extendable for additional validation rules
- Logging integration for validation tracking
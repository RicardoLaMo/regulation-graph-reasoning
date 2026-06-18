"""
Simple Data Validation Module

A lightweight data validation module for processing and validating 
complaint text data from CFPB datasets.
"""

from .validator import DataValidator, ValidationResult

__version__ = "0.1.0"
__all__ = ["DataValidator", "ValidationResult"]
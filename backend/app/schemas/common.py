"""Common schemas and utilities."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "not_found",
                "message": "Resource not found",
                "details": {"resource_id": 123}
            }
        }


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    error: str = Field("validation_error", description="Error type")
    message: str = Field("Validation failed", description="Error message")
    details: List[ValidationErrorDetail] = Field(..., description="Validation errors")

    class Config:
        schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Validation failed",
                "details": [
                    {
                        "field": "price",
                        "message": "Price must be greater than 0",
                        "code": "value_error.number.not_gt"
                    }
                ]
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }
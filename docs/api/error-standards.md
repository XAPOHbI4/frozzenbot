# FrozenBot API Error Standards

This document defines the standardized error handling and response formats for the FrozenBot API.

## Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "additional": "context information"
  }
}
```

### Fields

- **error** (string, required): Machine-readable error type identifier
- **message** (string, required): Human-readable error description
- **details** (object, optional): Additional context about the error

## HTTP Status Codes

### 2xx Success
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Request successful, no content to return

### 4xx Client Errors

#### 400 Bad Request
Invalid request syntax or parameters.

**Example:**
```json
{
  "error": "bad_request",
  "message": "Invalid request parameters",
  "details": {
    "parameter": "category_id",
    "value": "invalid",
    "expected": "positive integer"
  }
}
```

**Common causes:**
- Invalid JSON syntax
- Missing required fields
- Invalid parameter values
- Malformed request body

#### 401 Unauthorized
Authentication required or failed.

**Examples:**

Missing authentication:
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

Invalid JWT token:
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

Invalid Telegram initData:
```json
{
  "error": "unauthorized",
  "message": "Invalid Telegram initData signature"
}
```

#### 403 Forbidden
Authenticated but insufficient permissions.

**Example:**
```json
{
  "error": "forbidden",
  "message": "Admin access required",
  "details": {
    "required_role": "admin",
    "user_role": "user"
  }
}
```

#### 404 Not Found
Requested resource not found.

**Example:**
```json
{
  "error": "not_found",
  "message": "Product not found",
  "details": {
    "resource": "product",
    "id": 123
  }
}
```

#### 422 Validation Error
Request data validation failed.

**Example:**
```json
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": [
    {
      "field": "price",
      "message": "Price must be greater than 0",
      "code": "value_error.number.not_gt",
      "value": -10
    },
    {
      "field": "name",
      "message": "Name is required",
      "code": "value_error.missing"
    }
  ]
}
```

#### 429 Too Many Requests
Rate limit exceeded.

**Example:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded",
  "details": {
    "limit": 60,
    "window": "1 minute",
    "retry_after": 30
  }
}
```

### 5xx Server Errors

#### 500 Internal Server Error
Unexpected server error.

**Example:**
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "details": {
    "error_id": "err_123456789",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 503 Service Unavailable
Service temporarily unavailable.

**Example:**
```json
{
  "error": "service_unavailable",
  "message": "Service temporarily unavailable",
  "details": {
    "estimated_recovery": "2024-01-01T12:30:00Z"
  }
}
```

## Error Types by Category

### Authentication Errors
- `unauthorized` - Missing or invalid authentication
- `forbidden` - Insufficient permissions
- `token_expired` - JWT token expired
- `invalid_credentials` - Wrong username/password
- `telegram_auth_failed` - Telegram initData validation failed

### Validation Errors
- `validation_error` - Request data validation failed
- `missing_field` - Required field missing
- `invalid_format` - Field format invalid
- `value_out_of_range` - Value outside allowed range

### Resource Errors
- `not_found` - Resource not found
- `already_exists` - Resource already exists
- `conflict` - Resource state conflict
- `dependency_error` - Cannot modify due to dependencies

### Business Logic Errors
- `insufficient_stock` - Product out of stock
- `minimum_order_not_met` - Order below minimum amount
- `cart_expired` - Shopping cart expired
- `order_cannot_be_modified` - Order status prevents modification
- `payment_failed` - Payment processing failed

### System Errors
- `internal_server_error` - Unexpected server error
- `service_unavailable` - Service temporarily down
- `database_error` - Database operation failed
- `external_service_error` - Third-party service error

## Error Context by Endpoint

### Product Endpoints

**GET /api/products/{id}**
```json
// 404 Not Found
{
  "error": "not_found",
  "message": "Product not found",
  "details": {
    "product_id": 123
  }
}
```

**POST /api/products/** (Admin)
```json
// 422 Validation Error
{
  "error": "validation_error",
  "message": "Product validation failed",
  "details": [
    {
      "field": "category_id",
      "message": "Category does not exist",
      "code": "foreign_key_error",
      "value": 999
    }
  ]
}

// 403 Forbidden
{
  "error": "forbidden",
  "message": "Admin access required"
}
```

### Cart Endpoints

**POST /api/cart/items**
```json
// 400 Bad Request - Insufficient stock
{
  "error": "insufficient_stock",
  "message": "Not enough items in stock",
  "details": {
    "product_id": 1,
    "requested_quantity": 10,
    "available_quantity": 5
  }
}

// 400 Bad Request - Product inactive
{
  "error": "product_unavailable",
  "message": "Product is not available",
  "details": {
    "product_id": 1,
    "reason": "product_inactive"
  }
}
```

### Order Endpoints

**POST /api/orders/**
```json
// 400 Bad Request - Empty cart
{
  "error": "empty_cart",
  "message": "Cannot create order with empty cart",
  "details": {
    "telegram_id": 123456789
  }
}

// 400 Bad Request - Minimum order amount
{
  "error": "minimum_order_not_met",
  "message": "Order amount below minimum required",
  "details": {
    "current_amount": 1000.0,
    "minimum_amount": 1500.0,
    "missing_amount": 500.0
  }
}
```

**PUT /api/orders/{id}/status**
```json
// 409 Conflict - Invalid status transition
{
  "error": "invalid_status_transition",
  "message": "Cannot change order status",
  "details": {
    "current_status": "completed",
    "requested_status": "preparing",
    "allowed_transitions": []
  }
}
```

### Payment Endpoints

**POST /api/payments/webhook**
```json
// 400 Bad Request - Invalid webhook
{
  "error": "invalid_webhook_data",
  "message": "Webhook data validation failed",
  "details": {
    "missing_fields": ["transaction_id"],
    "invalid_fields": ["amount"]
  }
}
```

## Rate Limiting Errors

Rate limit errors include helpful headers:

**Response Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642678800
Retry-After: 30
```

**Error Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "details": {
    "limit": 60,
    "window": "1 minute",
    "retry_after": 30
  }
}
```

## Client Error Handling

### Frontend Implementation

```typescript
interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

class ApiClient {
  async request<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new ApiClientError(error, response.status);
    }

    return response.json();
  }
}

class ApiClientError extends Error {
  constructor(
    public error: ApiError,
    public status: number
  ) {
    super(error.message);
    this.name = 'ApiClientError';
  }

  get errorType(): string {
    return this.error.error;
  }

  get details(): Record<string, any> | undefined {
    return this.error.details;
  }

  isValidationError(): boolean {
    return this.errorType === 'validation_error';
  }

  isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isRateLimit(): boolean {
    return this.status === 429;
  }
}

// Usage example
try {
  const product = await apiClient.request<Product>('/api/products/123');
} catch (error) {
  if (error instanceof ApiClientError) {
    switch (error.errorType) {
      case 'not_found':
        showNotification('Product not found', 'error');
        break;
      case 'validation_error':
        handleValidationErrors(error.details);
        break;
      case 'unauthorized':
        redirectToLogin();
        break;
      case 'rate_limit_exceeded':
        const retryAfter = error.details?.retry_after || 60;
        showNotification(`Rate limit exceeded. Try again in ${retryAfter} seconds`, 'warning');
        break;
      default:
        showNotification('An error occurred', 'error');
    }
  }
}
```

### Form Validation Error Handling

```typescript
interface ValidationErrorDetail {
  field: string;
  message: string;
  code: string;
  value?: any;
}

function handleValidationErrors(details: ValidationErrorDetail[]) {
  const fieldErrors: Record<string, string[]> = {};

  details.forEach(error => {
    if (!fieldErrors[error.field]) {
      fieldErrors[error.field] = [];
    }
    fieldErrors[error.field].push(error.message);
  });

  // Update form field errors
  Object.entries(fieldErrors).forEach(([field, messages]) => {
    const fieldElement = document.querySelector(`[name="${field}"]`);
    if (fieldElement) {
      fieldElement.classList.add('error');
      const errorElement = fieldElement.parentElement?.querySelector('.error-message');
      if (errorElement) {
        errorElement.textContent = messages.join(', ');
      }
    }
  });
}
```

### Retry Logic

```typescript
async function requestWithRetry<T>(
  request: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await request();
    } catch (error) {
      if (error instanceof ApiClientError) {
        // Don't retry client errors (4xx)
        if (error.status >= 400 && error.status < 500) {
          throw error;
        }

        // Handle rate limiting
        if (error.status === 429) {
          const retryAfter = error.details?.retry_after || delay;
          if (attempt < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
            continue;
          }
        }
      }

      // Retry server errors (5xx) with exponential backoff
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt - 1)));
        continue;
      }

      throw error;
    }
  }

  throw new Error('Max retries exceeded');
}
```

## Error Logging and Monitoring

### Server-side Error Tracking

```python
import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    error_id = generate_error_id()

    # Log error details
    logger.error(
        f"API Error {error_id}: {type(exc).__name__}: {str(exc)}",
        extra={
            "error_id": error_id,
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "traceback": traceback.format_exc()
        }
    )

    # Return user-friendly error
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": {
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### Error Metrics

Track error metrics for monitoring:

- Error rate by endpoint
- Error types distribution
- Response time for error responses
- User-specific error patterns
- Rate limiting violations

### Client-side Error Reporting

```typescript
class ErrorReporter {
  static report(error: ApiClientError, context?: Record<string, any>) {
    // Send to error tracking service (e.g., Sentry)
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        tags: {
          errorType: error.errorType,
          httpStatus: error.status
        },
        extra: {
          ...error.details,
          ...context
        }
      });
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', error);
    }
  }
}
```

## Best Practices

### For API Consumers

1. **Always check HTTP status codes** before parsing response
2. **Handle specific error types** rather than generic error handling
3. **Implement retry logic** for transient errors (5xx, rate limits)
4. **Show user-friendly messages** based on error types
5. **Log errors** for debugging and monitoring
6. **Validate data** on client side to reduce validation errors

### For API Developers

1. **Use consistent error format** across all endpoints
2. **Provide meaningful error messages** that help users understand the issue
3. **Include relevant context** in error details
4. **Use appropriate HTTP status codes**
5. **Log errors** with sufficient context for debugging
6. **Document expected errors** for each endpoint
7. **Test error scenarios** thoroughly

### Security Considerations

1. **Don't expose sensitive information** in error messages
2. **Sanitize error details** to prevent information leakage
3. **Use generic messages** for security-related errors
4. **Rate limit error responses** to prevent abuse
5. **Log security events** for monitoring

---

This error handling standard ensures consistent, helpful, and secure error responses across the entire FrozenBot API.
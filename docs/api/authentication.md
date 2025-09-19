# FrozenBot API Authentication

This document describes the authentication mechanisms used in the FrozenBot API.

## Overview

The FrozenBot API uses multiple authentication methods depending on the client type:

1. **JWT Authentication** - For admin panel access
2. **Telegram WebApp Authentication** - For user interactions through Telegram WebApp
3. **Bot Token Authentication** - For internal bot operations (not covered in public API)

## 1. JWT Authentication

### Description
JWT (JSON Web Token) authentication is used for admin panel access. It provides secure, stateless authentication for administrative operations.

### How it works
1. Admin logs in with username/password
2. Server validates credentials and returns JWT access and refresh tokens
3. Client includes JWT token in `Authorization` header for subsequent requests
4. Server validates token and extracts user information

### Login Process

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "telegram_id": 123456789,
    "username": "admin",
    "first_name": "Admin",
    "is_admin": true,
    "is_active": true
  }
}
```

### Using JWT Tokens

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Example request:**
```bash
curl -H "Authorization: Bearer eyJ0eXAi..." \
     https://api.frozenbot.com/api/admin/dashboard/stats
```

### Token Refresh

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### JWT Token Structure

The JWT tokens contain the following claims:

**Access Token:**
```json
{
  "sub": "123456789",
  "user_id": 1,
  "username": "admin",
  "is_admin": true,
  "exp": 1642678800,
  "iat": 1642677000,
  "type": "access"
}
```

**Refresh Token:**
```json
{
  "sub": "123456789",
  "user_id": 1,
  "exp": 1645269000,
  "iat": 1642677000,
  "type": "refresh"
}
```

### Token Expiration

- **Access Token**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token**: 7 days (configurable)

## 2. Telegram WebApp Authentication

### Description
Telegram WebApp authentication validates users through Telegram's WebApp initData. This method ensures that requests come from legitimate Telegram users within the WebApp context.

### How it works
1. Telegram WebApp provides `initData` containing user information
2. Client sends `initData` in request header
3. Server validates `initData` signature using bot token
4. Server extracts user information from validated data

### InitData Structure

The initData string contains URL-encoded parameters:
```
query_id=AAH...&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22John%22%2C%22last_name%22%3A%22Doe%22%2C%22username%22%3A%22johndoe%22%2C%22language_code%22%3A%22en%22%7D&auth_date=1642677000&hash=abc123...
```

Decoded user object:
```json
{
  "id": 123456789,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "language_code": "en"
}
```

### Using Telegram WebApp Authentication

Include the initData in the `X-Telegram-Init-Data` header:

```http
X-Telegram-Init-Data: query_id=AAH...&user=%7B%22id%22%3A123456789...&auth_date=1642677000&hash=abc123...
```

**Example request:**
```bash
curl -H "X-Telegram-Init-Data: query_id=AAH..." \
     https://api.frozenbot.com/api/cart/123456789
```

### Validation Process

1. **Parse initData**: Extract parameters from URL-encoded string
2. **Verify timestamp**: Check `auth_date` is not too old (max 24 hours)
3. **Calculate hash**: Create HMAC-SHA256 hash using bot token
4. **Compare hashes**: Verify calculated hash matches provided hash
5. **Extract user**: Parse user data from validated initData

### Security Considerations

- InitData is only valid for 24 hours
- Each initData can only be used once (optional nonce checking)
- Bot token is used as HMAC key and must be kept secret
- All parameters must be included in hash calculation

## 3. Authentication Flow Examples

### Admin Panel Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB

    Client->>API: POST /auth/login {username, password}
    API->>DB: Validate credentials
    DB-->>API: User data
    API-->>Client: {access_token, refresh_token, user}

    Note over Client: Store tokens

    Client->>API: GET /api/admin/dashboard/stats<br/>Authorization: Bearer <token>
    API->>API: Validate JWT token
    API-->>Client: Dashboard data

    Note over Client: Token expires

    Client->>API: POST /auth/refresh {refresh_token}
    API-->>Client: {new_access_token}
```

### Telegram WebApp Flow

```mermaid
sequenceDiagram
    participant WebApp
    participant TelegramAPI
    participant API
    participant DB

    WebApp->>TelegramAPI: Get initData
    TelegramAPI-->>WebApp: initData with user info

    WebApp->>API: GET /api/cart/123456789<br/>X-Telegram-Init-Data: <initData>
    API->>API: Validate initData signature
    API->>DB: Get/create user by telegram_id
    DB-->>API: User data
    API-->>WebApp: Cart data
```

## 4. Error Responses

### JWT Authentication Errors

**401 Unauthorized - Invalid token:**
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

**401 Unauthorized - Missing token:**
```json
{
  "error": "unauthorized",
  "message": "Authorization header missing"
}
```

**403 Forbidden - Insufficient permissions:**
```json
{
  "error": "forbidden",
  "message": "Admin access required"
}
```

### Telegram WebApp Authentication Errors

**401 Unauthorized - Invalid initData:**
```json
{
  "error": "unauthorized",
  "message": "Invalid Telegram initData"
}
```

**401 Unauthorized - Expired initData:**
```json
{
  "error": "unauthorized",
  "message": "Telegram initData expired"
}
```

**400 Bad Request - Missing initData:**
```json
{
  "error": "bad_request",
  "message": "X-Telegram-Init-Data header required"
}
```

## 5. Implementation Examples

### Frontend (React/TypeScript)

**JWT Authentication:**
```typescript
class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  async login(username: string, password: string) {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      localStorage.setItem('tokens', JSON.stringify(data));
      return data.user;
    }
    throw new Error('Login failed');
  }

  async apiRequest(url: string, options: RequestInit = {}) {
    const headers = {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    let response = await fetch(url, { ...options, headers });

    // Try refresh if token expired
    if (response.status === 401 && this.refreshToken) {
      await this.refreshAccessToken();
      headers['Authorization'] = `Bearer ${this.accessToken}`;
      response = await fetch(url, { ...options, headers });
    }

    return response;
  }

  private async refreshAccessToken() {
    const response = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
    } else {
      this.logout();
    }
  }
}
```

**Telegram WebApp Authentication:**
```typescript
class TelegramAuthService {
  private initData: string;

  constructor() {
    // Get initData from Telegram WebApp
    this.initData = (window as any).Telegram?.WebApp?.initData || '';
  }

  async apiRequest(url: string, options: RequestInit = {}) {
    const headers = {
      'X-Telegram-Init-Data': this.initData,
      'Content-Type': 'application/json',
      ...options.headers
    };

    return fetch(url, { ...options, headers });
  }

  getCurrentUser() {
    const urlParams = new URLSearchParams(this.initData);
    const userParam = urlParams.get('user');
    return userParam ? JSON.parse(decodeURIComponent(userParam)) : null;
  }
}
```

### Backend (Python/FastAPI)

**JWT Authentication Dependency:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

**Telegram WebApp Authentication Dependency:**
```python
from fastapi import Depends, HTTPException, Header
import hmac
import hashlib
from urllib.parse import parse_qsl

async def validate_telegram_init_data(
    x_telegram_init_data: str = Header(alias="X-Telegram-Init-Data")
):
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Telegram-Init-Data header required"
        )

    try:
        parsed_data = dict(parse_qsl(x_telegram_init_data))
        hash_value = parsed_data.pop('hash', '')

        # Check auth_date (not older than 24 hours)
        auth_date = int(parsed_data.get('auth_date', 0))
        if time.time() - auth_date > 86400:  # 24 hours
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Telegram initData expired"
            )

        # Verify hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        data_check_string = '\n'.join([
            f"{key}={value}" for key, value in sorted(parsed_data.items())
        ])

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(hash_value, calculated_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram initData"
            )

        # Extract user data
        user_data = json.loads(parsed_data.get('user', '{}'))
        return user_data

    except (ValueError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram initData format"
        )
```

## 6. Security Best Practices

### JWT Security
- Use strong secret keys (minimum 256 bits)
- Implement proper token expiration
- Store refresh tokens securely
- Implement token blacklisting for logout
- Use HTTPS in production
- Validate all token claims

### Telegram WebApp Security
- Always validate initData signature
- Check timestamp to prevent replay attacks
- Implement rate limiting
- Validate user permissions
- Use HTTPS for all communications
- Keep bot token secure

### General Security
- Implement proper CORS policies
- Use rate limiting on authentication endpoints
- Log authentication attempts
- Implement account lockout after failed attempts
- Regular security audits
- Monitor for suspicious activities

## 7. Rate Limiting

Authentication endpoints are rate limited to prevent abuse:

- `/auth/login`: 5 attempts per minute per IP
- `/auth/refresh`: 10 attempts per minute per user
- WebApp endpoints: 60 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642678800
```

## 8. Testing Authentication

### Testing JWT Authentication
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/admin/dashboard/stats

# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Testing Telegram WebApp Authentication
```bash
# Make request with initData
curl -H "X-Telegram-Init-Data: query_id=AAH...&user=%7B%22id%22..." \
  http://localhost:8000/api/cart/123456789
```

This authentication system provides secure, scalable access control for the FrozenBot API while supporting both administrative and user-facing operations.
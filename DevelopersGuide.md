# Frontend Integration Guide
For connecting to Subscription Management Backend

## Prerequisites
- Backend server running at http://localhost:8000
- Frontend hosted at https://desicodes.vercel.app
- CORS configured to allow the frontend domain

## API Base URL
```
http://localhost:8000/api/v1
```

## Authentication Flow
1. Register user → POST /auth/register
2. Login → POST /auth/login → Returns JWT token
3. Use token → Include in Authorization header for all protected requests

## Endpoints

### Public Endpoints (no token required)
- **POST /auth/register** - Create new account
- **POST /auth/login** - Login and receive token

### Protected Endpoints (token required)
- **GET /auth/me** - Get current user information
- **GET /subscriptions** - Get user subscriptions
- **GET /billing/invoices** - Get user invoices
- **GET /payments/history** - Get payment history

## Request/Response Formats

### Registration Request
```
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

### Registration Response (201 Created)
```
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Login Request
```
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

### Login Response (200 OK)
```
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "is_active": true
  }
}
```

## Token Usage
Store the received token and include it in the Authorization header for all subsequent requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Details
- Token type: JWT
- Expiration: 24 hours
- Storage recommendation: localStorage or sessionStorage
- Required for all endpoints except /auth/register and /auth/login

## Error Responses

### 400 Bad Request
```
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```
{
  "detail": "Invalid email or password"
}
```

### 403 Forbidden
```
{
  "detail": "Inactive user"
}
```

## Development Steps

### 1. Verify Backend Connection
Check if backend is accessible by visiting http://localhost:8000/docs in browser.

### 2. Test Authentication Flow
Use curl or Postman to test:
- Register a user
- Login with credentials
- Use token to access protected endpoints

### 3. Implement in Frontend
- Store API base URL in environment variable
- Create service for API calls
- Handle token storage/retrieval
- Implement login/logout functionality
- Add token to all protected requests

## Testing Commands

### Using curl:
```
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'

# Get current user (with token)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## CORS Configuration
Backend is configured to allow requests from:
- http://localhost:3000
- https://desicodes.vercel.app

## Security Notes
- Tokens expire after 24 hours
- Always use HTTPS in production
- Store tokens securely (not in plain text)
- Clear tokens on logout

## Support
For integration issues:
1. Check browser console for errors
2. Verify backend is running
3. Ensure CORS is properly configured
4. Test with curl to isolate API issues

Contact backend team with:
- Error messages
- Request/response details
- Steps to reproduce the issue

## Production Notes
For production deployment:
- Update API base URL to production endpoint
- Ensure both frontend and backend use HTTPS
- Implement proper error handling
- Add request timeouts
- Consider implementing refresh token mechanism

This guide provides the essential information needed to integrate with the backend API. Follow the authentication flow and use the provided endpoint specifications to implement the frontend functionality.
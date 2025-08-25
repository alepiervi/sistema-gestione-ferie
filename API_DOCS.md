# 📚 API Documentation - Sistema Gestione Ferie e Permessi

## Base URL
```
Production: https://workleave-portal.preview.emergentagent.com/api
Development: http://localhost:8001/api
```

## Authentication

Tutti gli endpoint protetti richiedono un JWT token nell'header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 🔐 Authentication

#### POST /login
Autenticazione utente e ottenimento token JWT.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "admin|employee"
  }
}
```

### 👨‍💼 Admin Endpoints

#### GET /admin/dashboard
Statistiche dashboard amministratore.

**Auth:** Admin required

**Response:**
```json
{
  "pending_ferie": 0,
  "pending_permessi": 0,
  "pending_malattie": 0,
  "total_pending": 0
}
```

#### POST /admin/employees
Creazione nuovo dipendente.

**Auth:** Admin required

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### GET /admin/employees
Lista dipendenti.

**Auth:** Admin required

**Response:**
```json
[
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "created_at": "datetime",
    "is_active": true
  }
]
```

#### PUT /admin/requests/{request_id}
Approvazione/Rifiuto richiesta.

**Auth:** Admin required

**Request Body:**
```json
{
  "request_id": "string",
  "action": "approve|reject",
  "notes": "string (optional)"
}
```

#### PUT /admin/settings
Aggiornamento impostazioni amministratore.

**Auth:** Admin required

**Request Body:**
```json
{
  "email": "string"
}
```

### 👤 Employee Endpoints

#### POST /requests
Creazione nuova richiesta.

**Auth:** Employee required

**Request Body (Ferie):**
```json
{
  "type": "ferie",
  "start_date": "2025-09-01",
  "end_date": "2025-09-05"
}
```

**Request Body (Permesso):**
```json
{
  "type": "permesso",
  "permit_date": "2025-08-25",
  "start_time": "09:00",
  "end_time": "12:00"
}
```

**Request Body (Malattia):**
```json
{
  "type": "malattia",
  "sick_start_date": "2025-08-25",
  "sick_days": 3,
  "protocol_code": "PROT12345"
}
```

#### GET /requests
Lista richieste dell'utente corrente.

**Auth:** Required

**Response:**
```json
[
  {
    "id": "string",
    "user_id": "string",
    "type": "ferie|permesso|malattia",
    "status": "pending|approved|rejected",
    "start_date": "date (for ferie)",
    "end_date": "date (for ferie)",
    "permit_date": "date (for permesso)",
    "start_time": "time (for permesso)",
    "end_time": "time (for permesso)",
    "sick_start_date": "date (for malattia)",
    "sick_days": "integer (for malattia)",
    "protocol_code": "string (for malattia)",
    "admin_notes": "string (optional)",
    "created_at": "datetime",
    "updated_at": "datetime (optional)"
  }
]
```

#### PUT /requests/{request_id}
Modifica richiesta (solo se pending).

**Auth:** Employee required (owner)

**Request Body:** Same as POST /requests

#### DELETE /requests/{request_id}
Cancellazione richiesta (solo se pending).

**Auth:** Employee required (owner)

### 🔧 Utility Endpoints

#### PUT /change-password
Cambio password utente.

**Auth:** Required

**Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

#### GET /
Root endpoint con informazioni API.

**Response:**
```json
{
  "message": "Sistema Gestione Ferie e Permessi API",
  "version": "1.0.0"
}
```

## Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (invalid token or credentials)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **422**: Unprocessable Entity (validation error)
- **500**: Internal Server Error

## Error Response Format

```json
{
  "detail": "Error message description"
}
```

## Validation Rules

### Ferie (Vacation)
- `start_date` and `end_date` are required
- `end_date` must be after `start_date`
- Maximum 15 consecutive days allowed

### Permesso (Time Off)
- `permit_date`, `start_time`, and `end_time` are required
- Times must be in HH:MM format

### Malattia (Sick Leave)
- `sick_start_date`, `sick_days`, and `protocol_code` are required
- `sick_days` must be a positive integer
- `protocol_code` cannot be empty

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended to:
- Limit login attempts
- Throttle request creation
- Monitor for abuse

## Examples

### Complete Workflow Example

```bash
# 1. Login as admin
curl -X POST "https://workleave-portal.preview.emergentagent.com/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access_token": "eyJ...", "user": {...}}

# 2. Create employee
curl -X POST "https://workleave-portal.preview.emergentagent.com/api/admin/employees" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"username": "john.doe", "email": "john@company.com", "password": "secret123"}'

# 3. Login as employee
curl -X POST "https://workleave-portal.preview.emergentagent.com/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "secret123"}'

# 4. Create vacation request
curl -X POST "https://workleave-portal.preview.emergentagent.com/api/requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"type": "ferie", "start_date": "2025-09-01", "end_date": "2025-09-05"}'

# 5. Admin approves request
curl -X PUT "https://workleave-portal.preview.emergentagent.com/api/admin/requests/{request_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"request_id": "{request_id}", "action": "approve", "notes": "Approved for September vacation"}'
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `https://workleave-portal.preview.emergentagent.com/docs`
- **ReDoc**: `https://workleave-portal.preview.emergentagent.com/redoc`

These interfaces allow you to test all endpoints directly from the browser.

## Security Considerations

1. **JWT Tokens**: Expire after 30 days, store securely
2. **Password Hashing**: BCrypt with salt
3. **CORS**: Configure appropriately for production
4. **HTTPS**: Always use HTTPS in production
5. **Input Validation**: All inputs are validated server-side
6. **Role-based Access**: Endpoints are protected by user roles

## Support

For API questions or issues:
- Check the interactive docs at `/docs`
- Review this documentation
- Contact support team
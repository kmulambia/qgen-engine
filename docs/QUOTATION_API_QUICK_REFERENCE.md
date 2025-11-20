# Quotation API - Quick Reference

## Endpoints

### 1. Approve Quotation
```
POST /api/v1/quotations/{quotation_id}/approve
Authorization: Bearer {token}
Body: { "message": "optional" }
```

### 2. Resend Quotation
```
POST /api/v1/quotations/{quotation_id}/resend
Authorization: Bearer {token}
Body: { "message": "optional" }
```

### 3. Public View (No Auth)
```
GET /api/v1/quotations/public/{token}
No Authorization header needed
```

## Response Format

All endpoints return the same quotation object structure:

```typescript
{
  id: string;
  quotation_number: string;
  title: string;
  quotation_status: "sent" | "draft" | "approved" | "rejected" | "expired";
  sent_at: string | null;  // ISO datetime
  access_token: string | null;
  token_expires_at: string | null;  // ISO datetime
  total: number;
  currency: string;
  valid_until: string;  // ISO date
  client: { ... };
  items: [ ... ];
  // ... other fields
}
```

## Email Link Format

```
{WEBSITE_URL}/quotations/{quotation_id}?token={access_token}
```

## Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 400 | "Client email address is required" | Add email to client profile |
| 400 | "Quotation cannot be approved in its current status" | Check quotation status |
| 401 | "Invalid or expired access token" | Request new quotation email |
| 404 | "Quotation not found" | Verify quotation ID |

## Status Flow

```
draft → [approve] → sent
sent → [resend] → sent (status unchanged)
```

## Quick Code Snippets

### Approve
```typescript
await fetch(`/api/v1/quotations/${id}/approve`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
```

### Resend
```typescript
await fetch(`/api/v1/quotations/${id}/resend`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
```

### Public View
```typescript
const token = new URLSearchParams(window.location.search).get('token');
await fetch(`/api/v1/quotations/public/${token}`, {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
});
```


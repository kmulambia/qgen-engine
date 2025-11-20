# Quotation Approve Workflow - Frontend Integration Guide

## Overview

This document describes the new quotation approval workflow features that allow sending quotations to clients via email with secure public access links. The implementation includes three main endpoints:

1. **Approve Quotation** - Send quotation to client for the first time
2. **Resend Quotation** - Resend quotation email to client
3. **Public Quotation View** - View quotation using secure token (no authentication required)

---

## API Endpoints

### Base URL
All endpoints are prefixed with `/api/v1/quotations`

### Authentication
- **Approve** and **Resend** endpoints require JWT authentication (Bearer token)
- **Public View** endpoint does NOT require authentication

---

## 1. Approve Quotation

Sends a quotation to the client via email for the first time. This will:
- Change quotation status to "sent"
- Generate a secure access token
- Queue an email to the client
- Set the `sent_at` timestamp

### Endpoint
```
POST /api/v1/quotations/{quotation_id}/approve
```

### Headers
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Path Parameters
- `quotation_id` (UUID, required) - The ID of the quotation to approve

### Request Body
```json
{
  "message": "Optional custom message to include in email"
}
```

**Note:** The `message` field is optional. If not provided, send an empty object `{}` or omit the field.

### Response
**Status Code:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "quotation_number": "QT-2024-1234567890",
  "title": "Website Development Project",
  "description": "Complete website redesign and development",
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "layout_id": "770e8400-e29b-41d4-a716-446655440002",
  "quotation_date": "2024-01-15",
  "valid_until": "2024-02-15",
  "items": [
    {
      "item_id": "item-1",
      "description": "Frontend Development",
      "quantity": 40.00,
      "unit_price": 150.00,
      "unit": "hours",
      "total": 6000.00,
      "notes": null
    }
  ],
  "currency": "USD",
  "subtotal": 6000.00,
  "discount_percentage": 10.00,
  "discount_amount": 600.00,
  "tax_percentage": 8.00,
  "tax_amount": 432.00,
  "total": 5832.00,
  "notes": null,
  "terms_conditions": "Payment due within 30 days",
  "quotation_status": "sent",
  "sent_at": "2024-01-20T10:30:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_expires_at": "2024-02-19T10:30:00Z",
  "client": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "company_name": "Acme Corporation",
    "email": "info@acme.com",
    "contact_person_email": "john.doe@acme.com",
    "contact_person_name": "John Doe"
  },
  "layout": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "Standard Layout"
  },
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "status": "active"
}
```

### Error Responses

#### 404 Not Found
```json
{
  "detail": "Quotation not found"
}
```

#### 400 Bad Request
```json
{
  "detail": "Quotation cannot be approved in its current status"
}
```
**Note:** This occurs when quotation status is not "draft" or "sent"

```json
{
  "detail": "Client email address is required to send quotation"
}
```
**Note:** This occurs when the client has no email address configured

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "An error occurred while approving the quotation."
}
```

### Example Implementation

#### JavaScript/TypeScript (Fetch API)
```typescript
async function approveQuotation(quotationId: string, message?: string) {
  const token = localStorage.getItem('auth_token'); // Your token storage method
  
  try {
    const response = await fetch(
      `/api/v1/quotations/${quotationId}/approve`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message || undefined
        })
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to approve quotation');
    }
    
    const quotation = await response.json();
    return quotation;
  } catch (error) {
    console.error('Error approving quotation:', error);
    throw error;
  }
}
```

#### React Hook Example
```typescript
import { useState } from 'react';

function useApproveQuotation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const approveQuotation = async (quotationId: string, message?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        `/api/v1/quotations/${quotationId}/approve`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: message || undefined })
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to approve quotation');
      }
      
      const quotation = await response.json();
      return quotation;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  return { approveQuotation, loading, error };
}
```

---

## 2. Resend Quotation

Resends a quotation email to the client. This will:
- Regenerate the access token if it's expired or missing
- Update the `sent_at` timestamp
- Queue a new email to the client
- **Does NOT change the quotation status** (if already "sent", it remains "sent")

### Endpoint
```
POST /api/v1/quotations/{quotation_id}/resend
```

### Headers
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Path Parameters
- `quotation_id` (UUID, required) - The ID of the quotation to resend

### Request Body
```json
{
  "message": "Optional custom message to include in email"
}
```

**Note:** The `message` field is optional.

### Response
**Status Code:** `200 OK`

Same response structure as Approve Quotation endpoint.

### Error Responses

Same error responses as Approve Quotation endpoint, except:
- No "invalid_quotation_status" error (resend works regardless of status)

### Example Implementation

```typescript
async function resendQuotation(quotationId: string, message?: string) {
  const token = localStorage.getItem('auth_token');
  
  try {
    const response = await fetch(
      `/api/v1/quotations/${quotationId}/resend`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message || undefined
        })
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to resend quotation');
    }
    
    const quotation = await response.json();
    return quotation;
  } catch (error) {
    console.error('Error resending quotation:', error);
    throw error;
  }
}
```

---

## 3. Public Quotation View

Retrieves a quotation using a secure access token. This endpoint does NOT require authentication and is intended for clients to view quotations via the link sent in the email.

### Endpoint
```
GET /api/v1/quotations/public/{token}
```

### Headers
```
Content-Type: application/json
```

**Note:** No Authorization header required.

### Path Parameters
- `token` (string, required) - The JWT access token received in the email link

### Response
**Status Code:** `200 OK`

Same response structure as Approve Quotation endpoint, with full quotation details including:
- All line items
- Client information
- Layout information
- Financial calculations

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired access token"
}
```

#### 404 Not Found
```json
{
  "detail": "Quotation not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "An error occurred while retrieving the quotation."
}
```

### Example Implementation

#### Extract Token from URL
The email link format is:
```
{WEBSITE_URL}/quotations/{quotation_id}?token={access_token}
```

Example:
```
https://yourapp.com/quotations/550e8400-e29b-41d4-a716-446655440000?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### JavaScript/TypeScript
```typescript
// Extract token from URL query parameter
function getTokenFromURL(): string | null {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('token');
}

// Fetch quotation using token
async function getQuotationByToken(token: string) {
  try {
    const response = await fetch(
      `/api/v1/quotations/public/${token}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to load quotation');
    }
    
    const quotation = await response.json();
    return quotation;
  } catch (error) {
    console.error('Error loading quotation:', error);
    throw error;
  }
}

// React component example
function QuotationViewPage() {
  const [quotation, setQuotation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const token = getTokenFromURL();
    
    if (!token) {
      setError('No access token provided');
      setLoading(false);
      return;
    }
    
    getQuotationByToken(token)
      .then(data => {
        setQuotation(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!quotation) return <div>Quotation not found</div>;
  
  return (
    <div>
      <h1>Quotation {quotation.quotation_number}</h1>
      <h2>{quotation.title}</h2>
      {/* Render quotation details */}
    </div>
  );
}
```

#### React Router Example
```typescript
// Route definition
<Route 
  path="/quotations/:quotationId" 
  element={<QuotationViewPage />} 
/>

// Component
function QuotationViewPage() {
  const { quotationId } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  // ... rest of implementation
}
```

---

## Email Link Format

The email sent to clients contains a link in this format:

```
{WEBSITE_URL}/quotations/{quotation_id}?token={access_token}
```

### Token Details
- **Type:** JWT (JSON Web Token)
- **Expiration:** 30 days from when quotation is approved/sent
- **Contains:** Quotation ID and token type
- **Security:** Signed with server secret key

### Frontend Routing

You should set up a route to handle this URL pattern:

```typescript
// React Router example
<Route 
  path="/quotations/:id" 
  element={<PublicQuotationView />} 
/>

// Next.js example (app router)
// app/quotations/[id]/page.tsx
export default function QuotationPage({ 
  params, 
  searchParams 
}: { 
  params: { id: string };
  searchParams: { token?: string };
}) {
  const token = searchParams.token;
  // Fetch and display quotation
}
```

---

## UI/UX Recommendations

### 1. Approve Button
- Show "Approve & Send" button on quotation detail page
- Only enable if quotation status is "draft" or "sent"
- Show confirmation dialog before sending
- Display success message after approval
- Update quotation status in UI immediately

### 2. Resend Button
- Show "Resend Email" button on quotation detail page
- Enable for any quotation that has been sent before
- Show confirmation dialog
- Display success message

### 3. Public View Page
- Clean, professional design (client-facing)
- Display all quotation details clearly
- Show client information
- Display line items in a table
- Show financial summary (subtotal, discount, tax, total)
- Include terms and conditions
- Show valid until date prominently
- Handle expired/invalid tokens gracefully
- Provide contact information for support

### 4. Status Indicators
- Show "Sent" status with timestamp
- Display "Sent at: {date}" information
- Show token expiration date (if needed for internal use)

### Example UI States

```typescript
// Quotation status badge
function QuotationStatusBadge({ status, sentAt }) {
  const statusConfig = {
    draft: { label: 'Draft', color: 'gray' },
    sent: { label: 'Sent', color: 'blue' },
    approved: { label: 'Approved', color: 'green' },
    rejected: { label: 'Rejected', color: 'red' },
    expired: { label: 'Expired', color: 'orange' }
  };
  
  const config = statusConfig[status] || { label: status, color: 'gray' };
  
  return (
    <div className={`badge badge-${config.color}`}>
      {config.label}
      {status === 'sent' && sentAt && (
        <span className="text-xs ml-2">
          Sent: {new Date(sentAt).toLocaleDateString()}
        </span>
      )}
    </div>
  );
}
```

---

## Error Handling

### Common Error Scenarios

1. **No Client Email**
   - Show: "Cannot send quotation: Client email address is required"
   - Action: Prompt user to add email to client profile

2. **Invalid Status**
   - Show: "Quotation cannot be approved in its current status"
   - Action: Check quotation status before showing approve button

3. **Expired Token (Public View)**
   - Show: "This quotation link has expired. Please contact support."
   - Action: Provide contact information or resend option

4. **Invalid Token (Public View)**
   - Show: "Invalid access link. Please check your email for the correct link."
   - Action: Provide support contact

5. **Network Errors**
   - Show: "Failed to send quotation. Please try again."
   - Action: Retry button

### Error Handling Example

```typescript
function handleApproveError(error: any) {
  const errorMessage = error.message || error.detail || 'Unknown error';
  
  if (errorMessage.includes('email')) {
    return {
      title: 'Email Required',
      message: 'The client must have an email address to send quotations.',
      action: 'Go to Client Profile'
    };
  }
  
  if (errorMessage.includes('status')) {
    return {
      title: 'Invalid Status',
      message: 'This quotation cannot be approved in its current status.',
      action: null
    };
  }
  
  return {
    title: 'Error',
    message: 'Failed to approve quotation. Please try again.',
    action: 'Retry'
  };
}
```

---

## Testing Checklist

### Approve Quotation
- [ ] Successfully approve draft quotation
- [ ] Successfully approve already-sent quotation
- [ ] Error when quotation status is "approved"
- [ ] Error when quotation status is "rejected"
- [ ] Error when client has no email
- [ ] Error when quotation not found
- [ ] Authentication required

### Resend Quotation
- [ ] Successfully resend quotation
- [ ] Token regenerated if expired
- [ ] Error when client has no email
- [ ] Error when quotation not found
- [ ] Authentication required

### Public View
- [ ] Successfully view quotation with valid token
- [ ] Error with expired token
- [ ] Error with invalid token
- [ ] Error with missing token
- [ ] No authentication required
- [ ] All quotation data displayed correctly

---

## Environment Variables

The frontend should be aware of the following (if needed):

- `WEBSITE_URL` - Base URL for generating quotation links (configured on backend)
- API base URL - Where your API is hosted

---

## Additional Notes

1. **Email Delivery**: Emails are queued and sent asynchronously. The API returns immediately after queuing the email.

2. **Token Security**: Tokens are JWT-signed and expire after 30 days. Do not store tokens in localStorage for public view pages.

3. **Status Flow**: 
   - `draft` → `sent` (on approve)
   - `sent` → `sent` (on resend, status unchanged)

4. **Client Email Priority**: 
   - First tries `contact_person_email`
   - Falls back to `email` if contact person email not available

5. **Rate Limiting**: All endpoints are rate-limited. Handle 429 responses appropriately.

---

## Support

For questions or issues with integration, contact the backend team or refer to the API documentation at `/api/docs`.

---

## Changelog

- **2024-01-20**: Initial implementation
  - Added approve quotation endpoint
  - Added resend quotation endpoint
  - Added public quotation view endpoint
  - Added email template with secure links


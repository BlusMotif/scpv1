# API Documentation - KTU Student Report System

## 📋 Overview

The KTU Student Report System provides a RESTful API for managing student issues, user authentication, and administrative functions. This documentation covers all available endpoints, request/response formats, and authentication requirements.

## 🔐 Authentication

### Session-Based Authentication
The system uses Flask sessions for authentication. Users must log in to receive a session cookie.

```python
# Authentication check
if 'user_email' not in session:
    return redirect(url_for('login'))
```

### Role-Based Access Control
- **Student**: Basic issue management
- **Sub-Admin**: Student issue management within assigned categories  
- **Super Admin**: Full system administration

## 🌐 Base URL
```
Development: http://127.0.0.1:5000
Production: https://your-domain.com
```

## 📚 API Endpoints

### Authentication Endpoints

#### POST /login
Authenticate user and create session.

**Request Body:**
```json
{
  "email": "student@ktu.edu.gh",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "user": {
    "email": "student@ktu.edu.gh",
    "role": "student",
    "full_name": "John Doe"
  },
  "redirect_url": "/dashboard"
}
```

**Status Codes:**
- `200`: Success
- `401`: Invalid credentials
- `403`: Account not verified
- `400`: Missing required fields

#### POST /register
Create new user account.

**Request Body:**
```json
{
  "email": "newstudent@ktu.edu.gh",
  "password": "password123",
  "full_name": "Jane Smith",
  "confirm_password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Registration successful. Please verify your email.",
  "user_id": "firebase_uid_here"
}
```

**Status Codes:**
- `201`: User created successfully
- `400`: Validation errors
- `409`: Email already exists

#### GET /logout
End user session.

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

#### POST /forgot-password
Request password reset.

**Request Body:**
```json
{
  "email": "student@ktu.edu.gh"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Password reset email sent"
}
```

### Dashboard Endpoints

#### GET /dashboard
Get user dashboard based on role.

**Response (Student):**
```json
{
  "user": {
    "email": "student@ktu.edu.gh",
    "role": "student",
    "full_name": "John Doe"
  },
  "stats": {
    "total_issues": 5,
    "pending_issues": 2,
    "resolved_issues": 3,
    "in_progress_issues": 0
  },
  "recent_issues": [
    {
      "id": 1,
      "title": "Broken projector in Room 101",
      "status": "pending",
      "date": "2024-01-15",
      "category": "Infrastructure"
    }
  ]
}
```

#### GET /admin/dashboard
Get admin dashboard with system statistics.

**Authorization:** Super Admin only

**Response:**
```json
{
  "stats": {
    "total_users": 156,
    "total_issues": 89,
    "pending_issues": 23,
    "resolved_issues": 66,
    "categories": 8,
    "subadmins": 5
  },
  "recent_activities": [
    {
      "id": 1,
      "action": "Issue Created",
      "user": "john.doe@ktu.edu.gh",
      "timestamp": "2024-01-15T10:30:00Z",
      "details": "New infrastructure issue reported"
    }
  ],
  "quick_stats": {
    "today_issues": 12,
    "this_week_issues": 45,
    "active_users": 89
  }
}
```

### Issue Management Endpoints

#### GET /submit-issue
Get issue submission form data.

**Authorization:** Authenticated users

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Infrastructure",
      "description": "Building and facility issues"
    },
    {
      "id": 2,
      "name": "IT Support",
      "description": "Technology and computer issues"
    }
  ]
}
```

#### POST /submit-issue
Submit new issue.

**Authorization:** Authenticated users

**Request Body:**
```json
{
  "title": "Broken projector in Room 101",
  "description": "The projector in Room 101 is not working. Students cannot see presentations clearly.",
  "category": "Infrastructure",
  "priority": "medium"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Issue submitted successfully",
  "issue": {
    "id": 123,
    "title": "Broken projector in Room 101",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "ticket_number": "KTU-2024-123"
  }
}
```

#### GET /my-issues
Get current user's issues.

**Authorization:** Authenticated users

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_progress, resolved)
- `category` (optional): Filter by category
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)

**Response:**
```json
{
  "issues": [
    {
      "id": 123,
      "title": "Broken projector in Room 101",
      "description": "The projector is not working",
      "category": "Infrastructure",
      "status": "pending",
      "priority": "medium",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "assigned_to": null,
      "comments": []
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_items": 25,
    "items_per_page": 10
  }
}
```

#### GET /issues/{issue_id}
Get specific issue details.

**Authorization:** Issue owner, Sub-Admin, or Super Admin

**Response:**
```json
{
  "issue": {
    "id": 123,
    "title": "Broken projector in Room 101",
    "description": "Detailed description...",
    "category": "Infrastructure",
    "status": "in_progress",
    "priority": "medium",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:20:00Z",
    "user": {
      "email": "student@ktu.edu.gh",
      "full_name": "John Doe"
    },
    "assigned_to": {
      "email": "subadmin@ktu.edu.gh",
      "full_name": "Admin User"
    },
    "comments": [
      {
        "id": 1,
        "message": "Issue has been assigned to maintenance team",
        "author": "subadmin@ktu.edu.gh",
        "created_at": "2024-01-16T14:20:00Z"
      }
    ]
  }
}
```

#### PUT /issues/{issue_id}
Update issue status or details.

**Authorization:** Sub-Admin or Super Admin

**Request Body:**
```json
{
  "status": "in_progress",
  "comment": "Issue has been assigned to maintenance team",
  "assigned_to": "maintenance@ktu.edu.gh"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Issue updated successfully",
  "issue": {
    "id": 123,
    "status": "in_progress",
    "updated_at": "2024-01-16T14:20:00Z"
  }
}
```

### Admin Endpoints

#### GET /admin/analytics
Get system analytics and reports.

**Authorization:** Super Admin only

**Query Parameters:**
- `period` (optional): Time period (week, month, year)
- `category` (optional): Filter by category

**Response:**
```json
{
  "overview": {
    "total_issues": 234,
    "resolved_rate": 78.5,
    "avg_resolution_time": "2.3 days",
    "user_satisfaction": 4.2
  },
  "issue_trends": {
    "labels": ["Jan", "Feb", "Mar", "Apr"],
    "data": [45, 67, 52, 78]
  },
  "category_distribution": {
    "Infrastructure": 45,
    "IT Support": 32,
    "Academic": 28,
    "Other": 15
  },
  "status_breakdown": {
    "pending": 23,
    "in_progress": 45,
    "resolved": 166
  }
}
```

#### GET /admin/manage-subadmins
Get list of sub-administrators.

**Authorization:** Super Admin only

**Response:**
```json
{
  "subadmins": [
    {
      "id": 1,
      "username": "subadmin1",
      "email": "subadmin1@ktu.edu.gh",
      "full_name": "Sub Admin One",
      "is_active": true,
      "assigned_issues": 12,
      "login_count": 45,
      "last_login": "2024-01-15T09:30:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "stats": {
    "total_subadmins": 5,
    "active_subadmins": 4,
    "total_assigned_issues": 67
  }
}
```

#### POST /admin/create-subadmin
Create new sub-administrator account.

**Authorization:** Super Admin only

**Request Body:**
```json
{
  "username": "newsubadmin",
  "email": "newsubadmin@ktu.edu.gh",
  "full_name": "New Sub Admin",
  "password": "securepassword123",
  "confirm_password": "securepassword123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Sub-admin created successfully",
  "subadmin": {
    "id": 6,
    "username": "newsubadmin",
    "email": "newsubadmin@ktu.edu.gh",
    "role": "subadmin"
  }
}
```

#### PUT /admin/subadmin/{subadmin_id}/toggle
Activate/deactivate sub-administrator.

**Authorization:** Super Admin only

**Response:**
```json
{
  "status": "success",
  "message": "Sub-admin status updated",
  "subadmin": {
    "id": 1,
    "is_active": false
  }
}
```

#### GET /admin/system-settings
Get system configuration settings.

**Authorization:** Super Admin only

**Response:**
```json
{
  "settings_by_category": {
    "general": [
      {
        "key": "site_name",
        "value": "KTU Student Report System",
        "type": "text",
        "description": "System name displayed to users"
      }
    ],
    "notifications": [
      {
        "key": "email_notifications",
        "value": true,
        "type": "boolean",
        "description": "Enable email notifications"
      }
    ]
  }
}
```

#### POST /admin/system-settings
Update system settings.

**Authorization:** Super Admin only

**Request Body:**
```json
{
  "settings": {
    "site_name": "KTU Student Report System",
    "email_notifications": true,
    "maintenance_mode": false
  }
}
```

### Category Management

#### GET /admin/manage-categories
Get issue categories.

**Authorization:** Super Admin only

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Infrastructure",
      "description": "Building and facility issues",
      "issue_count": 45,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /admin/categories
Create new category.

**Authorization:** Super Admin only

**Request Body:**
```json
{
  "name": "New Category",
  "description": "Description of the new category",
  "color": "#007bff"
}
```

#### PUT /admin/categories/{category_id}
Update category.

**Authorization:** Super Admin only

#### DELETE /admin/categories/{category_id}
Delete category.

**Authorization:** Super Admin only

## 📊 Response Format

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Response data
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "errors": {
    "field_name": ["Validation error message"]
  },
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔍 Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request |
| 401  | Unauthorized |
| 403  | Forbidden |
| 404  | Not Found |
| 409  | Conflict |
| 422  | Unprocessable Entity |
| 500  | Internal Server Error |

## 🔄 Pagination

For endpoints that return lists, pagination is implemented:

```json
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 10,
    "total_items": 95,
    "items_per_page": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🔍 Filtering and Sorting

### Query Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)
- `sort`: Sort field (e.g., 'created_at', 'title')
- `order`: Sort order ('asc' or 'desc')
- `search`: Search term
- `status`: Filter by status
- `category`: Filter by category
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

### Example Request
```
GET /my-issues?page=2&limit=20&sort=created_at&order=desc&status=pending
```

## 🔐 Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authentication endpoints**: 5 requests per minute
- **General endpoints**: 100 requests per minute
- **Admin endpoints**: 200 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

## 🐛 Error Handling

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| VALIDATION_ERROR | Request validation failed |
| AUTHENTICATION_REQUIRED | User not authenticated |
| INSUFFICIENT_PERMISSIONS | User lacks required permissions |
| RESOURCE_NOT_FOUND | Requested resource doesn't exist |
| DUPLICATE_RESOURCE | Resource already exists |
| RATE_LIMIT_EXCEEDED | Too many requests |

### Example Error Response
```json
{
  "status": "error",
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "errors": {
    "email": ["Email is required"],
    "password": ["Password must be at least 6 characters"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📝 Request/Response Examples

### Submit Issue Example
```bash
curl -X POST http://127.0.0.1:5000/submit-issue \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "title": "Broken projector in Room 101",
    "description": "The projector is not working properly",
    "category": "Infrastructure"
  }'
```

### Get Dashboard Example
```bash
curl -X GET http://127.0.0.1:5000/dashboard \
  -H "Cookie: session=your_session_cookie"
```

## 🔧 SDK Examples

### Python SDK Example
```python
import requests

class KTUAPIClient:
    def __init__(self, base_url, session_cookie):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.set('session', session_cookie)
    
    def submit_issue(self, title, description, category):
        response = self.session.post(
            f"{self.base_url}/submit-issue",
            json={
                'title': title,
                'description': description,
                'category': category
            }
        )
        return response.json()
    
    def get_my_issues(self, status=None, page=1):
        params = {'page': page}
        if status:
            params['status'] = status
        
        response = self.session.get(
            f"{self.base_url}/my-issues",
            params=params
        )
        return response.json()

# Usage
client = KTUAPIClient('http://127.0.0.1:5000', 'your_session_cookie')
result = client.submit_issue(
    title="Network Issue",
    description="Cannot connect to WiFi",
    category="IT Support"
)
```

### JavaScript SDK Example
```javascript
class KTUAPIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async submitIssue(title, description, category) {
        const response = await fetch(`${this.baseUrl}/submit-issue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Include cookies
            body: JSON.stringify({
                title,
                description,
                category
            })
        });
        
        return await response.json();
    }
    
    async getMyIssues(status = null, page = 1) {
        const params = new URLSearchParams({ page });
        if (status) params.append('status', status);
        
        const response = await fetch(
            `${this.baseUrl}/my-issues?${params}`,
            { credentials: 'include' }
        );
        
        return await response.json();
    }
}

// Usage
const client = new KTUAPIClient('http://127.0.0.1:5000');
client.submitIssue('Network Issue', 'Cannot connect to WiFi', 'IT Support')
    .then(result => console.log(result));
```

---

**API Version**: 1.0  
**Last Updated**: January 2024  
**Base URL**: Configurable based on deployment

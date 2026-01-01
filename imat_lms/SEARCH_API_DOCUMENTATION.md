# 🔍 Search API Documentation

## Overview

The Search API provides comprehensive search functionality across the entire e-learning platform. It allows users to search for courses, modules, content, users, and assignments with advanced filtering and sorting capabilities.

---

## Base URL
```
/api/search/
```

---

## Features

✅ **Multi-type Search** - Search across courses, modules, content, users, and assignments
✅ **Advanced Filtering** - Filter by category, level, price, date, and more
✅ **Sorting Options** - Sort by relevance, date, rating, price
✅ **Search History** - Track user search queries
✅ **Saved Searches** - Save frequently used searches
✅ **Search Suggestions** - Auto-complete suggestions based on query
✅ **Search Analytics** - Track search performance metrics

---

## API Endpoints

### 1. Search Courses
**Endpoint:** `GET /api/search/courses/`

**Description:** Search for courses with advanced filtering

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (title, description, category) |
| category | string | No | Filter by course category |
| level | string | No | Filter by level: `beginner`, `intermediate`, `advanced` |
| min_price | float | No | Minimum course price |
| max_price | float | No | Maximum course price |
| is_trending | boolean | No | Only show trending courses |
| sort_by | string | No | Sort by: `recent` (default), `rating`, `price_low`, `price_high` |

**Example Request:**
```bash
GET /api/search/courses/?q=Python&category=programming&level=beginner&sort_by=rating
```

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "title": "Python Basics",
      "description": "Learn Python from scratch",
      "price": "99.99",
      "thumbnail": "https://...",
      "rating": 4.5,
      "category": "programming",
      "level": "beginner",
      "total_modules": 8,
      "total_lessons": 32,
      "is_trending": true,
      "is_enrolled": false
    }
  ],
  "search_time_ms": 45.32
}
```

---

### 2. Search Modules
**Endpoint:** `GET /api/search/modules/`

**Description:** Search for modules within courses

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (module title, description) |
| course_id | integer | No | Filter by specific course ID |
| sort_by | string | No | Sort by: `order` (default), `recent` |

**Example Request:**
```bash
GET /api/search/modules/?q=variables&course_id=1
```

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "title": "Variables and Data Types",
      "description": "Understanding variables in Python",
      "course_id": 1,
      "course_title": "Python Basics",
      "order": 1,
      "content_count": 4,
      "created_at": "2025-12-20T10:30:00Z"
    }
  ],
  "search_time_ms": 23.15
}
```

---

### 3. Search Content
**Endpoint:** `GET /api/search/content/`

**Description:** Search for course content (videos, quizzes, documents)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (content title, description) |
| content_type | string | No | Filter by type: `video`, `quiz`, `document`, `text` |
| course_id | integer | No | Filter by course ID |
| module_id | integer | No | Filter by module ID |

**Example Request:**
```bash
GET /api/search/content/?q=loops&content_type=video&course_id=1
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 5,
      "title": "For Loops",
      "description": "Understanding for loops in Python",
      "content_type": "video",
      "course_id": 1,
      "course_title": "Python Basics",
      "module_id": 2,
      "module_title": "Control Flow",
      "order": 1,
      "is_preview": false
    }
  ],
  "search_time_ms": 18.45
}
```

---

### 4. Search Users
**Endpoint:** `GET /api/search/users/`

**Description:** Search for users/instructors

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (name, email) |
| role | string | No | Filter by role: `student`, `instructor`, `admin` |

**Example Request:**
```bash
GET /api/search/users/?q=john&role=instructor
```

**Response (200 OK):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 5,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "role": "instructor",
      "profile_image": "https://..."
    }
  ],
  "search_time_ms": 12.67
}
```

---

### 5. Search Assignments
**Endpoint:** `GET /api/search/assignments/`

**Description:** Search for course assignments

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (assignment title, description) |
| course_id | integer | No | Filter by course ID |
| sort_by | string | No | Sort by: `recent` (default), `due_date` |

**Example Request:**
```bash
GET /api/search/assignments/?q=project&course_id=1&sort_by=due_date
```

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "title": "Final Project",
      "description": "Build a Python application",
      "course_id": 1,
      "course_title": "Python Basics",
      "due_date": "2025-12-31T23:59:59Z",
      "max_score": 100,
      "created_at": "2025-12-20T10:30:00Z"
    }
  ],
  "search_time_ms": 15.23
}
```

---

### 6. Comprehensive Search (All)
**Endpoint:** `GET /api/search/all/`

**Description:** Search across all entities at once

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |
| types | string | No | Comma-separated list of types: `courses,modules,content,users,assignments` (default: all) |

**Example Request:**
```bash
GET /api/search/all/?q=python&types=courses,modules,content
```

**Response (200 OK):**
```json
{
  "courses": [...],
  "modules": [...],
  "content": [...],
  "users": [],
  "assignments": [],
  "total_results": 8,
  "search_time_ms": 67.45
}
```

---

### 7. Search Suggestions (Authenticated)
**Endpoint:** `GET /api/search/suggestions/`

**Description:** Get auto-complete suggestions based on partial query

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Partial search query (minimum 2 characters) |

**Example Request:**
```bash
GET /api/search/suggestions/?q=py
```

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "suggestion": "Python Programming",
      "type": "course",
      "relevance_score": 0.95
    },
    {
      "suggestion": "Python Basics",
      "type": "course",
      "relevance_score": 0.92
    },
    {
      "suggestion": "PyTest Framework",
      "type": "module",
      "relevance_score": 0.88
    }
  ]
}
```

---

### 8. Search History (Authenticated)
**Endpoint:** `GET /api/search/history/`

**Description:** Get user's search history

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Number of results to return (default: 10) |

**Example Request:**
```bash
GET /api/search/history/?limit=20
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "query": "Python",
    "search_type": "courses",
    "results_count": 5,
    "created_at": "2025-12-22T14:30:00Z"
  },
  {
    "id": 2,
    "query": "variables",
    "search_type": "content",
    "results_count": 12,
    "created_at": "2025-12-22T14:20:00Z"
  }
]
```

---

### 9. Clear Search History (Authenticated)
**Endpoint:** `DELETE /api/search/clear-history/`

**Description:** Clear all search history for the authenticated user

**Example Request:**
```bash
DELETE /api/search/clear-history/
```

**Response (200 OK):**
```json
{
  "message": "Search history cleared successfully"
}
```

---

## Saved Searches (Authenticated)

### 10. List Saved Searches
**Endpoint:** `GET /api/search/saved/`

**Description:** Get all saved searches for the authenticated user

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "My Python Courses",
    "query": "Python",
    "search_type": "courses",
    "filters": {
      "level": "beginner",
      "sort_by": "rating"
    },
    "created_at": "2025-12-20T10:30:00Z",
    "updated_at": "2025-12-20T10:30:00Z"
  }
]
```

---

### 11. Create Saved Search
**Endpoint:** `POST /api/search/saved/`

**Description:** Create a new saved search

**Request Body:**
```json
{
  "name": "My Advanced Python Courses",
  "query": "Python",
  "search_type": "courses",
  "filters": {
    "level": "advanced",
    "sort_by": "rating",
    "min_price": 50
  }
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "My Advanced Python Courses",
  "query": "Python",
  "search_type": "courses",
  "filters": {
    "level": "advanced",
    "sort_by": "rating",
    "min_price": 50
  },
  "created_at": "2025-12-23T10:30:00Z",
  "updated_at": "2025-12-23T10:30:00Z"
}
```

---

### 12. Update Saved Search
**Endpoint:** `PUT /api/search/saved/{id}/`

**Description:** Update a saved search

**Request Body:**
```json
{
  "name": "My Favorite Advanced Python Courses",
  "query": "Python Programming",
  "search_type": "courses",
  "filters": {
    "level": "advanced",
    "sort_by": "rating",
    "min_price": 75
  }
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "My Favorite Advanced Python Courses",
  "query": "Python Programming",
  "search_type": "courses",
  "filters": {
    "level": "advanced",
    "sort_by": "rating",
    "min_price": 75
  },
  "created_at": "2025-12-23T10:30:00Z",
  "updated_at": "2025-12-23T11:15:00Z"
}
```

---

### 13. Delete Saved Search
**Endpoint:** `DELETE /api/search/saved/{id}/`

**Description:** Delete a saved search

**Response (204 No Content):**
```
(Empty response)
```

---

### 14. Execute Saved Search
**Endpoint:** `POST /api/search/saved/{id}/execute/`

**Description:** Execute a saved search and get the parameters

**Response (200 OK):**
```json
{
  "search_type": "courses",
  "query": "Python",
  "filters": {
    "level": "beginner",
    "sort_by": "rating"
  },
  "message": "Use these parameters to execute the search via the appropriate endpoint"
}
```

---

### 15. Get Saved Searches by Type
**Endpoint:** `GET /api/search/saved/by_type/?type=courses`

**Description:** Get saved searches filtered by search type

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Yes | Search type: `courses`, `modules`, `content`, `users`, `assignments`, `all` |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "My Python Courses",
    "query": "Python",
    "search_type": "courses",
    "filters": {...},
    "created_at": "2025-12-20T10:30:00Z",
    "updated_at": "2025-12-20T10:30:00Z"
  }
]
```

---

## Authentication

- **Public Endpoints**: `courses`, `modules`, `content`, `users`, `assignments`, `all`
- **Authenticated Endpoints**: `suggestions`, `history`, `clear-history`, `saved/*`

Include JWT token in Authorization header for authenticated endpoints:
```
Authorization: Bearer <your_jwt_token>
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Search query is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Common Use Cases

### 1. Search for beginner Python courses
```bash
GET /api/search/courses/?q=Python&level=beginner&sort_by=rating
```

### 2. Find all videos about loops
```bash
GET /api/search/content/?q=loops&content_type=video
```

### 3. Search for an instructor named John
```bash
GET /api/search/users/?q=John&role=instructor
```

### 4. Find assignments due soon
```bash
GET /api/search/assignments/?q=assignment&sort_by=due_date
```

### 5. Comprehensive search across platform
```bash
GET /api/search/all/?q=python&types=courses,modules
```

### 6. Get search suggestions while typing
```bash
GET /api/search/suggestions/?q=pyt
```

### 7. Save a frequently used search
```bash
POST /api/search/saved/
{
  "name": "Trending Programming Courses",
  "query": "programming",
  "search_type": "courses",
  "filters": {
    "is_trending": true,
    "sort_by": "rating"
  }
}
```

---

## Performance

- **Search queries are indexed** for faster retrieval
- **Search history is tracked** for analytics
- **Paginated results** for large result sets
- **Response time included** in all search responses (in milliseconds)
- **Caching** recommendations for frequently searched terms

---

## Database Models

### SearchQuery
Stores all search queries made by users for analytics and insights.

**Fields:**
- `user` - ForeignKey to User (nullable for anonymous searches)
- `query` - CharField(255) - The search term
- `search_type` - CharField - Type of search (all, courses, modules, content, users, assignments)
- `results_count` - IntegerField - Number of results returned
- `created_at` - DateTimeField - When the search was performed

**Indexes:**
- `(user, -created_at)`
- `(-created_at)`
- `(query)`

### SavedSearch
Allows users to save and reuse frequently used searches.

**Fields:**
- `user` - ForeignKey to User
- `name` - CharField(100) - User-friendly name for the saved search
- `query` - CharField(255) - The search query
- `search_type` - CharField - Type of search
- `filters` - JSONField - Dynamic filters for the search
- `created_at` - DateTimeField - When created
- `updated_at` - DateTimeField - When last updated

**Unique Constraint:** `(user, name)`

---

## Admin Interface

Both models have admin interfaces for management:
- **Search Queries** - View search analytics
- **Saved Searches** - Manage user saved searches

---

## Future Enhancements

- [ ] Full-text search with elasticsearch integration
- [ ] Search personalization based on user history
- [ ] Trending searches analytics
- [ ] Search filters autocomplete
- [ ] Advanced query syntax support
- [ ] Search result caching
- [ ] Real-time search suggestions
- [ ] Machine learning based search ranking

---

## Support

For issues or questions about the search API, please contact the development team.

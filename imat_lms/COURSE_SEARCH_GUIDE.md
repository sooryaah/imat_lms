# 🔍 Course Search & Discovery System

**Last Updated**: December 23, 2025

## Summary

A comprehensive course search and discovery system has been added to the IMAT LMS API, allowing users to find courses through multiple discovery paths similar to the mobile app UI shown in the design mockups.

---

## What's New ✨

### 1. **Enhanced Course Listing with Advanced Filters**
- Search by title, description, eligibility, and category
- Filter by difficulty level (beginner, intermediate, advanced)
- Filter by price range (min/max)
- Filter by minimum rating
- Filter trending courses
- Multiple sort options (price, rating, title, date)

### 2. **New Discovery Endpoints**

#### `/api/courses/search/`
Advanced search with all available filters. Best for frontend search implementations.

#### `/api/courses/categories/`
Get all available course categories with course counts. Perfect for building category grids.

#### `/api/courses/by_category/`
Browse courses grouped by category. Supports viewing all categories or drilling into a specific one.

#### `/api/courses/trending/`
Get trending/featured courses for homepage or featured section.

#### `/api/courses/recommended/`
Get AI-recommended courses based on rating and trending status.

---

## API Endpoints Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  COURSE DISCOVERY ENDPOINTS                 │
├─────────────────────────────────────────────────────────────┤
│ GET  /api/courses/                    - List with filters    │
│ GET  /api/courses/search/             - Advanced search      │
│ GET  /api/courses/categories/         - All categories       │
│ GET  /api/courses/by_category/        - Category browsing    │
│ GET  /api/courses/trending/           - Trending courses     │
│ GET  /api/courses/recommended/        - Recommended courses  │
│ POST /api/courses/                    - Create (admin)       │
│ GET  /api/courses/{id}/               - Course details       │
│ PUT  /api/courses/{id}/               - Update (admin)       │
│ DELETE /api/courses/{id}/             - Delete (admin)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### 1. Search for Courses
**Find all Python courses under $50:**
```bash
curl "http://localhost:8000/api/courses/?search=python&max_price=50&order_by=price"
```

### 2. Browse by Category
**Get all Language courses:**
```bash
curl "http://localhost:8000/api/courses/by_category/?category=Languages&limit=10"
```

### 3. Get All Categories
**Display category grid:**
```bash
curl "http://localhost:8000/api/courses/categories/"
```

### 4. Trending Courses
**Show featured courses:**
```bash
curl "http://localhost:8000/api/courses/trending/?limit=10"
```

### 5. Filter by Level and Rating
**Find top-rated beginner courses:**
```bash
curl "http://localhost:8000/api/courses/?level=beginner&min_rating=4.0&order_by=-rating"
```

---

## Mobile App Integration

### Home Screen
**Categories Grid View:**
```javascript
// Fetch all categories
GET /api/courses/categories/

Response:
{
  "categories": [
    { "category": "Languages", "count": 28 },
    { "category": "Media Production", "count": 18 },
    ...
  ]
}
```

### Category Screen
**Search within Category:**
```javascript
// User types "IELTS" in search
GET /api/courses/?category=Languages&search=IELTS

// Category filter with pagination
GET /api/courses/by_category/?category=Languages&limit=15
```

### Trending/Featured Section
```javascript
GET /api/courses/trending/?limit=20
```

### Search Results
```javascript
GET /api/courses/search/?search=photography&category=Media%20Production&order_by=-rating
```

---

## Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in title, description, eligibility, category | `search=python` |
| `category` | string | Filter by category (case-insensitive) | `category=languages` |
| `level` | string | Filter by level | `level=beginner` |
| `min_rating` | float | Minimum rating (0-5) | `min_rating=4.0` |
| `min_price` | float | Minimum price | `min_price=0` |
| `max_price` | float | Maximum price | `max_price=100` |
| `trending` | boolean | Filter trending courses | `trending=true` |
| `order_by` | string | Sort field | `order_by=-rating` |
| `page` | integer | Page number | `page=2` |
| `page_size` | integer | Items per page | `page_size=20` |

---

## Sort Options

```
title          → A-Z alphabetical
-title         → Z-A alphabetical
price          → Low to High
-price         → High to Low
rating         → Low to High rating
-rating        → High to High rating (most popular)
created_at     → Oldest first
-created_at    → Newest first (default)
```

---

## Response Format

Each course in results contains:

```json
{
  "id": 1,
  "title": "Python Basics",
  "description": "Learn Python programming...",
  "category": "Programming",
  "level": "beginner",
  "price": "49.99",
  "thumbnail": "https://example.com/thumb.jpg",
  "duration_months": 3,
  "total_lessons": 24,
  "total_modules": 6,
  "rating": 4.5,
  "is_trending": true,
  "is_enrolled": false  // Only for authenticated users
}
```

---

## Search Logic

### Case-Insensitive
All searches are case-insensitive:
- Searching "PYTHON" = "python" = "Python"

### Partial Matching
Searches support partial matches:
- `search=photo` matches "Photography", "Photoshop", etc.
- `category=lang` matches "Languages", "Language Arts", etc.

### Multi-Field Search
Search queries check multiple fields:
1. Course title
2. Course description
3. Eligibility requirements
4. Category

### AND Logic for Filters
When combining filters, they use AND logic:
- `?category=Languages&level=beginner&min_rating=4.0`
- Returns: Languages courses AND beginner level AND rated 4.0+

---

## Performance Optimizations

1. **Database Indexes** on:
   - `is_published` + `created_at` (for listing)
   - `category` (for category filters)

2. **Query Optimization**:
   - Uses `select_related()` for related objects
   - Efficient filtering at database level
   - Pagination to limit result sets

3. **Caching** (future enhancement):
   - Categories list cached
   - Trending courses cached

---

## Permissions & Access Control

### Anonymous Users
- ✅ Can view published courses
- ✅ Can search published courses
- ✅ Can browse categories
- ❌ Cannot see unpublished courses
- ❌ `is_enrolled` field always false

### Authenticated Users (Students)
- ✅ All anonymous permissions
- ✅ Can see enrolled courses
- ✅ `is_enrolled` shows their enrollment status
- ❌ Still cannot see unpublished courses

### Admin/Instructors
- ✅ Can see all courses (published + unpublished)
- ✅ All search and filter capabilities
- ✅ Can create/edit/delete courses

---

## Example Workflows

### Workflow 1: Homepage Discovery
```
1. GET /api/courses/categories/           → Display category tiles
2. GET /api/courses/trending/?limit=10    → Show featured courses
3. GET /api/courses/recommended/?limit=10 → Show recommendations
```

### Workflow 2: Category Browsing
```
1. GET /api/courses/categories/                          → Show categories
2. User clicks "Languages"
3. GET /api/courses/by_category/?category=Languages     → Show courses
4. User searches "IELTS"
5. GET /api/courses/?category=Languages&search=IELTS    → Filtered results
```

### Workflow 3: Detailed Search
```
1. User enters search: "Photography"
2. GET /api/courses/search/?search=photography           → Results
3. User filters: Level=Beginner, Rating=4.0+
4. GET /api/courses/?search=photography&level=beginner&min_rating=4.0
5. User sorts by price
6. GET /api/courses/?search=photography&level=beginner&min_rating=4.0&order_by=price
```

---

## Testing the API

### Using cURL

**1. Search for courses:**
```bash
curl -X GET "http://localhost:8000/api/courses/?search=python"
```

**2. Get categories:**
```bash
curl -X GET "http://localhost:8000/api/courses/categories/"
```

**3. Browse category:**
```bash
curl -X GET "http://localhost:8000/api/courses/by_category/?category=Languages"
```

**4. Get trending:**
```bash
curl -X GET "http://localhost:8000/api/courses/trending/"
```

### Using Postman
Import the Postman collection: `postman/IMAT_LMS_API.postman_collection.json`

Pre-built requests:
- ✅ Course Search
- ✅ Browse Categories
- ✅ Trending Courses
- ✅ Recommended Courses

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Invalid parameter",
  "details": "min_rating must be a number between 0 and 5"
}
```

### Common Errors

| Status | Cause | Fix |
|--------|-------|-----|
| 400 | Invalid filter value | Check parameter types and ranges |
| 401 | Authentication required | Provide valid token for protected endpoints |
| 404 | Course not found | Verify course ID exists |

---

## Future Enhancements

- [ ] Full-text search with relevance scoring
- [ ] Autocomplete/suggestions for search
- [ ] Filter by instructor name
- [ ] Filter by number of students
- [ ] Related/similar courses endpoint
- [ ] Search history for logged-in users
- [ ] Saved courses/wishlist
- [ ] Filter by skill tags
- [ ] Advanced filters (duration, language, etc.)

---

## Database Queries

All searches are optimized with database-level filtering:

```sql
-- Example: Find Python courses under $50, beginner level, rated 4+
SELECT * FROM courses_course
WHERE is_published = true
  AND title ILIKE '%python%'
  AND price <= 50.00
  AND level = 'beginner'
  AND rating >= 4.0
ORDER BY rating DESC, created_at DESC;
```

---

## Integration with Frontend

### React/Vue Example:
```javascript
// Search courses
async function searchCourses(query, filters) {
  const params = new URLSearchParams({
    search: query,
    ...filters
  });
  
  const response = await fetch(`/api/courses/search/?${params}`);
  return response.json();
}

// Browse category
async function getCoursesByCategory(category) {
  const response = await fetch(
    `/api/courses/by_category/?category=${category}`
  );
  return response.json();
}

// Get categories for grid
async function getCategories() {
  const response = await fetch('/api/courses/categories/');
  return response.json();
}
```

---

## Documentation Files

- **This file**: Overview and usage guide
- **README.md**: Main project documentation
- **ARCHITECTURE.md**: System design and structure

---

## Support

For issues or questions about the search API:
2. Review example requests above
3. Check Postman collection for pre-built requests
4. Verify course data is created with categories

---

**API Version**: 1.0  
**Last Updated**: December 23, 2025  
**Status**: ✅ Production Ready

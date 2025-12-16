# AFKPI Frontend - Replit AI Build Instructions

## Overview

Build a dashboard frontend for the AFKPI (Weekly Manufacturing KPI) application. The backend API is already built with FastAPI. Your job is to create the UI.

## Design Requirements

### Color Scheme (JTEC Brand)
- **Primary Orange**: `#FF6600`
- **Primary Black**: `#1a1a1a`
- **Background**: `#f5f5f5` (light gray)
- **Card Background**: `#ffffff`
- **Success Green**: `#28a745`
- **Warning Red**: `#dc3545`
- **Muted Text**: `#6c757d`

### Typography
- Font Family: `'Segoe UI', system-ui, -apple-system, sans-serif`
- Headings: Bold, dark gray `#1a1a1a`
- Body: Regular, `#333333`

### Layout
- Responsive (desktop-first, mobile-friendly)
- Sidebar navigation (collapsible on mobile)
- Header with logo, week selector, user menu
- Main content area with KPI cards and charts

## Pages to Build

### 1. Login Page (`/login`)
- Email and password form
- "AFKPI" title with JTEC orange accent
- Submit button (orange background, white text)
- Call `POST /api/auth/login` with `{email, password}`
- Store JWT token in localStorage
- Redirect to Dashboard on success

### 2. Dashboard (`/` or `/dashboard`)
**Header:**
- Week selector dropdown (call `GET /api/weeks`)
- Export button (Excel/PDF)
- User menu (name, logout)

**KPI Cards Row (3 cards):**
| Card | Data Source | Display |
|------|-------------|---------|
| Revenue Out | `/api/revenue` → `total_outbound` | Dollar format, vs last week % |
| Gross Margin | `/api/margin` → `overall_margin_percent` | Percentage, color-coded vs target |
| Labor Cost | `/api/labor` → `total_labor_cost` | Dollar format, job count |

**Charts:**
1. **Revenue by Product Group** - Horizontal bar chart
   - Data: `/api/revenue` → `by_product`
   - Group by `product_group`, show revenue bars
   - Orange bars for outbound, lighter orange for inbound

2. **Margin Trend** - Line chart
   - Data: `/api/margin/trend?weeks=13`
   - X-axis: week labels
   - Y-axis: margin percent
   - Add target line (dashed) at 30%

3. **Top Jobs by Cost** - Table
   - Data: `/api/labor` → `by_job` (top 10)
   - Columns: Job#, SO#, Labor, Burden, Total

### 3. Revenue Page (`/revenue`)
- Week selector
- Summary cards (Inbound, Outbound, Total)
- Revenue by Product Group table with drill-down links
- Revenue trend chart (13 weeks)

### 4. Margin Page (`/margin`)
- Week selector
- Summary cards (Revenue, Cost, Margin, Margin %)
- Margin by Product Group table
  - Columns: Group, Revenue, Cost, Margin, Margin%, Target, Variance
  - Color variance: green if positive, red if negative
- Click product group → drill to `/margin/{group}`

### 5. Margin Drill-Down (`/margin/:productGroup`)
- Back button
- Product group header
- Categories table with margins
- Click category → show jobs in that category

### 6. Labor Page (`/labor`)
- Week selector
- Summary cards (Direct Labor, Burden, Total, Job Count)
- Jobs table (sortable by cost)
- Click job → show job detail modal

### 7. Job Detail Modal/Page
- Job number, Sales Order, Part Number
- Cost breakdown: Labor, Burden, Material, Total
- Product Group, Category
- Back button

## API Integration

### Authentication
```javascript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token } = await response.json();
localStorage.setItem('token', access_token);

// Authenticated requests
const response = await fetch('/api/revenue', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});
```

### Key Endpoints
```javascript
GET /api/weeks                    // Week dropdown options
GET /api/revenue?week_id=5        // Revenue for specific week
GET /api/margin?week_id=5         // Margin for specific week
GET /api/margin/trend?weeks=13    // Margin trend
GET /api/labor?week_id=5          // Labor summary
GET /api/drill/product/{group}    // Category breakdown
GET /api/drill/job/{job_num}      // Job detail
```

## Chart Library

Use **Plotly.js** for charts:
```html
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
```

Example bar chart:
```javascript
Plotly.newPlot('revenue-chart', [{
  x: data.map(d => d.revenue),
  y: data.map(d => d.product_group),
  type: 'bar',
  orientation: 'h',
  marker: { color: '#FF6600' }
}], {
  title: 'Revenue by Product Group',
  margin: { l: 150 }
});
```

## Data Formatting

```javascript
// Currency
const formatCurrency = (val) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

// Percentage
const formatPercent = (val) => `${val.toFixed(1)}%`;

// Week label
const formatWeek = (year, week) => `${year}-W${week.toString().padStart(2, '0')}`;
```

## File Structure

```
templates/
├── base.html          # Base template with nav, header
├── login.html         # Login page
├── dashboard.html     # Main dashboard
├── revenue.html       # Revenue detail page
├── margin.html        # Margin detail page
├── margin_drill.html  # Margin drill-down
├── labor.html         # Labor detail page

static/
├── css/
│   └── style.css      # Custom styles
├── js/
│   ├── api.js         # API helper functions
│   ├── charts.js      # Chart rendering
│   └── app.js         # Main app logic
```

## Sample Users (for testing)

| Email | Password | Role |
|-------|----------|------|
| demo@jtec.com | demo123 | viewer |
| jesse.schroeder@jtec.com | demo123 | cfo |
| bryan.myers@jtec.com | demo123 | controller |

## Success Criteria

1. User can log in and see dashboard
2. KPI cards show current week data
3. Charts render with real data from API
4. Week selector changes all data
5. Drill-down navigation works (Group → Category → Job)
6. Export to Excel/PDF works
7. Mobile responsive (sidebar collapses)
8. Logout clears token and redirects to login

## Notes

- The backend runs on port 8000 (or Replit default)
- All API responses use JSON
- Error handling: show toast/alert on API errors
- Loading states: show spinner while fetching data

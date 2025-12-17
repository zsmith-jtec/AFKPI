# FOS Frontend - Replit AI Build Instructions

## IMPORTANT: First Steps

Before building the frontend, run these commands in the Replit Shell:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Seed the database with sample data (13 weeks of test data)
python seed_data.py

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Test it works:
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy"}
```

## Overview

Build a dashboard frontend for the FOS (Weekly Manufacturing KPI) application. The backend API is already built with FastAPI. Your job is to create the UI following the **JTEC Design System** specifications below.

---

## JTEC Design System

### Required CSS Dependencies

Include these in your base template `<head>`:

```html
<!-- Bootstrap 5.3.0 -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- Font Awesome 6.4.0 -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

<!-- Plotly.js for charts -->
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

<!-- Bootstrap JS (at end of body) -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

### CSS Variables

Add these CSS custom properties to your `style.css`:

```css
:root {
  /* Brand Colors */
  --jtec-orange: #FF6600;
  --jtec-orange-hover: #e65c00;
  --jtec-black: #1a1a1a;

  /* Neutrals */
  --white: #ffffff;
  --gray-50: #f8f9fa;
  --gray-100: #f5f5f5;
  --gray-200: #eee;
  --gray-300: #dee2e6;
  --gray-400: #ddd;
  --gray-500: #6c757d;
  --gray-600: #555;
  --gray-700: #444;
  --gray-800: #333;
  --gray-900: #1a1a1a;

  /* Status */
  --success: #4CAF50;
  --success-light: #90EE90;
  --info: #2196F3;
  --info-light: #87CEEB;
  --info-bg: #e3f2fd;
  --warning: #ffc107;
  --warning-bg: #fff3cd;
  --warning-text: #664d03;
  --danger: #f44336;

  /* Typography */
  --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.85rem;
  --font-size-md: 0.9rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.2rem;
  --font-size-xl: 1.3rem;
  --font-weight-normal: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Spacing */
  --spacing-xs: 2px;
  --spacing-sm: 4px;
  --spacing-md: 8px;
  --spacing-lg: 12px;
  --spacing-xl: 20px;

  /* Borders */
  --border-radius-sm: 3px;
  --border-radius-md: 4px;
  --border-radius-lg: 6px;
  --border-color: #dee2e6;

  /* Shadows */
  --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
  --shadow-md: 0 2px 8px rgba(0,0,0,0.1);
  --shadow-lg: 0 4px 12px rgba(0,0,0,0.3);
  --shadow-orange: 0 4px 6px rgba(255, 102, 0, 0.3);
  --shadow-orange-hover: 0 6px 12px rgba(255, 102, 0, 0.4);
  --focus-ring: 0 0 0 0.25rem rgba(255, 102, 0, 0.25);

  /* Transitions */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
}

body {
  font-family: var(--font-family);
  background-color: var(--gray-100);
  color: var(--gray-800);
}
```

### Color Palette Reference

| Name | Hex | Usage |
|------|-----|-------|
| **JTEC Orange** | `#FF6600` | Primary accent, buttons, headers, links |
| **JTEC Orange Hover** | `#e65c00` | Hover states |
| **JTEC Black** | `#1a1a1a` | Navbar, dark backgrounds |
| **White** | `#ffffff` | Card backgrounds |
| **Light Gray** | `#f5f5f5` | Page background |
| **Medium Gray** | `#6c757d` | Muted text |
| **Dark Gray** | `#333` | Body text |
| **Success Green** | `#4CAF50` | Positive variance, success states |
| **Danger Red** | `#f44336` | Negative variance, errors |

---

## Component Specifications

### Navbar

The navbar should be **dark (#1a1a1a)** with the JTEC branding pattern:

```html
<nav class="navbar navbar-dark" style="background-color: #1a1a1a; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
  <div class="container-fluid">
    <span class="navbar-brand" style="font-size: 1.3rem; font-weight: 700;">
      JTEC INDUSTRIES <span style="color: #FF6600;">|</span> FOS
    </span>
    <div class="d-flex align-items-center">
      <!-- Week selector and user menu go here -->
      <span class="text-muted" style="font-size: 0.85rem;">East Peoria, IL</span>
    </div>
  </div>
</nav>
```

**Key navbar rules:**
- Background: `#1a1a1a`
- Brand format: `JTEC INDUSTRIES | App Name` with orange `|` separator
- Font: Bold, 1.3rem
- Location text on right in muted gray
- Box shadow: `0 2px 4px rgba(0,0,0,0.1)`

### Footer

```html
<footer style="text-align: center; padding: 20px; margin-top: 30px; color: #6c757d; font-size: 0.85rem;">
  2025 Jtec Industries <span style="color: #FF6600;">|</span> East Peoria, IL
</footer>
```

### Buttons

**Primary Button (Orange):**
```css
.btn-jtec-primary {
  background-color: #FF6600;
  border-color: #FF6600;
  color: white;
  font-weight: 600;
  padding: 12px 20px;
  transition: all 0.3s ease;
}

.btn-jtec-primary:hover {
  background-color: #e65c00;
  border-color: #e65c00;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(255, 102, 0, 0.3);
}
```

**Secondary Button (Black):**
```css
.btn-jtec-secondary {
  background-color: #1a1a1a;
  border-color: #1a1a1a;
  color: white;
  font-weight: 600;
}

.btn-jtec-secondary:hover {
  background-color: #FF6600;
  border-color: #FF6600;
}
```

### Cards

```css
.card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border: none;
  border-radius: 0;
}

.card-header {
  font-weight: 600;
}

/* Orange header variant */
.card-header-orange {
  background-color: #FF6600;
  color: white;
}

/* Black header variant */
.card-header-dark {
  background-color: #1a1a1a;
  color: white;
}
```

### Forms

```css
.form-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.form-control {
  border: 2px solid #dee2e6;
  transition: border-color 0.2s;
}

.form-control:focus {
  border-color: #FF6600;
  box-shadow: 0 0 0 0.25rem rgba(255, 102, 0, 0.25);
}

.form-check-input:checked {
  background-color: #FF6600;
  border-color: #FF6600;
}
```

### KPI Cards

For the dashboard KPI summary cards:

```css
.kpi-card {
  background: white;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 3px solid #FF6600;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a1a;
}

.kpi-label {
  font-size: 0.85rem;
  color: #6c757d;
  text-transform: uppercase;
}

.kpi-change-positive {
  color: #4CAF50;
}

.kpi-change-negative {
  color: #f44336;
}
```

### Tables

```css
.table thead th {
  background-color: #1a1a1a;
  color: white;
  font-weight: 600;
  border: none;
}

.table tbody tr:hover {
  background-color: #f8f9fa;
}

/* Variance coloring */
.variance-positive {
  color: #4CAF50;
  font-weight: 600;
}

.variance-negative {
  color: #f44336;
  font-weight: 600;
}
```

### Links

```css
a {
  color: #FF6600;
}

a:hover {
  color: #e65c00;
}
```

---

## Layout

### Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FOS - Weekly KPI Dashboard</title>
  <!-- CSS dependencies here -->
</head>
<body style="background-color: #f5f5f5;">
  <!-- Navbar -->
  <nav class="navbar navbar-dark" style="background-color: #1a1a1a;">
    ...
  </nav>

  <!-- Sidebar + Main Content -->
  <div class="container-fluid">
    <div class="row">
      <!-- Sidebar (collapsible on mobile) -->
      <nav class="col-md-2 d-md-block bg-white sidebar" style="min-height: calc(100vh - 56px);">
        ...
      </nav>

      <!-- Main content -->
      <main class="col-md-10 ms-sm-auto px-4 py-3">
        ...
      </main>
    </div>
  </div>

  <!-- Footer -->
  <footer>...</footer>

  <!-- JS dependencies -->
</body>
</html>
```

### Sidebar Navigation

```css
.sidebar {
  box-shadow: 2px 0 4px rgba(0,0,0,0.1);
}

.sidebar .nav-link {
  color: #333;
  padding: 12px 20px;
  border-left: 3px solid transparent;
}

.sidebar .nav-link:hover {
  background-color: #f8f9fa;
  border-left-color: #FF6600;
}

.sidebar .nav-link.active {
  background-color: #fff3e0;
  border-left-color: #FF6600;
  color: #FF6600;
  font-weight: 600;
}
```

---

## Pages to Build

### 1. Login Page (`/login`)
- Centered card on light gray background
- "FOS" title with JTEC orange accent
- Email and password form fields
- Orange submit button
- Call `POST /api/auth/login` with `{email, password}`
- Store JWT token in localStorage
- Redirect to Dashboard on success

### 2. Dashboard (`/` or `/dashboard`)

**Header Section:**
- Week selector dropdown (call `GET /api/weeks`)
- Export button (Excel/PDF)
- User menu (name, logout)

**KPI Cards Row (3 cards):**
| Card | Data Source | Display |
|------|-------------|---------|
| Revenue Out | `/api/revenue` -> `total_outbound` | Dollar format, vs last week % |
| Gross Margin | `/api/margin` -> `overall_margin_percent` | Percentage, color-coded vs target |
| Labor Cost | `/api/labor` -> `total_labor_cost` | Dollar format, job count |

**Charts:**
1. **Revenue by Product Group** - Horizontal bar chart
   - Data: `/api/revenue` -> `by_product`
   - Orange bars (`#FF6600`) for outbound

2. **Margin Trend** - Line chart
   - Data: `/api/margin/trend?weeks=13`
   - Orange line for actual, dashed gray for target (30%)

3. **Top Jobs by Cost** - Table
   - Data: `/api/labor` -> `by_job` (top 10)
   - Dark header, hover rows

### 3. Revenue Page (`/revenue`)
- Week selector
- Summary cards (Inbound, Outbound, Total) with orange left border
- Revenue by Product Group table with drill-down links
- Revenue trend chart (13 weeks)

### 4. Margin Page (`/margin`)
- Week selector
- Summary cards (Revenue, Cost, Margin, Margin %)
- Margin by Product Group table
  - Columns: Group, Revenue, Cost, Margin, Margin%, Target, Variance
  - Variance: green (`#4CAF50`) if positive, red (`#f44336`) if negative
- Click product group -> drill to `/margin/{group}`

### 5. Margin Drill-Down (`/margin/:productGroup`)
- Back button (orange outline)
- Product group header with orange underline
- Categories table with margins
- Click category -> show jobs in that category

### 6. Labor Page (`/labor`)
- Week selector
- Summary cards (Direct Labor, Burden, Total, Job Count)
- Jobs table (sortable by cost, dark header)
- Click job -> show job detail modal

### 7. Job Detail Modal/Page
- Job number, Sales Order, Part Number
- Cost breakdown: Labor, Burden, Material, Total
- Product Group, Category
- Back/Close button

---

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

---

## Chart Configuration

Use **Plotly.js** with JTEC brand colors:

```javascript
// Bar chart example
Plotly.newPlot('revenue-chart', [{
  x: data.map(d => d.revenue),
  y: data.map(d => d.product_group),
  type: 'bar',
  orientation: 'h',
  marker: { color: '#FF6600' }
}], {
  title: { text: 'Revenue by Product Group', font: { family: 'Segoe UI', size: 16 } },
  margin: { l: 150 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)'
});

// Line chart example
Plotly.newPlot('trend-chart', [
  {
    x: data.map(d => d.label),
    y: data.map(d => d.margin_percent),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Actual',
    line: { color: '#FF6600', width: 3 },
    marker: { size: 8 }
  },
  {
    x: data.map(d => d.label),
    y: data.map(() => 30),
    type: 'scatter',
    mode: 'lines',
    name: 'Target',
    line: { color: '#6c757d', dash: 'dash', width: 2 }
  }
], {
  title: { text: 'Margin Trend', font: { family: 'Segoe UI' } },
  showlegend: true
});
```

---

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

---

## File Structure

```
templates/
├── base.html          # Base template with nav, sidebar, footer
├── login.html         # Login page
├── dashboard.html     # Main dashboard
├── revenue.html       # Revenue detail page
├── margin.html        # Margin detail page
├── margin_drill.html  # Margin drill-down
├── labor.html         # Labor detail page

static/
├── css/
│   └── style.css      # JTEC Design System styles
├── js/
│   ├── api.js         # API helper functions
│   ├── charts.js      # Chart rendering with Plotly
│   └── app.js         # Main app logic
```

---

## Sample Users (for testing)

| Email | Password | Role |
|-------|----------|------|
| demo@jtec.com | demo123 | viewer |
| jesse.schroeder@jtec.com | demo123 | cfo |
| bryan.myers@jtec.com | demo123 | controller |

---

## Success Criteria

1. User can log in and see dashboard
2. UI matches JTEC Design System (orange/black branding, correct fonts)
3. Navbar shows "JTEC INDUSTRIES | FOS" with orange separator
4. KPI cards show current week data with orange left border
5. Charts render with orange brand color
6. Tables have dark headers, variance coloring works
7. Week selector changes all data
8. Drill-down navigation works (Group -> Category -> Job)
9. Footer shows "2025 Jtec Industries | East Peoria, IL"
10. Mobile responsive (sidebar collapses)
11. Logout clears token and redirects to login

---

## Notes

- The backend runs on port 8000 (or Replit default)
- All API responses use JSON
- Error handling: show toast/alert on API errors (use Bootstrap alerts)
- Loading states: show spinner while fetching data
- All interactive elements should have subtle transitions (0.2s-0.3s)

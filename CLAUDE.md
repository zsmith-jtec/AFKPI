# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AFKPI** (Weekly Manufacturing KPI Application) - A planned internal web application for tracking key performance metrics across Finance, Sales, and Operations departments at a manufacturing company using Epicor ERP.

## Project Status

**Pre-development** - Planning phase. See `boss-questions.md` for outstanding decisions needed before implementation.

## Planned Architecture

```
Technology Stack (proposed):
- Backend: Python FastAPI
- Database: PostgreSQL or SQLite
- Frontend: React or Jinja templates
- Hosting: Replit (internal web app only)
- Data Source: Epicor ERP via weekly BAQ exports (CSV/Excel)
```

## Key Metrics to Track

| Metric | Departments | Drill-down |
|--------|-------------|------------|
| Inbound Revenue | Sales, Finance | Product Group → Category |
| Outbound Revenue | Sales, Finance | Product Group → Category |
| Direct Labor + Burden Hours | Operations, Finance | Job → Operation |
| Gross Margin | Finance | Product Group → Category → Job |
| Projected Revenue | Sales, Finance | Weekly |
| Projected Gross Margin | Finance | Product Group → Category |

## Data Model (Planned)

Core tables:
- `dim_product` - Product Group/Category mapping
- `dim_time_week` - ISO week dimension
- `dim_job` - Job/Sales Order linking
- `fact_revenue` - Weekly revenue by product/direction
- `fact_costs` - Weekly labor/burden/material costs by job

## Epicor Integration

Data sourced from Epicor BAQs:
- `OrderHed`, `OrderDtl` - Revenue (inbound/outbound)
- `JobHead`, `JobOper`, `LaborDtl` - Labor/burden hours
- `JobMtl` - Material costs
- `Part` - Product Group/Category mapping
- `ResourceGroup` - Labor/burden rates

## Development Notes

- Weekly batch updates (not real-time)
- Forecasting via ARIMA time-series models (statsmodels)
- Role-based views per department
- Finance must sign off on gross margin calculation logic
- Validate against manual Excel for 4 weeks before go-live

## Related Documents

- `Document4.docx` - Original Copilot planning conversation
- `boss-questions.md` - Outstanding questions and recommendations

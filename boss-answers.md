# Boss Answers - December 15, 2025

## Critical Questions

### 1. Budget & Resources
- **Budget**: $500
- **Who builds**: Internal Developer
- **Timeline**: 1 month for initial review

### 2. Why Custom vs. Commercial?
- **Power BI**: Not dismissed - author doesn't know enough about it to evaluate
- **Epicor native**: Evaluated - no out-of-box solution exists
- **Custom build**: Will be built in Replit or other AI platforms

### 3. Data Readiness
- **BAQs exist**: ~60% already developed
- **BAQ owners**: Adam Massens or Peter Hansen
- **Labor/burden rates**: Current (2025 DMT flush completed)

### 4. Calculation Definitions
- **Gross Margin**: Finance owns Corp. Mapping document for GM at Product Group/Category level
- **SEGMD app**: Handles tiered gross margin by quantity:
  - Target GM at specific quantity
  - Lower qty = slightly higher GM (buffer for overruns/unknowns)
  - Higher qty = progressive GM discount (volume incentive)
- **Finance sign-off**: Yes, Finance has authority
- **WIP/Partial shipments**:
  - Revenue/expense recognized at shipment
  - Epicor handles partial shipment splits correctly
  - WIP tracking NOT needed in this app

### 5. User Adoption
**Weekly Users**:
| Name | Role |
|------|------|
| Jesse Schroeder | CFO |
| Bryan Myers | Controller |
| Aaron Forinash | COO |
| Andrew Webb | Director of Operations |
| Zach Smith | Director of Autonomous Products |
| Dan Gannaway | Director of Sales |
| Mike Chasteen | Production Manager |
| Adam Massens | Lead Developer |
| Peter Hansen | Estimator |
| Jacob Myers | Inside Sales Specialist |

**Decisions enabled**: Date range sorting, data validation by SME role, KPI tracking, report exports

**Current state**: Multiple APIs for revenue/backlog, labor loading from resource group, job-specific data from Epicor reports

### 6. Success Criteria
- **Success**: Clear visuals showing revenue vs target, GM vs goal, labor vs forecast
- **ROI**: Consolidated good data enabling better business decisions
- **Phase 1 deadline**: 1 month

---

## Important Questions

### 7. Scope Concerns
- **V1 scope**: Yes - forecasting, alerts, drill-downs, role-based views all in V1
- **Start Finance-only**: Yes, if needed

### 8. Security & Compliance
- **IT review**: Not required
- **Access**: Officers, controller, directors only
- **Audit trails**: Yes, required

### 9. Technical Environment
- **Outgrow Replit**: Will migrate to platform that supports needs
- **Python/FastAPI expertise**: Yes, in-house
- **Data storage**: On-prem servers

### 10. Maintenance
- **Maintainer**: JTEC internal development team
- **Epicor changes**: Per user agreement, advanced notice required
- **Support plan**: Officers, directors, controller, and internal dev team

---

## Attachments Referenced
- `SEGMD - Gross Margin Target and Quantity Display Example.png` - Shows tiered GM curves by product category
- `Jtec Target Gross Margin.xlsx` - Target GM percentages by product (20%-40% range)

# FOS Project Plan

## Project Summary

| Item | Value |
|------|-------|
| **Project** | FOS - Weekly Manufacturing KPI Dashboard |
| **Budget** | $500 |
| **Timeline** | 1 month (working prototype) |
| **Developer** | Internal (Zach Smith) |
| **Platform** | Replit (FastAPI + SQLite) |
| **Users** | 10 stakeholders (Finance, Ops, Sales) |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FOS SYSTEM                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     Weekly CSV      ┌──────────────┐      ┌─────────────────┐
│              │     Export          │              │      │                 │
│  EPICOR ERP  │ ─────────────────▶  │  ON-PREM     │ ───▶ │  REPLIT APP     │
│              │                     │  SERVER      │      │                 │
│  - Orders    │     BAQ Exports:    │              │      │  FastAPI +      │
│  - Jobs      │     - Revenue       │  CSV/Excel   │      │  SQLite +       │
│  - Labor     │     - Labor         │  Files       │      │  Jinja UI       │
│  - Parts     │     - Jobs          │              │      │                 │
└──────────────┘     - Costs         └──────────────┘      └────────┬────────┘
                                                                    │
                                                                    ▼
                                                           ┌─────────────────┐
                                                           │  DASHBOARD UI   │
                                                           │                 │
                                                           │  - KPI Cards    │
                                                           │  - Charts       │
                                                           │  - Drill-down   │
                                                           │  - Exports      │
                                                           └─────────────────┘
                                                                    │
                                                                    ▼
                                                           ┌─────────────────┐
                                                           │  10 USERS       │
                                                           │                 │
                                                           │  CFO, COO,      │
                                                           │  Controller,    │
                                                           │  Directors      │
                                                           └─────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEEKLY DATA FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    MONDAY MORNING (Automated)
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    │   1. BAQ EXPORTS RUN                                                │
    │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
    │   │ Revenue BAQ  │  │ Labor BAQ    │  │ Jobs BAQ     │              │
    │   │              │  │              │  │              │              │
    │   │ OrderHed     │  │ LaborDtl     │  │ JobHead      │              │
    │   │ OrderDtl     │  │ JobOper      │  │ JobMtl       │              │
    │   │ ShipDtl      │  │ ResourceGrp  │  │ Part         │              │
    │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
    │          │                 │                 │                      │
    │          ▼                 ▼                 ▼                      │
    │   2. CSV FILES SAVED TO ON-PREM SERVER                              │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │  \\server\kpi\weekly\2025-W51\                              │   │
    │   │    ├── revenue_inbound.csv                                  │   │
    │   │    ├── revenue_outbound.csv                                 │   │
    │   │    ├── labor_hours.csv                                      │   │
    │   │    └── job_costs.csv                                        │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    │          │                                                          │
    │          ▼                                                          │
    │   3. ETL PROCESS (Replit cron or manual trigger)                    │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │  - Read CSV files                                           │   │
    │   │  - Validate & transform                                     │   │
    │   │  - Map Product Group → Category                             │   │
    │   │  - Calculate Gross Margin                                   │   │
    │   │  - Load to SQLite                                           │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    │          │                                                          │
    │          ▼                                                          │
    │   4. DASHBOARD AVAILABLE                                            │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │  Users see updated KPIs for prior week                      │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   dim_week       │       │   dim_product    │       │   dim_job        │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ week_id (PK)     │       │ product_id (PK)  │       │ job_id (PK)      │
│ week_start       │       │ product_line     │       │ job_num          │
│ week_end         │       │ product_group    │       │ sales_order_num  │
│ iso_year         │       │ category         │       │ part_num         │
│ iso_week         │       │ target_margin    │       │ product_id (FK)  │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         │         ┌────────────────┴────────────────┐         │
         │         │                                 │         │
         ▼         ▼                                 ▼         ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│     fact_revenue        │               │     fact_costs          │
├─────────────────────────┤               ├─────────────────────────┤
│ fact_id (PK)            │               │ fact_id (PK)            │
│ week_id (FK)            │               │ week_id (FK)            │
│ product_id (FK)         │               │ job_id (FK)             │
│ direction (In/Out)      │               │ direct_labor            │
│ revenue                 │               │ burden                  │
│ order_count             │               │ material_cost           │
└─────────────────────────┘               │ total_cost              │
                                          └─────────────────────────┘

┌─────────────────────────┐
│   audit_log             │
├─────────────────────────┤
│ log_id (PK)             │
│ timestamp               │
│ user                    │
│ action                  │
│ details                 │
└─────────────────────────┘
```

---

## User Interface Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FOS Dashboard                                      [Week: 2025-W51 ▼] [Export]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ REVENUE OUT     │  │ GROSS MARGIN    │  │ LABOR HOURS     │              │
│  │                 │  │                 │  │                 │              │
│  │   $1.2M         │  │   28.5%         │  │   4,200 hrs     │              │
│  │   ▲ +5% vs LW   │  │   ▼ -1.2% vs LW │  │   ▲ +3% vs LW   │              │
│  │   Target: $1.1M │  │   Target: 30%   │  │   Target: 4,000 │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  REVENUE BY PRODUCT GROUP                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │     $400K │████████████████████                   CarryMore         │    │
│  │     $350K │█████████████████                      CarryMatic        │    │
│  │     $250K │████████████                           CarryMax          │    │
│  │     $200K │██████████                             Warehouse         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  GROSS MARGIN TREND (13 Weeks)                     [Actual ── Target ···]  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  32% │                                                              │    │
│  │      │          ·····················································│    │
│  │  30% │      ╱╲      ╱╲                                              │    │
│  │      │     ╱  ╲    ╱  ╲    ╱╲                                       │    │
│  │  28% │────╱────╲──╱────╲──╱──╲──────────────────────────────────────│    │
│  │      │  W39  W41  W43  W45  W47  W49  W51                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  DRILL-DOWN: CarryMore > Custom Cart > Job J12345                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Job: J12345  |  SO: 45678  |  Revenue: $45,000  |  Margin: 31.2%   │    │
│  │  Labor: 120 hrs @ $45/hr = $5,400                                   │    │
│  │  Burden: 120 hrs @ $28/hr = $3,360                                  │    │
│  │  Material: $22,000                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Gross Margin Model (From Corp. Mapping)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TARGET GROSS MARGIN BY PRODUCT                          │
└─────────────────────────────────────────────────────────────────────────────┘

Product Line    Product Group              Category                  Target GM
─────────────────────────────────────────────────────────────────────────────
IPS             CarryLite                  All Categories            25%
IPS             CarryMax                   All Categories            25%
IPS             CarryMore                  Standard Carts            30%
IPS             CarryMore                  Mother Cart Powered       35%
IPS             CarryMore                  Mother Cart Non-Powered   35%
APS             CarryMatic                 Controls                  36.5%
APS             CarryMatic                 Bots (Lift, Move, etc)    35%
APS             CarryMatic                 Stations, P&D, Service    25%
APS             CarryMatic                 TugBot                    20%
IPS             General                    Casters                   33%
WPS             Warehouse Manufactured     Conveyors, Cranes         22%
WPS             Warehouse Manufactured     Docking Targets           25%
─────────────────────────────────────────────────────────────────────────────

                      TIERED MARGIN BY QUANTITY (SEGMD)

    Margin %
    38% │●
        │  ●
    34% │    ●───●───●
        │              ●───●───●
    30% │                        ●───●
        │
    26% │
        └────┬────┬────┬────┬────┬────┬────▶ Quantity
             1    2    6   11   26   51   75

    - Qty 1-2:    Prototype margin (higher buffer)
    - Target Qty: Base margin per Corp. Mapping
    - Qty > Target: Progressive volume discount
```

---

## 4-Week Implementation Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEEK 1: FOUNDATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────┬─────────────────────────────────────┐
│ DATA DISCOVERY                        │ PROJECT SETUP                       │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ [ ] Inventory BAQs with Adam/Peter    │ [ ] Create Replit project           │
│ [ ] Identify missing 40% BAQs         │ [ ] Set up FastAPI skeleton         │
│ [ ] Map Epicor tables to metrics      │ [ ] Create SQLite schema            │
│ [ ] Get sample exports (4 weeks)      │ [ ] Set up JWT auth structure       │
└───────────────────────────────────────┴─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEEK 2: DATA PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────┬─────────────────────────────────────┐
│ ETL DEVELOPMENT                       │ VALIDATION                          │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ [ ] Build CSV ingest scripts          │ [ ] Load 4-8 weeks historical       │
│ [ ] Map Product Group/Category        │ [ ] Compare to existing Excel       │
│ [ ] Calculate GM per Corp. Mapping    │ [ ] Fix any discrepancies           │
│ [ ] Aggregate by week                 │ [ ] Finance sign-off on calcs       │
└───────────────────────────────────────┴─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEEK 3: DASHBOARD                                    │
└─────────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────┬─────────────────────────────────────┐
│ UI DEVELOPMENT                        │ FEATURES                            │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ [ ] KPI cards (Revenue, GM, Labor)    │ [ ] Week selector                   │
│ [ ] Revenue by Product Group chart    │ [ ] Date range filtering            │
│ [ ] GM trend chart (13 weeks)         │ [ ] Drill-down navigation           │
│ [ ] Job detail view                   │ [ ] Export to Excel/PDF             │
└───────────────────────────────────────┴─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEEK 4: POLISH & REVIEW                              │
└─────────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────┬─────────────────────────────────────┐
│ FORECASTING & ALERTS                  │ UAT & HANDOFF                       │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ [ ] ARIMA forecast (8-week horizon)   │ [ ] User acceptance testing         │
│ [ ] Target vs actual highlighting     │ [ ] Stakeholder demo                │
│ [ ] Audit trail logging               │ [ ] Documentation                   │
│ [ ] Role-based view filtering         │ [ ] Maintenance handoff plan        │
└───────────────────────────────────────┴─────────────────────────────────────┘
```

---

## Key Metrics Definition

| Metric | Calculation | Source |
|--------|-------------|--------|
| **Inbound Revenue** | Sum of OrderDtl.DocExtPrice where Order is Open | OrderHed, OrderDtl |
| **Outbound Revenue** | Sum of ShipDtl revenue at shipment | ShipHead, ShipDtl |
| **Direct Labor Cost** | LaborDtl.LaborHrs × ResourceGroup.LaborRate | LaborDtl, ResourceGroup |
| **Burden Cost** | LaborDtl.BurdenHrs × ResourceGroup.BurdenRate | LaborDtl, ResourceGroup |
| **Material Cost** | Sum of JobMtl.ExtCost | JobMtl |
| **Gross Margin** | (Revenue - Labor - Burden - Material) / Revenue | Calculated |
| **Target GM** | From Corp. Mapping by Product Group/Category | Jtec Target Gross Margin.xlsx |

---

## BAQ Checklist

| BAQ Purpose | Exists? | Owner | Tables |
|-------------|---------|-------|--------|
| Inbound Revenue by Product | ? | Adam/Peter | OrderHed, OrderDtl, Part |
| Outbound Revenue by Product | ? | Adam/Peter | ShipHead, ShipDtl, Part |
| Labor Hours by Job | ? | Adam/Peter | LaborDtl, JobOper |
| Material Cost by Job | ? | Adam/Peter | JobMtl |
| Job to SO Linkage | ? | Adam/Peter | JobHead |
| Product Group/Category | ? | Adam/Peter | Part (ProdCode, PartClass) |

**Action**: Week 1 - Inventory with Adam Massens and Peter Hansen

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing BAQs (40%) | HIGH | Week 1: identify gaps, prioritize creation |
| GM calc mismatch | HIGH | Validate against Finance Excel weekly |
| 1-month timeline | MEDIUM | Start with Finance view, add Sales/Ops if time |
| $500 budget | LOW | Use free Replit tier, SQLite, no external services |

---

## Success Criteria

1. Dashboard shows Revenue (In/Out), GM, Labor for current + prior weeks
2. Drill-down works: Product Group → Category → Job
3. Numbers match Finance Excel validation (within 0.1%)
4. 10 stakeholders can log in and view their relevant data
5. Export to Excel works for reporting

---

## Files Reference

| File | Purpose |
|------|---------|
| `Jtec Target Gross Margin.xlsx` | Corp. Mapping - target GM by product |
| `SEGMD - Gross Margin Target and Quantity Display Example.png` | Tiered GM curves |
| `Document4.docx` | Original Copilot conversation (technical reference) |
| `boss-answers.md` | Stakeholder decisions documented |

---

## Next Steps

1. **You review this plan** - confirm approach looks correct
2. **I start Week 1** - BAQ inventory + Replit setup
3. **You coordinate with Adam/Peter** - get sample BAQ exports

Ready to proceed?

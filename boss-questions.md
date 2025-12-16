# AFKPI Project - Questions & Recommendations

**Review of**: Document4.docx (Microsoft Copilot conversation)
**Perspective**: CFO/COO of 150-employee manufacturing company
**Date**: December 15, 2025

---

## Critical Questions (Must Answer Before Proceeding)

### 1. Budget & Resources
- What is the budget for this project?
- Who will build this? Internal developer? Contractor? Copilot-assisted DIY?
- What is the expected timeline to have something usable?

### 2. Why Custom vs. Commercial?
- Why was Power BI dismissed? Cost? Limitations? Preference?
- Have we evaluated Epicor's native dashboards/analytics?
- What specific capabilities require a custom build?

### 3. Data Readiness
- Do BAQs already exist for all the required data (revenue by product group, labor by job, etc.)?
- Who owns the Epicor BAQ definitions and can modify them?
- Are the labor/burden rate tables in Epicor current (referencing the 2025 DMT flush)?

### 4. Calculation Definitions
- How exactly is "Gross Margin" calculated today? (The conversation mentions Corp. Mapping for Gross Margin document)
- Does Finance have sign-off authority on margin calculation logic?
- What handling for WIP, partial shipments, intercompany?

### 5. User Adoption
- Who specifically will use this weekly? Names/roles?
- What decisions will they make differently with this data?
- How do they currently get this information (Excel? Reports? Nothing)?

### 6. Success Criteria
- How will we know this project succeeded?
- What's the target ROI or time savings?
- What's the deadline for Phase 1?

---

## Important Questions (Answer Soon)

### 7. Scope Concerns
- The Copilot conversation includes forecasting, alerts, drill-downs, and role-based views. Is all of this V1?
- Can we start with just Finance margin view and expand later?
- What's the minimum viable product (MVP)?

### 8. Security & Compliance
- Does IT need to review Replit hosting for compliance?
- Who should have access to margin data? Is it sensitive?
- Does this need audit trails?

### 9. Technical Environment
- Replit was chosen - what happens if we outgrow it?
- Do we have Python/FastAPI expertise in-house?
- Where will the weekly data files be stored?

### 10. Maintenance
- Who maintains this after it's built?
- What happens when Epicor tables change?
- What's the support plan?

---

## Top 3 Recommendations

| # | Recommendation | Rationale |
|---|----------------|-----------|
| 1 | **Start with ONE view, not three** | The conversation tries to solve Finance, Sales, and Operations all at once. Pick Finance gross margin as the MVP. Prove value fast. |
| 2 | **Run parallel validation for 4 weeks** | Before anyone trusts the new app, it must match the manual Excel calculation exactly. Budget time for this. |
| 3 | **Get a cost comparison done before committing** | A Power BI dashboard connecting to Epicor might cost less and be more maintainable than a custom Python app. Make this a data-driven decision, not a preference-driven one. |

---

## Recommended Next Steps

### Week 1: Foundation

| # | Action | Owner | Deliverable |
|---|--------|-------|-------------|
| 1 | Answer critical questions above | Leadership | Decision document |
| 2 | Inventory existing BAQs for required data | Epicor Admin | BAQ checklist |
| 3 | Document current gross margin calculation | Finance | Calculation spec |
| 4 | Quick cost estimate: custom vs. Power BI | IT/Finance | 1-page comparison |

### Week 2-3: Planning

| # | Action | Owner | Deliverable |
|---|--------|-------|-------------|
| 5 | Define MVP scope (recommend Finance margin only) | Leadership | Scope document |
| 6 | Assign developer resource | Management | Resource allocation |
| 7 | Create project charter with success criteria | PM | Charter document |
| 8 | Security/IT review of Replit | IT | Approval or alternative |

### Week 4-6: Build MVP

| # | Action | Owner | Deliverable |
|---|--------|-------|-------------|
| 9 | Build BAQ exports for margin data | Epicor Admin | Scheduled exports |
| 10 | Develop Finance margin dashboard (historical only) | Developer | Working prototype |
| 11 | Validate against manual Excel calculation | Finance | Test results |
| 12 | User acceptance testing | Finance team | Feedback |

### Week 7+: Expand

| # | Action | Owner | Deliverable |
|---|--------|-------|-------------|
| 13 | Add Sales revenue views | Developer | Phase 2 |
| 14 | Add Operations labor/burden views | Developer | Phase 3 |
| 15 | Add forecasting capability | Developer | Phase 4 |
| 16 | Training & rollout | PM | Live system |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Technical debt - Copilot generated scaffolding code, not production-ready | HIGH | Requires experienced developer review |
| Data accuracy - Margin calculations must match finance definitions exactly | HIGH | Finance sign-off on calculation logic |
| Single point of failure - Replit hosting for business-critical app | MEDIUM | Consider backup/failover strategy |
| Maintenance burden - Custom app requires ongoing developer support | MEDIUM | Document thoroughly, plan for updates |
| Scope creep - Forecasting + drill-downs + alerts is ambitious V1 | MEDIUM | Phase the rollout |
| Security - JWT auth on Replit may not meet audit requirements | MEDIUM | Review with IT/compliance |

---

## What Was Missing from the Copilot Conversation

1. **Total Cost of Ownership (TCO)** - No discussion of development hours, ongoing maintenance, or hosting costs at scale

2. **Alternative Solutions** - Power BI, Epicor native dashboards, and third-party BI tools were dismissed without cost comparison

3. **Success Criteria** - No KPIs defined for measuring whether the project achieved its goals

4. **Data Governance** - No discussion of who owns BAQ definitions, change control, or data retention

5. **Implementation Timeline** - No phases or milestones defined

---

## Summary

The business need is valid. Weekly margin and revenue visibility would improve financial planning and operational decision-making.

**However**: The Copilot conversation provided good technical scaffolding but skipped critical business planning. This needs a proper project charter with scope, budget, success criteria, and resource allocation before development begins.

**Recommendation**: Proceed with caution using a phased pilot approach. Build Finance margin view first, validate against manual Excel, then expand.

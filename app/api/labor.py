"""Labor & Burden API endpoints.

Maps to jt_zLaborDtl01 BAQ:
- LaborDtl_LaborHrs, LaborDtl_BurdenHrs
- JobAsmbl_JobComplete (WIP vs Completed)
"""
from decimal import Decimal
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import DimWeek, DimJob, DimProduct, FactCosts
from app.schemas import LaborSummary, LaborByJob, WeekSummary

router = APIRouter()


@router.get("", response_model=LaborSummary)
def get_labor_summary(
    week_id: Optional[int] = None,
    status: Literal["all", "wip", "completed"] = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get labor and burden summary for a week."""
    # Get week (default to most recent)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        return LaborSummary(
            week=WeekSummary(week_id=0, iso_year=2025, iso_week=1, label="No data"),
            total_labor_hours=Decimal("0"),
            total_burden_hours=Decimal("0"),
            total_direct_labor=Decimal("0"),
            total_burden=Decimal("0"),
            total_labor_cost=Decimal("0"),
            job_count=0,
            by_job=[]
        )

    # Get totals including hours
    totals = db.query(
        func.sum(FactCosts.labor_hours).label("total_labor_hours"),
        func.sum(FactCosts.burden_hours).label("total_burden_hours"),
        func.sum(FactCosts.direct_labor).label("total_labor"),
        func.sum(FactCosts.burden).label("total_burden"),
        func.count(func.distinct(FactCosts.job_id)).label("job_count")
    ).filter(
        FactCosts.week_id == week.week_id
    ).first()

    total_labor_hours = totals.total_labor_hours or Decimal("0")
    total_burden_hours = totals.total_burden_hours or Decimal("0")
    total_direct_labor = totals.total_labor or Decimal("0")
    total_burden = totals.total_burden or Decimal("0")
    job_count = totals.job_count or 0

    # Get by job with product group, job status, and hours
    job_query = db.query(
        DimJob.job_num,
        DimJob.sales_order_num,
        DimJob.job_closed,
        DimProduct.product_group,
        func.sum(FactCosts.labor_hours).label("labor_hours"),
        func.sum(FactCosts.burden_hours).label("burden_hours"),
        func.sum(FactCosts.direct_labor).label("direct_labor"),
        func.sum(FactCosts.burden).label("burden")
    ).join(
        DimJob, FactCosts.job_id == DimJob.job_id
    ).outerjoin(
        DimProduct, DimJob.product_id == DimProduct.product_id
    ).filter(
        FactCosts.week_id == week.week_id
    )

    # Apply status filter (maps to JobAsmbl_JobComplete)
    if status == "wip":
        job_query = job_query.filter(DimJob.job_closed == False)
    elif status == "completed":
        job_query = job_query.filter(DimJob.job_closed == True)

    job_query = job_query.group_by(
        DimJob.job_num, DimJob.sales_order_num, DimJob.job_closed, DimProduct.product_group
    ).order_by(
        desc(func.sum(FactCosts.direct_labor + FactCosts.burden))
    ).limit(limit)

    by_job = []
    for row in job_query.all():
        labor_hrs = row.labor_hours or Decimal("0")
        burden_hrs = row.burden_hours or Decimal("0")
        labor = row.direct_labor or Decimal("0")
        burden = row.burden or Decimal("0")
        by_job.append(LaborByJob(
            job_num=row.job_num,
            sales_order_num=row.sales_order_num,
            product_group=row.product_group,
            job_closed=row.job_closed or False,
            labor_hours=labor_hrs,
            burden_hours=burden_hrs,
            direct_labor=labor,
            burden=burden,
            total_labor=labor + burden
        ))

    return LaborSummary(
        week=WeekSummary(
            week_id=week.week_id,
            iso_year=week.iso_year,
            iso_week=week.iso_week,
            label=f"{week.iso_year}-W{week.iso_week:02d}"
        ),
        total_labor_hours=total_labor_hours,
        total_burden_hours=total_burden_hours,
        total_direct_labor=total_direct_labor,
        total_burden=total_burden,
        total_labor_cost=total_direct_labor + total_burden,
        job_count=job_count,
        by_job=by_job
    )

"""Labor & Burden API endpoints."""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import DimWeek, DimJob, FactCosts
from app.schemas import LaborSummary, LaborByJob, WeekSummary

router = APIRouter()


@router.get("", response_model=LaborSummary)
def get_labor_summary(
    week_id: Optional[int] = None,
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
            total_direct_labor=Decimal("0"),
            total_burden=Decimal("0"),
            total_labor_cost=Decimal("0"),
            job_count=0,
            by_job=[]
        )

    # Get totals
    totals = db.query(
        func.sum(FactCosts.direct_labor).label("total_labor"),
        func.sum(FactCosts.burden).label("total_burden"),
        func.count(func.distinct(FactCosts.job_id)).label("job_count")
    ).filter(
        FactCosts.week_id == week.week_id
    ).first()

    total_direct_labor = totals.total_labor or Decimal("0")
    total_burden = totals.total_burden or Decimal("0")
    job_count = totals.job_count or 0

    # Get by job
    job_query = db.query(
        DimJob.job_num,
        DimJob.sales_order_num,
        func.sum(FactCosts.direct_labor).label("direct_labor"),
        func.sum(FactCosts.burden).label("burden")
    ).join(
        DimJob, FactCosts.job_id == DimJob.job_id
    ).filter(
        FactCosts.week_id == week.week_id
    ).group_by(
        DimJob.job_num, DimJob.sales_order_num
    ).order_by(
        desc(func.sum(FactCosts.direct_labor + FactCosts.burden))
    ).limit(limit)

    by_job = []
    for row in job_query.all():
        labor = row.direct_labor or Decimal("0")
        burden = row.burden or Decimal("0")
        by_job.append(LaborByJob(
            job_num=row.job_num,
            sales_order_num=row.sales_order_num,
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
        total_direct_labor=total_direct_labor,
        total_burden=total_burden,
        total_labor_cost=total_direct_labor + total_burden,
        job_count=job_count,
        by_job=by_job
    )

"""Gross Margin API endpoints."""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction
from app.schemas import (
    MarginSummary, MarginByProduct, MarginTrend, WeekSummary
)

router = APIRouter()


def calculate_margin_percent(revenue: Decimal, cost: Decimal) -> Decimal:
    """Calculate margin percentage safely."""
    if not revenue or revenue == 0:
        return Decimal("0")
    return ((revenue - cost) / revenue * 100).quantize(Decimal("0.01"))


@router.get("", response_model=MarginSummary)
def get_margin_summary(
    week_id: Optional[int] = None,
    product_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get gross margin summary for a week."""
    # Get week (default to most recent)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        return MarginSummary(
            week=WeekSummary(week_id=0, iso_year=2025, iso_week=1, label="No data"),
            by_product=[],
            total_revenue=Decimal("0"),
            total_cost=Decimal("0"),
            overall_margin=Decimal("0"),
            overall_margin_percent=Decimal("0")
        )

    # Get revenue by product group (outbound only for margin)
    revenue_query = db.query(
        DimProduct.product_group,
        func.sum(FactRevenue.revenue).label("revenue"),
        func.avg(DimProduct.target_margin).label("target_margin")
    ).join(
        DimProduct, FactRevenue.product_id == DimProduct.product_id
    ).filter(
        FactRevenue.week_id == week.week_id,
        FactRevenue.direction == Direction.OUTBOUND
    )

    if product_group:
        revenue_query = revenue_query.filter(DimProduct.product_group == product_group)

    revenue_query = revenue_query.group_by(DimProduct.product_group)
    revenue_results = {r.product_group: r for r in revenue_query.all()}

    # Get costs by product group (via job -> product mapping)
    cost_query = db.query(
        DimProduct.product_group,
        func.sum(FactCosts.direct_labor + FactCosts.burden + FactCosts.material_cost).label("total_cost")
    ).join(
        DimJob, FactCosts.job_id == DimJob.job_id
    ).join(
        DimProduct, DimJob.product_id == DimProduct.product_id
    ).filter(
        FactCosts.week_id == week.week_id
    )

    if product_group:
        cost_query = cost_query.filter(DimProduct.product_group == product_group)

    cost_query = cost_query.group_by(DimProduct.product_group)
    cost_results = {c.product_group: c.total_cost or Decimal("0") for c in cost_query.all()}

    # Build response
    by_product = []
    total_revenue = Decimal("0")
    total_cost = Decimal("0")

    all_groups = set(revenue_results.keys()) | set(cost_results.keys())

    for group in sorted(all_groups):
        rev_data = revenue_results.get(group)
        revenue = rev_data.revenue if rev_data else Decimal("0")
        target_margin = rev_data.target_margin if rev_data else None
        cost = cost_results.get(group, Decimal("0"))

        gross_margin = revenue - cost
        margin_percent = calculate_margin_percent(revenue, cost)

        variance = None
        if target_margin is not None:
            variance = margin_percent - (target_margin * 100)

        by_product.append(MarginByProduct(
            product_group=group,
            revenue=revenue,
            total_cost=cost,
            gross_margin=gross_margin,
            margin_percent=margin_percent,
            target_margin=target_margin,
            variance=variance
        ))

        total_revenue += revenue
        total_cost += cost

    overall_margin = total_revenue - total_cost
    overall_margin_percent = calculate_margin_percent(total_revenue, total_cost)

    return MarginSummary(
        week=WeekSummary(
            week_id=week.week_id,
            iso_year=week.iso_year,
            iso_week=week.iso_week,
            label=f"{week.iso_year}-W{week.iso_week:02d}"
        ),
        by_product=by_product,
        total_revenue=total_revenue,
        total_cost=total_cost,
        overall_margin=overall_margin,
        overall_margin_percent=overall_margin_percent
    )


@router.get("/trend", response_model=List[MarginTrend])
def get_margin_trend(
    weeks: int = Query(default=13, ge=1, le=52),
    product_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get gross margin trend over multiple weeks."""
    # Get recent weeks
    recent_weeks = db.query(DimWeek).order_by(
        desc(DimWeek.iso_year), desc(DimWeek.iso_week)
    ).limit(weeks).all()

    if not recent_weeks:
        return []

    trend = []
    for week in reversed(recent_weeks):  # Oldest first for charting
        summary = get_margin_summary(week_id=week.week_id, product_group=product_group, db=db)
        trend.append(MarginTrend(
            week_id=week.week_id,
            iso_year=week.iso_year,
            iso_week=week.iso_week,
            label=f"{week.iso_year}-W{week.iso_week:02d}",
            revenue=summary.total_revenue,
            total_cost=summary.total_cost,
            gross_margin=summary.overall_margin,
            margin_percent=summary.overall_margin_percent
        ))

    return trend

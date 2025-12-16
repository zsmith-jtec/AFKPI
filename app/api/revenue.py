"""Revenue API endpoints."""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import DimWeek, DimProduct, FactRevenue, Direction
from app.schemas import (
    RevenueSummary, RevenueByProduct, RevenueByWeek,
    WeekSummary, DirectionEnum
)

router = APIRouter()


@router.get("", response_model=RevenueSummary)
def get_revenue_summary(
    week_id: Optional[int] = None,
    product_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get revenue summary for a week, optionally filtered by product group."""
    # Get week (default to most recent)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        return RevenueSummary(
            week=WeekSummary(week_id=0, iso_year=2025, iso_week=1, label="No data"),
            by_product=[],
            total_inbound=Decimal("0"),
            total_outbound=Decimal("0")
        )

    # Build query
    query = db.query(
        DimProduct.product_group,
        FactRevenue.direction,
        func.sum(FactRevenue.revenue).label("revenue"),
        func.sum(FactRevenue.order_count).label("order_count"),
        func.avg(DimProduct.target_margin).label("target_margin")
    ).join(
        DimProduct, FactRevenue.product_id == DimProduct.product_id
    ).filter(
        FactRevenue.week_id == week.week_id
    )

    if product_group:
        query = query.filter(DimProduct.product_group == product_group)

    query = query.group_by(DimProduct.product_group, FactRevenue.direction)
    results = query.all()

    # Build response
    by_product = []
    total_inbound = Decimal("0")
    total_outbound = Decimal("0")

    for row in results:
        direction_enum = DirectionEnum.INBOUND if row.direction == Direction.INBOUND else DirectionEnum.OUTBOUND
        revenue_item = RevenueByProduct(
            product_group=row.product_group,
            direction=direction_enum,
            revenue=row.revenue or Decimal("0"),
            order_count=row.order_count or 0,
            target_margin=row.target_margin
        )
        by_product.append(revenue_item)

        if row.direction == Direction.INBOUND:
            total_inbound += row.revenue or Decimal("0")
        else:
            total_outbound += row.revenue or Decimal("0")

    return RevenueSummary(
        week=WeekSummary(
            week_id=week.week_id,
            iso_year=week.iso_year,
            iso_week=week.iso_week,
            label=f"{week.iso_year}-W{week.iso_week:02d}"
        ),
        by_product=by_product,
        total_inbound=total_inbound,
        total_outbound=total_outbound
    )


@router.get("/trend", response_model=List[RevenueByWeek])
def get_revenue_trend(
    weeks: int = Query(default=13, ge=1, le=52),
    direction: Optional[DirectionEnum] = None,
    db: Session = Depends(get_db)
):
    """Get revenue trend over multiple weeks."""
    # Get recent weeks
    recent_weeks = db.query(DimWeek).order_by(
        desc(DimWeek.iso_year), desc(DimWeek.iso_week)
    ).limit(weeks).all()

    if not recent_weeks:
        return []

    week_ids = [w.week_id for w in recent_weeks]

    # Query revenue by week
    query = db.query(
        DimWeek.week_id,
        DimWeek.iso_year,
        DimWeek.iso_week,
        FactRevenue.direction,
        func.sum(FactRevenue.revenue).label("revenue")
    ).join(
        DimWeek, FactRevenue.week_id == DimWeek.week_id
    ).filter(
        FactRevenue.week_id.in_(week_ids)
    ).group_by(
        DimWeek.week_id, DimWeek.iso_year, DimWeek.iso_week, FactRevenue.direction
    ).order_by(
        DimWeek.iso_year, DimWeek.iso_week
    )

    results = query.all()

    # Aggregate by week
    week_data = {}
    for row in results:
        key = row.week_id
        if key not in week_data:
            week_data[key] = {
                "week_id": row.week_id,
                "iso_year": row.iso_year,
                "iso_week": row.iso_week,
                "inbound": Decimal("0"),
                "outbound": Decimal("0")
            }
        if row.direction == Direction.INBOUND:
            week_data[key]["inbound"] = row.revenue or Decimal("0")
        else:
            week_data[key]["outbound"] = row.revenue or Decimal("0")

    # Build response
    trend = []
    for data in sorted(week_data.values(), key=lambda x: (x["iso_year"], x["iso_week"])):
        trend.append(RevenueByWeek(
            week_id=data["week_id"],
            iso_year=data["iso_year"],
            iso_week=data["iso_week"],
            inbound_revenue=data["inbound"],
            outbound_revenue=data["outbound"],
            total_revenue=data["inbound"] + data["outbound"]
        ))

    return trend

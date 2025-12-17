"""Weeks API endpoints."""
from typing import List
from collections import defaultdict
from calendar import month_abbr
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import DimWeek
from app.schemas import WeekRead, WeekSummary, MonthSummary

router = APIRouter()


@router.get("", response_model=List[WeekSummary])
def list_weeks(
    limit: int = 52,
    db: Session = Depends(get_db)
):
    """List available weeks, most recent first."""
    weeks = db.query(DimWeek).order_by(
        desc(DimWeek.iso_year),
        desc(DimWeek.iso_week)
    ).limit(limit).all()

    return [
        WeekSummary(
            week_id=w.week_id,
            iso_year=w.iso_year,
            iso_week=w.iso_week,
            label=f"{w.iso_year}-W{w.iso_week:02d}"
        )
        for w in weeks
    ]


@router.get("/current", response_model=WeekSummary)
def get_current_week(db: Session = Depends(get_db)):
    """Get the most recent week with data."""
    week = db.query(DimWeek).order_by(
        desc(DimWeek.iso_year),
        desc(DimWeek.iso_week)
    ).first()

    if not week:
        return WeekSummary(week_id=0, iso_year=2025, iso_week=1, label="No data")

    return WeekSummary(
        week_id=week.week_id,
        iso_year=week.iso_year,
        iso_week=week.iso_week,
        label=f"{week.iso_year}-W{week.iso_week:02d}"
    )


@router.get("/months", response_model=List[MonthSummary])
def list_months(
    limit: int = 13,
    db: Session = Depends(get_db)
):
    """List available months with their week IDs, most recent first."""
    weeks = db.query(DimWeek).order_by(
        desc(DimWeek.iso_year),
        desc(DimWeek.iso_week)
    ).all()

    # Group weeks by calendar month (based on week_start date)
    months_dict = defaultdict(list)
    for w in weeks:
        year = w.week_start.year
        month = w.week_start.month
        key = (year, month)
        months_dict[key].append(w.week_id)

    # Sort by year-month descending and convert to list
    sorted_months = sorted(months_dict.keys(), reverse=True)[:limit]

    return [
        MonthSummary(
            year=year,
            month=month,
            label=f"{month_abbr[month]} {year}",
            week_ids=months_dict[(year, month)]
        )
        for year, month in sorted_months
    ]


@router.get("/{week_id}", response_model=WeekRead)
def get_week(week_id: int, db: Session = Depends(get_db)):
    """Get details for a specific week."""
    week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    if not week:
        return None
    return week

"""Drill-down API endpoints."""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction
from app.schemas import DrillProductGroup, DrillCategory, JobDetail

router = APIRouter()


def calculate_margin_percent(revenue: Decimal, cost: Decimal) -> Decimal:
    """Calculate margin percentage safely."""
    if not revenue or revenue == 0:
        return Decimal("0")
    return ((revenue - cost) / revenue * 100).quantize(Decimal("0.01"))


@router.get("/product/{product_group}", response_model=DrillProductGroup)
def drill_to_product_group(
    product_group: str,
    week_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Drill down to categories within a product group."""
    # Get week (default to most recent)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        raise HTTPException(status_code=404, detail="No data available")

    # Get revenue by category (outbound)
    revenue_query = db.query(
        DimProduct.category,
        func.sum(FactRevenue.revenue).label("revenue"),
        func.count(func.distinct(FactRevenue.fact_id)).label("order_count")
    ).join(
        DimProduct, FactRevenue.product_id == DimProduct.product_id
    ).filter(
        FactRevenue.week_id == week.week_id,
        FactRevenue.direction == Direction.OUTBOUND,
        DimProduct.product_group == product_group
    ).group_by(DimProduct.category)

    revenue_results = {r.category: {"revenue": r.revenue or Decimal("0"), "orders": r.order_count}
                       for r in revenue_query.all()}

    # Get costs by category
    cost_query = db.query(
        DimProduct.category,
        func.sum(FactCosts.direct_labor + FactCosts.burden + FactCosts.material_cost).label("cost"),
        func.count(func.distinct(FactCosts.job_id)).label("job_count")
    ).join(
        DimJob, FactCosts.job_id == DimJob.job_id
    ).join(
        DimProduct, DimJob.product_id == DimProduct.product_id
    ).filter(
        FactCosts.week_id == week.week_id,
        DimProduct.product_group == product_group
    ).group_by(DimProduct.category)

    cost_results = {c.category: {"cost": c.cost or Decimal("0"), "jobs": c.job_count}
                    for c in cost_query.all()}

    # Build categories
    all_categories = set(revenue_results.keys()) | set(cost_results.keys())
    categories = []
    total_revenue = Decimal("0")
    total_cost = Decimal("0")

    for cat in sorted(all_categories):
        rev_data = revenue_results.get(cat, {"revenue": Decimal("0"), "orders": 0})
        cost_data = cost_results.get(cat, {"cost": Decimal("0"), "jobs": 0})

        revenue = rev_data["revenue"]
        cost = cost_data["cost"]
        margin = revenue - cost
        margin_percent = calculate_margin_percent(revenue, cost)

        categories.append(DrillCategory(
            category=cat,
            revenue=revenue,
            cost=cost,
            margin=margin,
            margin_percent=margin_percent,
            job_count=cost_data["jobs"]
        ))

        total_revenue += revenue
        total_cost += cost

    total_margin = total_revenue - total_cost
    overall_margin_percent = calculate_margin_percent(total_revenue, total_cost)

    return DrillProductGroup(
        product_group=product_group,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_margin=total_margin,
        margin_percent=overall_margin_percent,
        categories=categories
    )


@router.get("/category/{category}", response_model=List[JobDetail])
def drill_to_category(
    category: str,
    week_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Drill down to jobs within a category."""
    # Get week (default to most recent)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        return []

    # Get jobs with costs in this category
    jobs_query = db.query(
        DimJob.job_id,
        DimJob.job_num,
        DimJob.sales_order_num,
        DimJob.part_num,
        DimProduct.product_group,
        DimProduct.category,
        func.sum(FactCosts.direct_labor).label("direct_labor"),
        func.sum(FactCosts.burden).label("burden"),
        func.sum(FactCosts.material_cost).label("material_cost")
    ).join(
        DimJob, FactCosts.job_id == DimJob.job_id
    ).join(
        DimProduct, DimJob.product_id == DimProduct.product_id
    ).filter(
        FactCosts.week_id == week.week_id,
        DimProduct.category == category
    ).group_by(
        DimJob.job_id, DimJob.job_num, DimJob.sales_order_num, DimJob.part_num,
        DimProduct.product_group, DimProduct.category
    ).order_by(
        desc(func.sum(FactCosts.direct_labor + FactCosts.burden + FactCosts.material_cost))
    ).limit(limit)

    jobs = []
    for row in jobs_query.all():
        labor = row.direct_labor or Decimal("0")
        burden = row.burden or Decimal("0")
        material = row.material_cost or Decimal("0")
        total_cost = labor + burden + material

        jobs.append(JobDetail(
            job_id=row.job_id,
            job_num=row.job_num,
            sales_order_num=row.sales_order_num,
            part_num=row.part_num,
            direct_labor=labor,
            burden=burden,
            material_cost=material,
            total_cost=total_cost,
            product_group=row.product_group,
            category=row.category
        ))

    return jobs


@router.get("/job/{job_num}", response_model=JobDetail)
def drill_to_job(
    job_num: str,
    week_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific job."""
    # Find the job
    job = db.query(DimJob).filter(DimJob.job_num == job_num).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_num} not found")

    # Get week (default to most recent with data for this job)
    if week_id:
        week = db.query(DimWeek).filter(DimWeek.week_id == week_id).first()
    else:
        week = db.query(DimWeek).join(
            FactCosts, FactCosts.week_id == DimWeek.week_id
        ).filter(
            FactCosts.job_id == job.job_id
        ).order_by(
            desc(DimWeek.iso_year), desc(DimWeek.iso_week)
        ).first()

    if not week:
        # Return job info without cost data
        return JobDetail(
            job_id=job.job_id,
            job_num=job.job_num,
            sales_order_num=job.sales_order_num,
            part_num=job.part_num,
            product_id=job.product_id
        )

    # Get costs for this job in this week
    costs = db.query(
        func.sum(FactCosts.direct_labor).label("direct_labor"),
        func.sum(FactCosts.burden).label("burden"),
        func.sum(FactCosts.material_cost).label("material_cost")
    ).filter(
        FactCosts.job_id == job.job_id,
        FactCosts.week_id == week.week_id
    ).first()

    labor = costs.direct_labor or Decimal("0")
    burden = costs.burden or Decimal("0")
    material = costs.material_cost or Decimal("0")
    total_cost = labor + burden + material

    # Get product info
    product_group = None
    category = None
    if job.product:
        product_group = job.product.product_group
        category = job.product.category

    return JobDetail(
        job_id=job.job_id,
        job_num=job.job_num,
        sales_order_num=job.sales_order_num,
        part_num=job.part_num,
        product_id=job.product_id,
        direct_labor=labor,
        burden=burden,
        material_cost=material,
        total_cost=total_cost,
        product_group=product_group,
        category=category
    )

"""ETL Loader - Upsert transformed data into database."""
import pandas as pd
from decimal import Decimal
from datetime import date
from typing import Dict, Tuple, Optional
from sqlalchemy.orm import Session
import logging

from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction, AuditLog

logger = logging.getLogger(__name__)


def get_or_create_week(db: Session, week_start: date, iso_year: int, iso_week: int) -> DimWeek:
    """Get existing week or create new one."""
    week = db.query(DimWeek).filter(DimWeek.week_start == week_start).first()
    if not week:
        week_end = week_start + pd.Timedelta(days=6)
        week = DimWeek(
            week_start=week_start,
            week_end=week_end,
            iso_year=iso_year,
            iso_week=iso_week
        )
        db.add(week)
        db.flush()
        logger.info(f"Created week: {iso_year}-W{iso_week:02d}")
    return week


def get_or_create_product(
    db: Session,
    product_group: str,
    category: str,
    product_line: str = "IPS",
    target_margins: Optional[Dict[Tuple[str, str], Decimal]] = None
) -> DimProduct:
    """Get existing product or create new one."""
    product = db.query(DimProduct).filter(
        DimProduct.product_group == product_group,
        DimProduct.category == category
    ).first()

    if not product:
        target_margin = None
        if target_margins:
            target_margin = target_margins.get((product_group, category))

        product = DimProduct(
            product_line=product_line,
            product_group=product_group,
            category=category,
            target_margin=target_margin
        )
        db.add(product)
        db.flush()
        logger.info(f"Created product: {product_group} / {category}")
    return product


def get_or_create_job(
    db: Session,
    job_num: str,
    sales_order_num: Optional[str] = None,
    part_num: Optional[str] = None,
    product_id: Optional[int] = None
) -> DimJob:
    """Get existing job or create new one."""
    job = db.query(DimJob).filter(DimJob.job_num == job_num).first()

    if not job:
        job = DimJob(
            job_num=job_num,
            sales_order_num=sales_order_num,
            part_num=part_num,
            product_id=product_id
        )
        db.add(job)
        db.flush()
        logger.info(f"Created job: {job_num}")
    elif sales_order_num and not job.sales_order_num:
        # Update missing fields
        job.sales_order_num = sales_order_num
        if part_num:
            job.part_num = part_num
        if product_id:
            job.product_id = product_id
        db.flush()
    return job


def load_revenue(
    db: Session,
    revenue_df: pd.DataFrame,
    target_margins: Optional[Dict[Tuple[str, str], Decimal]] = None,
    user_email: str = "system@etl"
) -> int:
    """Load aggregated revenue data into fact table."""
    rows_loaded = 0

    for _, row in revenue_df.iterrows():
        # Get or create dimension records
        week = get_or_create_week(
            db,
            week_start=row["week_start"],
            iso_year=int(row["iso_year"]),
            iso_week=int(row["iso_week"])
        )

        product = get_or_create_product(
            db,
            product_group=str(row["product_group"]),
            category=str(row["category"]),
            target_margins=target_margins
        )

        # Determine direction
        direction = Direction.INBOUND if row["direction"] == "inbound" else Direction.OUTBOUND

        # Check for existing fact record
        existing = db.query(FactRevenue).filter(
            FactRevenue.week_id == week.week_id,
            FactRevenue.product_id == product.product_id,
            FactRevenue.direction == direction
        ).first()

        if existing:
            # Update existing
            existing.revenue = Decimal(str(row["revenue"]))
            existing.order_count = int(row["order_count"])
        else:
            # Create new
            fact = FactRevenue(
                week_id=week.week_id,
                product_id=product.product_id,
                direction=direction,
                revenue=Decimal(str(row["revenue"])),
                order_count=int(row["order_count"])
            )
            db.add(fact)

        rows_loaded += 1

    db.commit()

    # Audit log
    audit = AuditLog(
        user_email=user_email,
        action="UPLOAD",
        entity="revenue",
        details=f"Loaded {rows_loaded} revenue records"
    )
    db.add(audit)
    db.commit()

    logger.info(f"Loaded {rows_loaded} revenue records")
    return rows_loaded


def load_costs(
    db: Session,
    labor_df: pd.DataFrame,
    material_df: Optional[pd.DataFrame] = None,
    job_df: Optional[pd.DataFrame] = None,
    target_margins: Optional[Dict[Tuple[str, str], Decimal]] = None,
    user_email: str = "system@etl"
) -> int:
    """Load aggregated cost data into fact table."""
    rows_loaded = 0

    # Build job info lookup from job_df if provided
    job_info = {}
    if job_df is not None:
        for _, row in job_df.iterrows():
            job_num = str(row.get("JobNum", ""))
            if job_num:
                job_info[job_num] = {
                    "sales_order_num": str(row.get("OrderNum", "")) if pd.notna(row.get("OrderNum")) else None,
                    "part_num": str(row.get("PartNum", "")) if pd.notna(row.get("PartNum")) else None,
                    "prod_code": str(row.get("ProdCode", "Unknown")) if pd.notna(row.get("ProdCode")) else "Unknown"
                }

    # Build material lookup
    material_lookup = {}
    if material_df is not None:
        for _, row in material_df.iterrows():
            key = (int(row["iso_year"]), int(row["iso_week"]), str(row["JobNum"]))
            material_lookup[key] = Decimal(str(row["material_cost"]))

    # Load labor (and join material)
    for _, row in labor_df.iterrows():
        job_num = str(row["JobNum"])

        # Get job info
        info = job_info.get(job_num, {})
        sales_order_num = info.get("sales_order_num")
        part_num = info.get("part_num")
        prod_code = info.get("prod_code", "Unknown")

        # Get or create product (use prod_code as product_group)
        product = get_or_create_product(
            db,
            product_group=prod_code,
            category="Unknown",  # Will be updated when more info available
            target_margins=target_margins
        )

        # Get or create week
        week = get_or_create_week(
            db,
            week_start=row["week_start"],
            iso_year=int(row["iso_year"]),
            iso_week=int(row["iso_week"])
        )

        # Get or create job
        job = get_or_create_job(
            db,
            job_num=job_num,
            sales_order_num=sales_order_num,
            part_num=part_num,
            product_id=product.product_id
        )

        # Get material cost
        material_key = (int(row["iso_year"]), int(row["iso_week"]), job_num)
        material_cost = material_lookup.get(material_key, Decimal("0"))

        # Check for existing fact record
        existing = db.query(FactCosts).filter(
            FactCosts.week_id == week.week_id,
            FactCosts.job_id == job.job_id
        ).first()

        if existing:
            # Update existing
            existing.direct_labor = Decimal(str(row["direct_labor"]))
            existing.burden = Decimal(str(row["burden"]))
            existing.material_cost = material_cost
        else:
            # Create new
            fact = FactCosts(
                week_id=week.week_id,
                job_id=job.job_id,
                direct_labor=Decimal(str(row["direct_labor"])),
                burden=Decimal(str(row["burden"])),
                material_cost=material_cost
            )
            db.add(fact)

        rows_loaded += 1

    db.commit()

    # Audit log
    audit = AuditLog(
        user_email=user_email,
        action="UPLOAD",
        entity="costs",
        details=f"Loaded {rows_loaded} cost records"
    )
    db.add(audit)
    db.commit()

    logger.info(f"Loaded {rows_loaded} cost records")
    return rows_loaded

"""Seed sample data for AFKPI dashboard testing.

Run this script to populate the database with realistic sample data.
Usage: python seed_data.py
"""
import random
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction

# Product data from Corp. Mapping
PRODUCTS = [
    ("IPS", "CarryLite", "Custom Cart", Decimal("0.25")),
    ("IPS", "CarryLite", "Drum Cart", Decimal("0.25")),
    ("IPS", "CarryLite", "Kit Cart", Decimal("0.25")),
    ("IPS", "CarryMax", "Custom Cart", Decimal("0.25")),
    ("IPS", "CarryMax", "Lift Table", Decimal("0.25")),
    ("IPS", "CarryMore", "Custom Cart", Decimal("0.30")),
    ("IPS", "CarryMore", "Mother Cart Powered", Decimal("0.35")),
    ("IPS", "CarryMore", "Mother Cart Non Powered", Decimal("0.35")),
    ("IPS", "CarryMore", "Flatbed Rider Cart", Decimal("0.30")),
    ("IPS", "CarryMore", "Refuse Hopper", Decimal("0.30")),
    ("APS", "CarryMatic", "LiftBot", Decimal("0.35")),
    ("APS", "CarryMatic", "MoveBot", Decimal("0.35")),
    ("APS", "CarryMatic", "TugBot", Decimal("0.20")),
    ("APS", "CarryMatic", "Controls", Decimal("0.365")),
    ("WPS", "Warehouse Manufactured", "Conveyor - Gravity", Decimal("0.22")),
    ("WPS", "Warehouse Manufactured", "Conveyor - Powered", Decimal("0.22")),
]


def create_weeks(db: Session, num_weeks: int = 13) -> list[DimWeek]:
    """Create dimension weeks for the past N weeks."""
    weeks = []
    today = date.today()
    # Start from Monday of current week
    current_monday = today - timedelta(days=today.weekday())

    for i in range(num_weeks):
        week_start = current_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        iso_year, iso_week, _ = week_start.isocalendar()

        # Check if exists
        existing = db.query(DimWeek).filter(DimWeek.week_start == week_start).first()
        if existing:
            weeks.append(existing)
        else:
            week = DimWeek(
                week_start=week_start,
                week_end=week_end,
                iso_year=iso_year,
                iso_week=iso_week
            )
            db.add(week)
            db.flush()
            weeks.append(week)

    db.commit()
    return weeks


def create_products(db: Session) -> list[DimProduct]:
    """Create dimension products from Corp. Mapping."""
    products = []
    for line, group, category, margin in PRODUCTS:
        existing = db.query(DimProduct).filter(
            DimProduct.product_group == group,
            DimProduct.category == category
        ).first()
        if existing:
            products.append(existing)
        else:
            product = DimProduct(
                product_line=line,
                product_group=group,
                category=category,
                target_margin=margin
            )
            db.add(product)
            db.flush()
            products.append(product)

    db.commit()
    return products


def create_jobs(db: Session, products: list[DimProduct], num_jobs: int = 50) -> list[DimJob]:
    """Create sample jobs linked to products."""
    jobs = []
    for i in range(num_jobs):
        job_num = f"J{100000 + i}"
        existing = db.query(DimJob).filter(DimJob.job_num == job_num).first()
        if existing:
            jobs.append(existing)
        else:
            product = random.choice(products)
            job = DimJob(
                job_num=job_num,
                sales_order_num=f"SO{50000 + i}",
                part_num=f"PART-{product.category[:3].upper()}-{i:03d}",
                product_id=product.product_id
            )
            db.add(job)
            db.flush()
            jobs.append(job)

    db.commit()
    return jobs


def create_revenue(db: Session, weeks: list[DimWeek], products: list[DimProduct]):
    """Create sample revenue facts."""
    for week in weeks:
        for product in products:
            # Random revenue with some variation
            base_inbound = random.randint(10000, 100000)
            base_outbound = random.randint(15000, 120000)

            # Check if exists
            for direction in [Direction.INBOUND, Direction.OUTBOUND]:
                existing = db.query(FactRevenue).filter(
                    FactRevenue.week_id == week.week_id,
                    FactRevenue.product_id == product.product_id,
                    FactRevenue.direction == direction
                ).first()

                if not existing:
                    revenue = base_inbound if direction == Direction.INBOUND else base_outbound
                    fact = FactRevenue(
                        week_id=week.week_id,
                        product_id=product.product_id,
                        direction=direction,
                        revenue=Decimal(str(revenue)),
                        order_count=random.randint(1, 10)
                    )
                    db.add(fact)

    db.commit()


def create_costs(db: Session, weeks: list[DimWeek], jobs: list[DimJob]):
    """Create sample cost facts."""
    for week in weeks:
        # Only some jobs have activity each week
        active_jobs = random.sample(jobs, k=min(20, len(jobs)))

        for job in active_jobs:
            existing = db.query(FactCosts).filter(
                FactCosts.week_id == week.week_id,
                FactCosts.job_id == job.job_id
            ).first()

            if not existing:
                labor_hours = random.randint(4, 80)
                burden_hours = labor_hours  # Usually 1:1
                labor_rate = Decimal("45.00")
                burden_rate = Decimal("28.00")

                fact = FactCosts(
                    week_id=week.week_id,
                    job_id=job.job_id,
                    direct_labor=Decimal(str(labor_hours)) * labor_rate,
                    burden=Decimal(str(burden_hours)) * burden_rate,
                    material_cost=Decimal(str(random.randint(500, 15000)))
                )
                db.add(fact)

    db.commit()


def seed_database():
    """Main function to seed the database with sample data."""
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        print("Creating weeks (13 weeks of history)...")
        weeks = create_weeks(db, num_weeks=13)
        print(f"  Created {len(weeks)} weeks")

        print("Creating products (16 product categories)...")
        products = create_products(db)
        print(f"  Created {len(products)} products")

        print("Creating jobs (50 sample jobs)...")
        jobs = create_jobs(db, products, num_jobs=50)
        print(f"  Created {len(jobs)} jobs")

        print("Creating revenue data...")
        create_revenue(db, weeks, products)
        revenue_count = db.query(FactRevenue).count()
        print(f"  Created {revenue_count} revenue records")

        print("Creating cost data...")
        create_costs(db, weeks, jobs)
        cost_count = db.query(FactCosts).count()
        print(f"  Created {cost_count} cost records")

        print("\nSample data seeded successfully!")
        print(f"\nSummary:")
        print(f"  Weeks: {len(weeks)}")
        print(f"  Products: {len(products)}")
        print(f"  Jobs: {len(jobs)}")
        print(f"  Revenue records: {revenue_count}")
        print(f"  Cost records: {cost_count}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

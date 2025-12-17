"""Seed sample data for FOS dashboard testing.

Run this script to populate the database with realistic sample data.
Data structure mirrors Epicor BAQs for easy transition to live data.

BAQ Field Mappings:
- JtecSalesOrderBacklog → Revenue (inbound): OrderHed_OrderNum, OrderDtl_ProdCode, Calculated_OpenValue
- JtecGrossMargin → Revenue (outbound): ShipHead_ShipDate, Calculated_Amount, Calculated_Cost, ProdGrup_Description
- jt_zLaborDtl01 → Labor: LaborDtl_JobNum, LaborDtl_LaborHrs, LaborDtl_BurdenHrs, LaborDtl_PayrollDate, JobAsmbl_JobComplete
- jt_zjobhead01 → Jobs: JobHead_JobNum, JobHead_JobClosed, JobHead_ProdCode, JobHead_PartNum
- jt_zJobMaterial → Material: JobMtl_JobNum, JobMtl_EstUnitCost, JobMtl_RequiredQty, JobMtl_IssuedQty

Usage: python seed_data.py
"""
import random
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction

# =============================================================================
# PRODUCT DATA - Maps to Part.ProdCode + ProdGrup_Description from Epicor
# =============================================================================
# Format: (ProdCode, ProdGrup_Description, Category, TargetMargin)
# ProdCode comes from Part.ProdCode in Epicor (IPS, APS, WPS)
# ProdGrup_Description comes from ProdGrup table
PRODUCTS = [
    # IPS - Industrial Products & Services
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
    # APS - Automation Products & Services
    ("APS", "CarryMatic", "LiftBot", Decimal("0.35")),
    ("APS", "CarryMatic", "MoveBot", Decimal("0.35")),
    ("APS", "CarryMatic", "TugBot", Decimal("0.20")),
    ("APS", "CarryMatic", "Controls", Decimal("0.365")),
    # WPS - Warehouse Products & Services
    ("WPS", "Warehouse Manufactured", "Conveyor - Gravity", Decimal("0.22")),
    ("WPS", "Warehouse Manufactured", "Conveyor - Powered", Decimal("0.22")),
]

# =============================================================================
# SAMPLE PART NUMBERS - Mirrors JobHead_PartNum format from jt_zjobhead01
# =============================================================================
SAMPLE_PARTS = {
    "CarryLite": ["CL-100", "CL-200", "CL-300", "CL-DRUM-01", "CL-KIT-01"],
    "CarryMax": ["CM-500", "CM-600", "CM-LT-100", "CM-LT-200"],
    "CarryMore": ["CMR-1000", "CMR-MC-P", "CMR-MC-NP", "CMR-FBR", "CMR-RH-01"],
    "CarryMatic": ["CMATIC-LB", "CMATIC-MB", "CMATIC-TB", "CMATIC-CTRL"],
    "Warehouse Manufactured": ["WH-CONV-G", "WH-CONV-P", "WH-CONV-G2", "WH-CONV-P2"],
}


def create_weeks(db: Session, num_weeks: int = 13) -> list[DimWeek]:
    """Create dimension weeks for the past N weeks.

    Maps to: ShipHead_ShipDate (outbound) and LaborDtl_PayrollDate (labor)
    Week bucketing based on ISO week number.
    """
    weeks = []
    today = date.today()
    # Start from Monday of current week
    current_monday = today - timedelta(days=today.weekday())

    for i in range(num_weeks):
        week_start = current_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        iso_year, iso_week, _ = week_start.isocalendar()

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
    """Create dimension products.

    Maps to:
    - product_line = Part.ProdCode (IPS, APS, WPS)
    - product_group = ProdGrup_Description
    - category = Part.ClassID or custom category
    """
    products = []
    for prod_code, prod_group, category, margin in PRODUCTS:
        existing = db.query(DimProduct).filter(
            DimProduct.product_group == prod_group,
            DimProduct.category == category
        ).first()
        if existing:
            products.append(existing)
        else:
            product = DimProduct(
                product_line=prod_code,  # Maps to Part.ProdCode
                product_group=prod_group,  # Maps to ProdGrup_Description
                category=category,
                target_margin=margin
            )
            db.add(product)
            db.flush()
            products.append(product)

    db.commit()
    return products


def create_jobs(db: Session, products: list[DimProduct], num_jobs: int = 50) -> list[DimJob]:
    """Create sample jobs linked to products.

    Maps to jt_zjobhead01 BAQ:
    - job_num = JobHead_JobNum (format: starts with 0 or F, e.g., "012345", "F12345")
    - sales_order_num = Linked via JobProd to OrderHed_OrderNum
    - part_num = JobHead_PartNum
    - job_closed = JobHead_JobClosed (FALSE=WIP, TRUE=Completed)
    """
    jobs = []
    # Job numbers start with 0 or F per Epicor convention
    # 0-prefix for standard jobs, F-prefix for field service jobs
    base_order_num = 85000  # Sales orders

    for i in range(num_jobs):
        # Alternate between 0-prefix and F-prefix jobs (70% standard, 30% field service)
        if random.random() < 0.70:
            job_num = f"0{24001 + i}"  # e.g., "024001", "024002"
        else:
            job_num = f"F{24001 + i}"  # e.g., "F24001", "F24002"

        existing = db.query(DimJob).filter(DimJob.job_num == job_num).first()
        if existing:
            jobs.append(existing)
        else:
            product = random.choice(products)

            # Get realistic part number for this product group
            part_options = SAMPLE_PARTS.get(product.product_group, ["PART-001"])
            part_num = random.choice(part_options)

            # JobHead_JobClosed: FALSE=WIP, TRUE=Completed
            # Realistic distribution: ~65% WIP, ~35% Completed
            job_closed = random.random() < 0.35

            job = DimJob(
                job_num=job_num,  # JobHead_JobNum
                sales_order_num=str(base_order_num + i),  # OrderHed_OrderNum
                part_num=part_num,  # JobHead_PartNum
                product_id=product.product_id,
                job_closed=job_closed  # JobHead_JobClosed
            )
            db.add(job)
            db.flush()
            jobs.append(job)

    db.commit()
    return jobs


def create_revenue(db: Session, weeks: list[DimWeek], products: list[DimProduct]):
    """Create sample revenue facts.

    Maps to:
    - INBOUND (orders): JtecSalesOrderBacklog BAQ
      - Calculated_OpenValue = revenue amount
      - OrderDtl_ProdCode = product line
    - OUTBOUND (shipped): JtecGrossMargin BAQ
      - Calculated_Amount = revenue amount
      - Calculated_Cost = cost (for margin calc)
      - ProdGrup_Description = product group
    """
    for week in weeks:
        for product in products:
            # Revenue varies by product line (APS typically higher value)
            if product.product_line == "APS":
                base_inbound = random.randint(25000, 150000)
                base_outbound = random.randint(30000, 175000)
            elif product.product_line == "IPS":
                base_inbound = random.randint(15000, 80000)
                base_outbound = random.randint(20000, 100000)
            else:  # WPS
                base_inbound = random.randint(10000, 60000)
                base_outbound = random.randint(12000, 70000)

            for direction in [Direction.INBOUND, Direction.OUTBOUND]:
                existing = db.query(FactRevenue).filter(
                    FactRevenue.week_id == week.week_id,
                    FactRevenue.product_id == product.product_id,
                    FactRevenue.direction == direction
                ).first()

                if not existing:
                    # Calculated_OpenValue (inbound) or Calculated_Amount (outbound)
                    revenue = base_inbound if direction == Direction.INBOUND else base_outbound
                    fact = FactRevenue(
                        week_id=week.week_id,
                        product_id=product.product_id,
                        direction=direction,
                        revenue=Decimal(str(revenue)),
                        order_count=random.randint(1, 8)
                    )
                    db.add(fact)

    db.commit()


def create_costs(db: Session, weeks: list[DimWeek], jobs: list[DimJob], jobs_per_week: int = 40):
    """Create sample cost facts.

    Maps to jt_zLaborDtl01 BAQ:
    - LaborDtl_LaborHrs = direct labor hours
    - LaborDtl_BurdenHrs = burden hours
    - Labor cost = LaborHrs * ResourceGroup_ProdLabRate (default $45/hr)
    - Burden cost = BurdenHrs * ResourceGroup_ProdBurRate (default $28/hr)

    Maps to jt_zJobMaterial BAQ:
    - Material cost = JobMtl_EstUnitCost * JobMtl_IssuedQty
    """
    # Default rates from ResourceGroup (if not available in BAQ)
    labor_rate = Decimal("45.00")  # ResourceGroup_ProdLabRate
    burden_rate = Decimal("28.00")  # ResourceGroup_ProdBurRate

    for week in weeks:
        # Only some jobs have activity each week (realistic)
        active_jobs = random.sample(jobs, k=min(jobs_per_week, len(jobs)))

        for job in active_jobs:
            existing = db.query(FactCosts).filter(
                FactCosts.week_id == week.week_id,
                FactCosts.job_id == job.job_id
            ).first()

            if not existing:
                # LaborDtl_LaborHrs - typically 4-60 hours per job per week
                labor_hours = Decimal(str(random.randint(4, 60)))

                # LaborDtl_BurdenHrs - usually matches labor hours
                burden_hours = labor_hours

                # Calculate costs from hours * rates
                # ResourceGroup_ProdLabRate, ResourceGroup_ProdBurRate
                direct_labor = labor_hours * labor_rate
                burden = burden_hours * burden_rate

                # Material cost from jt_zJobMaterial
                # JobMtl_EstUnitCost * JobMtl_IssuedQty
                material_cost = Decimal(str(random.randint(200, 8000)))

                fact = FactCosts(
                    week_id=week.week_id,
                    job_id=job.job_id,
                    labor_hours=labor_hours,  # LaborDtl_LaborHrs
                    burden_hours=burden_hours,  # LaborDtl_BurdenHrs
                    direct_labor=direct_labor,
                    burden=burden,
                    material_cost=material_cost
                )
                db.add(fact)

    db.commit()


def seed_database():
    """Main function to seed the database with sample data."""
    print("Initializing database...")
    init_db()

    # Configuration - 13 months of sample data
    NUM_WEEKS = 56  # ~13 months
    NUM_JOBS = 250  # Realistic job count for 13 months
    JOBS_PER_WEEK = 45  # Active jobs per week

    db = SessionLocal()
    try:
        print(f"Creating weeks ({NUM_WEEKS} weeks = ~13 months)...")
        weeks = create_weeks(db, num_weeks=NUM_WEEKS)
        print(f"  Created {len(weeks)} weeks")

        print("Creating products (16 product categories)...")
        print("  Maps to: Part.ProdCode + ProdGrup_Description")
        products = create_products(db)
        print(f"  Created {len(products)} products")

        print(f"Creating jobs ({NUM_JOBS} sample jobs)...")
        print("  Maps to: jt_zjobhead01 (JobHead_JobNum, JobHead_JobClosed)")
        jobs = create_jobs(db, products, num_jobs=NUM_JOBS)
        wip_count = sum(1 for j in jobs if not j.job_closed)
        completed_count = sum(1 for j in jobs if j.job_closed)
        print(f"  Created {len(jobs)} jobs ({wip_count} WIP, {completed_count} Completed)")

        print("Creating revenue data...")
        print("  Maps to: JtecSalesOrderBacklog (inbound), JtecGrossMargin (outbound)")
        create_revenue(db, weeks, products)
        revenue_count = db.query(FactRevenue).count()
        print(f"  Created {revenue_count} revenue records")

        print(f"Creating cost data ({JOBS_PER_WEEK} active jobs/week)...")
        print("  Maps to: jt_zLaborDtl01 (labor), jt_zJobMaterial (material)")
        create_costs(db, weeks, jobs, jobs_per_week=JOBS_PER_WEEK)
        cost_count = db.query(FactCosts).count()
        print(f"  Created {cost_count} cost records")

        print("\n" + "="*60)
        print("Sample data seeded successfully!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  Weeks:           {len(weeks)}")
        print(f"  Products:        {len(products)}")
        print(f"  Jobs:            {len(jobs)} ({wip_count} WIP / {completed_count} Completed)")
        print(f"  Revenue records: {revenue_count}")
        print(f"  Cost records:    {cost_count}")
        print(f"\nBAQ Mappings Ready:")
        print(f"  - JtecSalesOrderBacklog → Revenue (inbound)")
        print(f"  - JtecGrossMargin → Revenue (outbound)")
        print(f"  - jt_zLaborDtl01 → Labor (with JobAsmbl_JobComplete)")
        print(f"  - jt_zjobhead01 → Jobs (JobHead_JobClosed)")
        print(f"  - jt_zJobMaterial → Material costs")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

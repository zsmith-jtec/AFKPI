"""ETL script to load real Epicor data into FOS database.

Pulls data from Epicor Connector at 192.168.50.10:8080 and loads into FOS.
"""
import requests
from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import DimWeek, DimProduct, DimJob, FactRevenue, FactCosts, Direction

EPICOR_CONNECTOR = "http://192.168.50.10:8080"

# Default rates if not in BAQ data
DEFAULT_LABOR_RATE = Decimal("45.00")
DEFAULT_BURDEN_RATE = Decimal("28.00")


def query_baq(baq_name: str, odata_filter: str = None, top: int = 10000) -> list:
    """Query a BAQ from the Epicor Connector."""
    payload = {
        "baq_name": baq_name,
        "user_id": "fos-etl",
        "parameters": {
            "$top": top
        }
    }
    if odata_filter:
        payload["parameters"]["$filter"] = odata_filter

    try:
        resp = requests.post(f"{EPICOR_CONNECTOR}/query", json=payload, timeout=120)
        data = resp.json()
        if data.get("error"):
            print(f"  Error querying {baq_name}: {data.get('message')}")
            return []
        return data.get("records", [])
    except Exception as e:
        print(f"  Exception querying {baq_name}: {e}")
        return []


def get_iso_week(dt: date) -> tuple:
    """Get ISO year and week number from a date."""
    iso = dt.isocalendar()
    return iso[0], iso[1]


def get_week_start(dt: date) -> date:
    """Get Monday of the week containing the date."""
    return dt - timedelta(days=dt.weekday())


def create_weeks_from_data(db: Session, dates: list) -> dict:
    """Create week dimension from actual dates in data."""
    weeks = {}
    for dt in dates:
        if not dt:
            continue
        week_start = get_week_start(dt)
        if week_start in weeks:
            continue

        iso_year, iso_week = get_iso_week(week_start)
        week_end = week_start + timedelta(days=6)

        existing = db.query(DimWeek).filter(DimWeek.week_start == week_start).first()
        if existing:
            weeks[week_start] = existing
        else:
            week = DimWeek(
                week_start=week_start,
                week_end=week_end,
                iso_year=iso_year,
                iso_week=iso_week
            )
            db.add(week)
            db.flush()
            weeks[week_start] = week

    db.commit()
    return weeks


def parse_date(date_str: str) -> date:
    """Parse ISO date string to date object."""
    if not date_str:
        return None
    try:
        # Handle ISO format: "2025-12-17T00:00:00-06:00"
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
    except:
        return None


def load_jobs(db: Session) -> dict:
    """Load jobs from jt_zjobhead01 BAQ."""
    print("Loading jobs from jt_zjobhead01 (2024+)...")
    # Filter to 2024+ jobs and get more records
    records = query_baq(
        "jt_zjobhead01",
        odata_filter="JobHead_StartDate ge 2024-01-01T00:00:00Z",
        top=50000
    )
    print(f"  Retrieved {len(records)} job records")

    jobs = {}
    prod_codes = set()
    skipped_uf = 0

    for rec in records:
        job_num = rec.get("JobHead_JobNum", "")
        if not job_num:
            continue

        # Skip UF (unfirm) jobs - these are planned, not actual
        if job_num.startswith("UF"):
            skipped_uf += 1
            continue

        prod_code = rec.get("JobHead_ProdCode", "OTHER")
        prod_codes.add(prod_code)

        # Find or create product (simplified - group by ProdCode)
        product = db.query(DimProduct).filter(
            DimProduct.product_line == prod_code
        ).first()

        if not product:
            product = DimProduct(
                product_line=prod_code,
                product_group=prod_code,
                category="General",
                target_margin=Decimal("0.25")
            )
            db.add(product)
            db.flush()

        existing = db.query(DimJob).filter(DimJob.job_num == job_num).first()
        if existing:
            jobs[job_num] = existing
        else:
            job = DimJob(
                job_num=job_num,
                sales_order_num=None,  # Would need JobProd join
                part_num=rec.get("JobHead_PartNum"),
                product_id=product.product_id,
                job_closed=rec.get("JobHead_JobClosed", False)
            )
            db.add(job)
            db.flush()
            jobs[job_num] = job

    db.commit()
    print(f"  Created/updated {len(jobs)} jobs")
    print(f"  Skipped {skipped_uf} UF (unfirm) jobs")
    print(f"  Product codes found: {prod_codes}")
    return jobs


def load_labor(db: Session, jobs: dict, weeks: dict):
    """Load labor data from jt_zLaborDtl01 BAQ."""
    print("Loading labor from jt_zLaborDtl01 (2024+)...")
    # Filter to 2024+ data for relevance
    records = query_baq(
        "jt_zLaborDtl01",
        odata_filter="LaborDtl_PayrollDate ge 2024-01-01T00:00:00Z",
        top=50000
    )
    print(f"  Retrieved {len(records)} labor records")

    # Aggregate by job + week
    labor_data = defaultdict(lambda: {
        "labor_hours": Decimal("0"),
        "burden_hours": Decimal("0"),
        "direct_labor": Decimal("0"),
        "burden": Decimal("0")
    })

    dates_found = []
    for rec in records:
        job_num = rec.get("LaborDtl_JobNum", "")
        labor_date = parse_date(rec.get("LaborDtl_PayrollDate") or rec.get("LaborDtl_ClockInDate"))

        if not job_num or not labor_date:
            continue

        dates_found.append(labor_date)
        week_start = get_week_start(labor_date)

        labor_hrs = Decimal(str(rec.get("LaborDtl_LaborHrs", 0) or 0))
        burden_hrs = Decimal(str(rec.get("LaborDtl_BurdenHrs", 0) or 0))

        key = (job_num, week_start)
        labor_data[key]["labor_hours"] += labor_hrs
        labor_data[key]["burden_hours"] += burden_hrs
        labor_data[key]["direct_labor"] += labor_hrs * DEFAULT_LABOR_RATE
        labor_data[key]["burden"] += burden_hrs * DEFAULT_BURDEN_RATE

    # Create weeks from labor dates
    if dates_found:
        weeks.update(create_weeks_from_data(db, dates_found))

    # Create cost records
    created = 0
    for (job_num, week_start), data in labor_data.items():
        job = jobs.get(job_num)
        week = weeks.get(week_start)

        if not job or not week:
            continue

        existing = db.query(FactCosts).filter(
            FactCosts.job_id == job.job_id,
            FactCosts.week_id == week.week_id
        ).first()

        if not existing:
            cost = FactCosts(
                week_id=week.week_id,
                job_id=job.job_id,
                labor_hours=data["labor_hours"],
                burden_hours=data["burden_hours"],
                direct_labor=data["direct_labor"],
                burden=data["burden"],
                material_cost=Decimal("0")  # From jt_zJobMaterial
            )
            db.add(cost)
            created += 1

    db.commit()
    print(f"  Created {created} cost records")


def load_revenue(db: Session, weeks: dict):
    """Load revenue from JtecGrossMargin (outbound) and JtecSalesOrderBacklog (inbound)."""
    print("Loading revenue from JtecGrossMargin (2024+)...")
    margin_records = query_baq(
        "JtecGrossMargin",
        odata_filter="ShipHead_ShipDate ge 2024-01-01T00:00:00Z",
        top=50000
    )
    print(f"  Retrieved {len(margin_records)} margin records")

    # Get products for grouping
    products = {p.product_group: p for p in db.query(DimProduct).all()}

    # Aggregate outbound revenue by product group + week
    revenue_data = defaultdict(lambda: {
        "inbound": Decimal("0"),
        "outbound": Decimal("0"),
        "order_count": 0
    })

    dates_found = []
    for rec in margin_records:
        ship_date = parse_date(rec.get("ShipHead_ShipDate"))
        if not ship_date:
            continue

        dates_found.append(ship_date)
        week_start = get_week_start(ship_date)
        prod_group = rec.get("ProdGrup_Description") or "Other"

        amount = Decimal(str(rec.get("Calculated_Amount", 0) or 0))

        key = (prod_group, week_start)
        revenue_data[key]["outbound"] += amount
        revenue_data[key]["order_count"] += 1

    # Create weeks
    if dates_found:
        weeks.update(create_weeks_from_data(db, dates_found))

    # Create revenue records
    created = 0
    for (prod_group, week_start), data in revenue_data.items():
        week = weeks.get(week_start)
        if not week:
            continue

        # Find or create product
        product = products.get(prod_group)
        if not product:
            product = DimProduct(
                product_line="OTHER",
                product_group=prod_group,
                category="General",
                target_margin=Decimal("0.25")
            )
            db.add(product)
            db.flush()
            products[prod_group] = product

        # Create outbound revenue
        existing = db.query(FactRevenue).filter(
            FactRevenue.week_id == week.week_id,
            FactRevenue.product_id == product.product_id,
            FactRevenue.direction == Direction.OUTBOUND
        ).first()

        if not existing and data["outbound"] > 0:
            rev = FactRevenue(
                week_id=week.week_id,
                product_id=product.product_id,
                direction=Direction.OUTBOUND,
                revenue=data["outbound"],
                order_count=data["order_count"]
            )
            db.add(rev)
            created += 1

    db.commit()
    print(f"  Created {created} revenue records")


def run_etl():
    """Main ETL function."""
    print("=" * 60)
    print("FOS ETL - Loading Real Epicor Data")
    print("=" * 60)
    print(f"Connector: {EPICOR_CONNECTOR}")
    print()

    # Initialize fresh database
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        weeks = {}

        # Load jobs first (creates products too)
        jobs = load_jobs(db)

        # Load labor data
        load_labor(db, jobs, weeks)

        # Load revenue
        load_revenue(db, weeks)

        # Summary
        print()
        print("=" * 60)
        print("ETL Complete!")
        print("=" * 60)
        print(f"Weeks:    {db.query(DimWeek).count()}")
        print(f"Products: {db.query(DimProduct).count()}")
        print(f"Jobs:     {db.query(DimJob).count()}")
        print(f"Revenue:  {db.query(FactRevenue).count()}")
        print(f"Costs:    {db.query(FactCosts).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    run_etl()

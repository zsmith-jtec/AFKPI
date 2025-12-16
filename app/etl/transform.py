"""ETL Transform - Clean, aggregate, and calculate metrics."""
import pandas as pd
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_iso_week(d: date) -> Tuple[int, int]:
    """Get ISO year and week number from a date."""
    iso = d.isocalendar()
    return iso[0], iso[1]


def get_week_bounds(d: date) -> Tuple[date, date]:
    """Get Monday and Sunday of the week containing the date."""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def parse_date(value) -> Optional[date]:
    """Parse various date formats to a date object."""
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value if isinstance(value, date) else value.date()
    if isinstance(value, str):
        # Try common formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def aggregate_revenue_by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue data by week and product group."""
    # Parse dates
    date_col = "OrderDate" if "OrderDate" in df.columns else "ShipDate"
    df["parsed_date"] = df[date_col].apply(parse_date)
    df = df.dropna(subset=["parsed_date"])

    # Add week info
    df["iso_year"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[0])
    df["iso_week"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[1])
    df["week_start"] = df["parsed_date"].apply(lambda d: get_week_bounds(d)[0])

    # Determine direction (inbound = open order, outbound = shipped/closed)
    if "OpenOrder" in df.columns:
        df["direction"] = df["OpenOrder"].apply(lambda x: "inbound" if x else "outbound")
    else:
        df["direction"] = "outbound"  # Default assumption

    # Ensure numeric revenue
    df["revenue"] = pd.to_numeric(df.get("DocExtPrice", 0), errors="coerce").fillna(0)

    # Get product mapping
    df["product_group"] = df.get("ProdCode", "Unknown")
    df["category"] = df.get("PartClass", "Unknown")

    # Aggregate
    agg = df.groupby(
        ["iso_year", "iso_week", "week_start", "product_group", "category", "direction"]
    ).agg(
        revenue=("revenue", "sum"),
        order_count=("OrderNum", "nunique")
    ).reset_index()

    logger.info(f"Aggregated revenue: {len(agg)} rows")
    return agg


def aggregate_labor_by_week(df: pd.DataFrame, rate_table: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Aggregate labor data by week and job."""
    # Parse dates
    date_col = "LaborDate" if "LaborDate" in df.columns else "ClockInDate"
    df["parsed_date"] = df[date_col].apply(parse_date)
    df = df.dropna(subset=["parsed_date"])

    # Add week info
    df["iso_year"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[0])
    df["iso_week"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[1])
    df["week_start"] = df["parsed_date"].apply(lambda d: get_week_bounds(d)[0])

    # Ensure numeric hours
    df["labor_hrs"] = pd.to_numeric(df.get("LaborHrs", 0), errors="coerce").fillna(0)
    df["burden_hrs"] = pd.to_numeric(df.get("BurdenHrs", 0), errors="coerce").fillna(0)

    # Get rates (use defaults if not provided)
    default_labor_rate = Decimal("45.00")
    default_burden_rate = Decimal("28.00")

    if rate_table is not None and "ResourceGrp" in df.columns:
        # Join rate table by resource group
        rate_dict = rate_table.set_index("ResourceGrp")[["LaborRate", "BurdenRate"]].to_dict("index")
        df["labor_rate"] = df["ResourceGrp"].apply(
            lambda x: rate_dict.get(x, {}).get("LaborRate", float(default_labor_rate))
        )
        df["burden_rate"] = df["ResourceGrp"].apply(
            lambda x: rate_dict.get(x, {}).get("BurdenRate", float(default_burden_rate))
        )
    else:
        df["labor_rate"] = float(default_labor_rate)
        df["burden_rate"] = float(default_burden_rate)

    # Calculate costs
    df["direct_labor_cost"] = df["labor_hrs"] * df["labor_rate"]
    df["burden_cost"] = df["burden_hrs"] * df["burden_rate"]

    # Aggregate by week and job
    agg = df.groupby(
        ["iso_year", "iso_week", "week_start", "JobNum"]
    ).agg(
        direct_labor=("direct_labor_cost", "sum"),
        burden=("burden_cost", "sum"),
        labor_hours=("labor_hrs", "sum"),
        burden_hours=("burden_hrs", "sum")
    ).reset_index()

    logger.info(f"Aggregated labor: {len(agg)} rows")
    return agg


def aggregate_material_by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate material costs by week and job."""
    # Parse dates
    date_col = "IssueDate" if "IssueDate" in df.columns else "TranDate"
    df["parsed_date"] = df[date_col].apply(parse_date)
    df = df.dropna(subset=["parsed_date"])

    # Add week info
    df["iso_year"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[0])
    df["iso_week"] = df["parsed_date"].apply(lambda d: get_iso_week(d)[1])
    df["week_start"] = df["parsed_date"].apply(lambda d: get_week_bounds(d)[0])

    # Ensure numeric cost
    df["material_cost"] = pd.to_numeric(df.get("ExtCost", 0), errors="coerce").fillna(0)

    # Aggregate by week and job
    agg = df.groupby(
        ["iso_year", "iso_week", "week_start", "JobNum"]
    ).agg(
        material_cost=("material_cost", "sum")
    ).reset_index()

    logger.info(f"Aggregated material: {len(agg)} rows")
    return agg


def load_target_margins(file_path: str) -> Dict[Tuple[str, str], Decimal]:
    """Load target gross margins from Corp. Mapping file."""
    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)

    # Handle the structure of Corp. Mapping file
    # Expected columns: Product Line, Product Group (Unnamed:2), Category, Jtec US Margin
    margins = {}

    current_group = None
    for _, row in df.iterrows():
        # Check if this row has a product group
        if pd.notna(row.get("Unnamed: 2")) and str(row.get("Unnamed: 2")).strip() not in ["x", "X", ""]:
            current_group = str(row.get("Unnamed: 2")).strip()

        # Check if this row has a category and margin
        category = row.get("Category")
        margin = row.get("Jtec US Margin")

        if pd.notna(category) and pd.notna(margin) and current_group:
            try:
                margin_val = Decimal(str(margin))
                margins[(current_group, str(category))] = margin_val
            except:
                pass

    logger.info(f"Loaded {len(margins)} target margins")
    return margins


def calculate_gross_margin(revenue: Decimal, cost: Decimal) -> Tuple[Decimal, Decimal]:
    """Calculate gross margin (absolute and percentage)."""
    margin = revenue - cost
    if revenue and revenue > 0:
        margin_pct = (margin / revenue) * 100
    else:
        margin_pct = Decimal("0")
    return margin, margin_pct.quantize(Decimal("0.01"))

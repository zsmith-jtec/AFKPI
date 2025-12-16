"""ETL Ingest - Load CSV/Excel files into staging dataframes."""
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def load_csv(file_path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    logger.info(f"Loading CSV: {file_path}")
    df = pd.read_csv(file_path, encoding=encoding)
    logger.info(f"Loaded {len(df)} rows from {file_path.name}")
    return df


def load_excel(file_path: Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Load an Excel file into a DataFrame."""
    logger.info(f"Loading Excel: {file_path}")
    df = pd.read_excel(file_path, sheet_name=sheet_name or 0)
    logger.info(f"Loaded {len(df)} rows from {file_path.name}")
    return df


def detect_file_type(file_path: Path) -> str:
    """Detect file type from extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    elif suffix in [".xlsx", ".xls"]:
        return "excel"
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def load_file(file_path: Path) -> pd.DataFrame:
    """Load a file (CSV or Excel) into a DataFrame."""
    file_type = detect_file_type(file_path)
    if file_type == "csv":
        return load_csv(file_path)
    else:
        return load_excel(file_path)


def validate_columns(df: pd.DataFrame, required_columns: list, file_name: str) -> bool:
    """Validate that required columns exist in the DataFrame."""
    missing = set(required_columns) - set(df.columns)
    if missing:
        logger.error(f"Missing columns in {file_name}: {missing}")
        return False
    return True


# Expected columns for each BAQ export type
REVENUE_COLUMNS = [
    "OrderNum", "OrderDate", "PartNum", "ProdCode", "PartClass",
    "DocExtPrice", "OpenOrder"
]

LABOR_COLUMNS = [
    "JobNum", "LaborDate", "ResourceGrp", "LaborHrs", "BurdenHrs",
    "LaborRate", "BurdenRate"
]

JOB_COLUMNS = [
    "JobNum", "OrderNum", "PartNum", "ProdCode"
]

MATERIAL_COLUMNS = [
    "JobNum", "IssueDate", "ExtCost"
]


def load_revenue_export(file_path: Path) -> pd.DataFrame:
    """Load and validate a revenue BAQ export."""
    df = load_file(file_path)

    # Try to map common column variations
    column_mapping = {
        "Order_OrderNum": "OrderNum",
        "Order_OrderDate": "OrderDate",
        "Part_PartNum": "PartNum",
        "Part_ProdCode": "ProdCode",
        "Part_PartClass": "PartClass",
        "OrderDtl_DocExtPriceDtl": "DocExtPrice",
        "OrderHed_OpenOrder": "OpenOrder",
    }
    df = df.rename(columns=column_mapping)

    # Check for required columns (be flexible)
    core_columns = ["OrderNum", "DocExtPrice"]
    if not validate_columns(df, core_columns, file_path.name):
        logger.warning(f"Revenue file may be missing key columns. Available: {list(df.columns)}")

    return df


def load_labor_export(file_path: Path) -> pd.DataFrame:
    """Load and validate a labor BAQ export."""
    df = load_file(file_path)

    column_mapping = {
        "LaborDtl_JobNum": "JobNum",
        "LaborDtl_ClockInDate": "LaborDate",
        "LaborDtl_ResourceGrpID": "ResourceGrp",
        "LaborDtl_LaborHrs": "LaborHrs",
        "LaborDtl_BurdenHrs": "BurdenHrs",
    }
    df = df.rename(columns=column_mapping)

    core_columns = ["JobNum", "LaborHrs"]
    if not validate_columns(df, core_columns, file_path.name):
        logger.warning(f"Labor file may be missing key columns. Available: {list(df.columns)}")

    return df


def load_job_export(file_path: Path) -> pd.DataFrame:
    """Load and validate a job BAQ export."""
    df = load_file(file_path)

    column_mapping = {
        "JobHead_JobNum": "JobNum",
        "JobHead_OrderNum": "OrderNum",
        "JobHead_PartNum": "PartNum",
        "Part_ProdCode": "ProdCode",
    }
    df = df.rename(columns=column_mapping)

    core_columns = ["JobNum"]
    if not validate_columns(df, core_columns, file_path.name):
        logger.warning(f"Job file may be missing key columns. Available: {list(df.columns)}")

    return df


def load_material_export(file_path: Path) -> pd.DataFrame:
    """Load and validate a material cost BAQ export."""
    df = load_file(file_path)

    column_mapping = {
        "JobMtl_JobNum": "JobNum",
        "JobMtl_IssueDate": "IssueDate",
        "JobMtl_ExtCost": "ExtCost",
    }
    df = df.rename(columns=column_mapping)

    core_columns = ["JobNum", "ExtCost"]
    if not validate_columns(df, core_columns, file_path.name):
        logger.warning(f"Material file may be missing key columns. Available: {list(df.columns)}")

    return df

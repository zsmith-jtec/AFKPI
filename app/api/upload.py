"""File Upload API - Upload Excel/CSV files from Epicor BAQ exports."""

import io
import pandas as pd
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.schemas import UserInfo

# ETL functions
from app.etl.transform import (
    aggregate_revenue_by_week,
    aggregate_labor_by_week,
    aggregate_material_by_week,
)
from app.etl.loader import load_revenue, load_costs

router = APIRouter()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an Excel/CSV file and process it into the database.

    Args:
        file: The uploaded file (Excel or CSV)
        file_type: Type of data - "revenue", "labor", "jobs", "material"
        current_user: JWT authenticated user
        db: Database session

    Returns:
        Processing results with row counts
    """
    # Validate file type parameter
    valid_types = ["revenue", "labor", "jobs", "material"]
    if file_type not in valid_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid file_type. Must be one of: {valid_types}"
        )

    # Validate file extension
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Must be CSV or Excel (.csv, .xlsx, .xls)",
        )

    try:
        # Read file content
        content = await file.read()

        # Load into DataFrame
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")

        # Log available columns for debugging
        columns = list(df.columns)

        # Process based on file type
        result = {
            "success": True,
            "file_type": file_type,
            "filename": filename,
            "columns_found": columns,
            "rows_in_file": len(df),
            "rows_processed": 0,
            "message": "",
        }

        if file_type == "revenue":
            result = process_revenue(df, db, current_user.email, result)
        elif file_type == "labor":
            result = process_labor(df, db, current_user.email, result)
        elif file_type == "jobs":
            result = process_jobs(df, db, current_user.email, result)
        elif file_type == "material":
            result = process_material(df, db, current_user.email, result)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def process_revenue(
    df: pd.DataFrame, db: Session, user_email: str, result: dict
) -> dict:
    """Process revenue upload."""
    # Try to map columns
    column_mapping = {
        "Order_OrderNum": "OrderNum",
        "OrderHed_OrderNum": "OrderNum",
        "Order_OrderDate": "OrderDate",
        "OrderHed_OrderDate": "OrderDate",
        "Part_PartNum": "PartNum",
        "OrderDtl_PartNum": "PartNum",
        "Part_ProdCode": "ProdCode",
        "OrderDtl_ProdCode": "ProdCode",
        "Part_PartClass": "PartClass",
        "OrderDtl_DocExtPriceDtl": "DocExtPrice",
        "OrderHed_OpenOrder": "OpenOrder",
    }
    df = df.rename(columns=column_mapping)

    # Check for required columns
    required = ["DocExtPrice"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        result["success"] = False
        result["message"] = (
            f"Missing required columns: {missing}. Found: {list(df.columns)}"
        )
        return result

    # Aggregate by week
    try:
        aggregated = aggregate_revenue_by_week(df)
        rows = load_revenue(db, aggregated, user_email=user_email)
        result["rows_processed"] = rows
        result["message"] = f"Successfully loaded {rows} revenue records"
    except Exception as e:
        result["success"] = False
        result["message"] = f"Error aggregating revenue: {str(e)}"

    return result


def process_labor(df: pd.DataFrame, db: Session, user_email: str, result: dict) -> dict:
    """Process labor upload."""
    # Try to map columns
    column_mapping = {
        "LaborDtl_JobNum": "JobNum",
        "LaborDtl_ClockInDate": "LaborDate",
        "LaborDtl_ResourceGrpID": "ResourceGrp",
        "LaborDtl_LaborHrs": "LaborHrs",
        "LaborDtl_BurdenHrs": "BurdenHrs",
    }
    df = df.rename(columns=column_mapping)

    # Check for required columns
    required = ["JobNum", "LaborHrs"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        result["success"] = False
        result["message"] = (
            f"Missing required columns: {missing}. Found: {list(df.columns)}"
        )
        return result

    # Aggregate by week
    try:
        aggregated = aggregate_labor_by_week(df)
        rows = load_costs(db, aggregated, user_email=user_email)
        result["rows_processed"] = rows
        result["message"] = f"Successfully loaded {rows} labor records"
    except Exception as e:
        result["success"] = False
        result["message"] = f"Error aggregating labor: {str(e)}"

    return result


def process_jobs(df: pd.DataFrame, db: Session, user_email: str, result: dict) -> dict:
    """Process jobs upload - updates job dimension table."""
    # Try to map columns
    column_mapping = {
        "JobHead_JobNum": "JobNum",
        "JobHead_OrderNum": "OrderNum",
        "JobHead_PartNum": "PartNum",
        "Part_ProdCode": "ProdCode",
    }
    df = df.rename(columns=column_mapping)

    # Check for required columns
    if "JobNum" not in df.columns:
        result["success"] = False
        result["message"] = (
            f"Missing required column: JobNum. Found: {list(df.columns)}"
        )
        return result

    # Store job info for later use
    result["rows_processed"] = len(df)
    result["message"] = (
        f"Found {len(df)} jobs. Job data is used when processing labor uploads."
    )
    result["note"] = "Upload labor file after jobs to link job details."

    return result


def process_material(
    df: pd.DataFrame, db: Session, user_email: str, result: dict
) -> dict:
    """Process material cost upload."""
    # Try to map columns
    column_mapping = {
        "JobMtl_JobNum": "JobNum",
        "JobMtl_IssueDate": "IssueDate",
        "JobMtl_ExtCost": "ExtCost",
    }
    df = df.rename(columns=column_mapping)

    # Check for required columns
    required = ["JobNum", "ExtCost"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        result["success"] = False
        result["message"] = (
            f"Missing required columns: {missing}. Found: {list(df.columns)}"
        )
        return result

    # Aggregate by week
    try:
        aggregated = aggregate_material_by_week(df)
        result["rows_processed"] = len(aggregated)
        result["message"] = (
            f"Found {len(aggregated)} material cost records. Upload labor file to combine."
        )
    except Exception as e:
        result["success"] = False
        result["message"] = f"Error aggregating material: {str(e)}"

    return result


@router.get("/columns")
async def get_expected_columns():
    """Return expected column names for each file type."""
    return {
        "revenue": {
            "required": ["DocExtPrice"],
            "recommended": [
                "OrderNum",
                "OrderDate",
                "PartNum",
                "ProdCode",
                "PartClass",
                "OpenOrder",
            ],
            "notes": "Revenue value should be in DocExtPrice column",
        },
        "labor": {
            "required": ["JobNum", "LaborHrs"],
            "recommended": [
                "LaborDate",
                "ResourceGrp",
                "BurdenHrs",
                "LaborRate",
                "BurdenRate",
            ],
            "notes": "Labor hours per job",
        },
        "jobs": {
            "required": ["JobNum"],
            "recommended": ["OrderNum", "PartNum", "ProdCode"],
            "notes": "Links jobs to sales orders and product codes",
        },
        "material": {
            "required": ["JobNum", "ExtCost"],
            "recommended": ["IssueDate"],
            "notes": "Material costs per job",
        },
    }

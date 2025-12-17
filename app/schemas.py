"""Pydantic schemas for API request/response validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from enum import Enum


class DirectionEnum(str, Enum):
    """Revenue direction enum for API."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ============ WEEK SCHEMAS ============

class WeekBase(BaseModel):
    """Base schema for week."""
    week_start: date
    week_end: date
    iso_year: int
    iso_week: int


class WeekRead(WeekBase):
    """Week response schema."""
    week_id: int
    model_config = ConfigDict(from_attributes=True)


class WeekSummary(BaseModel):
    """Simplified week for dropdowns."""
    week_id: int
    iso_year: int
    iso_week: int
    label: str  # e.g., "2025-W51"


class MonthSummary(BaseModel):
    """Simplified month for dropdowns."""
    year: int
    month: int
    label: str  # e.g., "Dec 2025"
    week_ids: List[int]  # Week IDs that fall within this month


# ============ PRODUCT SCHEMAS ============

class ProductBase(BaseModel):
    """Base schema for product."""
    product_line: str
    product_group: str
    category: str
    target_margin: Optional[Decimal] = None


class ProductRead(ProductBase):
    """Product response schema."""
    product_id: int
    model_config = ConfigDict(from_attributes=True)


# ============ JOB SCHEMAS ============

class JobBase(BaseModel):
    """Base schema for job."""
    job_num: str
    sales_order_num: Optional[str] = None
    part_num: Optional[str] = None


class JobRead(JobBase):
    """Job response schema."""
    job_id: int
    product_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class JobDetail(JobRead):
    """Job with cost details for drill-down."""
    direct_labor: Decimal = Decimal("0")
    burden: Decimal = Decimal("0")
    material_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    revenue: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    product_group: Optional[str] = None
    category: Optional[str] = None


# ============ REVENUE SCHEMAS ============

class RevenueByProduct(BaseModel):
    """Revenue aggregated by product group (combined inbound/outbound)."""
    product_group: str
    inbound: Decimal = Decimal("0")
    outbound: Decimal = Decimal("0")
    order_count: int = 0
    target_margin: Optional[Decimal] = None


class RevenueByWeek(BaseModel):
    """Revenue for a specific week."""
    week_id: int
    iso_year: int
    iso_week: int
    inbound_revenue: Decimal
    outbound_revenue: Decimal
    total_revenue: Decimal


class RevenueSummary(BaseModel):
    """Revenue summary response."""
    week: WeekSummary
    by_product: List[RevenueByProduct]
    total_inbound: Decimal
    total_outbound: Decimal


# ============ MARGIN SCHEMAS ============

class MarginByProduct(BaseModel):
    """Gross margin by product group."""
    product_group: str
    revenue: Decimal
    total_cost: Decimal
    gross_margin: Decimal  # Revenue - Cost
    margin_percent: Decimal  # (Revenue - Cost) / Revenue * 100
    target_margin: Optional[Decimal] = None
    variance: Optional[Decimal] = None  # Actual - Target


class MarginTrend(BaseModel):
    """Margin trend over time."""
    week_id: int
    iso_year: int
    iso_week: int
    label: str
    revenue: Decimal
    total_cost: Decimal
    gross_margin: Decimal
    margin_percent: Decimal


class MarginSummary(BaseModel):
    """Margin summary response."""
    week: WeekSummary
    by_product: List[MarginByProduct]
    total_revenue: Decimal
    total_cost: Decimal
    overall_margin: Decimal
    overall_margin_percent: Decimal


# ============ LABOR SCHEMAS ============

class LaborByJob(BaseModel):
    """Labor costs by job - maps to jt_zLaborDtl01 BAQ."""
    job_num: str
    sales_order_num: Optional[str]
    product_group: Optional[str] = None
    job_closed: bool = False  # False=WIP, True=Completed (JobAsmbl_JobComplete)
    labor_hours: Decimal = Decimal("0")  # LaborDtl_LaborHrs
    burden_hours: Decimal = Decimal("0")  # LaborDtl_BurdenHrs
    direct_labor: Decimal  # labor_hours * ResourceGroup_ProdLabRate
    burden: Decimal  # burden_hours * ResourceGroup_ProdBurRate
    total_labor: Decimal


class LaborSummary(BaseModel):
    """Labor summary response - maps to jt_zLaborDtl01 BAQ."""
    week: WeekSummary
    total_labor_hours: Decimal = Decimal("0")  # Sum of LaborDtl_LaborHrs
    total_burden_hours: Decimal = Decimal("0")  # Sum of LaborDtl_BurdenHrs
    total_direct_labor: Decimal  # Sum of labor costs
    total_burden: Decimal  # Sum of burden costs
    total_labor_cost: Decimal  # total_direct_labor + total_burden
    job_count: int
    by_job: List[LaborByJob]


# ============ FORECAST SCHEMAS ============

class ForecastPoint(BaseModel):
    """Single forecast data point."""
    iso_year: int
    iso_week: int
    label: str
    predicted: Decimal
    lower_bound: Decimal
    upper_bound: Decimal


class ForecastResponse(BaseModel):
    """Forecast response with historical and predicted values."""
    metric: str  # "margin", "revenue", etc.
    historical: List[MarginTrend]
    forecast: List[ForecastPoint]


# ============ DRILL-DOWN SCHEMAS ============

class DrillCategory(BaseModel):
    """Category level drill-down."""
    category: str
    revenue: Decimal
    cost: Decimal
    margin: Decimal
    margin_percent: Decimal
    job_count: int


class DrillProductGroup(BaseModel):
    """Product group drill-down response."""
    product_group: str
    total_revenue: Decimal
    total_cost: Decimal
    total_margin: Decimal
    margin_percent: Decimal
    categories: List[DrillCategory]


# ============ AUTH SCHEMAS ============

class TokenRequest(BaseModel):
    """Login request."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """Current user info."""
    email: str
    name: str
    role: str


# ============ AUDIT SCHEMAS ============

class AuditEntry(BaseModel):
    """Audit log entry."""
    log_id: int
    timestamp: datetime
    user_email: str
    action: str
    entity: Optional[str]
    details: Optional[str]
    model_config = ConfigDict(from_attributes=True)


# ============ UPLOAD SCHEMAS ============

class UploadResponse(BaseModel):
    """Response after CSV upload."""
    status: str
    rows_processed: int
    week_start: date
    week_end: date
    message: str

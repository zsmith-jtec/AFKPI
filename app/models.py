"""SQLAlchemy ORM models for FOS database."""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Boolean,
    ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class Direction(enum.Enum):
    """Revenue direction - inbound (orders) or outbound (shipped)."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ============ DIMENSION TABLES ============

class DimWeek(Base):
    """Week dimension table for time-series analysis."""
    __tablename__ = "dim_week"

    week_id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(Date, nullable=False, unique=True)
    week_end = Column(Date, nullable=False)
    iso_year = Column(Integer, nullable=False)
    iso_week = Column(Integer, nullable=False)

    # Relationships
    revenues = relationship("FactRevenue", back_populates="week")
    costs = relationship("FactCosts", back_populates="week")


class DimProduct(Base):
    """Product dimension with hierarchy: Line > Group > Category."""
    __tablename__ = "dim_product"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_line = Column(String(50), nullable=False)  # IPS, APS, WPS
    product_group = Column(String(100), nullable=False)  # CarryMore, CarryMatic, etc.
    category = Column(String(100), nullable=False)  # Custom Cart, LiftBot, etc.
    target_margin = Column(Numeric(5, 4), nullable=True)  # e.g., 0.3000 for 30%

    # Relationships
    revenues = relationship("FactRevenue", back_populates="product")
    jobs = relationship("DimJob", back_populates="product")


class DimJob(Base):
    """Job dimension linking jobs to sales orders and products."""
    __tablename__ = "dim_job"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_num = Column(String(50), nullable=False, unique=True)
    sales_order_num = Column(String(50), nullable=True)
    part_num = Column(String(100), nullable=True)
    product_id = Column(Integer, ForeignKey("dim_product.product_id"), nullable=True)
    job_closed = Column(Boolean, default=False)  # False=WIP, True=Completed

    # Relationships
    product = relationship("DimProduct", back_populates="jobs")
    costs = relationship("FactCosts", back_populates="job")


# ============ FACT TABLES ============

class FactRevenue(Base):
    """Revenue fact table - weekly revenue by product and direction."""
    __tablename__ = "fact_revenue"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    week_id = Column(Integer, ForeignKey("dim_week.week_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("dim_product.product_id"), nullable=False)
    direction = Column(SQLEnum(Direction), nullable=False)
    revenue = Column(Numeric(18, 2), nullable=False, default=0)
    order_count = Column(Integer, nullable=False, default=0)

    # Relationships
    week = relationship("DimWeek", back_populates="revenues")
    product = relationship("DimProduct", back_populates="revenues")


class FactCosts(Base):
    """Costs fact table - weekly costs by job.

    Maps to jt_zLaborDtl01 and jt_zJobMaterial BAQs.
    """
    __tablename__ = "fact_costs"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    week_id = Column(Integer, ForeignKey("dim_week.week_id"), nullable=False)
    job_id = Column(Integer, ForeignKey("dim_job.job_id"), nullable=False)

    # Labor hours from LaborDtl_LaborHrs, LaborDtl_BurdenHrs
    labor_hours = Column(Numeric(10, 2), nullable=False, default=0)
    burden_hours = Column(Numeric(10, 2), nullable=False, default=0)

    # Labor costs = hours * rate (ResourceGroup_ProdLabRate, ResourceGroup_ProdBurRate)
    direct_labor = Column(Numeric(18, 2), nullable=False, default=0)
    burden = Column(Numeric(18, 2), nullable=False, default=0)

    # Material from jt_zJobMaterial (EstUnitCost * IssuedQty)
    material_cost = Column(Numeric(18, 2), nullable=False, default=0)

    # Relationships
    week = relationship("DimWeek", back_populates="costs")
    job = relationship("DimJob", back_populates="costs")

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost (labor + burden + material)."""
        return (self.direct_labor or 0) + (self.burden or 0) + (self.material_cost or 0)


# ============ AUDIT TABLE ============

class AuditLog(Base):
    """Audit log for tracking all data changes and user actions."""
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_email = Column(String(255), nullable=False)
    action = Column(String(50), nullable=False)  # LOGIN, UPLOAD, VIEW, EXPORT
    entity = Column(String(100), nullable=True)  # e.g., "revenue", "margin"
    details = Column(Text, nullable=True)  # JSON string with additional info

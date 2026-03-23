from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from .product import PriceData, SupplyDemandData, ProfitAnalysis

class ReportBase(BaseModel):
    title: str
    period_start: date
    period_end: date

class ReportCreate(ReportBase):
    products: Optional[List[str]] = []
    include_forecast: bool = True
    custom_prompt: Optional[str] = None

class Report(ReportBase):
    id: str
    created_at: datetime
    status: str
    progress: Optional[int] = 0
    total_rows: Optional[int] = 0
    processed_rows: Optional[int] = 0
    file_path: Optional[str] = None
    html_content: Optional[str] = None
    pdf_path: Optional[str] = None
    word_path: Optional[str] = None
    
    # Analysis results can be embedded or fetched separately
    price_analysis: Optional[List[PriceData]] = None
    supply_demand_analysis: Optional[List[SupplyDemandData]] = None
    profit_analysis: Optional[List[ProfitAnalysis]] = None

class ReportList(BaseModel):
    items: List[Report]
    total: int

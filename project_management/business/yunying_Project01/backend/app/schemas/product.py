from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ProductBase(BaseModel):
    product_code: str
    product_name: str
    specification: Optional[str] = None
    origin: Optional[str] = None

class PriceData(ProductBase):
    price_date: date
    market_price: Optional[float] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_rate: Optional[float] = None
    is_abnormal: bool = False

class SupplyDemandData(BaseModel):
    product_code: str
    data_date: date
    inventory_level: Optional[float] = None
    demand_ratio: Optional[float] = None
    supply_demand_balance: Optional[float] = None
    is_warning: bool = False
    forecast_trend: Optional[str] = None
    forecast_confidence: Optional[float] = None

class ProfitAnalysis(BaseModel):
    product_code: str
    cost_per_ton: Optional[float] = None
    profit_per_ton: Optional[float] = None
    profit_change_rate: Optional[float] = None
    analysis_text: Optional[str] = None

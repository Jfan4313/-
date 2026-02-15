from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

@dataclass
class SimulationResult:
    module_name: str
    annual_revenue: float
    total_investment: float
    annual_maintenance_cost: float
    payback_period_years: float
    roi: float
    irr: float
    carbon_reduction_tons: float
    # Detailed time-series data for analysis (optional)
    hourly_savings: Optional[np.ndarray] = None
    daily_savings: Optional[np.ndarray] = None
    # Calculation details for transparency
    calculation_details: Optional[Dict[str, Any]] = None

class BaseModule:
    def __init__(self, name: str):
        self.name = name

    def calculate(self, inputs: Dict[str, Any]) -> SimulationResult:
        """
        Main calculation entry point.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement calculate()")

    def calculate_financials(self, investment: float, annual_net_cashflow: float, lifespan_years: int = 10) -> Dict[str, float]:
        """
        Helper to calculate basic financial metrics.
        """
        if investment <= 0:
            return {
                "payback_years": 0.0,
                "roi": float('inf'),
                "irr": float('inf')
            }
        
        # Simple Payback
        payback = investment / annual_net_cashflow if annual_net_cashflow > 0 else float('inf')
        
        # Simple ROI
        total_return = (annual_net_cashflow * lifespan_years) - investment
        roi = (total_return / investment) * 100
        
        # Simplified IRR (assuming constant cashflow)
        # -Investment + Sum(Cashflow / (1+r)^t) = 0
        # This is a rough approximation; for precise IRR we need year-by-year cashflow series
        # We will iterate to find r
        try:
            cashflows = [-investment] + [annual_net_cashflow] * lifespan_years
            irr = np.irr(cashflows) * 100
            if np.isnan(irr):
                irr = 0.0
        except:
            irr = 0.0

        return {
            "payback_years": round(payback, 2),
            "roi": round(roi, 2),
            "irr": round(irr, 2)
        }

@dataclass
class MicrogridVisualizationResult:
    """微电网可视化结果扩展"""
    # 继承基础结果
    module_name: str
    annual_revenue: float
    total_investment: float
    annual_maintenance_cost: float
    payback_period_years: float
    roi: float
    irr: float
    carbon_reduction_tons: float

    # 时间序列快照（每小时）
    hourly_snapshots: List[Dict[str, Any]] = field(default_factory=list)

    # Sankey图数据
    sankey_nodes: List[str] = field(default_factory=list)
    sankey_links: List[Dict[str, Any]] = field(default_factory=list)

    # 动画帧数据
    animation_frames: List[Dict[str, Any]] = field(default_factory=list)

    # 场景对比数据
    scenario_comparison: Optional[Dict[str, Any]] = None

    # 详细计算过程
    calculation_details: Optional[Dict[str, Any]] = None

    # 时序数据（用于图表）
    hourly_savings: Optional[np.ndarray] = None
    daily_savings: Optional[np.ndarray] = None

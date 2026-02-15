"""
储能模块 v2
支持：峰谷套利、正低价/负电价策略、AI优化
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from .base import BaseModule, SimulationResult
from .models import StorageSystem

class StorageModuleV2(BaseModule):
    def __init__(self):
        super().__init__("Energy Storage System")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        计算储能系统收益
        """
        capacity_kwh = inputs.get("capacity_kwh", 1000)
        power_kw = inputs.get("power_kw", 500)
        efficiency = inputs.get("efficiency", 0.9)
        investment = inputs.get("total_investment", 0)
        price_curve = inputs.get("price_curve", np.array([0.8] * 24))
        ai_enabled = inputs.get("ai_enabled", False)
        # 默认过网费（如果没有传入，使用0.2）
        grid_fee = inputs.get("grid_fee", 0.2)
        emission_factor = inputs.get("emission_factor", 0.5366)

        # 模拟引擎进行套利分析
        from .simulation_engine import SimulationEngine, SimulationConfig
        sim_engine = SimulationEngine(SimulationConfig(price_curve=price_curve))
        
        # 套利模拟
        arbitrage_res = sim_engine.simulate_storage_arbitrage(
            capacity_kwh=capacity_kwh,
            power_kw=power_kw,
            efficiency=efficiency,
            price_curve=price_curve,
            ai_enabled=ai_enabled,
            grid_fee=grid_fee
        )

        annual_revenue = arbitrage_res.get("AI年利润") if ai_enabled else arbitrage_res.get("无AI年利润")
        if annual_revenue is None:
            annual_revenue = 0
            
        annual_maintenance = investment * 0.015
        annual_net = annual_revenue - annual_maintenance

        metrics = self.calculate_financials(investment, annual_net)

        result = SimulationResult(
            module_name=self.name,
            annual_revenue=annual_revenue,
            total_investment=investment,
            annual_maintenance_cost=annual_maintenance,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=0  # 储能本身通常不直接减排
        )

        result.calculation_details = arbitrage_res
        return result

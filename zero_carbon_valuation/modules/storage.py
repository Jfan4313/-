"""
储能模块 v2
支持：AI vs 无AI对比、4种电价策略、详细计算展示
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from .base import BaseModule, SimulationResult

class StorageModuleV2(BaseModule):
    def __init__(self):
        super().__init__("Energy Storage (Arbitrage)")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        计算储能套利收益

        Inputs:
        - capacity_kwh: float
        - power_kw: float
        - efficiency_rt: float
        - price_curve: List[float] (24h)
        - cycles_per_day: int
        - investment_per_kwh: float
        - ai_enabled: bool
        - grid_fee: float (过网费)
        """
        capacity = inputs.get("capacity_kwh", 0)
        power = inputs.get("power_kw", 0)
        eff = inputs.get("efficiency_rt", 0.90)
        investment_unit = inputs.get("investment_per_kwh", 1300)
        cycles = inputs.get("cycles_per_day", 2)
        ai_enabled = inputs.get("ai_enabled", False)
        grid_fee = inputs.get("grid_fee", 0.2)

        # 电价曲线
        default_curve = [0.3] * 8 + [1.2] * 4 + [0.7] * 2 + [1.2] * 4 + [0.3] * 6
        prices = np.array(inputs.get("price_curve", default_curve))

        # 计算充放电时长
        hours_to_charge = capacity / power if power > 0 else 0

        if ai_enabled:
            # AI模式：动态寻找最优时段
            sorted_idx = np.argsort(prices)
            charge_hours = sorted_idx[:int(hours_to_charge)]
            discharge_hours = sorted_idx[-int(hours_to_charge):]

            avg_charge_price = float(np.mean(prices[charge_hours]))
            avg_discharge_price = float(np.mean(prices[discharge_hours]))

            strategy = "AI动态优化"
            charge_hours_str = f"小时 {sorted(charge_hours.tolist())}"
            discharge_hours_str = f"小时 {sorted(discharge_hours.tolist())}"
        else:
            # 无AI模式：固定时段
            avg_charge_price = float(np.mean(prices[0:4]))
            avg_discharge_price = float(np.mean(prices[14:18]))

            strategy = "固定时段(0-4充/14-18放)"
            charge_hours_str = "0:00-4:00"
            discharge_hours_str = "14:00-18:00"

        # 单次循环利润
        charge_cost = capacity * (avg_charge_price + grid_fee)
        discharge_revenue = capacity * eff * avg_discharge_price
        single_cycle_profit = discharge_revenue - charge_cost

        # 日/年利润
        daily_profit = single_cycle_profit * cycles
        annual_profit = daily_profit * 330

        # 投资与财务
        investment = capacity * investment_unit
        annual_maint = investment * 0.015
        net_cashflow = annual_profit - annual_maint

        metrics = self.calculate_financials(investment, net_cashflow, lifespan_years=10)

        result = SimulationResult(
            module_name=self.name,
            annual_revenue=annual_profit,
            total_investment=investment,
            annual_maintenance_cost=annual_maint,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=0  # 储能本身不直接减排
        )

        # 附加计算详情
        result.calculation_details = {
            "策略": strategy,
            "充电时段": charge_hours_str,
            "放电时段": discharge_hours_str,
            "平均充电电价": round(avg_charge_price, 4),
            "平均放电电价": round(avg_discharge_price, 4),
            "峰谷价差": round(avg_discharge_price - avg_charge_price, 4),
            "过网费": grid_fee,
            "单次充电成本": round(charge_cost, 2),
            "单次放电收入": round(discharge_revenue, 2),
            "单次循环利润": round(single_cycle_profit, 2),
            "日循环次数": cycles,
            "日利润": round(daily_profit, 2),
            "年运行天数": 330,
            "年利润": round(annual_profit, 2),
            "计算公式": [
                "充电成本 = 容量 × (充电电价 + 过网费)",
                "放电收入 = 容量 × 效率 × 放电电价",
                "单次利润 = 放电收入 - 充电成本",
                "年利润 = 单次利润 × 日循环次数 × 年运行天数",
            ],
        }

        return result

    def compare_with_without_ai(self, inputs: dict) -> Dict[str, Any]:
        """对比有AI和无AI的收益"""
        inputs_no_ai = {**inputs, "ai_enabled": False}
        inputs_ai = {**inputs, "ai_enabled": True}

        result_no_ai = self.calculate(inputs_no_ai)
        result_ai = self.calculate(inputs_ai)

        delta = result_ai.annual_revenue - result_no_ai.annual_revenue
        pct = (delta / result_no_ai.annual_revenue * 100) if result_no_ai.annual_revenue > 0 else 0

        return {
            "无AI模式": {
                "年利润": round(result_no_ai.annual_revenue, 2),
                "日利润": round(result_no_ai.annual_revenue / 330, 2),
                "策略": "固定时段充放电",
                "详情": result_no_ai.calculation_details,
            },
            "AI模式": {
                "年利润": round(result_ai.annual_revenue, 2),
                "日利润": round(result_ai.annual_revenue / 330, 2),
                "策略": "动态优化充放电",
                "详情": result_ai.calculation_details,
            },
            "对比": {
                "年增收": round(delta, 2),
                "增收比例": f"{pct:.1f}%",
                "结论": f"AI模式相比固定时段模式，年增收约 {round(delta, 2)} 元，提升 {pct:.1f}%",
            },
        }

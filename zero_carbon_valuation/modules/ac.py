"""
空调模块 v2
支持：分体机/中央空调、热惯性预冷、AI优化
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from .base import BaseModule, SimulationResult
from .models import ACSystem, ACType

class ACModuleV2(BaseModule):
    def __init__(self):
        super().__init__("Air Conditioning System")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        计算空调系统改造收益

        Inputs:
        - ac_systems: List[ACSystem] (多个空调系统)
        - cop_old: float (旧系统平均COP)
        - cop_new: float (新系统平均COP)
        - electricity_price: float
        - total_investment: float
        - ai_enabled: bool
        - ai_precool_saving_pct: float (AI预冷额外节省比例)
        - building_area_sqm: float
        - thermal_coefficient: float
        """
        ac_systems: List[ACSystem] = inputs.get("ac_systems", [])
        cop_old = inputs.get("cop_old", 3.0)
        cop_new = inputs.get("cop_new", 4.5)
        price = inputs.get("electricity_price", 0.8)
        investment = inputs.get("total_investment", 0)
        ai_enabled = inputs.get("ai_enabled", False)
        ai_precool_saving_pct = inputs.get("ai_precool_saving_pct", 0.08)
        emission_factor = inputs.get("emission_factor", 0.5703)

        # 汇总所有空调系统的年耗电量
        total_consumption_old = 0
        total_consumption_new = 0
        system_details = []

        for ac in ac_systems:
            annual_consumption = ac.get_annual_consumption_kwh()
            # 旧系统能耗反推（假设新系统COP对应的能耗）
            if ac.ac_type == ACType.SPLIT:
                old_consumption = annual_consumption * (ac.unit_cop / cop_old)
                new_consumption = annual_consumption * (ac.unit_cop / cop_new)
            else:
                old_consumption = annual_consumption * (ac.central_cop / cop_old)
                new_consumption = annual_consumption * (ac.central_cop / cop_new)

            total_consumption_old += old_consumption
            total_consumption_new += new_consumption

            system_details.append({
                "name": ac.name,
                "type": ac.ac_type.value,
                "旧年耗电": round(old_consumption, 2),
                "新年耗电": round(new_consumption, 2),
            })

        # 硬件改造节电
        hardware_saving_kwh = total_consumption_old - total_consumption_new

        # AI预冷额外节电
        ai_saving_kwh = 0
        if ai_enabled:
            ai_saving_kwh = total_consumption_new * ai_precool_saving_pct

        total_saving_kwh = hardware_saving_kwh + ai_saving_kwh
        annual_revenue = total_saving_kwh * price
        annual_maintenance = investment * 0.02
        annual_net = annual_revenue - annual_maintenance

        carbon_reduction = total_saving_kwh * emission_factor / 1000.0
        metrics = self.calculate_financials(investment, annual_net)

        result = SimulationResult(
            module_name=self.name,
            annual_revenue=annual_revenue,
            total_investment=investment,
            annual_maintenance_cost=annual_maintenance,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=carbon_reduction
        )

        # 附加计算详情
        result.calculation_details = {
            "系统明细": system_details,
            "旧系统总耗电_kwh": round(total_consumption_old, 2),
            "新系统总耗电_kwh": round(total_consumption_new, 2),
            "硬件节电_kwh": round(hardware_saving_kwh, 2),
            "AI预冷额外节电_kwh": round(ai_saving_kwh, 2) if ai_enabled else "未启用",
            "总节电_kwh": round(total_saving_kwh, 2),
            "计算公式": [
                "旧系统耗电 = 制冷需求 / 旧COP",
                "新系统耗电 = 制冷需求 / 新COP",
                "硬件节电 = 旧耗电 - 新耗电",
                "AI节电 = 新耗电 × AI优化率" if ai_enabled else "",
            ],
        }

        return result

    def compare_with_without_ai(self, inputs: dict) -> Dict[str, Any]:
        """对比有AI和无AI的收益"""
        inputs_no_ai = {**inputs, "ai_enabled": False}
        inputs_ai = {**inputs, "ai_enabled": True}

        result_no_ai = self.calculate(inputs_no_ai)
        result_ai = self.calculate(inputs_ai)

        return {
            "无AI": {
                "年节省_rmb": round(result_no_ai.annual_revenue, 2),
                "ROI": result_no_ai.roi,
            },
            "有AI": {
                "年节省_rmb": round(result_ai.annual_revenue, 2),
                "ROI": result_ai.roi,
            },
            "AI增收": round(result_ai.annual_revenue - result_no_ai.annual_revenue, 2),
            "AI增收比例": f"{((result_ai.annual_revenue - result_no_ai.annual_revenue) / result_no_ai.annual_revenue * 100):.1f}%" if result_no_ai.annual_revenue > 0 else "N/A",
        }

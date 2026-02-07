"""
照明模块 v2
支持：多区域、多类型灯具、AI调光
"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .base import BaseModule, SimulationResult
from .models import LightingZone, LightingSystem, LightingType

class LightingModuleV2(BaseModule):
    def __init__(self):
        super().__init__("Lighting Renovation")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        计算照明改造收益

        Inputs:
        - lighting_zones: List[LightingZone] (多个照明区域)
        - electricity_price: float
        - investment_per_fixture: float (平均单灯改造成本)
        - ai_enabled: bool
        - ai_dimming_saving_pct: float (AI调光额外节省比例)
        """
        zones: List[LightingZone] = inputs.get("lighting_zones", [])
        price = inputs.get("electricity_price", 0.85)
        inv_per = inputs.get("investment_per_fixture", 100)
        ai_enabled = inputs.get("ai_enabled", False)
        ai_dimming_pct = inputs.get("ai_dimming_saving_pct", 0.15)
        emission_factor = inputs.get("emission_factor", 0.5703)

        zone_details = []
        total_saving_kwh = 0
        total_fixtures = 0

        for zone in zones:
            saving = zone.get_annual_saving_kwh()
            total_saving_kwh += saving
            total_fixtures += zone.fixture_count

            zone_details.append({
                "区域名称": zone.name,
                "灯具类型": zone.lighting_type.value,
                "数量": zone.fixture_count,
                "改造前功率_w": zone.power_per_fixture_w,
                "改造后功率_w": zone.new_power_per_fixture_w,
                "日运行小时": zone.daily_hours,
                "年节电_kwh": round(saving, 2),
            })

        # 硬件改造节电
        hardware_saving_kwh = total_saving_kwh

        # AI调光额外节电（基于改造后的用电量）
        # 改造后年用电 = 新功率 × 时间
        post_retrofit_consumption = sum(
            z.fixture_count * z.new_power_per_fixture_w / 1000 * z.daily_hours * z.annual_days
            for z in zones
        )
        ai_saving_kwh = post_retrofit_consumption * ai_dimming_pct if ai_enabled else 0

        total_saving = hardware_saving_kwh + ai_saving_kwh
        annual_revenue = total_saving * price

        # 投资
        investment = total_fixtures * inv_per
        annual_maint = investment * 0.01
        net_cashflow = annual_revenue - annual_maint

        carbon_reduction = total_saving * emission_factor / 1000.0
        metrics = self.calculate_financials(investment, net_cashflow)

        result = SimulationResult(
            module_name=self.name,
            annual_revenue=annual_revenue,
            total_investment=investment,
            annual_maintenance_cost=annual_maint,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=carbon_reduction
        )

        result.calculation_details = {
            "区域明细": zone_details,
            "总灯具数": total_fixtures,
            "硬件改造节电_kwh": round(hardware_saving_kwh, 2),
            "AI调光节电_kwh": round(ai_saving_kwh, 2) if ai_enabled else "未启用",
            "总节电_kwh": round(total_saving, 2),
            "年节省电费_rmb": round(annual_revenue, 2),
            "计算公式": [
                "单区节电 = (旧功率 - 新功率) × 数量 × 日时长 × 年天数 / 1000",
                "AI节电 = 改造后用电量 × AI调光节省率" if ai_enabled else "",
                "年节省 = 总节电 × 电价",
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

        return {
            "无AI": {
                "年节省_rmb": round(result_no_ai.annual_revenue, 2),
                "节电_kwh": result_no_ai.calculation_details.get("总节电_kwh", 0),
            },
            "有AI": {
                "年节省_rmb": round(result_ai.annual_revenue, 2),
                "节电_kwh": result_ai.calculation_details.get("总节电_kwh", 0),
            },
            "AI增收": round(delta, 2),
            "AI调光说明": "AI通过自然光感应+人感控制，在满足照度需求时自动调低亮度",
        }

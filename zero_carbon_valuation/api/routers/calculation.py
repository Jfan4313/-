"""
计算API路由
提供各改造模块的计算服务
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import sys
import os

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    SolarCalculationRequest,
    StorageCalculationRequest,
    HVACCalculationRequest,
    LightingCalculationRequest,
    EVChargingCalculationRequest,
    CalculationResult
)

router = APIRouter(prefix="/api/v1/calculation", tags=["Calculation"])


@router.post("/solar", response_model=CalculationResult)
async def calculate_solar(req: SolarCalculationRequest) -> CalculationResult:
    """
    光伏收益计算

    计算公式:
    - 总发电量 = 装机容量 × 年利用小时数
    - 自用电量 = 总发电量 × 自用比例
    - 上网电量 = 总发电量 × (1 - 自用比例)
    - 年收益 = 自用电量 × 购电价格 + 上网电量 × 上网电价
    - 投资 = 装机容量 × 1000 × 单价
    - 年维护费 = 投资 × 1%
    - 碳减排 = 总发电量 × 排放因子 / 1000
    """
    try:
        # 总发电量 (kWh)
        total_generation = req.capacity_kw * req.yield_hours

        # 自用和上网电量
        self_use_kwh = total_generation * req.self_use_ratio
        feed_in_kwh = total_generation * (1 - req.self_use_ratio)

        # 年收益 (元)
        annual_revenue = (self_use_kwh * req.buy_price) + (feed_in_kwh * req.sell_price)

        # 投资 (元) -> 转为万元
        total_investment = req.capacity_kw * 1000 * req.cost_per_w / 10000

        # 年维护费 (万元)
        annual_maintenance = total_investment * 0.01

        # 年净现金流 (万元)
        annual_net_cashflow = (annual_revenue / 10000) - annual_maintenance

        # 财务指标
        roi, irr, payback = _calculate_financials(total_investment, annual_net_cashflow, lifespan_years=25)

        # 碳减排 (吨)
        carbon_reduction = total_generation * req.emission_factor / 1000

        # NPV (简化计算，假设10年)
        discount_rate = 0.05
        npv = -total_investment + sum(
            annual_net_cashflow / ((1 + discount_rate) ** year)
            for year in range(1, 11)
        )

        # 逐时数据
        hourly_data = None
        if req.include_hourly:
            hourly_data = _generate_pv_hourly_data(req.capacity_kw, req.yield_hours, req.self_use_ratio)

        return CalculationResult(
            investment=round(total_investment, 2),
            annual_saving=round(annual_net_cashflow, 2),
            roi=round(roi, 2),
            irr=round(irr, 2),
            payback_period=round(payback, 2),
            npv=round(npv, 2),
            carbon_reduction=round(carbon_reduction, 2),
            hourly_data=hourly_data[:24] if hourly_data else None,
            calculation_details={
                "总发电量_kWh": total_generation,
                "自用电量_kWh": round(self_use_kwh, 2),
                "上网电量_kWh": round(feed_in_kwh, 2),
                "年收益_万元": round(annual_revenue / 10000, 2),
                "年维护费_万元": round(annual_maintenance, 2),
                "计算公式": "年收益 = 自用电量×购电价 + 上网电量×上网电价"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/storage", response_model=CalculationResult)
async def calculate_storage(req: StorageCalculationRequest) -> CalculationResult:
    """
    储能套利计算

    计算公式:
    - 单次循环收益 = 容量 × 效率 × 放电价 - 容量 × 充电价
    - 年收益 = 单次循环收益 × 循环次数/天 × 365天
    - 投资 = 容量 × 1300元/kWh
    - 年维护费 = 投资 × 3%
    """
    try:
        # 基础参数
        capacity_kwh = req.capacity_kwh
        efficiency = req.efficiency

        # 如果提供了电价曲线，使用曲线计算
        if req.price_curve and len(req.price_curve) == 24:
            # 找出最低4小时作为充电时段，最高4小时作为放电时段
            sorted_indices = sorted(range(24), key=lambda i: req.price_curve[i])
            charge_indices = sorted_indices[:4]
            discharge_indices = sorted_indices[-4:]

            avg_charge_price = sum(req.price_curve[i] for i in charge_indices) / 4 + req.grid_fee
            avg_discharge_price = sum(req.price_curve[i] for i in discharge_indices) / 4
        else:
            # 默认: 谷时0-4点充电, 峰时14-18点放电
            avg_charge_price = 0.32 + req.grid_fee
            avg_discharge_price = 1.62

        # 单次循环收益 (元)
        cycle_revenue = capacity_kwh * efficiency * avg_discharge_price - capacity_kwh * avg_charge_price

        # 年收益 (万元)
        annual_revenue = cycle_revenue * req.cycles_per_day * 365 / 10000

        # 投资 (万元)
        total_investment = capacity_kwh * 1300 / 10000

        # 年维护费 (万元)
        annual_maintenance = total_investment * 0.03

        # 年净现金流
        annual_net_cashflow = annual_revenue - annual_maintenance

        # 财务指标
        roi, irr, payback = _calculate_financials(total_investment, annual_net_cashflow, lifespan_years=10)

        # 碳减排 (储能本身不直接减排，通过转移负荷间接减排)
        carbon_reduction = 0

        return CalculationResult(
            investment=round(total_investment, 2),
            annual_saving=round(annual_net_cashflow, 2),
            roi=round(roi, 2),
            irr=round(irr, 2),
            payback_period=round(payback, 2),
            npv=0,
            carbon_reduction=carbon_reduction,
            calculation_details={
                "充电电价_元kWh": round(avg_charge_price, 3),
                "放电电价_元kWh": round(avg_discharge_price, 3),
                "单次循环收益_元": round(cycle_revenue, 2),
                "年收益_万元": round(annual_revenue, 2),
                "年维护费_万元": round(annual_maintenance, 2),
                "AI优化": req.ai_enabled
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/hvac", response_model=CalculationResult)
async def calculate_hvac(req: HVACCalculationRequest) -> CalculationResult:
    """
    空调节能计算

    计算公式:
    - 旧系统耗电 = 制冷需求 / 旧COP
    - 新系统耗电 = 制冷需求 / 新COP
    - 硬件节电 = 旧系统耗电 - 新系统耗电
    - AI预冷额外节电 = 新系统耗电 × AI优化率
    - 总节电 = 硬件节电 + AI节电
    """
    try:
        if not req.buildings:
            # 默认建筑数据
            total_area = 10000  # 平方米
            cooling_load_per_m2 = 0.15  # kW/m²
        else:
            total_area = sum(b.get("area", 0) for b in req.buildings)
            cooling_load_per_m2 = 0.15

        # 年制冷需求 (kWh)
        annual_cooling_load = total_area * cooling_load_per_m2 * 1000

        # 旧系统耗电
        old_power = annual_cooling_load / req.current_avg_cop

        # 新系统耗电
        new_power = annual_cooling_load / req.target_cop

        # 硬件节电
        hardware_saving = old_power - new_power

        # AI预冷额外节电
        ai_saving = new_power * req.ai_precool_saving_pct if req.ai_enabled else 0

        # 总节电
        total_saving = hardware_saving + ai_saving

        # 年节省 (万元)
        annual_saving_rmb = total_saving * req.electricity_price / 10000

        # 投资估算 (万元) - 简化: 200元/平米
        total_investment = total_area * 200 / 10000

        # 财务指标
        roi, irr, payback = _calculate_financials(total_investment, annual_saving_rmb, lifespan_years=15)

        # 碳减排 (吨)
        carbon_reduction = total_saving * req.emission_factor / 1000

        return CalculationResult(
            investment=round(total_investment, 2),
            annual_saving=round(annual_saving_rmb, 2),
            roi=round(roi, 2),
            irr=round(irr, 2),
            payback_period=round(payback, 2),
            npv=0,
            carbon_reduction=round(carbon_reduction, 2),
            calculation_details={
                "建筑面积_m2": total_area,
                "旧系统耗电_kWh": round(old_power, 0),
                "新系统耗电_kWh": round(new_power, 0),
                "硬件节电_kWh": round(hardware_saving, 0),
                "AI节电_kWh": round(ai_saving, 0),
                "总节电_kWh": round(total_saving, 0),
                "年节省_万元": round(annual_saving_rmb, 2),
                "AI优化": req.ai_enabled
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/lighting", response_model=CalculationResult)
async def calculate_lighting(req: LightingCalculationRequest) -> CalculationResult:
    """
    照明节能计算
    """
    try:
        if not req.areas:
            # 默认区域数据
            total_lights = 1000
            old_power = 40  # W
            new_power = 15  # W
            daily_hours = 10
        else:
            total_lights = sum(a.get("count", 0) for a in req.areas)
            old_power = sum(a.get("oldPower", 40) * a.get("count", 0) for a in req.areas) / total_lights if total_lights > 0 else 40
            new_power = sum(a.get("newPower", 15) * a.get("count", 0) for a in req.areas) / total_lights if total_lights > 0 else 15
            daily_hours = sum(a.get("hours", 10) for a in req.areas) / len(req.areas) if req.areas else 10

        # 硬件节电
        hardware_saving = (old_power - new_power) * total_lights * daily_hours * 365 / 1000  # kWh

        # AI调光额外节电
        after_hardware_power = new_power * total_lights * daily_hours * 365 / 1000
        ai_saving = after_hardware_power * req.ai_dimming_saving_pct if req.ai_enabled else 0

        # 总节电
        total_saving = hardware_saving + ai_saving

        # 年节省 (万元)
        annual_saving_rmb = total_saving * req.electricity_price / 10000

        # 投资 (万元) - 简化: 100元/灯
        total_investment = total_lights * 100 / 10000

        # 财务指标
        roi, irr, payback = _calculate_financials(total_investment, annual_saving_rmb, lifespan_years=10)

        # 碳减排 (吨)
        carbon_reduction = total_saving * req.emission_factor / 1000

        return CalculationResult(
            investment=round(total_investment, 2),
            annual_saving=round(annual_saving_rmb, 2),
            roi=round(roi, 2),
            irr=round(irr, 2),
            payback_period=round(payback, 2),
            npv=0,
            carbon_reduction=round(carbon_reduction, 2),
            calculation_details={
                "灯具数量": total_lights,
                "旧功率_W": round(old_power, 1),
                "新功率_W": round(new_power, 1),
                "硬件节电_kWh": round(hardware_saving, 0),
                "AI节电_kWh": round(ai_saving, 0),
                "总节电_kWh": round(total_saving, 0),
                "年节省_万元": round(annual_saving_rmb, 2),
                "AI优化": req.ai_enabled
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/ev", response_model=CalculationResult)
async def calculate_ev(req: EVChargingCalculationRequest) -> CalculationResult:
    """
    充电桩收益计算
    """
    try:
        # 日充电量 (kWh)
        daily_charging = req.charger_count * req.power_per_charger_kw * req.daily_util_hours

        # 年充电量 (kWh)
        annual_charging = daily_charging * 365

        # 年服务费收入 (万元)
        annual_revenue = annual_charging * req.service_fee_per_kwh / 10000

        # 投资 (万元)
        total_investment = req.charger_count * req.investment_per_charger / 10000

        # 年维护费 (万元)
        annual_maintenance = total_investment * 0.03

        # 年净现金流
        annual_net_cashflow = annual_revenue - annual_maintenance

        # 财务指标
        roi, irr, payback = _calculate_financials(total_investment, annual_net_cashflow, lifespan_years=10)

        return CalculationResult(
            investment=round(total_investment, 2),
            annual_saving=round(annual_net_cashflow, 2),
            roi=round(roi, 2),
            irr=round(irr, 2),
            payback_period=round(payback, 2),
            npv=0,
            carbon_reduction=0,
            calculation_details={
                "充电桩数量": req.charger_count,
                "年充电量_kWh": round(annual_charging, 0),
                "年服务费收入_万元": round(annual_revenue, 2),
                "年维护费_万元": round(annual_maintenance, 2)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


# ========== 辅助函数 ==========

def _calculate_financials(investment: float, annual_net_cashflow: float, lifespan_years: int = 10) -> tuple:
    """计算财务指标: ROI, IRR, 回收期"""
    if investment <= 0:
        return (0, 0, 0)

    # 回收期 (年)
    payback = investment / annual_net_cashflow if annual_net_cashflow > 0 else float('inf')

    # ROI (%)
    total_return = (annual_net_cashflow * lifespan_years) - investment
    roi = (total_return / investment) * 100 if investment > 0 else 0

    # IRR (%) - 简化计算
    try:
        cashflows = [-investment] + [annual_net_cashflow] * lifespan_years
        # 使用牛顿迭代法求IRR
        irr = _newton_irr(cashflows)
    except:
        irr = 0

    return (roi, irr, payback)


def _newton_irr(cashflows, max_iterations=100, tolerance=1e-6):
    """牛顿迭代法求IRR"""
    rate = 0.1  # 初始猜测10%
    for _ in range(max_iterations):
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))
        d_npv = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cashflows))
        if abs(d_npv) < tolerance:
            break
        rate = rate - npv / d_npv
        if abs(rate) > 10:  # 防止发散
            break
    return rate * 100


def _generate_pv_hourly_data(capacity_kw: float, yield_hours: float, self_use_ratio: float) -> list:
    """生成光伏逐时数据 (24小时)"""
    hourly_data = []
    for hour in range(24):
        if 6 <= hour <= 18:
            # 日间发电 (钟形曲线)
            generation = capacity_kw * yield_hours / 365 * (3.14159 * (hour - 6) / 12)
            # 修正钟形曲线
            normalized = 1 + 0.5 * ((hour - 12) / 6) ** 2
            generation = max(0, generation / normalized)
        else:
            generation = 0

        self_use = generation * self_use_ratio
        feed_in = generation * (1 - self_use_ratio)

        hourly_data.append({
            "hour": hour,
            "generation": round(generation, 2),
            "self_use": round(self_use, 2),
            "feed_in": round(feed_in, 2)
        })

    return hourly_data

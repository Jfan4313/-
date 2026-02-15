"""
8760小时模拟API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import sys
import os

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SimulationRequest, SimulationOutput

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])


@router.post("/8760", response_model=SimulationOutput)
async def run_8760_simulation(req: SimulationRequest) -> SimulationOutput:
    """
    运行8760小时完整模拟

    模拟内容:
    - 光伏自发自用分析
    - 储能套利模拟
    - 空调预冷模拟

    返回各模块的模拟结果
    """
    try:
        # 构建模拟配置
        config = SimulationConfig(
            hours=8760,
            province=req.province,
        )

        # 初始化模拟引擎
        engine = SimulationEngine(config)

        results: Dict[str, Any] = {
            "aggregate": {
                "province": req.province,
                "simulation_hours": 8760
            }
        }

        # 光伏自发自用分析
        if req.pv_capacity_kw > 0:
            pv_result = engine.analyze_pv_self_consumption(
                annual_load_kwh=req.annual_load_kwh or 1000000,
                pv_capacity_kw=req.pv_capacity_kw,
                pv_yield_hours=1100,
                load_curve_type="workday"
            )
            results["pv"] = pv_result

        # 储能套利模拟
        if req.storage_capacity_kwh > 0:
            # 生成电价曲线
            if req.price_mode == "tou" and req.tou_segments:
                price_curve = _generate_tou_price_curve(req.tou_segments)
            elif req.price_mode == "spot" and req.spot_prices:
                price_curve = req.spot_prices[:24] * (8760 // 24)
            else:
                # 默认分时电价
                price_curve = _generate_default_price_curve()

            storage_result = engine.simulate_storage_arbitrage(
                capacity_kwh=req.storage_capacity_kwh,
                power_kw=req.storage_power_kw,
                efficiency=0.9,
                price_curve=price_curve[:8760],
                ai_enabled=False,
                grid_fee=0.2
            )
            results["storage"] = storage_result

        # 空调预冷模拟
        # 生成制冷需求曲线
        cooling_load = _generate_cooling_load_profile(req.province, 8760)

        hvac_result = engine.simulate_ac_with_precooling(
            cooling_load_profile=cooling_load,
            cop=4.5,
            price_curve=_generate_default_price_curve()[:8760],
            building_thermal_mass=1.0,
            ai_enabled=False
        )
        results["hvac"] = hvac_result

        # 聚合指标
        results["aggregate"]["total_carbon_reduction"] = results.get("pv", {}).get("self_use_kwh", 0) * 0.5703 / 1000

        return SimulationOutput(**results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟失败: {str(e)}")


# ========== 辅助函数 ==========

def _generate_tou_price_curve(tou_segments: list) -> list:
    """生成分时电价曲线 (24小时重复)"""
    # 创建24小时电价映射
    hourly_prices = [0] * 24
    for segment in tou_segments:
        start = segment.get("start", 0)
        end = segment.get("end", 24)
        price = segment.get("price", 0.5)
        for h in range(start, end):
            hourly_prices[h % 24] = price

    # 扩展到8760小时
    return hourly_prices * (8760 // 24) + hourly_prices[: (8760 % 24)]


def _generate_default_price_curve() -> list:
    """生成默认分时电价曲线 (广东省)"""
    hourly_prices = [
        0.32,  # 0点
        0.32,
        0.32,
        0.32,
        0.32,
        0.32,
        0.32,
        0.32,
        0.68,  # 8点
        0.68,
        0.68,
        1.15,  # 11点
        1.15,
        1.15,
        1.62,  # 14点
        1.62,
        1.62,
        1.62,
        1.15,  # 18点
        1.15,
        0.68,  # 20点
        0.68,
        0.68
    ]
    return hourly_prices * (8760 // 24) + hourly_prices[: (8760 % 24)]


def _generate_cooling_load_profile(province: str, hours: int) -> list:
    """生成制冷需求曲线"""
    import numpy as np

    # 省份对应的温度峰值
    temp_factors = {
        "广东省": 1.2,
        "江苏省": 1.0,
        "浙江省": 1.05,
        "上海市": 1.1,
        "北京市": 0.9,
    }
    factor = temp_factors.get(province, 1.0)

    # 生成曲线
    profile = []
    for h in range(hours):
        hour_of_day = h % 24
        day_of_year = h / 24

        # 季节性因子 (夏季高)
        seasonal = 1 + 0.5 * np.sin(2 * np.pi * (day_of_year - 90) / 365)

        # 日变化 (下午高)
        daily = 0.5 + 0.5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)

        base_load = 100 * factor  # 基础负荷
        profile.append(base_load * seasonal * daily)

    return profile

"""
电价模式引擎
支持：分时电价 (TOU)、动态电价 (现货市场)、固定电价
"""
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from .models import PricingMode, TOUPeriod, PricingConfig

# ==================== 预设电价模板 ====================

def get_guangdong_tou_template() -> List[TOUPeriod]:
    """广东省工商业分时电价模板（示例）"""
    return [
        TOUPeriod(name="谷时", price=0.32, start_hour=0, end_hour=8),
        TOUPeriod(name="峰时", price=1.05, start_hour=8, end_hour=12),
        TOUPeriod(name="平时", price=0.68, start_hour=12, end_hour=14),
        TOUPeriod(name="峰时", price=1.05, start_hour=14, end_hour=19),
        TOUPeriod(name="尖峰", price=1.35, start_hour=19, end_hour=22),
        TOUPeriod(name="谷时", price=0.32, start_hour=22, end_hour=24),
    ]

def get_jiangsu_tou_template() -> List[TOUPeriod]:
    """江苏省工商业分时电价模板（示例）"""
    return [
        TOUPeriod(name="谷时", price=0.35, start_hour=0, end_hour=8),
        TOUPeriod(name="峰时", price=1.10, start_hour=8, end_hour=11),
        TOUPeriod(name="尖峰", price=1.50, start_hour=11, end_hour=13),
        TOUPeriod(name="平时", price=0.72, start_hour=13, end_hour=17),
        TOUPeriod(name="峰时", price=1.10, start_hour=17, end_hour=21),
        TOUPeriod(name="谷时", price=0.35, start_hour=21, end_hour=24),
    ]

# ==================== 电价引擎 ====================

class PricingEngine:
    """电价计算引擎"""

    def __init__(self, config: PricingConfig):
        self.config = config
        self._hourly_prices: Optional[np.ndarray] = None

    def generate_24h_curve(self) -> np.ndarray:
        """生成24小时电价曲线"""
        prices = np.zeros(24)
        
        if self.config.mode == PricingMode.FIXED:
            prices[:] = self.config.fixed_price
        elif self.config.mode == PricingMode.TOU:
            for hour in range(24):
                prices[hour] = self.config.get_price_at_hour(hour)
        else:
            # 动态电价：外部注入或使用默认模拟曲线
            if self._hourly_prices is not None:
                prices = self._hourly_prices
            else:
                prices = self._generate_simulated_dynamic_curve()
        
        return prices

    def _generate_simulated_dynamic_curve(self) -> np.ndarray:
        """模拟动态电价曲线（用于演示）"""
        # 基于现货市场特征的模拟曲线
        base = np.array([
            0.20, 0.18, 0.15, 0.12, 0.10, 0.08, 0.10, 0.25,  # 0-7
            0.45, 0.60, 0.75, 0.90, 0.70, 0.50, 0.55, 0.65,  # 8-15
            0.80, 1.00, 1.20, 1.50, 1.30, 0.90, 0.50, 0.30   # 16-23
        ])
        # 添加随机波动 ±10%
        noise = np.random.uniform(-0.1, 0.1, 24) * base
        return base + noise

    def set_dynamic_prices(self, prices: np.ndarray):
        """设置动态电价曲线（外部数据）"""
        if len(prices) != 24:
            raise ValueError("电价曲线必须为24小时数据")
        self._hourly_prices = prices

    def get_price_spread(self) -> dict:
        """计算峰谷价差信息"""
        curve = self.generate_24h_curve()
        return {
            "min_price": float(np.min(curve)),
            "max_price": float(np.max(curve)),
            "spread": float(np.max(curve) - np.min(curve)),
            "avg_price": float(np.mean(curve)),
            "min_hour": int(np.argmin(curve)),
            "max_hour": int(np.argmax(curve)),
        }

    def find_optimal_charge_discharge_hours(self, charge_hours: int = 4, discharge_hours: int = 4) -> dict:
        """
        为储能系统寻找最优充放电时段
        返回最低价的N小时（充电）和最高价的N小时（放电）
        """
        curve = self.generate_24h_curve()
        sorted_indices = np.argsort(curve)
        
        charge_indices = sorted(sorted_indices[:charge_hours].tolist())
        discharge_indices = sorted(sorted_indices[-discharge_hours:].tolist())
        
        avg_charge_price = float(np.mean(curve[sorted_indices[:charge_hours]]))
        avg_discharge_price = float(np.mean(curve[sorted_indices[-discharge_hours:]]))
        
        return {
            "charge_hours": charge_indices,
            "discharge_hours": discharge_indices,
            "avg_charge_price": avg_charge_price,
            "avg_discharge_price": avg_discharge_price,
            "expected_spread": avg_discharge_price - avg_charge_price,
        }

    def calculate_storage_revenue(
        self,
        capacity_kwh: float,
        power_kw: float,
        efficiency: float = 0.90,
        cycles_per_day: int = 2,
        ai_enabled: bool = False
    ) -> dict:
        """
        计算储能套利收益

        参数:
            capacity_kwh: 储能容量
            power_kw: 充放功率
            efficiency: 往返效率
            cycles_per_day: 日充放电次数
            ai_enabled: 是否启用AI优化

        返回:
            包含详细计算过程的字典
        """
        curve = self.generate_24h_curve()
        hours_per_cycle = capacity_kwh / power_kw if power_kw > 0 else 0

        if ai_enabled:
            # AI模式：动态寻找最优时段
            optimal = self.find_optimal_charge_discharge_hours(
                charge_hours=int(hours_per_cycle),
                discharge_hours=int(hours_per_cycle)
            )
            charge_price = optimal["avg_charge_price"]
            discharge_price = optimal["avg_discharge_price"]
        else:
            # 无AI模式：固定时段（假设凌晨充电、下午放电）
            charge_price = float(np.mean(curve[0:4]))    # 0-4点
            discharge_price = float(np.mean(curve[14:18]))  # 14-18点

        # 单次循环收益计算
        charge_cost = capacity_kwh * charge_price
        discharge_revenue = capacity_kwh * efficiency * discharge_price
        single_cycle_profit = discharge_revenue - charge_cost

        # 日/年收益
        daily_profit = single_cycle_profit * cycles_per_day
        annual_profit = daily_profit * 330  # 年运行约330天

        return {
            "mode": "AI优化" if ai_enabled else "固定时段",
            "charge_price": round(charge_price, 4),
            "discharge_price": round(discharge_price, 4),
            "price_spread": round(discharge_price - charge_price, 4),
            "单次充电成本": round(charge_cost, 2),
            "单次放电收入": round(discharge_revenue, 2),
            "单次循环利润": round(single_cycle_profit, 2),
            "日利润": round(daily_profit, 2),
            "年利润": round(annual_profit, 2),
            "计算公式": f"年利润 = (放电量 × 放电电价 × 效率 - 充电量 × 充电电价) × 循环次数 × 年运行天数",
        }

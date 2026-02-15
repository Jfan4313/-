"""
8760小时模拟引擎
支持逐小时计算，结合温度曲线和负荷曲线
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class SimulationConfig:
    """模拟配置"""
    hours: int = 8760                       # 8760h = 1年
    temperature_curve: Optional[np.ndarray] = None
    load_curve: Optional[np.ndarray] = None
    price_curve: Optional[np.ndarray] = None
    province: str = "广东省" # 默认为广东省

# 典型省份气候数据 (年均温, 季节性温差, 日夜温差, 纬度)
PROVINCE_CLIMATE_DATA = {
    "广东省": {"temp_avg": 22, "temp_amp": 13, "daily_amp": 7, "lat": 23},
    "江苏省": {"temp_avg": 16, "temp_amp": 24, "daily_amp": 8, "lat": 32},
    "浙江省": {"temp_avg": 17, "temp_amp": 22, "daily_amp": 7, "lat": 30},
    "山东省": {"temp_avg": 14, "temp_amp": 26, "daily_amp": 9, "lat": 36},
    "河北省": {"temp_avg": 12, "temp_amp": 28, "daily_amp": 10, "lat": 38},
    "河南省": {"temp_avg": 15, "temp_amp": 26, "daily_amp": 10, "lat": 34},
    "湖北省": {"temp_avg": 16, "temp_amp": 24, "daily_amp": 8, "lat": 30},
    "四川省": {"temp_avg": 16, "temp_amp": 18, "daily_amp": 7, "lat": 30},
    "陕西省": {"temp_avg": 13, "temp_amp": 26, "daily_amp": 10, "lat": 34},
}

class SimulationEngine:
    """模拟引擎"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self._init_default_curves()

    def _init_default_curves(self):
        """初始化默认曲线"""
        hours = self.config.hours
        
        # 获取省份数据
        province_data = PROVINCE_CLIMATE_DATA.get(self.config.province, PROVINCE_CLIMATE_DATA["广东省"])

        # 温度曲线：年度周期 + 日周期
        if self.config.temperature_curve is None:
            days = np.arange(hours) / 24
            # 年周期：夏季最高（7月），冬季最低（1月）
            annual_cycle = province_data["temp_avg"] + \
                          (province_data["temp_amp"]/2) * np.sin(2 * np.pi * (days - 105) / 365) # 4月升温
            # 日周期：下午最高，凌晨最低
            hour_of_day = np.arange(hours) % 24
            daily_cycle = (province_data["daily_amp"]/2) * np.sin(2 * np.pi * (hour_of_day - 9) / 24) # 9点开始升温
            self.config.temperature_curve = annual_cycle + daily_cycle



        # 负荷曲线：工作日模式
        if self.config.load_curve is None:
            hour_of_day = np.arange(hours) % 24
            # 基础负荷 + 工作时间高峰
            base_load = 0.3
            work_peak = np.where((hour_of_day >= 8) & (hour_of_day <= 18), 0.7, 0.0)
            self.config.load_curve = base_load + work_peak

    def simulate_ac_with_precooling(
        self,
        cooling_load_profile: np.ndarray,
        cop: float,
        price_curve: np.ndarray,
        building_thermal_mass: float = 1.0,  # 热惯性系数 (小时)
        ai_enabled: bool = False
    ) -> Dict[str, Any]:
        """
        模拟空调系统能耗，含预冷策略

        参数:
            cooling_load_profile: 8760小时制冷需求 (kW)
            cop: 空调能效比
            price_curve: 8760小时电价曲线
            building_thermal_mass: 建筑热惯性（可提前制冷的小时数）
            ai_enabled: 是否启用AI预冷优化

        返回:
            包含能耗、成本和节省的详细信息
        """
        hours = len(cooling_load_profile)
        
        # 基准能耗：直接按需制冷
        baseline_power = cooling_load_profile / cop
        baseline_cost = np.sum(baseline_power * price_curve)

        if not ai_enabled:
            return {
                "模式": "按需制冷",
                "年耗电量_kwh": float(np.sum(baseline_power)),
                "年电费_rmb": round(baseline_cost, 2),
                "节省_rmb": 0,
                "计算公式": "年电费 = Σ(制冷负荷 / COP × 电价)",
            }

        # AI预冷策略：在低电价时段提前制冷
        optimized_power = baseline_power.copy()
        thermal_mass_hours = int(building_thermal_mass)

        for h in range(thermal_mass_hours, hours):
            current_price = price_curve[h]
            # 检查前N小时是否有更低电价
            prev_prices = price_curve[max(0, h - thermal_mass_hours):h]
            if len(prev_prices) > 0 and np.min(prev_prices) < current_price * 0.8:
                # 将部分负荷转移到低价时段
                shift_ratio = 0.5  # 转移50%负荷
                shift_hour = max(0, h - thermal_mass_hours) + int(np.argmin(prev_prices))
                shift_amount = optimized_power[h] * shift_ratio
                optimized_power[shift_hour] += shift_amount
                optimized_power[h] -= shift_amount

        optimized_cost = np.sum(optimized_power * price_curve)
        savings = baseline_cost - optimized_cost

        return {
            "模式": "AI预冷优化",
            "年耗电量_kwh": float(np.sum(optimized_power)),
            "基准电费_rmb": round(baseline_cost, 2),
            "优化后电费_rmb": round(optimized_cost, 2),
            "节省_rmb": round(savings, 2),
            "节省比例": f"{(savings / baseline_cost * 100):.1f}%",
            "计算公式": "节省 = 基准电费 - 优化后电费（负荷转移至低电价时段）",
            "热惯性小时数": thermal_mass_hours,
        }

    def simulate_storage_arbitrage(
        self,
        capacity_kwh: float,
        power_kw: float,
        efficiency: float,
        price_curve: np.ndarray,
        ai_enabled: bool = False,
        grid_fee: float = 0.2
    ) -> Dict[str, Any]:
        """
        模拟储能套利（含负价策略）

        参数:
            capacity_kwh: 储能容量
            power_kw: 充放功率
            efficiency: 往返效率
            price_curve: 24小时电价曲线（现货价，不含过网费）
            ai_enabled: 是否启用AI优化
            grid_fee: 过网费（固定成本）
        """
        # 实际买电成本 = 现货价 + 过网费
        buy_price_curve = price_curve + grid_fee
        # 上网收入 = 现货价（不含过网费）
        sell_price_curve = price_curve

        daily_profit_no_ai = 0
        daily_profit_ai = 0
        strategy_log = []

        # 简化：按日模拟
        for cycle in range(2):  # 每日2个循环
            if ai_enabled:
                # AI策略：分析4种场景
                for h in range(24):
                    spot_price = price_curve[h]

                    # 策略判断
                    if spot_price > 1.0:
                        # 极高价：放电
                        strategy_log.append(f"[{h}:00] 极高价({spot_price:.2f})：放电")
                        daily_profit_ai += capacity_kwh * efficiency * spot_price / 2
                    elif spot_price < -grid_fee:
                        # 深负价：买电赚钱！
                        actual_cost = spot_price + grid_fee  # 负值=赚钱
                        strategy_log.append(f"[{h}:00] 深负价({spot_price:.2f})：买电充储，实际赚{-actual_cost:.2f}/kWh")
                        daily_profit_ai += capacity_kwh * (-actual_cost) / 2
                    elif -grid_fee <= spot_price < 0:
                        # 浅负价陷阱：不操作
                        strategy_log.append(f"[{h}:00] ⚠️ 浅负价({spot_price:.2f})：不操作（实际买电成本{spot_price + grid_fee:.2f}仍为正）")
                    elif spot_price < 0.3:
                        # 正低价：充电
                        strategy_log.append(f"[{h}:00] 低价({spot_price:.2f})：充电")
                        daily_profit_ai -= capacity_kwh * (spot_price + grid_fee) / 2
            else:
                # 无AI：固定时段
                charge_price = float(np.mean(buy_price_curve[0:4]))
                discharge_price = float(np.mean(sell_price_curve[14:18]))
                daily_profit_no_ai += (capacity_kwh * efficiency * discharge_price - capacity_kwh * charge_price)

        annual_profit_no_ai = daily_profit_no_ai * 330
        annual_profit_ai = daily_profit_ai * 330

        return {
            "无AI年利润": round(annual_profit_no_ai, 2) if not ai_enabled else None,
            "AI年利润": round(annual_profit_ai, 2) if ai_enabled else None,
            "策略日志（示例）": strategy_log[:5] if ai_enabled else [],
            "计算说明": "AI模式分析4种电价场景（极高价/正低价/浅负价陷阱/深负价），动态决策",
        }

    def analyze_pv_self_consumption(
        self,
        annual_load_kwh: float,
        pv_capacity_kw: float,
        pv_yield_hours: float = 1100,
        load_curve_type: str = "workday" # workday, 24h, school
    ) -> Dict[str, Any]:
        """
        分析光伏自发自用比例 (逐小时)
        
        参数:
            annual_load_kwh: 年总负荷 (kWh)
            pv_capacity_kw: 光伏装机 (kW)
            pv_yield_hours: 年利用小时数
            load_curve_type: 负荷曲线类型 (workday=工厂/办公, 24h=数据中心/生鲜, school=学校含假期)
            
        返回:
            自用比例, 自用电量, 上网电量
        """
        hours = 8760
        
        # 1. 生成光伏发电曲线 (简化的钟形曲线)
        # 日发电分布：6点-18点，12点达到峰值
        hour_of_day = np.arange(hours) % 24
        # 正弦波模拟日照强度，仅在白昼有效
        daylight_hours = np.where((hour_of_day >= 6) & (hour_of_day <= 18), 
                                  np.sin(np.pi * (hour_of_day - 6) / 12), 0)
        # 叠加季节性因子 (夏天强冬天弱)
        day_of_year = np.arange(hours) / 24
        season_factor = 1 + 0.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365) # 春分前后开始增强
        
        raw_pv_curve = daylight_hours * season_factor
        
        # 归一化并缩放至总发电量
        total_raw = np.sum(raw_pv_curve)
        target_total_gen = pv_capacity_kw * pv_yield_hours
        
        if total_raw > 0:
            pv_curve = raw_pv_curve / total_raw * target_total_gen
        else:
            pv_curve = np.zeros(hours)
            
        # 2. 生成负荷曲线
        # 基础波动
        base_fluctuation = 0.8 + 0.4 * np.random.rand(hours) # 0.8~1.2
        
        if load_curve_type == "school":
            # 学校模式：寒暑假低负荷
            # 寒假: 1月中-2月中 (约30天，第15-45天) -> hours 360-1080
            # 暑假: 7月初-8月底 (约60天，第180-240天) -> hours 4320-5760
            is_vacation = ((day_of_year >= 15) & (day_of_year <= 45)) | \
                          ((day_of_year >= 180) & (day_of_year <= 240))
            
            # 正常日: 8-17点高负荷
            work_hours = np.where((hour_of_day >= 8) & (hour_of_day <= 17), 1.5, 0.3)
            # 假期: 整体低负荷
            vacation_factor = np.where(is_vacation, 0.2, 1.0)
            
            raw_load_curve = work_hours * vacation_factor * base_fluctuation
            
        elif load_curve_type == "24h":
            # 24小时持续负荷
            raw_load_curve = np.ones(hours) * base_fluctuation
            
        else: # workday (default)
            # 工厂/办公: 8-18点高负荷, 中午小休
            work_factor = np.where((hour_of_day >= 8) & (hour_of_day <= 18), 1.0, 0.2)
            # 区分工作日/周末 (每7天休1天)
            is_weekend = (day_of_year.astype(int) % 7) == 6
            weekend_factor = np.where(is_weekend, 0.4, 1.0)
            
            raw_load_curve = work_factor * weekend_factor * base_fluctuation

        # 归一化负荷
        total_raw_load = np.sum(raw_load_curve)
        if total_raw_load > 0:
            load_curve = raw_load_curve / total_raw_load * annual_load_kwh
        else:
            load_curve = np.zeros(hours)
            
        # 3. 逐小时对比
        self_use_curve = np.minimum(load_curve, pv_curve)
        feed_in_curve = pv_curve - self_use_curve
        
        total_self_use = np.sum(self_use_curve)
        total_feed_in = np.sum(feed_in_curve)
        total_gen = np.sum(pv_curve)
        
        self_use_ratio = total_self_use / total_gen if total_gen > 0 else 0
        
        return {
            "self_use_ratio": self_use_ratio,
            "self_use_kwh": total_self_use,
            "feed_in_kwh": total_feed_in,
            "total_gen_kwh": total_gen
        }

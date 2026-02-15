"""
数据模型定义
项目 → 楼栋 → 设备组 三级层次结构
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

# ==================== 枚举类型 ====================

class ACType(Enum):
    SPLIT = "分体机"
    CENTRAL = "中央空调"
    VRV = "多联机"

class LightingType(Enum):
    FLUORESCENT = "荧光灯管"
    LED_TUBE = "LED灯管"
    LED_DOWNLIGHT = "LED筒灯"
    LED_PANEL = "LED面板灯"
    HIGH_BAY = "工矿灯"

class PricingMode(Enum):
    TOU = "分时电价"
    DYNAMIC = "动态电价"
    FIXED = "固定电价"

class MicrogridScenario(Enum):
    """微电网场景类型"""
    PEAK_VALLEY = "峰谷电价套利"
    ISLAND_MODE = "电网故障/孤岛运行"
    EV_CHARGING = "电动汽车有序充电"
    AI_OPTIMIZATION = "AI优化对比"

class WeatherCondition(Enum):
    """天气条件"""
    SUNNY = "晴天"
    CLOUDY = "阴天"
    RAINY = "雨天"

# ==================== 设备组件 ====================

@dataclass
class ACSystem:
    """空调系统配置"""
    name: str
    ac_type: ACType
    # 分体机参数
    unit_count: int = 0           # 台数
    unit_power_kw: float = 0      # 单台功率 kW
    unit_cop: float = 3.0         # 单台COP
    # 中央空调参数
    cooling_capacity_kw: float = 0  # 制冷量 kW
    central_cop: float = 4.5        # 系统COP
    # 通用参数
    daily_run_hours: float = 8.0
    annual_days: int = 200          # 年运行天数（制冷季）

    def get_annual_consumption_kwh(self) -> float:
        """计算年耗电量"""
        if self.ac_type == ACType.SPLIT:
            return self.unit_count * self.unit_power_kw * self.daily_run_hours * self.annual_days
        else:
            # 中央空调：制冷量 / COP = 电功率
            power_kw = self.cooling_capacity_kw / self.central_cop
            return power_kw * self.daily_run_hours * self.annual_days

@dataclass
class LightingZone:
    """照明区域"""
    name: str
    lighting_type: LightingType
    fixture_count: int
    power_per_fixture_w: float      # 改造前单灯功率
    new_power_per_fixture_w: float  # 改造后单灯功率
    daily_hours: float = 10.0
    annual_days: int = 365

    def get_annual_saving_kwh(self) -> float:
        """计算年节电量"""
        delta_power_kw = (self.power_per_fixture_w - self.new_power_per_fixture_w) / 1000.0
        return self.fixture_count * delta_power_kw * self.daily_hours * self.annual_days

@dataclass
class LightingSystem:
    """照明系统（多区域）"""
    zones: List[LightingZone] = field(default_factory=list)

    def get_total_annual_saving_kwh(self) -> float:
        return sum(z.get_annual_saving_kwh() for z in self.zones)

# ==================== 楼栋 ====================

@dataclass
class Building:
    """楼栋"""
    name: str
    area_sqm: float                      # 建筑面积 m²
    thermal_coefficient: float = 0.5     # 热导系数 (0-1, 值越小保温越好)
    ac_systems: List[ACSystem] = field(default_factory=list)
    lighting_system: Optional[LightingSystem] = None

# ==================== 共享资产 ====================

@dataclass
class PVSystem:
    """光伏系统"""
    capacity_kw: float
    annual_yield_hours: float = 1100
    self_use_ratio: float = 0.8
    investment_per_w: float = 3.0

@dataclass
class StorageSystem:
    """储能系统"""
    capacity_kwh: float
    power_kw: float
    efficiency_rt: float = 0.90
    investment_per_kwh: float = 1300
    cycles_per_day: int = 2

@dataclass
class ChargingSystem:
    """充电桩系统"""
    charger_count: int
    power_per_charger_kw: float = 7.0
    daily_util_hours: float = 4.0
    service_fee_per_kwh: float = 0.5
    investment_per_charger: float = 3000

# ==================== 电价配置 ====================

@dataclass
class TOUPeriod:
    """分时电价时段"""
    name: str           # 尖/峰/平/谷
    price: float        # 电价 RMB/kWh
    start_hour: int     # 开始小时 (0-23)
    end_hour: int       # 结束小时 (0-23)

@dataclass
class PricingConfig:
    """电价配置"""
    mode: PricingMode
    fixed_price: float = 0.85               # 固定电价
    tou_periods: List[TOUPeriod] = field(default_factory=list)
    grid_fee: float = 0.2                   # 过网费（输配电费）

    def get_price_at_hour(self, hour: int) -> float:
        """获取指定小时的电价"""
        if self.mode == PricingMode.FIXED:
            return self.fixed_price
        elif self.mode == PricingMode.TOU:
            for period in self.tou_periods:
                if period.start_hour <= hour < period.end_hour:
                    return period.price
            # 默认返回第一个时段价格
            return self.tou_periods[0].price if self.tou_periods else 0.85
        else:
            # 动态电价：需要外部注入价格曲线
            return 0.85

# ==================== 项目 ====================


@dataclass
class Transformer:
    """变压器/接入点"""
    name: str
    capacity_kva: float
    # 关联的户号 (用于计算基准负荷)
    account_ids: List[str] = field(default_factory=list)
    # 关联的资产 (分台变独立配置)
    pv_capacity_kw: float = 0
    storage_capacity_kwh: float = 0
    charging_power_kw: float = 0
    
    # 计算结果缓存
    annual_load_kwh: float = 0
    annual_pv_generation_kwh: float = 0
    self_use_ratio: float = 0.8  # 该台变的自用比例

@dataclass
class Project:
    """零碳项目"""
    name: str
    location: str
    buildings: List[Building] = field(default_factory=list)
    
    # 资产配置 (全局或汇总)
    pv_system: Optional[PVSystem] = None
    storage_system: Optional[StorageSystem] = None
    charging_system: Optional[ChargingSystem] = None
    
    # 多台变配置 (New)
    transformers: List[Transformer] = field(default_factory=list)
    
    pricing_config: Optional[PricingConfig] = None
    emission_factor: float = 0.5703         # 电网排放因子 tCO2/MWh
    
    # AI平台配置
    ai_enabled: bool = False
    ai_efficiency_pct: float = 0.05         # 能效提升率
    ai_load_shift_pct: float = 0.03         # 负荷优化率
    ai_implementation_cost: float = 200000
    ai_annual_saas_fee: float = 50000

# ==================== 微电网配置 ====================

@dataclass
class MicrogridConfig:
    """微电网配置"""
    # 组件容量
    pv_capacity_kw: float = 1000
    storage_capacity_kwh: float = 500
    storage_power_kw: float = 200
    charging_power_kw: float = 70
    ac_capacity_kw: float = 300
    lighting_power_kw: float = 50
    production_load_kw: float = 500

    # 仿真参数
    simulation_hours: int = 24
    ai_enabled: bool = True
    ai_efficiency_gain: float = 0.05

    # 天气影响因子
    weather_impact_factors: Dict[str, float] = field(default_factory=lambda: {
        "sunny": 1.0,
        "cloudy": 0.6,
        "rainy": 0.3
    })

    # 关键负荷比例（孤岛模式使用）
    critical_load_ratio: float = 0.7

    # SOC保护阈值
    soc_min: float = 0.2
    soc_max: float = 0.95


"""
Pydantic模型定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ========== 计算请求/响应 ==========

class SolarCalculationRequest(BaseModel):
    """光伏计算请求"""
    capacity_kw: float = Field(..., description="光伏装机容量 (kW)")
    yield_hours: float = Field(default=1100, description="年利用小时数")
    self_use_ratio: float = Field(default=0.8, description="自用比例 (0-1)")
    buy_price: float = Field(default=0.8, description="购电价格 (元/kWh)")
    sell_price: float = Field(default=0.35, description="上网电价 (元/kWh)")
    cost_per_w: float = Field(default=3.0, description="单位投资 (元/W)")
    emission_factor: float = Field(default=0.5703, description="碳排放因子 (tCO2/MWh)")
    include_hourly: bool = Field(default=False, description="是否返回逐时数据")


class StorageCalculationRequest(BaseModel):
    """储能计算请求"""
    capacity_kwh: float = Field(..., description="储能容量 (kWh)")
    power_kw: float = Field(..., description="充放功率 (kW)")
    efficiency: float = Field(default=0.9, description="往返效率 (0-1)")
    cycles_per_day: int = Field(default=2, description="每日循环次数")
    grid_fee: float = Field(default=0.2, description="过网费 (元/kWh)")
    ai_enabled: bool = Field(default=False, description="是否启用AI优化")
    price_curve: List[float] = Field(default=[], description="24小时电价曲线")


class HVACCalculationRequest(BaseModel):
    """空调计算请求"""
    buildings: List[Dict[str, Any]] = Field(default=[], description="建筑列表")
    electricity_price: float = Field(default=0.85, description="电价 (元/kWh)")
    current_avg_cop: float = Field(default=3.2, description="当前平均COP")
    target_cop: float = Field(default=4.5, description="目标COP")
    ai_enabled: bool = Field(default=False, description="是否启用AI预冷")
    ai_precool_saving_pct: float = Field(default=0.08, description="AI预冷节省比例")
    emission_factor: float = Field(default=0.5703, description="碳排放因子")


class LightingCalculationRequest(BaseModel):
    """照明计算请求"""
    areas: List[Dict[str, Any]] = Field(default=[], description="区域列表")
    electricity_price: float = Field(default=0.85, description="电价 (元/kWh)")
    ai_enabled: bool = Field(default=False, description="是否启用AI调光")
    ai_dimming_saving_pct: float = Field(default=0.15, description="AI调光节省比例")
    emission_factor: float = Field(default=0.5703, description="碳排放因子")


class EVChargingCalculationRequest(BaseModel):
    """充电桩计算请求"""
    charger_count: int = Field(..., description="充电桩数量")
    power_per_charger_kw: float = Field(default=7.0, description="单桩功率 (kW)")
    daily_util_hours: float = Field(default=4.0, description="日均利用小时")
    service_fee_per_kwh: float = Field(default=0.5, description="服务费 (元/kWh)")
    investment_per_charger: float = Field(default=3000, description="单桩投资 (元)")


# ========== 模拟请求/响应 ==========

class SimulationRequest(BaseModel):
    """8760小时模拟请求"""
    province: str = Field(default="广东省", description="省份")
    price_mode: Literal["tou", "fixed", "spot"] = Field(default="tou", description="电价模式")
    fixed_price: float = Field(default=0.85, description="固定电价")
    tou_segments: List[Dict[str, Any]] = Field(default=[], description="分时电价段")
    spot_prices: List[float] = Field(default=[], description="现货价格曲线")
    pv_capacity_kw: float = Field(default=0, description="光伏容量")
    storage_capacity_kwh: float = Field(default=0, description="储能容量")
    storage_power_kw: float = Field(default=0, description="储能功率")
    annual_load_kwh: float = Field(default=0, description="年负荷")
    include_hourly_data: bool = Field(default=True, description="是否包含逐时数据")


class SimulationOutput(BaseModel):
    """模拟输出"""
    pv: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    hvac: Optional[Dict[str, Any]] = None
    aggregate: Optional[Dict[str, Any]] = None


# ========== 计算结果 ==========

class CalculationResult(BaseModel):
    """计算结果"""
    investment: float = Field(..., description="投资 (万元)")
    annual_saving: float = Field(..., description="年收益 (万元)")
    roi: float = Field(..., description="投资回报率 (%)")
    irr: float = Field(..., description="内部收益率 (%)")
    payback_period: float = Field(..., description="回收期 (年)")
    npv: float = Field(default=0, description="净现值 (万元)")
    carbon_reduction: float = Field(..., description="碳减排 (吨)")
    hourly_data: Optional[List[Dict[str, float]]] = None
    calculation_details: Dict[str, Any] = Field(default_factory=dict)


# ========== 持久化请求/响应 ==========

class ProjectSaveRequest(BaseModel):
    """项目保存请求"""
    project_id: Optional[str] = Field(None, description="项目ID")
    project_name: str = Field(..., description="项目名称")
    username: str = Field(default="default", description="用户名")
    config: Dict[str, Any] = Field(..., description="项目配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    version: str = Field(default="1.0", description="版本")


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    projects: List[Dict[str, Any]] = Field(default_factory=list)


class MemoryUpdateRequest(BaseModel):
    """记忆更新请求"""
    username: str = Field(default="default", description="用户名")
    updates: Dict[str, Any] = Field(..., description="更新内容")


# ========== 导出请求/响应 ==========

class ExportRequest(BaseModel):
    """导出请求"""
    project_data: Dict[str, Any] = Field(..., description="项目数据")
    project_name: str = Field(..., description="项目名称")
    export_format: Literal["json", "excel"] = Field(default="json", description="导出格式")

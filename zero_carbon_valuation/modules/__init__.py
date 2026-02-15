"""
模块导出
"""
# 基础类
from .base import BaseModule, SimulationResult, MicrogridVisualizationResult

# 数据模型
from .models import (
    ACType, LightingType, PricingMode,
    ACSystem, LightingZone, LightingSystem,
    Building, PVSystem, StorageSystem, ChargingSystem,
    TOUPeriod, PricingConfig, Project, Transformer,
    MicrogridScenario, WeatherCondition, MicrogridConfig
)

# 电价引擎
from .pricing import PricingEngine, get_guangdong_tou_template, get_jiangsu_tou_template

# 模拟引擎
from .simulation_engine import SimulationEngine, SimulationConfig

# 计算模块
from .lighting import LightingModuleV2 as LightingModule
from .ac import ACModuleV2 as ACModule
from .pv import PVModule
from .storage import StorageModuleV2 as StorageModule
from .charging import ChargingModule
from .ai_platform import AIPlatformModule
from .carbon import CarbonAssetModule
from .reporting import generate_excel_report
from .persistence import (
    register_user, login_user, save_project,
    list_projects, delete_project
)

# 微电网协调展示模块
from .microgrid_visualizer import MicrogridVisualizerModule
from .scenario_engine import ScenarioEngine, HourlySnapshot
from .visualization_engine import VisualizationEngine, get_scenario_description


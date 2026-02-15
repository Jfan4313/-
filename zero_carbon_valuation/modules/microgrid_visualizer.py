"""
微电网协调展示模块
整合场景引擎和可视化引擎
"""
from typing import Dict, Any, List, Optional
import numpy as np

from .base import BaseModule, MicrogridVisualizationResult
from .models import MicrogridScenario, WeatherCondition, MicrogridConfig
from .scenario_engine import ScenarioEngine, HourlySnapshot
from .visualization_engine import VisualizationEngine


class MicrogridVisualizerModule(BaseModule):
    """微电网协调展示模块"""

    def __init__(self):
        super().__init__("Microgrid + AI Platform Visualization")
        self.scenario_engine: Optional[ScenarioEngine] = None
        self.viz_engine: Optional[VisualizationEngine] = None

    def calculate(self, inputs: Dict[str, Any]) -> MicrogridVisualizationResult:
        """核心计算入口"""
        # 获取配置
        config = inputs.get('config', MicrogridConfig())
        scenario = inputs.get('scenario', MicrogridScenario.PEAK_VALLEY)
        weather = inputs.get('weather', WeatherCondition.SUNNY)
        hours = inputs.get('hours', 24)

        # 初始化引擎
        self.scenario_engine = ScenarioEngine(config)
        self.viz_engine = VisualizationEngine()

        # 运行仿真
        snapshots = self.scenario_engine.run_simulation(scenario, weather, hours)

        # 计算财务指标
        financials = self._calculate_financials_from_snapshots(snapshots, config)

        # 生成Sankey数据
        sankey_data = self._generate_sankey_data(snapshots)

        # 生成动画帧
        animation_frames = self.viz_engine.create_animation_frames(snapshots)

        # 计算碳减排
        carbon_reduction = self._calculate_carbon_reduction(snapshots, config)

        # 如果是AI优化对比，生成对比数据
        scenario_comparison = None
        if scenario == MicrogridScenario.AI_OPTIMIZATION:
            scenario_comparison = self._generate_ai_comparison(snapshots, config, weather, hours)

        return MicrogridVisualizationResult(
            module_name=self.name,
            annual_revenue=financials['annual_revenue'],
            total_investment=financials['total_investment'],
            annual_maintenance_cost=financials['annual_maintenance'],
            payback_period_years=financials['payback_years'],
            roi=financials['roi'],
            irr=financials['irr'],
            carbon_reduction_tons=carbon_reduction,
            hourly_snapshots=[self._snapshot_to_dict(s) for s in snapshots],
            sankey_nodes=sankey_data['nodes'],
            sankey_links=sankey_data['links'],
            animation_frames=animation_frames,
            scenario_comparison=scenario_comparison,
            calculation_details=financials
        )

    def _calculate_financials_from_snapshots(
        self,
        snapshots: List[HourlySnapshot],
        config: MicrogridConfig
    ) -> Dict[str, float]:
        """从快照计算财务指标"""
        # 年度成本
        daily_cost = sum(s.metrics.get('instant_cost', 0) for s in snapshots)
        annual_cost = daily_cost * 330  # 年运行约330天

        # 估算投资（简化计算）
        investment = (
            config.pv_capacity_kw * 3000 +  # 光伏 3元/W
            config.storage_capacity_kwh * 1300 +  # 储能 1300元/kWh
            config.charging_power_kw * 3000 +  # 充电桩 3000元/kW
            200000  # AI平台
        )

        # 维护成本
        annual_maintenance = investment * 0.02

        # 估算年收益（基于节省的电费）
        # 基准电费（无优化）
        baseline_price = np.mean([0.8] * 24)
        baseline_load = np.mean([s.metrics.get('total_load', 0) for s in snapshots])
        baseline_daily_cost = baseline_load * baseline_price * 24
        baseline_annual_cost = baseline_daily_cost * 330

        # 节省的收益
        annual_revenue = max(0, baseline_annual_cost - annual_cost)
        net_cashflow = annual_revenue - annual_maintenance

        # 财务指标
        if investment > 0 and net_cashflow > 0:
            payback = investment / net_cashflow
            total_return = (net_cashflow * 10) - investment
            roi = (total_return / investment) * 100
            cashflows = [-investment] + [net_cashflow] * 10
            try:
                irr = np.irr(cashflows) * 100
                if np.isnan(irr):
                    irr = 0.0
            except:
                irr = 0.0
        else:
            payback = 0.0
            roi = 0.0
            irr = 0.0

        return {
            'annual_revenue': annual_revenue,
            'total_investment': investment,
            'annual_maintenance': annual_maintenance,
            'annual_cost': annual_cost,
            'payback_years': round(payback, 2),
            'roi': round(roi, 2),
            'irr': round(irr, 2)
        }

    def _generate_sankey_data(
        self,
        snapshots: List[HourlySnapshot]
    ) -> Dict[str, Any]:
        """生成Sankey图数据（使用峰值时刻）"""
        if not snapshots:
            return {'nodes': [], 'links': []}

        # 使用12点（正午）的快照
        peak_snapshot = snapshots[12] if len(snapshots) > 12 else snapshots[0]

        nodes = list(peak_snapshot.nodes.keys())
        links = []

        for flow in peak_snapshot.flows:
            links.append({
                'from': flow.from_node,
                'to': flow.to_node,
                'value': abs(flow.power_kw)
            })

        return {
            'nodes': nodes,
            'links': links
        }

    def _calculate_carbon_reduction(
        self,
        snapshots: List[HourlySnapshot],
        config: MicrogridConfig
    ) -> float:
        """计算碳减排量"""
        emission_factor = 0.5703  # tCO2/MWh

        # 光伏发电总量
        total_pv_gen = sum(s.metrics.get('pv_generation', 0) for s in snapshots) * 330 / 1000  # MWh/年

        # 减排量
        carbon_reduction = total_pv_gen * emission_factor

        return carbon_reduction

    def _generate_ai_comparison(
        self,
        snapshots: List[HourlySnapshot],
        config: MicrogridConfig,
        weather: WeatherCondition,
        hours: int
    ) -> Dict[str, Any]:
        """生成AI优化对比数据"""
        # 计算固定策略（无AI）
        ai_enabled_backup = config.ai_enabled
        config.ai_enabled = False

        no_ai_engine = ScenarioEngine(config)
        snapshots_no_ai = no_ai_engine.run_simulation(
            MicrogridScenario.PEAK_VALLEY, weather, hours
        )

        config.ai_enabled = ai_enabled_backup

        # 提取对比数据
        comparison = {
            'ai_enabled': True,
            'costs_ai': [s.metrics.get('instant_cost', 0) for s in snapshots],
            'costs_no_ai': [s.metrics.get('instant_cost', 0) for s in snapshots_no_ai],
            'soc_ai': [s.metrics.get('soc', 0) for s in snapshots],
            'soc_no_ai': [s.metrics.get('soc', 0) for s in snapshots_no_ai],
            'grid_power_ai': [s.metrics.get('grid_power', 0) for s in snapshots],
            'grid_power_no_ai': [s.metrics.get('grid_power', 0) for s in snapshots_no_ai],
        }

        # 计算节省
        total_cost_ai = sum(comparison['costs_ai'])
        total_cost_no_ai = sum(comparison['costs_no_ai'])
        comparison['total_saving'] = total_cost_no_ai - total_cost_ai
        comparison['saving_percentage'] = (comparison['total_saving'] / total_cost_no_ai * 100
                                        if total_cost_no_ai > 0 else 0)

        return comparison

    def _snapshot_to_dict(self, snapshot: HourlySnapshot) -> Dict[str, Any]:
        """将快照转换为字典"""
        return {
            'hour': snapshot.hour,
            'scenario': snapshot.scenario.value,
            'weather': snapshot.weather.value,
            'nodes': {
                name: {
                    'power': node.power_kw,
                    'soc': node.soc,
                    'color': node.color
                }
                for name, node in snapshot.nodes.items()
            },
            'flows': [
                {
                    'from': flow.from_node,
                    'to': flow.to_node,
                    'power': flow.power_kw,
                    'cost': flow.cost_rmb
                }
                for flow in snapshot.flows
            ],
            'metrics': snapshot.metrics,
            'ai_decision': snapshot.ai_decision
        }

    def get_visualization_engine(self) -> Optional[VisualizationEngine]:
        """获取可视化引擎实例"""
        return self.viz_engine

    def get_scenario_engine(self) -> Optional[ScenarioEngine]:
        """获取场景引擎实例"""
        return self.scenario_engine

"""
场景仿真引擎
处理4种微电网场景的能量平衡计算和AI优化
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import numpy as np

from .models import MicrogridScenario, WeatherCondition, MicrogridConfig

# ==================== 分时电价曲线（广东模板） ====================

GUANGDONG_PRICE_CURVE = np.array([
    0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32,  # 0-7点 谷时
    1.05, 1.05, 1.05, 1.05,                          # 8-11点 峰时
    0.68, 0.68,                                        # 12-13点 平时
    1.05, 1.05, 1.05, 1.05, 1.05,                    # 14-18点 峰时
    1.35, 1.35, 1.35,                                 # 19-21点 尖峰
    0.32, 0.32, 0.32                                  # 22-23点 谷时
])

# ==================== 典型光伏发电曲线 ====================

TYPICAL_PV_CURVE_SUNNY = np.array([
    0, 0, 0, 0, 0, 0,          # 0-5点
    20, 80, 150, 250,            # 6-9点
    350, 420, 450, 450,          # 10-13点
    420, 350, 250, 150,          # 14-17点
    80, 20, 0, 0, 0, 0          # 18-23点
])  # 每kW装机每小时的kW输出

# 归一化到0-1范围
TYPICAL_PV_CURVE_SUNNY = TYPICAL_PV_CURVE_SUNNY / np.max(TYPICAL_PV_CURVE_SUNNY)

# ==================== 典型负荷曲线 ====================

TYPICAL_LOAD_PROFILE = np.array([
    0.5, 0.4, 0.4, 0.4, 0.5, 0.6,  # 0-5点
    0.8, 0.9, 1.0, 1.0,              # 6-9点
    1.0, 1.0, 0.9, 0.9,              # 10-13点
    1.0, 1.0, 0.9, 0.8,              # 14-17点
    0.9, 1.0, 0.8, 0.7, 0.6, 0.5    # 18-23点
])  # 负荷系数（0-1）

# ==================== 场景引擎 ====================

@dataclass
class EnergyFlow:
    """能量流动"""
    from_node: str
    to_node: str
    power_kw: float
    cost_rmb: float = 0

@dataclass
class NodeState:
    """节点状态"""
    name: str
    power_kw: float
    soc: Optional[float] = None  # 仅储能节点有SOC
    color: str = "#999999"

@dataclass
class HourlySnapshot:
    """某一时刻的模拟快照"""
    hour: int
    scenario: MicrogridScenario
    weather: WeatherCondition
    nodes: Dict[str, NodeState]
    flows: List[EnergyFlow]
    metrics: Dict[str, float]
    ai_decision: Optional[str] = None


class ScenarioEngine:
    """场景仿真引擎"""

    def __init__(self, config: MicrogridConfig):
        self.config = config
        self.price_curve = GUANGDONG_PRICE_CURVE

    def run_simulation(
        self,
        scenario: MicrogridScenario,
        weather: WeatherCondition,
        hours: int = 24
    ) -> List[HourlySnapshot]:
        """运行仿真"""
        if scenario == MicrogridScenario.PEAK_VALLEY:
            return self._simulate_peak_valley(weather, hours)
        elif scenario == MicrogridScenario.ISLAND_MODE:
            return self._simulate_island_mode(weather, hours)
        elif scenario == MicrogridScenario.EV_CHARGING:
            return self._simulate_ev_charging(weather, hours)
        elif scenario == MicrogridScenario.AI_OPTIMIZATION:
            return self._simulate_ai_optimization(weather, hours)
        else:
            return []

    def _calculate_pv_output(self, hour: int, weather: WeatherCondition) -> float:
        """计算光伏发电量"""
        # 基础发电曲线
        base_output = TYPICAL_PV_CURVE_SUNNY[hour % 24]

        # 天气影响
        weather_factor = self.config.weather_impact_factors.get(weather.value.lower(), 1.0)

        return self.config.pv_capacity_kw * base_output * weather_factor

    def _calculate_load(self, hour: int) -> Dict[str, float]:
        """计算各负荷"""
        load_factor = TYPICAL_LOAD_PROFILE[hour % 24]

        return {
            "ac": self.config.ac_capacity_kw * load_factor,
            "lighting": self.config.lighting_power_kw * load_factor,
            "production": self.config.production_load_kw * load_factor,
            "charging": self.config.charging_power_kw * load_factor,
        }

    def _simulate_peak_valley(
        self,
        weather: WeatherCondition,
        hours: int
    ) -> List[HourlySnapshot]:
        """峰谷电价套利场景"""
        snapshots = []
        soc = 0.5  # 初始SOC 50%

        for hour in range(hours):
            # 计算光伏发电
            pv_gen = self._calculate_pv_output(hour, weather)

            # 计算负荷
            loads = self._calculate_load(hour)
            total_load = sum(loads.values())

            # 电价
            price = self.price_curve[hour % 24]

            # 决策
            if self.config.ai_enabled:
                decision = self._ai_peak_valley_decision(soc, price, pv_gen, total_load, hour)
            else:
                decision = self._fixed_peak_valley_decision(soc, price, pv_gen, total_load, hour)

            # 更新SOC和能量流
            soc, flows, nodes, metrics = self._update_peak_valley_energy(
                soc, decision, pv_gen, loads, price, hour
            )

            snapshot = HourlySnapshot(
                hour=hour,
                scenario=MicrogridScenario.PEAK_VALLEY,
                weather=weather,
                nodes=nodes,
                flows=flows,
                metrics=metrics,
                ai_decision=decision.get("description", "")
            )
            snapshots.append(snapshot)

        return snapshots

    def _ai_peak_valley_decision(
        self,
        soc: float,
        price: float,
        pv_gen: float,
        load: float,
        hour: int
    ) -> Dict[str, float]:
        """AI峰谷决策"""
        decision = {
            'grid_charge_kw': 0,
            'grid_discharge_kw': 0,
            'pv_to_storage_kw': 0,
            'storage_to_load_kw': 0,
            'description': ""
        }

        # 光伏优先存入储能
        if soc < self.config.soc_max and pv_gen > load:
            excess_pv = pv_gen - load
            decision['pv_to_storage_kw'] = min(excess_pv, self.config.storage_power_kw)

        # 基于价格决策
        if price < 0.4:  # 低谷
            if soc < 0.9:
                decision['grid_charge_kw'] = self.config.storage_power_kw
                decision['description'] = f"低价({price:.2f})充电"
        elif price > 1.0:  # 高峰
            if soc > self.config.soc_min:
                decision['grid_discharge_kw'] = self.config.storage_power_kw
                decision['description'] = f"高价({price:.2f})放电"

        return decision

    def _fixed_peak_valley_decision(
        self,
        soc: float,
        price: float,
        pv_gen: float,
        load: float,
        hour: int
    ) -> Dict[str, float]:
        """固定峰谷决策"""
        decision = {
            'grid_charge_kw': 0,
            'grid_discharge_kw': 0,
            'pv_to_storage_kw': 0,
            'storage_to_load_kw': 0,
            'description': ""
        }

        # 固定时段策略
        if 0 <= hour % 24 < 8:  # 谷时充电
            if soc < 0.9:
                decision['grid_charge_kw'] = self.config.storage_power_kw
                decision['description'] = "谷时固定充电"
        elif 14 <= hour % 24 < 22:  # 峰时放电
            if soc > self.config.soc_min:
                decision['grid_discharge_kw'] = self.config.storage_power_kw
                decision['description'] = "峰时固定放电"

        return decision

    def _update_peak_valley_energy(
        self,
        soc: float,
        decision: Dict[str, float],
        pv_gen: float,
        loads: Dict[str, float],
        price: float,
        hour: int
    ) -> Tuple[float, List[EnergyFlow], Dict[str, NodeState], Dict[str, float]]:
        """更新峰谷能量流"""
        flows = []
        total_load = sum(loads.values())

        # 充电功率
        charge_power = decision['grid_charge_kw'] + decision['pv_to_storage_kw']
        # 放电功率
        discharge_power = decision['grid_discharge_kw']

        # 更新SOC
        net_charge = charge_power * 0.95 - discharge_power / 0.95  # 考虑效率
        soc += net_charge / self.config.storage_capacity_kwh
        soc = max(0.0, min(1.0, soc))  # 限制范围

        # 能量流
        if decision['grid_charge_kw'] > 0:
            flows.append(EnergyFlow(
                from_node="电网",
                to_node="储能",
                power_kw=decision['grid_charge_kw'],
                cost_rmb=decision['grid_charge_kw'] * price
            ))

        if decision['pv_to_storage_kw'] > 0:
            flows.append(EnergyFlow(
                from_node="光伏",
                to_node="储能",
                power_kw=decision['pv_to_storage_kw'],
                cost_rmb=0
            ))

        # 光伏直接供电
        pv_direct = min(pv_gen - decision['pv_to_storage_kw'], total_load)
        if pv_direct > 0:
            flows.append(EnergyFlow(
                from_node="光伏",
                to_node="总负荷",
                power_kw=pv_direct,
                cost_rmb=0
            ))

        # 储能放电
        if decision['grid_discharge_kw'] > 0:
            flows.append(EnergyFlow(
                from_node="储能",
                to_node="总负荷",
                power_kw=decision['grid_discharge_kw'],
                cost_rmb=0
            ))

        # 电网供电
        grid_supply = max(0, total_load - pv_direct - decision['grid_discharge_kw'])
        if grid_supply > 0:
            flows.append(EnergyFlow(
                from_node="电网",
                to_node="总负荷",
                power_kw=grid_supply,
                cost_rmb=grid_supply * price
            ))

        # 节点状态
        nodes = {
            "光伏": NodeState("光伏", pv_gen, color="#FFD700"),
            "储能": NodeState("储能", discharge_power - charge_power, soc=soc, color="#4CAF50"),
            "电网": NodeState("电网", -grid_supply - decision['grid_charge_kw'], color="#666666"),
            "总负荷": NodeState("总负荷", total_load, color="#F44336"),
            "空调": NodeState("空调", loads.get("ac", 0), color="#2196F3"),
            "照明": NodeState("照明", loads.get("lighting", 0), color="#FFEB3B"),
            "生产": NodeState("生产", loads.get("production", 0), color="#9C27B0"),
            "充电桩": NodeState("充电桩", loads.get("charging", 0), color="#FF5722"),
        }

        # 指标
        metrics = {
            'soc': soc,
            'price': price,
            'pv_generation': pv_gen,
            'total_load': total_load,
            'grid_power': grid_supply - decision['grid_charge_kw'],  # 负值表示购电
            'storage_power': discharge_power - charge_power,  # 正值表示放电
            'instant_cost': grid_supply * price
        }

        return soc, flows, nodes, metrics

    def _simulate_island_mode(
        self,
        weather: WeatherCondition,
        hours: int
    ) -> List[HourlySnapshot]:
        """孤岛模式"""
        snapshots = []
        soc = 0.8  # 孤岛前预充至80%

        for hour in range(hours):
            # 光伏发电
            pv_gen = self._calculate_pv_output(hour, weather)

            # 计算负荷
            loads = self._calculate_load(hour)
            total_load = sum(loads.values())
            critical_load = total_load * self.config.critical_load_ratio

            # 能量平衡
            net_energy = pv_gen - critical_load
            load_shedding = 0

            if net_energy > 0:
                # 剩余能量存入储能
                charge_power = min(net_energy, self.config.storage_power_kw)
                charge_amount = charge_power * 0.95  # 充电效率
                soc = min(1.0, soc + charge_amount / self.config.storage_capacity_kwh)
            else:
                # 储能放电
                discharge_needed = abs(net_energy)
                discharge_possible = min(soc * self.config.storage_capacity_kwh * 0.95,
                                       self.config.storage_power_kw)
                actual_discharge = discharge_possible
                soc -= actual_discharge / (self.config.storage_capacity_kwh * 0.95)

                # 负荷削减
                if actual_discharge < discharge_needed:
                    load_shedding = discharge_needed - actual_discharge

            # 能量流
            flows = []
            if pv_gen > 0:
                flows.append(EnergyFlow(
                    from_node="光伏",
                    to_node="总负荷",
                    power_kw=min(pv_gen, critical_load),
                    cost_rmb=0
                ))

            if net_energy > 0:
                flows.append(EnergyFlow(
                    from_node="光伏",
                    to_node="储能",
                    power_kw=min(net_energy, self.config.storage_power_kw),
                    cost_rmb=0
                ))

            if net_energy < 0 and actual_discharge > 0:
                flows.append(EnergyFlow(
                    from_node="储能",
                    to_node="总负荷",
                    power_kw=actual_discharge,
                    cost_rmb=0
                ))

            # 节点状态
            nodes = {
                "光伏": NodeState("光伏", pv_gen, color="#FFD700"),
                "储能": NodeState("储能", actual_discharge if net_energy < 0 else -min(net_energy, self.config.storage_power_kw),
                                  soc=soc, color="#4CAF50"),
                "总负荷": NodeState("总负荷", critical_load, color="#F44336"),
                "空调": NodeState("空调", loads.get("ac", 0) * self.config.critical_load_ratio, color="#2196F3"),
                "照明": NodeState("照明", loads.get("lighting", 0) * self.config.critical_load_ratio, color="#FFEB3B"),
                "生产": NodeState("生产", loads.get("production", 0) * self.config.critical_load_ratio, color="#9C27B0"),
            }

            # 指标
            metrics = {
                'soc': soc,
                'pv_generation': pv_gen,
                'total_load': critical_load,
                'load_shedding_kwh': load_shedding,
                'island_duration': hour + 1,
                'reliability': 1.0 - (load_shedding / critical_load) if critical_load > 0 else 1.0
            }

            snapshot = HourlySnapshot(
                hour=hour,
                scenario=MicrogridScenario.ISLAND_MODE,
                weather=weather,
                nodes=nodes,
                flows=flows,
                metrics=metrics,
                ai_decision="孤岛运行中"
            )
            snapshots.append(snapshot)

        return snapshots

    def _simulate_ev_charging(
        self,
        weather: WeatherCondition,
        hours: int
    ) -> List[HourlySnapshot]:
        """电动汽车有序充电场景"""
        snapshots = []
        soc = 0.5

        for hour in range(hours):
            pv_gen = self._calculate_pv_output(hour, weather)
            loads = self._calculate_load(hour)
            total_load = sum(loads.values())
            price = self.price_curve[hour % 24]

            # EV充电决策
            if self.config.ai_enabled:
                ev_power = self._ai_ev_charging(price, pv_gen, hour)
            else:
                ev_power = self.config.charging_power_kw  # 固定功率

            # 更新SOC和能量流
            soc, flows, nodes, metrics = self._update_ev_charging_energy(
                soc, ev_power, pv_gen, loads, price, hour
            )

            snapshot = HourlySnapshot(
                hour=hour,
                scenario=MicrogridScenario.EV_CHARGING,
                weather=weather,
                nodes=nodes,
                flows=flows,
                metrics=metrics,
                ai_decision=f"EV充电功率: {ev_power:.1f}kW"
            )
            snapshots.append(snapshot)

        return snapshots

    def _ai_ev_charging(
        self,
        price: float,
        pv_gen: float,
        hour: int
    ) -> float:
        """AI EV充电决策"""
        # 低价时段：满功率
        if price < 0.4:
            return self.config.charging_power_kw
        # 光伏充足：使用绿电
        elif pv_gen > 100:
            return min(self.config.charging_power_kw, pv_gen * 0.5)
        # 高价时段：降功率
        elif price > 1.0:
            return self.config.charging_power_kw * 0.3
        else:
            return self.config.charging_power_kw * 0.6

    def _update_ev_charging_energy(
        self,
        soc: float,
        ev_power: float,
        pv_gen: float,
        loads: Dict[str, float],
        price: float,
        hour: int
    ) -> Tuple[float, List[EnergyFlow], Dict[str, NodeState], Dict[str, float]]:
        """更新EV充电能量流"""
        flows = []
        total_load = sum(loads.values()) + ev_power

        # 能量流
        if pv_gen > 0:
            flows.append(EnergyFlow(
                from_node="光伏",
                to_node="总负荷",
                power_kw=min(pv_gen, total_load),
                cost_rmb=0
            ))

        grid_supply = max(0, total_load - pv_gen)
        if grid_supply > 0:
            flows.append(EnergyFlow(
                from_node="电网",
                to_node="总负荷",
                power_kw=grid_supply,
                cost_rmb=grid_supply * price
            ))

        # 节点状态
        nodes = {
            "光伏": NodeState("光伏", pv_gen, color="#FFD700"),
            "电网": NodeState("电网", -grid_supply, color="#666666"),
            "总负荷": NodeState("总负荷", total_load, color="#F44336"),
            "充电桩": NodeState("充电桩", ev_power, color="#FF5722"),
            "空调": NodeState("空调", loads.get("ac", 0), color="#2196F3"),
            "照明": NodeState("照明", loads.get("lighting", 0), color="#FFEB3B"),
            "生产": NodeState("生产", loads.get("production", 0), color="#9C27B0"),
        }

        # 指标
        metrics = {
            'soc': soc,
            'price': price,
            'pv_generation': pv_gen,
            'total_load': total_load,
            'ev_charging_power': ev_power,
            'grid_power': -grid_supply,
            'instant_cost': grid_supply * price
        }

        return soc, flows, nodes, metrics

    def _simulate_ai_optimization(
        self,
        weather: WeatherCondition,
        hours: int
    ) -> List[HourlySnapshot]:
        """AI优化对比场景（计算固定策略和AI策略）"""
        # 先计算固定策略
        snapshots_fixed = self._simulate_peak_valley(weather, hours)

        # 暂时禁用AI
        ai_enabled_backup = self.config.ai_enabled
        self.config.ai_enabled = False
        snapshots_no_ai = self._simulate_peak_valley(weather, hours)
        self.config.ai_enabled = ai_enabled_backup

        # 合并结果，添加对比信息
        results = []
        for i in range(hours):
            # AI优化后的快照
            ai_snapshot = snapshots_fixed[i]
            no_ai_snapshot = snapshots_no_ai[i]

            # 计算节省
            cost_saving = no_ai_snapshot.metrics['instant_cost'] - ai_snapshot.metrics['instant_cost']

            # 更新指标
            ai_snapshot.metrics['cost_saving'] = cost_saving
            ai_snapshot.ai_decision += f" | 节省: ¥{cost_saving:.2f}"

            results.append(ai_snapshot)

        return results

"""
可视化引擎
处理动态能量流图、Sankey图等可视化
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .scenario_engine import HourlySnapshot, EnergyFlow, NodeState

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ==================== 节点位置配置 ====================

NODE_POSITIONS = {
    '电网': {'pos': (0.5, 0.9), 'color': '#666666', 'label': '电网'},
    '光伏': {'pos': (0.2, 0.6), 'color': '#FFD700', 'label': '光伏'},
    '储能': {'pos': (0.5, 0.5), 'color': '#4CAF50', 'label': '储能'},
    '充电桩': {'pos': (0.8, 0.5), 'color': '#FF5722', 'label': '充电桩'},
    '空调': {'pos': (0.3, 0.3), 'color': '#2196F3', 'label': '空调'},
    '照明': {'pos': (0.5, 0.3), 'color': '#FFEB3B', 'label': '照明'},
    '生产': {'pos': (0.7, 0.3), 'color': '#9C27B0', 'label': '生产'},
    '总负荷': {'pos': (0.5, 0.1), 'color': '#F44336', 'label': '总负荷'},
}

NODE_COLORS = {
    '电网': '#666666',
    '光伏': '#FFD700',
    '储能': '#4CAF50',
    '充电桩': '#FF5722',
    '空调': '#2196F3',
    '照明': '#FFEB3B',
    '生产': '#9C27B0',
    '总负荷': '#F44336',
}


# ==================== 可视化引擎类 ====================

class VisualizationEngine:
    """可视化引擎"""

    def __init__(self):
        self.node_positions = NODE_POSITIONS.copy()
        self.node_colors = NODE_COLORS.copy()

    def create_dynamic_energy_flow(
        self,
        snapshot: HourlySnapshot,
        width: int = 700,
        height: int = 500
    ) -> go.Figure:
        """创建动态能量流图"""
        if not PLOTLY_AVAILABLE:
            return self._create_placeholder()

        fig = go.Figure()

        # 添加节点
        for node_name, node in snapshot.nodes.items():
            pos = self.node_positions.get(node_name, {'pos': (0.5, 0.5)})
            fig.add_trace(go.Scatter(
                x=[pos['pos'][0]],
                y=[pos['pos'][1]],
                mode='markers+text',
                marker=dict(
                    size=40,
                    color=node.color,
                    line=dict(color='black', width=2)
                ),
                text=[node_name],
                textposition='bottom center',
                name=node_name,
                hovertemplate=f"<b>{node_name}</b><br>功率: {node.power_kw:.1f} kW"
                + f"<br>SOC: {node.soc*100:.1f}%" if node.soc is not None else ""
                + "<extra></extra>",
                showlegend=False
            ))

        # 添加能量流箭头
        for flow in snapshot.flows:
            from_node = snapshot.nodes.get(flow.from_node)
            to_node = snapshot.nodes.get(flow.to_node)

            if from_node and to_node:
                from_pos = self.node_positions.get(flow.from_node, {'pos': (0.5, 0.5)})
                to_pos = self.node_positions.get(flow.to_node, {'pos': (0.5, 0.5)})

                # 线宽表示功率大小
                line_width = max(2, abs(flow.power_kw) / 20)
                line_color = self._get_flow_color(flow.power_kw)

                fig.add_trace(go.Scatter(
                    x=[from_pos['pos'][0], to_pos['pos'][0]],
                    y=[from_pos['pos'][1], to_pos['pos'][1]],
                    mode='lines',
                    line=dict(width=line_width, color=line_color),
                    hoverinfo='text',
                    text=f"{flow.from_node} → {flow.to_node}<br>"
                          f"功率: {flow.power_kw:.1f} kW<br>"
                          f"成本: ¥{flow.cost_rmb:.2f}",
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False
                ))

        # 更新布局
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 1]),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 1]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=height,
            width=width,
            annotations=[
                dict(
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    text=f"时间: {snapshot.hour:02d}:00 | 天气: {snapshot.weather.value} | "
                          f"场景: {snapshot.scenario.value}",
                    showarrow=False,
                    font=dict(size=14, color='#333333'),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='#333333',
                    borderwidth=1,
                    borderpad=5
                ),
                dict(
                    x=0.02, y=0.02,
                    xref='paper', yref='paper',
                    text=f"AI决策: {snapshot.ai_decision or '无'}",
                    showarrow=False,
                    font=dict(size=12, color='#666666'),
                    bgcolor='rgba(200,200,200,0.5)'
                )
            ]
        )

        return fig

    def create_sankey_diagram(
        self,
        snapshot: HourlySnapshot,
        width: int = 800,
        height: int = 400
    ) -> go.Figure:
        """创建Sankey能量平衡图"""
        if not PLOTLY_AVAILABLE:
            return self._create_placeholder()

        # 提取所有节点
        all_nodes = list(snapshot.nodes.keys())

        # 构建Sankey数据
        labels = []
        source = []
        target = []
        values = []

        for flow in snapshot.flows:
            if flow.from_node not in labels:
                labels.append(flow.from_node)
            if flow.to_node not in labels:
                labels.append(flow.to_node)

            source.append(labels.index(flow.from_node))
            target.append(labels.index(flow.to_node))
            values.append(abs(flow.power_kw))

        # 节点颜色
        node_colors = [self.node_colors.get(node, '#999999') for node in labels]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=labels,
                color=node_colors
            ),
            link=dict(
                source=source,
                target=target,
                value=values,
                color='rgba(0,0,0,0.2)'
            )
        )])

        fig.update_layout(
            title_text=f"能量流动平衡 - {snapshot.hour:02d}:00",
            font_size=12,
            height=height,
            width=width,
            margin=dict(l=0, r=0, t=30, b=0)
        )

        return fig

    def create_metrics_panel(self, snapshot: HourlySnapshot) -> Dict[str, Any]:
        """创建指标面板数据"""
        metrics = snapshot.metrics

        panel_data = {
            'SOC': {
                'value': f"{metrics.get('soc', 0) * 100:.1f}%",
                'delta': f"{(metrics.get('soc', 0) - 0.5) * 100:+.1f}%" if 'soc' in metrics else None
            },
            '光伏发电': {
                'value': f"{metrics.get('pv_generation', 0):.1f} kW",
                'delta': None
            },
            '储能功率': {
                'value': f"{metrics.get('storage_power', 0):+.1f} kW",
                'delta': None,
                'delta_color': 'normal' if metrics.get('storage_power', 0) >= 0 else 'inverse'
            },
            '当前电价': {
                'value': f"¥{metrics.get('price', 0.8):.3f}/kWh",
                'delta': None
            },
            '电网交互': {
                'value': f"{metrics.get('grid_power', 0):+.1f} kW",
                'delta': "购电" if metrics.get('grid_power', 0) > 0 else "售电" if metrics.get('grid_power', 0) < 0 else "无"
            },
            '总负荷': {
                'value': f"{metrics.get('total_load', 0):.1f} kW",
                'delta': None
            },
            '瞬时成本': {
                'value': f"¥{metrics.get('instant_cost', 0):.2f}",
                'delta': f"¥{metrics.get('cost_saving', 0):+.2f}" if 'cost_saving' in metrics else None
            },
        }

        # 孤岛模式特殊指标
        if 'load_shedding_kwh' in metrics:
            panel_data['负荷削减'] = {
                'value': f"{metrics.get('load_shedding_kwh', 0):.1f} kW",
                'delta': None
            }
            panel_data['供电可靠性'] = {
                'value': f"{metrics.get('reliability', 1.0) * 100:.1f}%",
                'delta': None
            }

        # EV充电特殊指标
        if 'ev_charging_power' in metrics:
            panel_data['EV充电功率'] = {
                'value': f"{metrics.get('ev_charging_power', 0):.1f} kW",
                'delta': None
            }

        return panel_data

    def create_animation_frames(
        self,
        snapshots: List[HourlySnapshot]
    ) -> List[Dict[str, Any]]:
        """生成动画帧数据"""
        frames = []

        for snapshot in snapshots:
            frame_data = {
                'hour': snapshot.hour,
                'nodes': {name: {'power': node.power_kw, 'soc': node.soc, 'color': node.color}
                          for name, node in snapshot.nodes.items()},
                'flows': [{'from': flow.from_node, 'to': flow.to_node, 'power': flow.power_kw}
                          for flow in snapshot.flows],
                'metrics': snapshot.metrics,
                'ai_decision': snapshot.ai_decision
            }
            frames.append(frame_data)

        return frames

    def create_comparison_chart(
        self,
        snapshots_ai: List[HourlySnapshot],
        snapshots_no_ai: List[HourlySnapshot],
        width: int = 800,
        height: int = 400
    ) -> go.Figure:
        """创建AI优化对比图表"""
        if not PLOTLY_AVAILABLE:
            return self._create_placeholder()

        hours = [s.hour for s in snapshots_ai]

        # 提取数据
        costs_ai = [s.metrics.get('instant_cost', 0) for s in snapshots_ai]
        costs_no_ai = [s.metrics.get('instant_cost', 0) for s in snapshots_no_ai]
        savings = [snapshots_no_ai[i].metrics.get('instant_cost', 0) -
                   snapshots_ai[i].metrics.get('instant_cost', 0)
                   for i in range(len(hours))]

        fig = go.Figure()

        # AI优化成本
        fig.add_trace(go.Scatter(
            x=hours,
            y=costs_ai,
            mode='lines+markers',
            name='AI优化',
            line=dict(color='#4CAF50', width=2),
            marker=dict(size=6)
        ))

        # 固定策略成本
        fig.add_trace(go.Scatter(
            x=hours,
            y=costs_no_ai,
            mode='lines+markers',
            name='固定策略',
            line=dict(color='#FF5722', width=2),
            marker=dict(size=6)
        ))

        # 节省
        fig.add_trace(go.Bar(
            x=hours,
            y=savings,
            name='节省',
            marker=dict(color='#FFD700', opacity=0.5)
        ))

        fig.update_layout(
            title_text="AI优化前后成本对比",
            xaxis_title="时间 (小时)",
            yaxis_title="瞬时成本 (元)",
            height=height,
            width=width,
            barmode='overlay',
            hovermode='x unified'
        )

        return fig

    def _get_flow_color(self, power: float) -> str:
        """根据功率获取颜色"""
        if power > 0:
            return '#4CAF50'  # 绿色 - 正向流动
        elif power < 0:
            return '#FF5722'  # 橙色 - 反向流动
        else:
            return '#999999'  # 灰色 - 无流动

    def _create_placeholder(self) -> go.Figure:
        """创建占位符图表（当Plotly不可用时）"""
        fig = go.Figure()
        fig.add_annotation(
            text="Plotly未安装，无法显示图表<br>请运行: pip install plotly",
            xref='paper', yref='paper',
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='gray')
        )
        return fig


# ==================== 辅助函数 ====================

def get_scenario_description(scenario_type: str) -> str:
    """获取场景说明"""
    descriptions = {
        "峰谷电价套利": """
**场景描述**:
利用分时电价差进行储能充放电套利

**策略**:
- 低谷时段(0:00-8:00): 低价充电
- 高峰时段(14:00-22:00): 高价放电
- 光伏优先自用，余电存入储能

**AI优化**:
- 动态调整充放电窗口
- 避开峰电高价时段购电
- 最大化光伏自用率
        """,

        "电网故障/孤岛运行": """
**场景描述**:
电网故障时，微网独立运行

**策略**:
- 光伏+储能供给关键负荷
- SOC<20%时启动负荷削减
- 故障前预充储能至80%

**关键指标**:
- 供电可靠性
- 负荷削减量
- 持续供电时长
        """,

        "电动汽车有序充电": """
**场景描述**:
多辆电动汽车同时充电的负荷管理

**策略**:
- 低谷电价时段优先充电
- 光伏充足时优先使用绿电
- 动态分配充电功率

**AI优化**:
- 预测车辆到达/离开时间
- 最小化充电成本
- 平衡电网负荷
        """,

        "AI优化对比": """
**场景描述**:
对比AI优化前后的能量分配和成本

**对比项**:
- 能量分配策略
- 储能充放电时机
- 光伏自用率
- 总用电成本
        """
    }

    return descriptions.get(scenario_type, "暂无说明")

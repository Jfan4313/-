import streamlit as st
import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go

# 必须是第一个Streamlit命令
st.set_page_config(page_title="零碳项目收益估值系统", layout="wide")

# Set default Plotly theme to 'plotly_white' for academic/paper style
pio.templates.default = "plotly_white"

from modules import (
    ACType, LightingType, PricingMode,
    PricingEngine, get_guangdong_tou_template, get_jiangsu_tou_template,
    LightingModule, ACModule, PVModule, StorageModule,
    ChargingModule, AIPlatformModule, CarbonAssetModule,
    generate_excel_report, SimulationEngine, SimulationConfig,
    register_user, login_user, save_project, list_projects, delete_project,
    MicrogridVisualizerModule, VisualizationEngine, ScenarioEngine,
    MicrogridScenario, WeatherCondition, MicrogridConfig, get_scenario_description
)

# 状态同步回调函数
def update_from_editor(target_key, editor_key):
    """从DataEditor的临时State同步到持久化State"""
    if editor_key in st.session_state:
        st.session_state[target_key] = st.session_state[editor_key]

# ==================== Concise Report Style (Academic/Paper) ====================
st.markdown("""
<style>
    /* 引入字体：Inter (UI) 和 Merriweather (标题/数据) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Merriweather:wght@300;400;700&display=swap');

    /* === 全局变量 (学术报告风格) === */
    :root {
        --primary-color: #003366;    /* Academic Navy Blue */
        --primary-light: #E6EEF5;    /* Very Light Blue */
        --bg-color: #FFFFFF;         /* Pure White (Paper) */
        --surface-color: #FFFFFF;    /* White */
        --text-color: #111111;       /* Near Black (Ink) */
        --text-light: #555555;       /* Dark Grey */
        --accent-color: #800000;     /* Maroon (Highlights) */
        --border-color: #DDDDDD;     /* Light Grey Border */
        --shadow-sm: none;           /* Flat Design for Paper Feel */
        --shadow-md: 0 4px 6px rgba(0,0,0,0.05); /* Very subtle if needed */
        --radius-sm: 2px;
        --radius-md: 4px;
    }

    /* === 全局样式重置 & 布局优化 === */
    .stApp {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        line-height: 1.6; /* 增加行高，防止重叠 */
    }
    
    /* 修正颜色覆盖：移除 !important 以允许 Streamlit 隐藏内部标签 */
    .stApp p, .stApp div, .stApp span, 
    .stMarkdown, .stText, 
    h1, h2, h3, h4, h5, h6,
    .stSelectbox label, .stNumberInput label, .stTextInput label {
        color: var(--text-color);
    }

    /* 恢复Primary Color的组件 */
    h1, .stMetricValue {
        color: var(--primary-color) !important;
    }
    
    /* 标题样式：使用衬线体 (Serif) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Merriweather', serif !important;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--primary-color) !important;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    
    /* 主标题特殊处理 */
    h1 {
        font-size: 2.5rem !important;
        border-bottom: 3px solid var(--primary-color);
        padding-bottom: 0.5rem;
        margin-top: 0;
    }

    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border-color);
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: var(--text-color) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* === 组件样式 (Flat & Minimalist) === */
    /* Metric / Stat Card */
    div[data-testid="stMetric"] {
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--primary-color); /* Left accent bar */
        border-radius: var(--radius-sm);
        padding: 1rem;
        box-shadow: var(--shadow-sm);
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--text-light) !important;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'Merriweather', serif !important;
        color: var(--primary-color) !important;
        font-weight: 700;
        font-size: 1.8rem !important;
    }

    /* Tabs 样式 (简洁线条) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0px;
        margin-bottom: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 3rem;
        height: auto;
        background-color: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        color: var(--text-light) !important;
        font-weight: 600;
        font-size: 1rem;
        padding: 0 0.5rem;
        margin-bottom: -2px;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary-color) !important;
        border-bottom: 3px solid var(--primary-color);
        background-color: transparent;
    }
    
    /* 按钮样式 (Secondary Action style, minimalist) */
    button[data-testid="stBaseButton-primary"] {
        background-color: var(--primary-color) !important;
        border: 1px solid var(--primary-color) !important;
        color: white !important;
        border-radius: var(--radius-sm);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.2s;
    }
    
    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #002244 !important; /* Darker Navy */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    button[data-testid="stBaseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
        border-radius: var(--radius-sm);
        font-family: 'Inter', sans-serif;
    }
    
    button[data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--text-light) !important;
    }

    /* 数据表格 (学术风格 - 三线表) */
    .stDataFrame {
        border: none;
        border-top: 2px solid var(--text-color);
        border-bottom: 2px solid var(--text-color);
    }
    .stDataFrame thead tr th {
        border-bottom: 1px solid var(--text-color) !important;
        font-weight: 700;
    }

    /* Expander (Clean Box) */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm);
        margin-bottom: 1rem;
    }
    
    [data-testid="stExpander"] summary {
        background-color: #FFFFFF !important;
        color: var(--text-color) !important;
        font-weight: 600;
    }
    
    [data-testid="stExpander"] summary:hover {
        background-color: #F8F9FA !important;
    }

    [data-testid="stExpander"] > div[role="region"] {
        background-color: #FFFFFF !important;
        border-top: 1px solid var(--border-color);
        padding: 1rem;
    }
    
    /* Chart Containers */
    .stPlotlyChart {
        border: 1px solid #EEEEEE;
        padding: 10px;
        background-color: white !important;
        border-radius: var(--radius-sm);
    }

    /* Input Fields - Deep Fix for White Theme */
    div[data-baseweb="select"] > div, 
    input[type="text"], 
    input[type="number"],
    .stSelectbox div[data-baseweb="select"],
    div[data-testid="stMarkdownContainer"] p {
        background-color: #FFFFFF !important;
        color: var(--text-color) !important;
    }

    div[data-baseweb="select"] {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* Ensure dropdown list is also white */
    div[data-baseweb="popover"] ul {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li {
        color: var(--text-color) !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #F0F2F6 !important;
    }
    
    /* 分割线 */
    hr {
        border-top: 1px solid var(--border-color);
        margin: 2rem 0;
    }

</style>
""", unsafe_allow_html=True)

# ==================== 用户认证与项目管理 ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# 侧边栏登录控制
with st.sidebar:
    if not st.session_state.logged_in:
        st.title("👤 用户登录")
        auth_mode = st.radio("模式", ["登录", "注册"], horizontal=True)
        login_user_input = st.text_input("用户名", key="login_user")
        login_pw_input = st.text_input("密码", type="password", key="login_pw")
        
        if auth_mode == "登录":
            if st.button("立即登录", use_container_width=True, type="primary"):
                if login_user(login_user_input, login_pw_input):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user_input
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
        else:
            if st.button("完成注册", use_container_width=True):
                if login_user_input and login_pw_input:
                    success, msg = register_user(login_user_input, login_pw_input)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("请输入用户名和密码")
    else:
        st.markdown(f"欢迎, **{st.session_state.username}**")
        if st.button("退出账户", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        st.markdown("---")
        st.subheader("📂 项目记录中心")
        
        # 保存项目
        with st.expander("💾 保存当前配置"):
            p_name = st.text_input("项目存档名称", placeholder="输入项目名称...")
            if st.button("立即存盘", use_container_width=True, type="primary"):
                if p_name:
                    # 提取需要持久化的状态
                    persist_keys = [
                        "baseline", "modules_result", "transformers_list", 
                        "account_tf_mapping", "pv_tf_config", 
                        "project_scenario", "view_mode", "project_name",
                        "pricing_mode", "fixed_price", "base_price", "volatility",
                        "tou_option", "tou_periods", "tou_config",
                        "project_mode", "emc_ratio", "emc_years",
                        "emission_factor"
                    ]
                    save_data = {k: st.session_state[k] for k in persist_keys if k in st.session_state}
                    if save_project(st.session_state.username, p_name, save_data):
                        st.toast(f"✅ 项目【{p_name}】保存成功！")
                    else:
                        st.error("保存失败，请重试")
                else:
                    st.warning("名称不能为空")

        # 加载项目
        with st.expander("📖 载入历史记录"):
            projs = list_projects(st.session_state.username)
            if not projs:
                st.caption("暂无历史记录")
            else:
                p_display_list = [f"{p['project_name']} ({p['timestamp'][5:16].replace('T', ' ')})" for p in projs]
                selected_idx = st.selectbox("选择要载入的项目", range(len(p_display_list)), format_func=lambda i: p_display_list[i])
                
                l_col1, l_col2 = st.columns(2)
                if l_col1.button("确认载入", use_container_width=True):
                    selected_data = projs[selected_idx]["data"]
                    # 恢复状态
                    for k, v in selected_data.items():
                        st.session_state[k] = v
                    st.success("配置已成功载入")
                    st.rerun()
                
                if l_col2.button("删除记录", use_container_width=True):
                    if delete_project(st.session_state.username, projs[selected_idx]["filename"]):
                        st.rerun()

# 强制登录拦截
if not st.session_state.logged_in:
    st.title("零碳项目收益估值系统")
    st.info("请通过左侧边栏登录后开始使用系统。")
    st.stop()

st.title("零碳项目收益估值系统")
st.caption("CONCISE REPORT SYSTEM | 节能改造前后对比 | 光储充分项计算")
st.markdown("---")


# ==================== 场景配置 ====================
SCENARIO_CONFIG = {
    "🏭 零碳工厂": {
        "building_types": ["工厂/仓库"],
        "step1_tabs": [
            {"label": "📊 基本信息", "key": "basic"},
            {"label": "💡 照明设备", "key": "lighting"},
            {"label": "❄️ 空调设备", "key": "ac"},
            {"label": "🚿 热水设备", "key": "hotwater"},  # 工厂宿舍/食堂可能需要
            {"label": "🏭 动力设备", "key": "motors"},  # 新增
            {"label": "☀️ 现有光伏", "key": "existing_pv"},
            {"label": "🔋 现有储能", "key": "existing_storage"}
        ],
        "step2_tabs": ["💡 照明改造", "❄️ 空调改造", "🚿 热水改造", "🏭 动力节能", "☀️ 光伏", "🔋 储能", "🔌 充电桩", "🤖 AI平台", "⚡ 微电网+AI协调展示", "🌐 微电网/VPP", "🌱 碳资产"]
    },
    "🏫 零碳校园": {
        "building_types": ["学校"],
        "step1_tabs": [
            {"label": "📊 基本信息", "key": "basic"},
            {"label": "💡 照明设备", "key": "lighting"},
            {"label": "❄️ 空调设备", "key": "ac"},
            {"label": "🚿 热水设备", "key": "hotwater"},
            {"label": "☀️ 现有光伏", "key": "existing_pv"},
        ],
        "step2_tabs": ["💡 照明改造", "❄️ 空调改造", "🚿 热水改造", "☀️ 光伏", "🔋 储能", "🔌 充电桩", "🤖 AI平台", "⚡ 微电网+AI协调展示", "🌐 微电网/VPP", "🌱 碳资产"]
    },
    "🏢 零碳商办": {
        "building_types": ["商业综合体", "办公楼", "酒店", "医院"],
        "step1_tabs": [
            {"label": "📊 基本信息", "key": "basic"},
            {"label": "💡 照明设备", "key": "lighting"},
            {"label": "❄️ 空调设备", "key": "ac"},
            {"label": "🚿 热水设备", "key": "hotwater"},
            {"label": "☀️ 现有光伏", "key": "existing_pv"},
            {"label": "🔋 现有储能", "key": "existing_storage"}
        ],
        "step2_tabs": ["💡 照明改造", "❄️ 空调改造", "🚿 热水改造", "☀️ 光伏", "🔋 储能", "🔌 充电桩", "🤖 AI平台", "⚡ 微电网+AI协调展示", "🌐 微电网/VPP", "🌱 碳资产"]
    }
}

# ==================== 侧边栏：项目设置 ====================
with st.sidebar:
    st.header("🏭 项目设置")
    
    # 视图模式选择
    view_mode = st.radio(
        "工作模式", 
        ["🚀 快速演示 (Quick)", "🛠️ 详细分步 (Expert)"],
        index=0,
        key="view_mode",
        help="快速演示模式适合汇报展示，详细分步模式适合精准录入"
    )
    st.markdown("---")
    
    # 场景选择
    project_scenario = st.selectbox(
        "应用场景", 
        list(SCENARIO_CONFIG.keys()),
        index=0,
        key="project_scenario",
        help="选择场景将自动加载适配的模块和参数"
    )
    
    st.caption(f"当前模式: {project_scenario}")
    
    # 获取当前场景配置
    current_config = SCENARIO_CONFIG[project_scenario]
    
    st.markdown("---")
    
    project_name_input = st.text_input("项目名称", value="某零碳园区改造项目", key="project_name")

# ==================== 侧边栏：电价设置 ====================
st.sidebar.header("⚡ 电价设置")

pricing_mode = st.sidebar.radio("电价模式", ["分时电价", "固定电价", "动态电价"], key="pricing_mode")

if pricing_mode == "固定电价":
    fixed_price = st.sidebar.number_input("固定电价 (RMB/kWh)", value=0.85, step=0.01, key="fixed_price")
    avg_price = fixed_price
    price_curve = np.array([fixed_price] * 24)
    
elif pricing_mode == "动态电价":
    st.sidebar.info("动态电价：基于实时市场价格波动")
    base_price = st.sidebar.number_input("基准电价 (RMB/kWh)", value=0.70, step=0.01, key="base_price")
    volatility = st.sidebar.slider("波动幅度 (%)", min_value=10, max_value=50, value=30, key="volatility")
    
    # 生成模拟动态电价曲线（基于典型负荷曲线）
    np.random.seed(42)  # 固定随机种子保证可复现
    typical_pattern = np.array([0.6, 0.55, 0.5, 0.5, 0.55, 0.7, 0.85, 1.0, 
                                1.1, 1.15, 1.2, 1.15, 1.0, 0.95, 1.0, 1.1,
                                1.2, 1.3, 1.35, 1.25, 1.1, 0.9, 0.75, 0.65])
    price_curve = base_price * typical_pattern * (1 + np.random.uniform(-volatility/100, volatility/100, 24))
    avg_price = price_curve.mean()
    
    with st.sidebar.expander("📈 查看动态电价曲线"):
        fig_price = px.line(x=list(range(24)), y=price_curve, markers=True)
        fig_price.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0),
                               xaxis_title="小时", yaxis_title="电价(元)")
        st.plotly_chart(fig_price, use_container_width=True)

else:  # 分时电价
    # 选择模板或自定义
    tou_option = st.sidebar.selectbox("电价来源", ["广东模板", "江苏模板", "自定义"], key="tou_option")
    
    if tou_option == "广东模板":
        default_periods = [
            {"时段": "谷时", "开始": 0, "结束": 8, "电价": 0.32},
            {"时段": "峰时", "开始": 8, "结束": 12, "电价": 1.05},
            {"时段": "平时", "开始": 12, "结束": 14, "电价": 0.68},
            {"时段": "峰时", "开始": 14, "结束": 19, "电价": 1.05},
            {"时段": "尖峰", "开始": 19, "结束": 22, "电价": 1.35},
            {"时段": "谷时", "开始": 22, "结束": 24, "电价": 0.32},
        ]
    elif tou_option == "江苏模板":
        default_periods = [
            {"时段": "谷时", "开始": 0, "结束": 8, "电价": 0.35},
            {"时段": "峰时", "开始": 8, "结束": 11, "电价": 1.10},
            {"时段": "尖峰", "开始": 11, "结束": 13, "电价": 1.50},
            {"时段": "平时", "开始": 13, "结束": 17, "电价": 0.72},
            {"时段": "峰时", "开始": 17, "结束": 21, "电价": 1.10},
            {"时段": "谷时", "开始": 21, "结束": 24, "电价": 0.35},
        ]
    else:
        default_periods = [
            {"时段": "谷时", "开始": 0, "结束": 8, "电价": 0.40},
            {"时段": "峰时", "开始": 8, "结束": 12, "电价": 1.00},
            {"时段": "平时", "开始": 12, "结束": 18, "电价": 0.70},
            {"时段": "峰时", "开始": 18, "结束": 22, "电价": 1.00},
            {"时段": "谷时", "开始": 22, "结束": 24, "电价": 0.40},
        ]
    
    # 使用对话框弹窗编辑电价表，提供更大的编辑空间
    @st.dialog("编辑分时电价表", width="large")
    def edit_tou_prices():
        st.markdown("### ⚡ 分时电价设置")
        st.info("请编辑以下表格，支持添加/删除时段")
        
        # 优先从session_state加载自定义数据
        if "custom_tou_periods" in st.session_state:
            initial_data = st.session_state.custom_tou_periods
        else:
            initial_data = default_periods
            
        tou_df = pd.DataFrame(initial_data)
        edited = st.data_editor(
            tou_df, 
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic",
            height=400,
            column_config={
                "时段": st.column_config.SelectboxColumn("时段", options=["谷时", "平时", "峰时", "尖峰"], width="medium"),
                "开始": st.column_config.NumberColumn("开始小时", min_value=0, max_value=24, step=1, width="small"),
                "结束": st.column_config.NumberColumn("结束小时", min_value=0, max_value=24, step=1, width="small"),
                "电价": st.column_config.NumberColumn("电价(元/kWh)", min_value=0, step=0.01, format="%.2f", width="medium"),
            }
        )
        if st.button("✅ 确认保存", type="primary", use_container_width=True):
            st.session_state.custom_tou_periods = edited.to_dict('records')
            st.rerun()
    
    # 检查是否有自定义电价
    if "custom_tou_periods" in st.session_state:
        tou_periods = st.session_state.custom_tou_periods
    else:
        tou_periods = default_periods
    
    # 显示当前电价摘要
    st.sidebar.caption(f"当前: {len(tou_periods)}个时段")
    if st.sidebar.button("✏️ 编辑电价表", use_container_width=True):
        edit_tou_prices()
    
    # 生成24小时电价曲线
    price_curve = np.zeros(24)
    for period in tou_periods:
        for h in range(int(period["开始"]), int(period["结束"])):
            if 0 <= h < 24:
                price_curve[h] = period["电价"]
    
    avg_price = price_curve.mean()
    
    # 电价曲线图
    with st.sidebar.expander("📈 查看电价曲线"):
        fig_price = px.line(x=list(range(24)), y=price_curve, markers=True)
        fig_price.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0),
                               xaxis_title="小时", yaxis_title="电价(元)")
        st.plotly_chart(fig_price, use_container_width=True)

st.sidebar.metric("平均电价", f"¥{avg_price:.3f}/kWh")
st.sidebar.markdown("---")

# ==================== 侧边栏：工程模式 ====================
st.sidebar.header("🏗️ 工程模式")
project_mode = st.sidebar.radio("投资模式", ["EPC（业主自投）", "EMC（节能分成）"], key="project_mode")

if project_mode == "EMC（节能分成）":
    with st.sidebar.expander("📊 EMC分成参数", expanded=True):
        emc_investor_ratio = st.slider("投资方分成比例(%)", 50, 90, 70, key="emc_ratio",
                                       help="节能收益中投资方所占比例")
        emc_sharing_years = st.number_input("分成年限", value=5, min_value=1, max_value=15, key="emc_years",
                                            help="节能分成的合同年限")
        emc_owner_ratio = 100 - emc_investor_ratio
        st.caption(f"业主分成: {emc_owner_ratio}% | 投资方分成: {emc_investor_ratio}%")
else:
    emc_investor_ratio = 0
    emc_sharing_years = 0
    emc_owner_ratio = 100

st.sidebar.markdown("---")
st.sidebar.markdown("---")
# 默认排放因子（如果碳资产模块未配置）
if "emission_factor" not in st.session_state:
    st.session_state.emission_factor = 0.5366  # 默认华东电网

emission_factor = st.session_state.emission_factor

# ==================== 主流程 ====================
# ==================== 主流程 ====================

if "Quick" in view_mode:
    # 🚀 快速演示模式 - 单页大屏风格
    st.header("🚀 零碳项目快速仿真看板 (Simulation Dashboard)")
    st.caption("即时调整关键参数，实时查看投资回报与减排效益")
    
    # 布局：左侧参数面板(30%)，右侧结果看板(70%)
    dash_col1, dash_col2 = st.columns([1, 2.5], gap="large")
    
    with dash_col1:
        st.subheader("🎛️ 关键参数调节")
        
        with st.expander("🏢 基础概况", expanded=True):
            q_area = st.number_input("建筑面积 (m²)", value=50000, step=5000)
            q_bill = st.number_input("年电费 (万元)", value=450, step=10)
            q_kwh = q_bill * 10000 / avg_price # 估算
            st.caption(f"推算年用电: {q_kwh/10000:.1f}万度")

        with st.expander("💡 节能改造 (照明/空调)", expanded=True):
            enable_retro = st.checkbox("启用设备节能", value=True)
            if enable_retro:
                q_save_pct = st.slider("整体综合节能率 (%)", 5, 40, 15)
                q_retro_inv = st.number_input("改造投资估算 (万元)", value=100, step=10)
            else:
                q_save_pct = 0
                q_retro_inv = 0

        with st.expander("☀️ 光伏系统", expanded=True):
            enable_pv = st.checkbox("启用光伏", value=True)
            if enable_pv:
                q_pv_cap = st.slider("装机容量 (kWp)", 0, 5000, 800, step=100)
                q_pv_yield = 1100 # 利用小时
                q_pv_cost = 3.0 # 元/W
                q_pv_inv = q_pv_cap * q_pv_cost / 10 # 万元
                st.caption(f"投资估算: {q_pv_inv:.1f}万元")
            else:
                q_pv_cap = 0
                q_pv_inv = 0

        with st.expander("🔋 储能系统", expanded=True):
            enable_st = st.checkbox("启用储能", value=True)
            if enable_st:
                q_st_cap = st.slider("储能容量 (kWh)", 0, 5000, 1000, step=100)
                q_st_cost = 1200 # 元/kWh
                q_st_inv = q_st_cap * q_st_cost / 10000 # 万元
                st.caption(f"投资估算: {q_st_inv:.1f}万元")
            else:
                q_st_cap = 0
                q_st_inv = 0
        
        with st.expander("🤖 AI平台", expanded=True):
            enable_ai_q = st.checkbox("启用AI平台", value=True)
            if enable_ai_q:
                q_ai_inv = st.number_input("软件投入 (万元)", value=20, step=5)
                q_ai_boost = st.slider("额外效益提升 (%)", 0, 10, 5) / 100
            else:
                q_ai_inv = 0
                q_ai_boost = 0

    # === 快速计算逻辑 ===
    # 1. 节能收益
    base_kwh = q_kwh
    save_kwh = base_kwh * (q_save_pct / 100)
    save_rev = save_kwh * avg_price
    
    # 2. 光伏收益
    pv_gen = 0
    pv_rev = 0
    if enable_pv:
        pv_gen = q_pv_cap * 1100
        # 假设80%自用(按电价)，20%上网(0.45)
        # 如果是学校场景，消纳率降低
        qs_self_ratio = 0.5 if "校园" in project_scenario else 0.8
        pv_rev = pv_gen * (qs_self_ratio * avg_price + (1-qs_self_ratio) * 0.45)
        
    # 3. 储能收益 (简易估算：2充2放，价差0.7)
    st_rev = 0
    if enable_st:
        st_rev = q_st_cap * 0.7 * 0.9 * 2 * 330 # 330天
        
    # 4. AI增益
    ai_rev = 0
    if enable_ai_q:
        ai_rev = (save_rev + pv_rev + st_rev) * q_ai_boost
        
    # 汇总
    total_rev = save_rev + pv_rev + st_rev + ai_rev
    total_inv = (q_retro_inv + q_pv_inv + q_st_inv + q_ai_inv) * 10000
    
    payback = total_inv / total_rev if total_rev > 0 else 99
    roi = (total_rev * 10 - total_inv) / total_inv * 100 if total_inv > 0 else 0
    carbon_red = (save_kwh + pv_gen) * emission_factor / 1000

    with dash_col2:
        # 核心指标卡片
        st.markdown("##### 📈 核心投资回报指标")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总投资 (万元)", f"{total_inv/10000:.1f}", help="包含设备及安装", delta_color="inverse")
        m2.metric("年综合收益 (万元)", f"{total_rev/10000:.1f}", delta=f"ROI {roi/10:.1f}%")
        m3.metric("静态回收期 (年)", f"{payback:.1f}", delta="-优" if payback < 5 else "一般", delta_color="inverse")
        m4.metric("年碳减排 (tCO₂)", f"{carbon_red:.1f}", help="环保效益显著")
        
        st.markdown("---")
        
        # 图表区域
        c1, c2 = st.columns(2)
        
        with c1:
            # 瀑布图
            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "total"],
                x=["节能改造", "光伏发电", "储能&AI", "总收益"],
                y=[save_rev/10000, pv_rev/10000, (st_rev+ai_rev)/10000, 0],
                text=[f"{save_rev/10000:.1f}", f"{pv_rev/10000:.1f}", f"{(st_rev+ai_rev)/10000:.1f}", f"{total_rev/10000:.1f}"],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))
            fig_wf.update_layout(
                title="💰 年收益构成分析 (万元)", 
                height=300,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color='#111111'),
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_wf, use_container_width=True, theme=None)
            
        with c2:
            # 现金流图
            years = list(range(11))
            cfs = [-total_inv/10000]
            curr = -total_inv/10000
            for _ in range(1, 11):
                curr += total_rev/10000
                cfs.append(curr)
                
            fig_cf = px.line(x=years, y=cfs, markers=True, title="📊 10年累计现金流预测 (万元)", template="plotly_white")
            fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
            fig_cf.update_layout(
                height=300,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color='#111111'),
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cf, use_container_width=True, theme=None)
            
        # 敏感性分析 (新增)
        st.markdown("##### 🔍 敏感性分析：电价波动对回收期的影响")
        sens_prices = [avg_price * (0.8 + 0.05 * i) for i in range(9)] # -20% ~ +20%
        sens_paybacks = []
        for p in sens_prices:
            # 简单重算收益
            _save = save_kwh * p
            _pv = pv_gen * (0.8 * p + 0.2 * 0.45)
            _st = q_st_cap * (p * 0.8) * 0.9 * 2 * 330 if enable_st else 0 # 假设价差随均价同比例缩放
            _ai = (_save + _pv + _st) * q_ai_boost
            _tot = _save + _pv + _st + _ai
            sens_paybacks.append(total_inv / _tot if _tot > 0 else 99)
            
        fig_sens = px.bar(x=[f"{x:.2f}元" for x in sens_prices], y=sens_paybacks, 
                          title="不同平均电价下的回收期 (年)", labels={"x": "平均电价", "y": "回收期"},
                          template="plotly_white")
        # 标记当前点
        curr_idx = 4 # 1.0倍
        fig_sens.update_traces(marker_color=['#003366' if i == curr_idx else '#88CCEE' for i in range(9)])
        fig_sens.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#111111'),
            height=250,
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_sens, use_container_width=True, theme=None)

else:
    # ==================== 原 Step-by-Step 专家模式 ====================
    main_tabs = st.tabs(["📋 Step 1: 现状信息", "🔧 Step 2: 改造方案", "📊 Step 3: 效益对比"])
    
    # ... (Step 1 代码) ...
    # 将原有代码缩进或放入else块中
    # 由于代码量大，这里只作为逻辑示意，实际操作需要小心处理缩进
    # 为避免大规模缩进导致diff困难，这里可以仅用if包裹，或直接return
    pass

# ==================== Step 1: 现状信息 ====================
if "Expert" in view_mode:
    with main_tabs[0]:
        st.header("📋 现状信息录入")
        st.info("请在各子页面中填写现有设备信息，数据将自动保存")
        
        # 动态生成Tab
        step1_labels = [t["label"] for t in current_config["step1_tabs"]]
        step1_subtabs_list = st.tabs(step1_labels)
        # 映射 key -> tab对象
        step1_tab_map = {t["key"]: step1_subtabs_list[i] for i, t in enumerate(current_config["step1_tabs"])}
        
        # 存储基准数据
        if "basic" in step1_tab_map:
            with step1_tab_map["basic"]:
                if "baseline" not in st.session_state:
                    st.session_state.baseline = {}
                
                # === 建筑基本信息 ===
                st.markdown("##### 🏢 建筑基本信息")
                bld_col1, bld_col2, bld_col3 = st.columns(3)
            with bld_col1:
                # 获取当前场景允许的建筑类型
                allowed_types = current_config.get("building_types", ["商业综合体", "办公楼", "工厂/仓库", "酒店", "医院", "学校"])
                
                building_type = st.selectbox(
                    "建筑类型",
                    options=allowed_types,
                    key="building_type",
                    help="选择建筑类型以获得更准确的用电分析"
                )
            with bld_col2:
                building_area = st.number_input(
                    "建筑面积 (m²)", 
                    value=100000, 
                    min_value=1000, 
                    step=5000,
                    key="building_area",
                    help="建筑总面积，用于计算能耗密度"
                )
            with bld_col3:
                operating_hours = st.number_input(
                    "日运营时间 (h)",
                    value=12,
                    min_value=1,
                    max_value=24,
                    key="operating_hours",
                    help="每天正常运营小时数"
                )
                
                # 新增省份选择
                province = st.selectbox(
                    "地理省份",
                    options=["广东省", "江苏省", "浙江省", "山东省", "河北省", "河南省", "湖北省", "四川省", "陕西省"],
                    index=0,
                    help="不同省份的日照和温度特性不同，影响光伏和空调计算"
                )
            
            # 保存建筑信息
            st.session_state.baseline["building_type"] = building_type
            st.session_state.baseline["building_area"] = building_area
            st.session_state.baseline["operating_hours"] = operating_hours
            st.session_state.baseline["province"] = province
            
            # === 建筑类型参考能耗密度 (kWh/m²/年) ===
            BUILDING_ENERGY_BENCHMARK = {
                "商业综合体": {"照明": 50, "空调": 80, "动力电梯": 30, "其他": 40, "total": 200},
                "办公楼": {"照明": 30, "空调": 50, "动力电梯": 15, "其他": 25, "total": 120},
                "工厂/仓库": {"照明": 15, "空调": 20, "动力设备": 100, "其他": 15, "total": 150},
                "酒店": {"照明": 40, "空调": 70, "动力电梯": 20, "其他": 50, "total": 180},
                "医院": {"照明": 45, "空调": 60, "动力设备": 50, "其他": 45, "total": 200},
                "学校": {"照明": 25, "空调": 35, "动力设备": 10, "其他": 20, "total": 90},
            }
            
            benchmark = BUILDING_ENERGY_BENCHMARK.get(building_type, BUILDING_ENERGY_BENCHMARK["商业综合体"])
            
            # 显示参考能耗
            with st.expander("📊 查看该建筑类型参考能耗密度"):
                ref_cols = st.columns(len(benchmark))
                for i, (category, density) in enumerate(benchmark.items()):
                    expected_kwh = density * building_area
                    ref_cols[i].metric(
                        category if category != "total" else "总计",
                        f"{density} kWh/m²", 
                        f"预计 {expected_kwh/10000:.1f}万kWh/年"
                    )
            
            st.markdown("---")
            
            # === 新增：基础设施配置 (变压器) ===
            st.markdown("##### 🔌 供配电设施 (台变/接入点)")
            st.info("请定义项目中的变压器/接入点，后续将用于分台变计算光伏消纳。")
            
            if "transformers_list" not in st.session_state:
                st.session_state.transformers_list = [
                    {"name": "1#变压器", "capacity": 2000, "id": "T1"},
                    {"name": "2#变压器", "capacity": 1000, "id": "T2"}
                ]
            
            tf_df = pd.DataFrame(st.session_state.transformers_list)
            edited_tf = st.data_editor(
                tf_df,
                column_config={
                    "name": "变压器名称",
                    "capacity": st.column_config.NumberColumn("容量 (kVA)", min_value=50, step=50, format="%d"),
                    "id": st.column_config.TextColumn("编号 (ID)", validate="^[A-Za-z0-9_]+$")
                },
                num_rows="dynamic",
                key="tf_editor",
                use_container_width=True,
                hide_index=True
            )
            # 实时同步回 session_state
            st.session_state.transformers_list = edited_tf.to_dict('records')
            
            transformer_names = [t["name"] for t in st.session_state.transformers_list]

            st.markdown("---")
            
            uploaded_file = st.file_uploader("📁 上传电费单Excel (可选)", type=['xlsx', 'xls', 'csv'])
            
            # 设备类型分类函数（结合建筑信息）
            def classify_account_device_type(monthly_data, annual_kwh, building_type, building_area, account_name=""):
                """基于用电特征和建筑信息智能分类户号对应的设备类型
                
                分类规则：
                1. 先根据用电特征（变异系数、季节性）初步分类
                2. 再结合建筑类型的典型能耗密度验证
                """
                if len(monthly_data) < 6:
                    return "未知", "数据不足", 0
                
                # 计算统计特征
                mean_val = np.mean(monthly_data)
                std_val = np.std(monthly_data)
                cv = std_val / mean_val if mean_val > 0 else 0  # 变异系数
                
                # 计算能耗密度
                energy_density = annual_kwh / building_area if building_area > 0 else 0
                
                # 计算夏季比
                if len(monthly_data) >= 12:
                    summer_avg = np.mean(monthly_data[5:9])  # 6-9月
                    other_months = list(monthly_data[:5]) + list(monthly_data[9:])
                    other_avg = np.mean(other_months) if other_months else mean_val
                    summer_ratio = summer_avg / other_avg if other_avg > 0 else 1
                else:
                    summer_ratio = 1
                
                # 获取该建筑类型的参考能耗
                bench = BUILDING_ENERGY_BENCHMARK.get(building_type, BUILDING_ENERGY_BENCHMARK["商业综合体"])
                
                # 智能分类逻辑
                if summer_ratio > 1.25:
                    # 夏季用电明显增加 → 空调系统
                    match_pct = min(100, energy_density / bench["空调"] * 100) if "空调" in bench else 50
                    return "空调系统", f"夏季(6-9月)用电是其他月份的{summer_ratio:.2f}倍", match_pct
                
                elif cv < 0.08:
                    # 极稳定 → 24h基础负荷（数据中心、冷库等）
                    return "24h基础负荷", f"变异系数{cv:.3f}极低，全年持续运行", 90
                
                elif cv < 0.15:
                    # 较稳定 → 照明或稳定动力
                    if building_type in ["工厂/仓库"]:
                        return "生产设备", f"变异系数{cv:.3f}，工厂稳定生产负荷", 80
                    else:
                        return "照明+电梯", f"变异系数{cv:.3f}，照明/电梯等稳定负荷", 75
                
                elif cv < 0.25:
                    # 中等波动 → 综合负荷
                    return "综合负荷", f"变异系数{cv:.3f}，包含多类设备", 60
                
                else:
                    # 高波动 → 动力设备或季节性设备
                    if building_type in ["工厂/仓库"]:
                        return "生产动力", f"变异系数{cv:.3f}，生产波动较大", 70
                    else:
                        return "动力设备", f"变异系数{cv:.3f}，用电波动较大", 65
            
            if uploaded_file:
                try:
                    # 支持xlsx和csv
                    if uploaded_file.name.endswith('.csv'):
                        df_raw = pd.read_csv(uploaded_file, header=None)
                    else:
                        df_raw = pd.read_excel(uploaded_file, header=None)
                        
                    st.markdown("##### 📄 原始数据预览")
                    st.dataframe(df_raw, use_container_width=True, height=280)
                    
                    # === 自动识别电费单格式 ===
                    # 格式: 行0=户号名称, 行1=电表编号, 行2=列标题, 行3-14=月度数据, 行15=合计
                    # 列0=月份名称, 列1-N=各户号数据
                    
                    account_analysis = []
                    
                    # 获取户号名称（第一行，从第二列开始）
                    account_names = df_raw.iloc[0, 1:].tolist()
                    
                    # 获取月度数据（第4-15行，即索引3-14）
                    # 检查数据行范围
                    data_start = 3  # 第4行开始是月度数据
                    data_end = min(15, len(df_raw))  # 到第15行或文件结束
                    
                    for col_idx, account_name in enumerate(account_names, start=1):
                        if pd.isna(account_name):
                            continue
                        
                        account_name_str = str(account_name).strip()
                        
                        # 提取该户号的12个月数据
                        monthly_data = []
                        for row_idx in range(data_start, data_end):
                            try:
                                val = df_raw.iloc[row_idx, col_idx]
                                if pd.notna(val):
                                    monthly_data.append(float(val))
                            except:
                                pass
                        
                        if len(monthly_data) >= 6:  # 至少有6个月数据
                            monthly_arr = np.array(monthly_data)
                            annual_kwh = np.sum(monthly_arr)
                            device_type, reason, confidence = classify_account_device_type(
                                monthly_arr, annual_kwh, building_type, building_area, account_name_str)
                            
                            # 计算能耗密度
                            energy_density = annual_kwh / building_area if building_area > 0 else 0
                            
                            account_analysis.append({
                                "户号": account_name_str,
                                "年用电(万kWh)": annual_kwh / 10000,
                                "能耗密度(kWh/m²)": energy_density,
                                "推测设备类型": device_type,
                                "分类依据": reason,
                                "置信度": f"{confidence}%",
                                "monthly_data": monthly_arr,
                                "annual_kwh": annual_kwh
                            })
                    
                    if account_analysis:
                        st.markdown("##### 🔍 户号智能分析结果")
                        st.caption("💡 AI已自动分类，您可以在下方手动修改设备类型")
                        
                        # 准备可编辑数据
                        device_type_options = ["照明+电梯", "空调系统", "24h基础负荷", "综合负荷", "动力设备", "生产设备", "其他"]
                        
                        # 展示表格（只读信息）
                        st.markdown("##### 📋 户号分析结果")
                        display_data = []
                        for a in account_analysis:
                            display_data.append({
                                "户号": a["户号"],
                                "年用电(万kWh)": round(a["年用电(万kWh)"], 1),
                                "能耗密度(kWh/m²)": round(a["能耗密度(kWh/m²)"], 1),
                                "AI推测类型": a["推测设备类型"],
                                "AI依据": a["分类依据"],
                                "置信度": a["置信度"],
                            })
                        
                        st.dataframe(display_data, use_container_width=True, hide_index=True)
                        
                        # 设备类型多选编辑区
                        st.markdown("##### ✏️ 设备类型修改（可多选）")
                        st.caption("💡 点击展开修改每个户号的设备类型，支持多选")
                        
                        # 在渲染multiselect前，初始化session_state中的key（仅首次）
                        for a in account_analysis:
                            account_id = a["户号"]
                            key_name = f"device_type_{account_id}"
                            if key_name not in st.session_state:
                                # 首次初始化：使用AI推测类型
                                default_type = a["推测设备类型"] if a["推测设备类型"] in device_type_options else "综合负荷"
                                st.session_state[key_name] = [default_type]
                        
                        edited_device_types = {}
                        with st.expander("修改设备类型", expanded=False):
                            for a in account_analysis:
                                account_id = a["户号"]
                                key_name = f"device_type_{account_id}"
                                
                                # 不使用default参数，完全依赖session_state中的key值
                                selected = st.multiselect(
                                    f"**{account_id}** ({a['年用电(万kWh)']:.1f}万kWh)",
                                    options=device_type_options,
                                    key=key_name
                                )
                                edited_device_types[account_id] = selected if selected else ["其他"]
                        
                        # 更新account_analysis中的设备类型
                        for i, a in enumerate(account_analysis):
                            types = edited_device_types.get(a["户号"], [a["推测设备类型"]])
                            account_analysis[i]["推测设备类型"] = ",".join(types)
                        
                        # 汇总统计
                        total_annual_kwh = sum([a['annual_kwh'] for a in account_analysis])
                        total_energy_density = total_annual_kwh / building_area if building_area > 0 else 0
                        
                        # 与参考值对比
                        expected_total = benchmark["total"] * building_area
                        compare_pct = total_annual_kwh / expected_total * 100 if expected_total > 0 else 100
                        
                        st.markdown("##### 📊 用电构成分析")
                        
                        # 总体对比
                        compare_cols = st.columns(3)
                        compare_cols[0].metric("实际年用电", f"{total_annual_kwh/10000:.1f} 万kWh")
                        compare_cols[1].metric("能耗密度", f"{total_energy_density:.1f} kWh/m²", 
                                              f"参考值 {benchmark['total']} kWh/m²")
                        compare_cols[2].metric("vs参考值", f"{compare_pct:.0f}%", 
                                              "偏高" if compare_pct > 110 else ("偏低" if compare_pct < 90 else "正常"))
                        # === 新增：户号关联变压器 ===
                        st.markdown("##### 🔗 户号-台变关联")
                        st.caption("请确认每个户号归属的变压器，以便准确计算分台变消纳")
                        
                        transformer_options = [t["name"] for t in st.session_state.transformers_list] if "transformers_list" in st.session_state else []
                        if not transformer_options:
                            st.warning("⚠️ 未检测到变压器配置，请在上方【供配电设施】中添加变压器")
                        else:
                            # 准备初始数据
                            tf_mapping_data = []
                            # 尝试从session_state中恢复已有映射
                            saved_mapping = st.session_state.get("account_tf_mapping", {})
                            
                            for a in account_analysis:
                                acc_id = a["户号"]
                                # 默认归属第一个变压器，或读取保存值
                                curr_tf = saved_mapping.get(acc_id, transformer_options[0])
                                if curr_tf not in transformer_options:
                                    curr_tf = transformer_options[0]
                                
                                tf_mapping_data.append({"户号": acc_id, "归属变压器": curr_tf})
                            
                            tf_mapping_df = pd.DataFrame(tf_mapping_data)
                            
                            edited_mapping = st.data_editor(
                                tf_mapping_df,
                                column_config={
                                    "户号": st.column_config.TextColumn("户号", disabled=True),
                                    "归属变压器": st.column_config.SelectboxColumn(
                                        "归属变压器", 
                                        options=transformer_options,
                                        required=True
                                    )
                                },
                                hide_index=True,
                                use_container_width=True,
                                key="tf_mapping_editor"
                            )
                            
                            # 保存映射
                            new_mapping = dict(zip(edited_mapping["户号"], edited_mapping["归属变压器"]))
                            st.session_state["account_tf_mapping"] = new_mapping
                            
                            # 将变压器归属写入account_analysis
                            transformer_loads = {t: 0.0 for t in transformer_options}
                            for i, a in enumerate(account_analysis):
                                a["transformer_id"] = new_mapping.get(a["户号"], "Unknown")
                                if a["transformer_id"] in transformer_loads:
                                    transformer_loads[a["transformer_id"]] += a["annual_kwh"]
                            
                            # 保存变压器基准负荷到session_state，供Step 2使用
                            st.session_state.baseline["transformer_loads"] = transformer_loads
                            
                            # 展示分台变负荷统计
                            st.markdown("###### 📊 分台变基准负荷统计")
                            tf_cols = st.columns(len(transformer_options))
                            for idx, tf_name in enumerate(transformer_options):
                                load = transformer_loads.get(tf_name, 0)
                                capacity_info = next((t for t in st.session_state.transformers_list if t["name"] == tf_name), None)
                                cap = capacity_info["capacity"] if capacity_info else 0
                                # 负载率估算 (假设年平均负载率 = 年电量 / (容量*8760*0.9)) -> 粗略参考
                                avg_load_rate = (load / (cap * 8760 * 0.9)) * 100 if cap > 0 else 0
                                
                                if idx < len(tf_cols):
                                    tf_cols[idx].metric(
                                        tf_name,
                                        f"{load/10000:.1f} 万kWh",
                                        f"容载比: {avg_load_rate:.1f}% (估)"
                                    )

                        st.markdown("---")
                        
                        # 按设备类型汇总（使用可能被用户修改后的类型，支持一个户号多个类型）
                        type_summary = {}
                        for i, a in enumerate(account_analysis):
                            types_str = account_analysis[i]["推测设备类型"]
                            types_list = types_str.split(",") if types_str else ["其他"]
                            # 按类型数量平分电量
                            kwh_per_type = a['annual_kwh'] / len(types_list)
                            for dtype in types_list:
                                dtype = dtype.strip()
                                if dtype not in type_summary:
                                    type_summary[dtype] = {"kwh": 0, "accounts": [], "density": 0}
                                type_summary[dtype]["kwh"] += kwh_per_type
                                if a['户号'][:15] not in type_summary[dtype]["accounts"]:
                                    type_summary[dtype]["accounts"].append(a['户号'][:15])
                        
                        # 计算各类型密度
                        for dtype in type_summary:
                            type_summary[dtype]["density"] = type_summary[dtype]["kwh"] / building_area
                        
                        st.markdown("---")
                        type_cols = st.columns(min(len(type_summary) + 1, 5))
                        type_cols[0].metric("户号数", f"{len(account_analysis)} 个")
                        for i, (dtype, info) in enumerate(type_summary.items()):
                            if i + 1 < len(type_cols):
                                pct = info["kwh"] / total_annual_kwh * 100 if total_annual_kwh > 0 else 0
                                type_cols[i+1].metric(
                                    dtype, 
                                    f"{info['kwh']/10000:.1f} 万kWh", 
                                    f"{pct:.1f}% | {info['density']:.1f}kWh/m²"
                                )
                        
                        # 可视化
                        with st.expander("📈 查看用电分析图表"):
                            tab_pie, tab_trend = st.tabs(["用电构成", "月度趋势"])
                            
                            with tab_pie:
                                fig_pie = px.pie(
                                    values=[info["kwh"] for info in type_summary.values()],
                                    names=list(type_summary.keys()),
                                    title="按设备类型用电构成",
                                    hole=0.4
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                            
                            with tab_trend:
                                fig_trend = go.Figure()
                                months = ['1月', '2月', '3月', '4月', '5月', '6月', 
                                          '7月', '8月', '9月', '10月', '11月', '12月']
                                for a in account_analysis:
                                    short_name = a['户号'][:12] + "..." if len(a['户号']) > 12 else a['户号']
                                    fig_trend.add_trace(go.Scatter(
                                        x=months[:len(a['monthly_data'])],
                                        y=a['monthly_data'],
                                        mode='lines+markers',
                                        name=f"{short_name} ({a['推测设备类型']})"
                                    ))
                                fig_trend.update_layout(
                                    title="各户号月度用电趋势",
                                    xaxis_title="月份",
                                    yaxis_title="用电量(kWh)",
                                    height=350
                                )
                                st.plotly_chart(fig_trend, use_container_width=True)
                        
                        st.success(f"✅ 解析成功！识别到 **{len(account_analysis)}** 个结算户，年总用电量: **{total_annual_kwh/10000:.1f}** 万kWh")
                        
                        # 保存到session_state
                        st.session_state.baseline["account_analysis"] = account_analysis
                        st.session_state.baseline["type_summary"] = type_summary
                    else:
                        st.warning("⚠️ 未能识别有效数据，请检查电费单格式")
                        total_annual_kwh = 5000000
                        
                except Exception as e:
                    st.error(f"解析失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    total_annual_kwh = 5000000
            else:
                st.info("💡 上传电费单可自动识别多户号并分析设备类型（照明、空调、动力等）")
                col1, col2 = st.columns(2)
                total_annual_kwh = col1.number_input("年总用电量 (kWh)", value=5000000, step=100000)
                annual_bill = col2.number_input("年总电费 (RMB)", value=int(5000000 * avg_price), step=100000)
            
            st.session_state.baseline["annual_kwh"] = total_annual_kwh
            st.session_state.baseline["annual_bill"] = total_annual_kwh * avg_price
            
            st.markdown("---")
            st.metric("📊 年总用电量", f"{total_annual_kwh:,.0f} kWh", help="基准用电量")
        
    # ==================== 子Tab 2: 照明设备 ====================
    if "lighting" in step1_tab_map:
        with step1_tab_map["lighting"]:
            st.subheader("💡 照明设备配置")
            
            has_lighting_info = st.checkbox("✅ 有照明设备信息", value=True, key="has_lighting_info",
                                            help="如果没有收集到照明信息或不需要此模块，请取消勾选")
            
            if has_lighting_info:
                st.info("请添加所有照明设备类型，系统将自动汇总计算总能耗")
                
                # 默认照明设备数据
                if "lighting_devices" not in st.session_state:
                    st.session_state.lighting_devices = [
                        {"名称": "LED筒灯", "数量": 800, "功率(W)": 12, "日运行(h)": 10},
                        {"名称": "老式荧光灯", "数量": 500, "功率(W)": 40, "日运行(h)": 10},
                    ]

                # 优化 DataEditor 状态管理，防止"需要输入两次"的问题
                # 只有当 DataFrame 不在 session_state 时才初始化
                if "lighting_df" not in st.session_state:
                    st.session_state.lighting_df = pd.DataFrame(st.session_state.lighting_devices)

                edited_lighting_df = st.data_editor(
                    st.session_state.lighting_df,
                    key="lighting_editor",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    height=400,
                    column_config={
                        "名称": st.column_config.TextColumn("设备名称", width="large"),
                        "数量": st.column_config.NumberColumn("数量", min_value=0, step=1, width="medium"),
                        "功率(W)": st.column_config.NumberColumn("功率(W)", min_value=0, step=1, width="medium"),
                        "日运行(h)": st.column_config.NumberColumn("日运行(h)", min_value=0, max_value=24, step=1, width="medium"),
                    }
                )
                
                # 同步回 session_state，供其他模块计算使用
                # 注意：这里同时更新 lighting_devices (List[Dict]) 和 lighting_df (DataFrame)
                if not edited_lighting_df.equals(st.session_state.lighting_df):
                    st.session_state.lighting_df = edited_lighting_df
                    st.session_state.lighting_devices = edited_lighting_df.to_dict('records')
                    st.rerun() # 强制刷新以确保数据一致性 (可选，但推荐)
                
                # 兼容后续代码使用 list
                edited_lighting = st.session_state.lighting_devices
                
                # 计算总能耗
                total_lighting_kwh = 0
                for device in edited_lighting:
                    if all(k in device for k in ["数量", "功率(W)", "日运行(h)"]):
                        kwh = device["数量"] * device["功率(W)"] / 1000 * device["日运行(h)"] * 365
                        total_lighting_kwh += kwh
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("设备类型数", len(edited_lighting))
                col2.metric("灯具总数", sum([d.get("数量", 0) for d in edited_lighting]))
                col3.metric("年总耗电", f"{total_lighting_kwh:,.0f} kWh")
                
                st.session_state.baseline["lighting_kwh"] = total_lighting_kwh
                st.session_state.baseline["lighting_devices"] = edited_lighting
            else:
                st.warning("⚠️ 未录入照明设备信息，照明改造模块将被跳过")
                st.session_state.baseline["lighting_kwh"] = 0
                st.session_state.baseline["lighting_devices"] = []
    
    # ==================== 子Tab 3: 空调设备 ====================
    if "ac" in step1_tab_map:
        with step1_tab_map["ac"]:
            st.subheader("❄️ 空调设备配置")
            
            has_ac_info = st.checkbox("✅ 有空调设备信息", value=True, key="has_ac_info",
                                      help="如果没有收集到空调信息或不需要此模块，请取消勾选")
            
            if has_ac_info:
                st.info("请添加所有空调系统，支持分体机和中央空调混合配置")
                
                # 默认空调系统数据
                if "ac_systems" not in st.session_state:
                    st.session_state.ac_systems = [
                        {"名称": "办公区多联机", "数量": 1, "类型": "多联机(VRF)", "制冷量(kW)": 500, "输入功率(kW)": 150.0, "能效比(COP)": 3.3, "辅机功率(kW)": 5.0, "日运行(h)": 10},
                        {"名称": "车间分体机", "数量": 10, "类型": "分体空调", "制冷量(kW)": 50, "输入功率(kW)": 18.0, "能效比(COP)": 2.8, "辅机功率(kW)": 0.0, "日运行(h)": 8},
                    ]
                
                # 默认空调系统数据
                if "ac_systems" not in st.session_state:
                    st.session_state.ac_systems = [
                        {"名称": "办公区多联机", "数量": 1, "类型": "多联机(VRF)", "制冷量(kW)": 500, "输入功率(kW)": 150.0, "能效比(COP)": 3.3, "辅机功率(kW)": 5.0, "日运行(h)": 10},
                        {"名称": "车间分体机", "数量": 10, "类型": "分体空调", "制冷量(kW)": 50, "输入功率(kW)": 18.0, "能效比(COP)": 2.8, "辅机功率(kW)": 0.0, "日运行(h)": 8},
                    ]
                
                # 优化 DataEditor 状态管理
                if "ac_systems_df" not in st.session_state:
                    st.session_state.ac_systems_df = pd.DataFrame(st.session_state.ac_systems)

                edited_ac_df = st.data_editor(
                    st.session_state.ac_systems_df,
                    key="ac_systems_editor",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    height=400,
                    column_config={
                        "名称": st.column_config.TextColumn("系统名称", width="medium"),
                        "数量": st.column_config.NumberColumn("数量", min_value=1, step=1, width="small"),
                        "类型": st.column_config.SelectboxColumn("类型", options=["离心机组", "螺杆机组", "多联机(VRF)", "分体空调", "磁悬浮机组"], width="medium"),
                        "制冷量(kW)": st.column_config.NumberColumn("单台制冷量(kW)", min_value=0, step=10, width="small"),
                        "输入功率(kW)": st.column_config.NumberColumn("单台功率(kW)", min_value=0, step=1, width="small", help="压缩机额定功率"),
                        "能效比(COP)": st.column_config.NumberColumn("COP", min_value=0, step=0.1, width="small"),
                        "辅机功率(kW)": st.column_config.NumberColumn("辅机功率(kW)", min_value=0, step=0.5, width="small", help="单台水泵、冷却塔风机等总功率"),
                        "日运行(h)": st.column_config.NumberColumn("日运行(h)", min_value=0, max_value=24, step=1, width="small"),
                    }
                )
                
                # 同步回 session_state
                if not edited_ac_df.equals(st.session_state.ac_systems_df):
                    st.session_state.ac_systems_df = edited_ac_df
                    st.session_state.ac_systems = edited_ac_df.to_dict('records')
                    st.rerun()

                edited_ac = st.session_state.ac_systems

                st.markdown("ℹ️ **说明**: 辅机功率包含冷冻泵、冷却泵和冷却塔风机的总功率。如果未知，可按主机功率的15%-25%估算。")
                
                # 计算总能耗
                total_ac_kwh = 0
                for system in edited_ac:
                    # 兼容旧数据格式（防止KeyError）
                    count = system.get("数量", 1)
                    q = system.get("制冷量(kW)", 0)
                    p_input = system.get("输入功率(kW)", 0)
                    cop = system.get("能效比(COP)", 3.0)
                    h = system.get("日运行(h)", 0)
                    aux_p = system.get("辅机功率(kW)", 0.0)
                    
                    # 优先使用输入功率，如果未填则用制冷量推算
                    if p_input > 0:
                        host_power = p_input
                    elif cop > 0:
                        host_power = q / cop
                    else:
                        host_power = 0
                        
                    # 单台总功率 = 主机 + 辅机
                    unit_power = host_power + aux_p
                    
                    # 估算全年空调能耗 (制冷季120天 + 制暖季60天, 负载率0.6)
                    # 高级版可改为按月度温差计算
                    annual_hours = (120 + 60) * h * 0.6
                    kwh = unit_power * count * annual_hours
                    total_ac_kwh += kwh
                
                st.markdown("---")
                ac_col1, ac_col2, ac_col3 = st.columns(3)
                ac_col1.metric("空调系统数", len(edited_ac))
                ac_col2.metric("总制冷量", f"{sum([s.get('制冷量(kW)', 0) for s in edited_ac]):,.0f} kW")
                ac_col3.metric("年总耗电/等效", f"{total_ac_kwh:,.0f} kWh")
                
                st.session_state.baseline["ac_kwh"] = total_ac_kwh
                # 存储主要类型
                if len(edited_ac) > 0:
                    st.session_state.baseline["ac_type"] = edited_ac[0].get("类型", "分体空调")
                st.session_state.baseline["ac_systems"] = edited_ac
            else:
                st.warning("⚠️ 未录入空调设备信息，空调改造模块将被跳过")
                st.session_state.baseline["ac_kwh"] = 0
                st.session_state.baseline["ac_type"] = "分体空调"
                st.session_state.baseline["ac_systems"] = []
    
    # ==================== 子Tab 4: 热水设备 ====================
    if "hotwater" in step1_tab_map:
        with step1_tab_map["hotwater"]:
            st.subheader("🚿 热水设备配置")
            
            has_hw_info = st.checkbox("✅ 有热水设备信息", value=True, key="has_hw_info",
                                      help="如果没有收集到热水信息或不需要此模块，请取消勾选")
            
            if has_hw_info:
                st.info("请添加所有热水系统，支持电热水器、燃气锅炉、空气能热泵")
                
                # 默认热水系统数据
                if "hotwater_systems" not in st.session_state:
                    st.session_state.hotwater_systems = [
                        {"名称": "宿舍楼电热水器", "类型": "电热水器", "日热水量(吨)": 5, "温升(℃)": 40, "效率/COP": 0.9},
                        {"名称": "食堂燃气锅炉", "类型": "燃气锅炉", "日热水量(吨)": 10, "温升(℃)": 50, "效率/COP": 0.85},
                    ]
                
                # 可编辑表格
                df_hw = pd.DataFrame(st.session_state.hotwater_systems)
                edited_hw_df = st.data_editor(
                    df_hw,
                    key="hw_systems_editor",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    height=400,
                    column_config={
                        "名称": st.column_config.TextColumn("系统名称", width="medium"),
                        "类型": st.column_config.SelectboxColumn("类型", options=["电热水器", "燃气锅炉", "空气能热泵"], width="medium"),
                        "日热水量(吨)": st.column_config.NumberColumn("日热水量(吨)", min_value=0, step=0.1, width="medium"),
                        "温升(℃)": st.column_config.NumberColumn("温升(℃)", min_value=0, step=1, width="small"),
                        "效率/COP": st.column_config.NumberColumn("效率/COP", help="电热水器/燃气:效率 空气能:COP", min_value=0, step=0.1, width="small"),
                    }
                )
                st.session_state.hotwater_systems = edited_hw_df.to_dict('records')
                edited_hw = st.session_state.hotwater_systems
                
                # 计算总能耗
                total_hw_kwh = 0
                for system in edited_hw:
                    if all(k in system for k in ["类型", "日热水量(吨)", "温升(℃)", "效率/COP"]):
                        日热水量 = system.get("日热水量(吨)", 0)
                        温升 = system.get("温升(℃)", 0)
                        效率COP = system.get("效率/COP", 0.9)
                        类型 = system.get("类型", "电热水器")
                        
                        daily_heat_kwh = 日热水量 * 1.16 * 温升
                        
                        if 类型 in ["电热水器", "燃气锅炉"]:
                            daily_kwh = daily_heat_kwh / 效率COP
                        else:
                            daily_kwh = daily_heat_kwh / 效率COP
                        
                        total_hw_kwh += daily_kwh * 365
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("系统数量", len(edited_hw))
                col2.metric("日总热水量", f"{sum([s.get('日热水量(吨)', 0) for s in edited_hw]):.1f} 吨")
                col3.metric("年总耗电/等效", f"{total_hw_kwh:,.0f} kWh")
                
                st.session_state.baseline["hotwater_kwh"] = total_hw_kwh
                if len(edited_hw) > 0:
                    st.session_state.baseline["hotwater_type"] = edited_hw[0].get("类型", "电热水器")
                st.session_state.baseline["hotwater_systems"] = edited_hw
            else:
                st.warning("⚠️ 未录入热水设备信息，热水改造模块将被跳过")
                st.session_state.baseline["hotwater_kwh"] = 0
                st.session_state.baseline["hotwater_type"] = "电热水器"
                st.session_state.baseline["hotwater_systems"] = []
    

    if "existing_pv" in step1_tab_map:
        with step1_tab_map["existing_pv"]:
            st.subheader("☀️ 现有光伏系统")
            st.info("如果项目已安装光伏，请在此录入现有系统信息，用于评估扩容方案")
            
            has_existing_pv = st.checkbox("已有光伏系统", value=False, key="has_pv")
            
            if has_existing_pv:
                pv_col1, pv_col2, pv_col3 = st.columns(3)
                with pv_col1:
                    existing_pv_capacity = st.number_input(
                        "装机容量 (kWp)", value=500, min_value=0, step=50, key="exist_pv_cap",
                        help="现有光伏系统的额定装机容量")
                    current_solar_gen = st.number_input(
                        "当前年发电量 (kWh)", value=500000, step=10000, key="exist_pv_gen",
                        help="如果不清楚，可保留默认估算值")
                with pv_col2:
                    existing_pv_year = st.number_input(
                        "投运年份", value=2020, min_value=2010, max_value=2026, key="exist_pv_year",
                        help="系统投入运行的年份")
                    existing_pv_decay = st.number_input(
                        "年衰减率 (%)", value=0.5, step=0.1, key="exist_pv_decay",
                        help="组件每年的效率衰减") / 100
                with pv_col3:
                    # 估算当前剩余寿命（假设25年寿命）
                    years_running = 2026 - existing_pv_year
                    remaining_life = max(0, 25 - years_running)
                    st.metric("已运行年限", f"{years_running} 年")
                    st.metric("理论剩余寿命", f"{remaining_life} 年")
                
                st.session_state.baseline["existing_pv"] = {
                    "capacity": existing_pv_capacity,
                    "year": existing_pv_year,
                    "decay": existing_pv_decay,
                    "generation": current_solar_gen
                }
            else:
                st.session_state.baseline["existing_pv"] = None
    
    # ==================== 子Tab 6: 现有储能 ====================
    if "existing_storage" in step1_tab_map:
        with step1_tab_map["existing_storage"]:
            st.subheader("🔋 现有储能系统")
            st.info("如果项目已安装储能，请在此录入现有系统信息，用于评估扩容方案")
            
            has_existing_storage = st.checkbox("已有储能系统", value=False, key="has_st")
            
            if has_existing_storage:
                st_col1, st_col2, st_col3 = st.columns(3)
                with st_col1:
                    existing_st_capacity = st.number_input(
                        "额定容量 (kWh)", value=500, min_value=0, step=50, key="exist_st_cap",
                        help="现有储能系统的额定容量")
                    existing_st_power = st.number_input(
                        "额定功率 (kW)", value=125, min_value=0, step=10, key="exist_st_pow",
                        help="充放电功率")
                with st_col2:
                    existing_st_year = st.number_input(
                        "投运年份", value=2023, min_value=2018, max_value=2026, key="exist_st_year",
                        help="系统投入运行的年份")
                    existing_st_cycles = st.number_input(
                        "日充放次数", value=2, min_value=1, max_value=4, key="exist_st_cyc")
                with st_col3:
                    existing_st_decay = st.number_input(
                        "年容量衰减 (%)", value=2.0, step=0.1, key="exist_st_decay",
                        help="每年的容量衰减率") / 100
                    existing_st_eff = st.slider(
                        "往返效率 (%)", 80, 95, 90, key="exist_st_eff") / 100
                
                # 计算当前可用容量
                years_running = 2026 - existing_st_year
                capacity_factor = max(0.8, 1 - existing_st_decay * years_running)  # 最低80%
                current_capacity = existing_st_capacity * capacity_factor
                
                st.markdown("---")
                st.metric("当前可用估算容量", f"{current_capacity:.0f} kWh", delta=f"-{(1-capacity_factor)*100:.1f}%")
                
                st.session_state.baseline["existing_storage"] = {
                    "capacity": existing_st_capacity,
                    "power": existing_st_power,
                    "year": existing_st_year,
                    "cycles": existing_st_cycles,
                    "decay": existing_st_decay,
                    "efficiency": existing_st_eff
                }
            else:
                st.session_state.baseline["existing_storage"] = None

    # ==================== 子Tab 7: 动力设备 (新增) ====================
    if "motors" in step1_tab_map:
        with step1_tab_map["motors"]:
            st.subheader("🏭 动力设备配置 (空压机/电机/风机)")
            st.info("此模块专门针对工厂场景，用于评估生产动力设备的能效水平。")
            st.warning("⚠️ 功能开发中，即将上线...")
            # 可以在这里添加一些占位输入
            st.checkbox("✅ 有动力设备信息", value=False, disabled=True)


# ==================== Step 2: 改造方案 ====================
if "Expert" in view_mode:
    with main_tabs[1]:
        st.header("🔧 改造方案配置")
        
        # 动态生成Tab
        step2_labels = current_config["step2_tabs"]
        retrofit_tabs_list = st.tabs(step2_labels)
        # 映射 label -> tab对象
        step2_tab_map = {label: retrofit_tabs_list[i] for i, label in enumerate(step2_labels)}
    
    # 存储各模块结果
    if "modules_result" not in st.session_state:
        st.session_state.modules_result = {}
    
    # --- 照明改造 ---
    if "💡 照明改造" in step2_tab_map:
        with step2_tab_map["💡 照明改造"]:
            st.subheader("💡 照明改造")
            enable_lighting = st.checkbox("启用照明改造", value=True)
            
            if enable_lighting:
                # 从 Step 1 读取现状数据（只读展示）
                baseline_lighting_kwh = st.session_state.baseline.get("lighting_kwh", 0)
                
                st.markdown("##### 📋 现状设备（来自 Step 1）")
                if baseline_lighting_kwh > 0:
                    st.info(f"年耗电量: {baseline_lighting_kwh:,.0f} kWh（已在 Step 1 中填写）")
                else:
                    st.warning("⚠️ 请先在 Step 1 填写现状照明设备信息")
                
                # 只填写改造后的参数
                st.markdown("##### 🔧 改造方案")
                col1, col2 = st.columns(2)
                with col1:
                    lt_count = st.number_input("灯具数量", value=1500, step=100, key="lt_c",
                                              help="需改造的灯具数量")
                    lt_old_power = st.number_input("原功率(W)", value=40, step=5, key="lt_op")
                    lt_hours = st.number_input("日运行小时", value=10, step=1, key="lt_h")
                
                with col2:
                    lt_new_power = st.number_input("新功率(W)", value=12, step=1, key="lt_np",
                                                  help="改造后的LED灯功率")
                    lt_inv_per = st.number_input("单灯投资(RMB)", value=80, step=10, key="lt_inv")
                
                # 计算
                old_kwh = lt_count * lt_old_power / 1000 * lt_hours * 365
                new_kwh = lt_count * lt_new_power / 1000 * lt_hours * 365
                saving_kwh = old_kwh - new_kwh
                saving_rmb = saving_kwh * avg_price
                investment = lt_count * lt_inv_per
                payback = investment / saving_rmb if saving_rmb > 0 else 999
                
                st.markdown("##### 效益分析")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("年节电", f"{saving_kwh:,.0f} kWh")
                c2.metric("年节省", f"¥{saving_rmb:,.0f}")
                c3.metric("投资", f"¥{investment:,.0f}")
                c4.metric("回收期", f"{payback:.1f} 年")
                
                st.session_state.modules_result["照明"] = {
                    "old_kwh": old_kwh, "new_kwh": new_kwh, "saving_kwh": saving_kwh,
                    "saving_rmb": saving_rmb, "investment": investment, "payback": payback
                }
            else:
                st.session_state.modules_result["照明"] = None
    
    # --- 空调改造 ---
    if "❄️ 空调改造" in step2_tab_map:
        with step2_tab_map["❄️ 空调改造"]:
            st.subheader("❄️ 空调改造")
            enable_ac = st.checkbox("启用空调改造", value=True)
            
            if enable_ac:
                baseline_ac_kwh = st.session_state.baseline.get("ac_kwh", 0)
                baseline_cop = st.session_state.baseline.get("ac_cop", 3.0)
                
                st.info(f"现状年耗电: {baseline_ac_kwh:,.0f} kWh | 平均COP: {baseline_cop:.2f}")
                
                ac_method = st.radio("改造方式", ["高效机房替换", "磁悬浮机组改造", "AI群控优化"], horizontal=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    target_cop = st.slider("目标综合COP", 3.0, 6.5, 5.0, step=0.1)
                    ac_saving_rate = 1 - (baseline_cop / target_cop)
                with col2:
                    ac_inv_per_kw = st.number_input("单位投资(元/kW冷量)", value=1500, step=100)
                    total_cooling_capacity = sum([s.get('制冷量(kW)', 0) for s in st.session_state.baseline.get("ac_systems", [])])
                    # 如果没有现状数据，给个默认值
                    if total_cooling_capacity == 0:
                        total_cooling_capacity = 1000
                
                # 计算
                # 如果没有现状耗电，反推一个
                if baseline_ac_kwh == 0:
                    baseline_ac_kwh = total_cooling_capacity / 3.0 * 2000 # 估算
                
                saving_kwh = baseline_ac_kwh * ac_saving_rate
                saving_rmb = saving_kwh * avg_price
                investment = total_cooling_capacity * ac_inv_per_kw
                payback = investment / saving_rmb if saving_rmb > 0 else 999
                
                st.markdown("##### 效益分析")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("节电率", f"{ac_saving_rate*100:.1f}%")
                c2.metric("年节省", f"¥{saving_rmb:,.0f}")
                c3.metric("投资", f"¥{investment:,.0f}")
                c4.metric("回收期", f"{payback:.1f} 年")
                
                st.session_state.modules_result["空调"] = {
                    "saving_kwh": saving_kwh, "saving_rmb": saving_rmb, 
                    "investment": investment, "payback": payback
                }
            else:
                st.session_state.modules_result["空调"] = None
    
    # --- 热水改造 ---
    if "🚿 热水改造" in step2_tab_map:
        with step2_tab_map["🚿 热水改造"]:
            st.subheader("🚿 热水系统改造")
            enable_hw = st.checkbox("启用热水改造", value=False)
            
            if enable_hw:
                # 从 Step 1 读取现状数据（只读展示）
                baseline_hw_kwh = st.session_state.baseline.get("hotwater_kwh", 0)
                baseline_hw_type = st.session_state.baseline.get("hotwater_type", "未知")
                
                st.info(f"现状年耗电: {baseline_hw_kwh:,.0f} kWh | 主要类型: {baseline_hw_type}")
                
                hw_method = st.radio("改造方式", ["空气能热泵替代", "太阳能+辅助加热", "余热回收"], horizontal=True)
                
                # 假设节能率
                hw_saving_rates = {"空气能热泵替代": 0.6, "太阳能+辅助加热": 0.7, "余热回收": 0.5}
                hw_saving_rate_default = hw_saving_rates.get(hw_method, 0.6)
                
                col1, col2 = st.columns(2)
                with col1:
                    hw_saving_rate = st.slider("预计节能率", 0.3, 0.9, hw_saving_rate_default, step=0.05, key="hw_sr")
                
                with col2:
                    hw_investment = st.number_input("改造投资(RMB)", value=200000, step=10000, key="hw_inv")
                
                # 计算
                # 如果没有现状耗电，反推
                if baseline_hw_kwh == 0:
                    baseline_hw_kwh = 100000 # 估算
                
                saving_kwh = baseline_hw_kwh * hw_saving_rate
                saving_rmb = saving_kwh * avg_price
                payback = hw_investment / saving_rmb if saving_rmb > 0 else 999
                
                st.markdown("##### 效益分析")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("年节电", f"{saving_kwh:,.0f} kWh")
                c2.metric("年节省", f"¥{saving_rmb:,.0f}")
                c3.metric("投资", f"¥{hw_investment:,.0f}")
                c4.metric("回收期", f"{payback:.1f} 年")
                
                st.session_state.modules_result["热水"] = {
                    "saving_kwh": saving_kwh, "saving_rmb": saving_rmb, 
                    "investment": hw_investment, "payback": payback
                }
            else:
                st.session_state.modules_result["热水"] = None
    
    # --- 动力节能 (新增) ---
    if "🏭 动力节能" in step2_tab_map:
        with step2_tab_map["🏭 动力节能"]:
            st.subheader("🏭 动力系统节能（空压机/电机/风机）")
            st.info("针对工厂场景的高耗能动力设备进行变频改造或高效替换。")
            st.warning("⚠️ 功能开发中，即将上线...")
            st.session_state.modules_result["动力"] = None

    # --- 光伏系统 ---
    if "☀️ 光伏" in step2_tab_map:
        with step2_tab_map["☀️ 光伏"]:
            st.subheader("☀️ 分布式光伏系统")
            enable_pv = st.checkbox("启用光伏建设", value=True)
            
            if enable_pv:
                # 读取现有光伏信息
                existing_pv_info = st.session_state.baseline.get("existing_pv")
                if existing_pv_info:
                    st.info(f"现有光伏装机: {existing_pv_info['capacity']} kWp (投运于 {existing_pv_info['year']}年)")
                    st.caption("新建设施将作为扩容系统接入")

                col1, col2 = st.columns(2)
                with col1:
                    available_area = st.number_input("可用屋顶面积(m²)", value=5000, step=100,
                                                    help="1kWp约需10m²面积")
                    pv_price_per_w = st.number_input("单瓦造价(元/W)", value=3.2, step=0.1)
                
                with col2:
                    solar_yield = st.number_input("年利用小时数", value=1100, step=50,
                                                 help="华东/华南约1000-1100h，西北可达1300h+")
                    
                    # 针对学校场景的自用比例调整
                    is_school = "校园" in project_scenario
                    default_self_ratio = 0.5 if is_school else 0.8
                    
                    # 检查是否有变压器配置
                    transformers_list = st.session_state.transformers_list if "transformers_list" in st.session_state else []
                    
                    if not transformers_list:
                        self_use_ratio = st.slider("自发自用比例", 0.0, 1.0, default_self_ratio,
                                                  help="自用部分的电价收益通常高于上网电价")
                        if is_school:
                            st.warning("⚠️ 检测到【零碳校园】场景：考虑到寒暑假期间（约3个月）校园负荷极低，光伏消纳率会显著下降，建议自用比例设置在 40%-60% 之间。")
                    else:
                        st.info("已启用分台变消纳计算，请在下方配置每台变压器的光伏装机")
                        self_use_ratio = default_self_ratio # 初始显示，后续重新计算
                
                # 假设上网电价 (脱硫燃煤标杆电价)
                feed_in_tariff = 0.45 
                
                # === 光伏装机配置 (支持分台变) ===
                if transformers_list:
                    transformer_loads = st.session_state.baseline.get("transformer_loads", {})
                    
                    st.markdown("###### 🏭 分台变光伏装机配置")
                    tf_pv_data = []
                    
                    # 为data_editor准备数据，尝试从session恢复
                    saved_pv_config = st.session_state.get("pv_tf_config", {})
                    
                    for t in transformers_list:
                        tf_name = t["name"]
                        base_load = transformer_loads.get(tf_name, 0)
                        
                        # 默认装机：按负荷比例估算或0
                        default_cap = 0
                        if tf_name in saved_pv_config:
                             default_cap = saved_pv_config[tf_name].get("cap", 0)
                             default_ratio = saved_pv_config[tf_name].get("ratio", default_self_ratio * 100)
                        else:
                             default_ratio = default_self_ratio * 100

                        tf_pv_data.append({
                            "变压器": tf_name,
                            "基准年负荷": int(base_load),
                            "设计装机(kWp)": default_cap,
                            "自用比例(%)": default_ratio,
                            "calc_kwh": int(base_load) # 隐藏列，用于后台计算
                        })
                    
                    # 自动计算按钮
                    if st.button("🔄 自动计算自用比例 (基于负荷曲线)", use_container_width=True):
                        # 获取当前所选省份
                        current_province = st.session_state.baseline.get("province", "广东省")
                        
                        sim_engine = SimulationEngine(SimulationConfig(province=current_province))
                        updated_data = []
                        for item in tf_pv_data:
                            # 确定负荷类型
                            load_type = "school" if "校园" in project_scenario else "workday"
                            
                            # 调用模拟引擎分析
                            res = sim_engine.analyze_pv_self_consumption(
                                annual_load_kwh=item["基准年负荷"],
                                pv_capacity_kw=item["设计装机(kWp)"],
                                pv_yield_hours=solar_yield,
                                load_curve_type=load_type
                            )
                            
                            # 更新自用比例
                            new_ratio = res["self_use_ratio"] * 100
                            item["自用比例(%)"] = round(new_ratio, 1)
                            updated_data.append(item)
                            
                            st.toast(f"{item['变压器']}: 自用比例更新为 {new_ratio:.1f}%")
                        
                        # 更新显示数据
                        tf_pv_data = updated_data
                        
                        # 同时更新session state，防止重绘丢失
                        new_pv_config = {}
                        for item in tf_pv_data:
                             new_pv_config[item["变压器"]] = {"cap": item["设计装机(kWp)"], "ratio": item["自用比例(%)"]}
                        st.session_state["pv_tf_config"] = new_pv_config
                        
                    
                    edited_pv_tf = st.data_editor(
                        pd.DataFrame(tf_pv_data),
                        column_config={
                            "变压器": st.column_config.TextColumn(disabled=True),
                            "基准年负荷": st.column_config.NumberColumn(format="%d kWh", disabled=True),
                            "设计装机(kWp)": st.column_config.NumberColumn(min_value=0, step=10, required=True),
                            "自用比例(%)": st.column_config.NumberColumn(min_value=0, max_value=100, step=0.1, format="%.1f%%", help="该台变下的光伏消纳比例"),
                            "calc_kwh": None # 隐藏
                        },
                        hide_index=True,
                        key="pv_tf_editor_v1",
                        use_container_width=True
                    )

                    
                    # 保存配置到session
                    new_pv_config = {}
                    for _, row in edited_pv_tf.iterrows():
                        new_pv_config[row["变压器"]] = {"cap": row["设计装机(kWp)"], "ratio": row["自用比例(%)"]}
                    st.session_state["pv_tf_config"] = new_pv_config

                    # 计算总指标
                    pv_capacity = edited_pv_tf["设计装机(kWp)"].sum()
                    
                    # 分台变计算收益汇总
                    total_revenue_year1 = 0
                    weighted_self_ratio_numerator = 0
                    
                    for _, row in edited_pv_tf.iterrows():
                        cap = row["设计装机(kWp)"]
                        ratio = row["自用比例(%)"] / 100.0
                        gen = cap * solar_yield
                        rev = gen * (ratio * avg_price + (1 - ratio) * feed_in_tariff)
                        total_revenue_year1 += rev
                        weighted_self_ratio_numerator += gen * ratio
                        
                    total_generation = pv_capacity * solar_yield
                    if total_generation > 0:
                        self_use_ratio = weighted_self_ratio_numerator / total_generation
                    
                    total_revenue = total_revenue_year1
                    
                else:
                    # 原有逻辑：统一计算
                    max_capacity = available_area / 10
                    pv_capacity = st.slider("设计装机容量(kWp)", 0, int(max_capacity)+100, int(max_capacity), step=10)
                    total_generation = pv_capacity * solar_yield
                    
                    revenue_self = total_generation * self_use_ratio * avg_price
                    revenue_grid = total_generation * (1 - self_use_ratio) * feed_in_tariff
                    total_revenue = revenue_self + revenue_grid
                
                payback = pv_investment / total_revenue if total_revenue > 0 else 999
                
                # 简单IRR估算 (25年)
                cash_flows = [-pv_investment] + [total_revenue] * 25
                try:
                    irr = np.irr(cash_flows) * 100 if pv_investment > 0 else 0
                except:
                    irr = 0
                
                st.markdown("##### 投资评估")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("年发电量", f"{total_generation:,.0f} kWh")
                c2.metric("年收益", f"¥{total_revenue:,.0f}")
                c3.metric("总投资", f"¥{pv_investment:,.0f}")
                c4.metric("IRR / 回收期", f"{irr:.1f}% / {payback:.1f}年")
                
                # 年度现金流图表
                yearly_data = []
                for i in range(1, 26):
                    decay = 0.005 * (i - 1)
                    gen = total_generation * (1 - decay)
                    rev = gen * (self_use_ratio * avg_price + (1 - self_use_ratio) * feed_in_tariff)
                    yearly_data.append({"Year": i, "发电量": gen, "收益": rev})
                
                chart_data = pd.DataFrame(yearly_data)
                st.bar_chart(chart_data, x="Year", y="收益", height=200)
                
                # 保存结果
                # 计算25年总发电量和总收益
                total_gen_25y = sum(d["发电量"] for d in yearly_data)
                total_rev_25y = sum(d["收益"] for d in yearly_data)
                # 计算净现值 NPV (折现率 8%)
                discount_rate = 0.08
                npv = -pv_investment + sum(d["收益"] / ((1 + discount_rate) ** d["Year"]) for d in yearly_data)
                total_profit = total_rev_25y - pv_investment # 简单净利润（不考虑折现）

                # 估算回收期（使用动态现金流）
                cumulative_cash = -pv_investment
                payback_year = 25
                for d in yearly_data:
                    cumulative_cash += d["收益"]
                    if cumulative_cash >= 0:
                        payback_year = d["Year"] # 简化
                        break

                st.session_state.modules_result["光伏"] = {
                    "capacity": pv_capacity,  # 装机容量kWp
                    "generation": yearly_data[0]['发电量'], # 首年发电量
                    "revenue": yearly_data[0]['收益'], # 首年收益
                    "investment": pv_investment,
                    "payback": payback_year,
                    "irr": irr,
                    "npv": npv,
                    "total_generation": total_gen_25y,
                    "total_profit": total_profit,
                    "yearly_data": yearly_data
                }
            else:
                st.session_state.modules_result["光伏"] = None

    # --- 储能系统 ---
    if "🔋 储能" in step2_tab_map:
        with step2_tab_map["🔋 储能"]:
            st.subheader("🔋 储能系统配置")
            enable_storage = st.checkbox("启用储能", value=True)
            
            if enable_storage:
                # 读取现有储能信息
                existing_st_info = st.session_state.baseline.get("existing_storage")
                if existing_st_info:
                    st.info(f"现有储能: {existing_st_info['capacity']} kWh / {existing_st_info['power']} kW")
                    st.caption("新建设施将作为扩容系统接入")

                col1, col2 = st.columns(2)
                with col1:
                    st_capacity = st.number_input("储能容量(kWh)", value=200, step=50)
                    st_power = st.number_input("额定功率(kW)", value=100, step=50)
                
                with col2:
                    st_price_per_wh = st.number_input("单价(元/Wh)", value=1.2, step=0.1)
                    st_cycles = st.number_input("日循环次数", value=2, step=1)
                
                # 收益计算 (峰谷套利)
                # 假设峰谷价差 0.8元
                peak_valley_diff = 0.8
                daily_profit = st_capacity * peak_valley_diff * st_cycles * 0.9 # 效率损失
                annual_profit = daily_profit * 330 # 运行330天
                
                st_investment = st_capacity * 1000 * st_price_per_wh
                
                payback = st_investment / annual_profit if annual_profit > 0 else 999
                
                st.markdown("##### 效益分析")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("单次充放收益", f"¥{st_capacity * peak_valley_diff:.0f}")
                c2.metric("年收益", f"¥{annual_profit:,.0f}")
                c3.metric("总投资", f"¥{st_investment:,.0f}")
                c4.metric("回收期", f"{payback:.1f} 年")
                
                # 储能全生命周期分析 (10年)
                st_yearly_data = []
                discount_rate = 0.08
                for i in range(1, 11):
                    # 假定容量衰减导致收益下降
                    st_decay = 0.02 * (i-1)
                    rev = annual_profit * (1 - st_decay)
                    st_yearly_data.append({"Year": i, "日收益(元)": daily_profit*(1-st_decay), "年收益(元)": rev})

                # 计算总收益和NPV
                total_rev_10y = sum(d["年收益(元)"] for d in st_yearly_data)
                npv = -st_investment + sum(d["年收益(元)"] / ((1 + discount_rate) ** d["Year"]) for d in st_yearly_data)
                total_profit = total_rev_10y - st_investment

                 # 估算回收期
                cumulative_cash = -st_investment
                payback_year = 10
                for d in st_yearly_data:
                    cumulative_cash += d["年收益(元)"]
                    if cumulative_cash >= 0:
                        payback_year = d["Year"] # 简化
                        break

                st.session_state.modules_result["储能"] = {
                    "capacity": st_capacity,  # 容量kWh
                    "power": st_power,  # 功率kW
                    "daily_profit": st_yearly_data[0]['日收益(元)'], 
                    "revenue": st_yearly_data[0]['年收益(元)'],
                    "investment": st_investment, 
                    "payback": payback_year,
                    "npv": npv,
                    "total_profit": total_profit,
                    "yearly_data": st_yearly_data
                }
            else:
                st.session_state.modules_result["储能"] = None
    
    # --- 充电桩 ---
    if "🔌 充电桩" in step2_tab_map:
        with step2_tab_map["🔌 充电桩"]:
            st.subheader("🔌 充电桩建设")
            enable_cp = st.checkbox("启用充电桩", value=True)
            
            if enable_cp:
                col1, col2 = st.columns(2)
                with col1:
                    cp_fast_count = st.number_input("快充桩数量(60kW)", value=5, step=1)
                    cp_slow_count = st.number_input("慢充桩数量(7kW)", value=20, step=1)
                
                with col2:
                    cp_service_fee = st.number_input("服务费(元/kWh)", value=0.4, step=0.1)
                    cp_utilization = st.slider("平均利用率(%)", 5, 50, 15) / 100
                
                # 投资估算
                inv_fast = cp_fast_count * 60000 # 假设6万一个
                inv_slow = cp_slow_count * 5000  # 假设5千一个
                total_inv = inv_fast + inv_slow
                
                # 总功率
                total_power = cp_fast_count * 60 + cp_slow_count * 7
                
                # 收益估算
                # 功率 * 24h * 利用率 * 365 * 服务费
                daily_kwh_fast = cp_fast_count * 60 * 24 * cp_utilization
                daily_kwh_slow = cp_slow_count * 7 * 24 * cp_utilization
                annual_kwh = (daily_kwh_fast + daily_kwh_slow) * 365
                annual_revenue = annual_kwh * cp_service_fee
                
                payback = total_inv / annual_revenue if annual_revenue > 0 else 999
                
                st.markdown("##### 效益分析")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("总功率", f"{total_power} kW")
                c2.metric("年充电量", f"{annual_kwh:,.0f} kWh")
                c3.metric("年服务费收入", f"¥{annual_revenue:,.0f}")
                c4.metric("总投资", f"¥{total_inv:,.0f}")
                
                st.session_state.modules_result["充电桩"] = {
                    "annual_kwh": annual_kwh, "revenue": annual_revenue,
                    "investment": total_inv, "payback": payback,
                    "power": total_power
                }
            else:
                st.session_state.modules_result["充电桩"] = None

    # --- AI平台 ---
    if "🤖 AI平台" in step2_tab_map:
        with step2_tab_map["🤖 AI平台"]:
            st.subheader("🤖 AI能源管控平台")
            enable_ai = st.checkbox("启用AI平台", value=True)
            
            if enable_ai:
                st.info("通过AI智能算法，实现照明、空调等负荷的精细化管控与节能。")
                col1, col2 = st.columns(2)
                with col1:
                    ai_impl_cost = st.number_input("实施费用(RMB)", value=200000, step=10000, key="ai_impl")
                with col2:
                    ai_saving_pct = st.slider("综合额外节能潜力(%)", 1, 10, 5) / 100
                
                # 读取其他模块收益
                base_saving_rmb = 0
                lt_res = st.session_state.modules_result.get("照明")
                if lt_res: base_saving_rmb += lt_res.get("saving_rmb", 0)
                ac_res = st.session_state.modules_result.get("空调")
                if ac_res: base_saving_rmb += ac_res.get("saving_rmb", 0)
                
                # 额外节能收益
                total_kwh = st.session_state.baseline.get("annual_kwh", 1000000)
                if total_kwh == 0: total_kwh = 1000000
                
                ai_saving_rmb = total_kwh * avg_price * ai_saving_pct
                
                payback = ai_impl_cost / ai_saving_rmb if ai_saving_rmb > 0 else 999
                
                st.metric("年额外节省", f"¥{ai_saving_rmb:,.0f}")
                st.metric("投资回收期", f"{payback:.1f} 年")
                
                st.session_state.modules_result["AI平台"] = {
                    "saving_rmb": ai_saving_rmb, "investment": ai_impl_cost, "payback": payback
                }
            else:
                st.session_state.modules_result["AI平台"] = None

    # --- ⚡ 微电网+AI协调展示 ---
    if "⚡ 微电网+AI协调展示" in step2_tab_map:
        with step2_tab_map["⚡ 微电网+AI协调展示"]:
            st.subheader("⚡ 微电网+AI管理平台协调展示")
            st.caption("实时能量流动 · 多场景模拟 · AI优化对比")

            # === 顶部控制面板 ===
            with st.container():
                control_col1, control_col2, control_col3, control_col4 = st.columns(4)

                with control_col1:
                    scenario = st.selectbox(
                        "模拟场景",
                        ["峰谷电价套利", "电网故障/孤岛运行", "电动汽车有序充电", "AI优化对比"],
                        key="mg_scenario"
                    )

                with control_col2:
                    weather = st.selectbox(
                        "天气条件",
                        ["晴天", "阴天", "雨天"],
                        key="mg_weather"
                    )

                with control_col3:
                    time_range = st.slider(
                        "时间范围",
                        min_value=0, max_value=23, value=(8, 20),
                        key="mg_time_range"
                    )

                with control_col4:
                    auto_play = st.button(
                        "▶️ 自动播放动画",
                        type="primary",
                        key="mg_autoplay"
                    )

            st.markdown("---")

            # === 初始化微电网可视化模块 ===
            if "mg_module" not in st.session_state:
                st.session_state.mg_module = MicrogridVisualizerModule()
                st.session_state.mg_config = MicrogridConfig()
                st.session_state.mg_snapshots = []

            mg_module = st.session_state.mg_module

            # === 场景映射 ===
            scenario_map = {
                "峰谷电价套利": MicrogridScenario.PEAK_VALLEY,
                "电网故障/孤岛运行": MicrogridScenario.ISLAND_MODE,
                "电动汽车有序充电": MicrogridScenario.EV_CHARGING,
                "AI优化对比": MicrogridScenario.AI_OPTIMIZATION
            }

            weather_map = {
                "晴天": WeatherCondition.SUNNY,
                "阴天": WeatherCondition.CLOUDY,
                "雨天": WeatherCondition.RAINY
            }

            # === 运行仿真 ===
            current_scenario = scenario_map[scenario]
            current_weather = weather_map[weather]

            # 检查是否需要重新计算
            cache_key = f"{current_scenario.value}_{current_weather.value}"
            if st.session_state.get("mg_cache_key") != cache_key:
                with st.spinner("生成仿真数据中..."):
                    inputs = {
                        'config': st.session_state.mg_config,
                        'scenario': current_scenario,
                        'weather': current_weather,
                        'hours': 24
                    }
                    result = mg_module.calculate(inputs)
                    st.session_state.mg_result = result
                    st.session_state.mg_snapshots = result.hourly_snapshots
                    st.session_state.mg_cache_key = cache_key
                st.toast("✅ 仿真完成！")

            # === 中间可视化区域 ===
            viz_col1, viz_col2 = st.columns([2, 1])

            with viz_col1:
                # 动态能量流图
                st.subheader("实时能量流动")

                # 时间控制条
                current_hour = st.slider(
                    "当前时刻",
                    min_value=time_range[0],
                    max_value=time_range[1],
                    value=time_range[0],
                    key="mg_current_hour"
                )

                # 获取可视化引擎
                viz_engine = mg_module.get_visualization_engine()
                scenario_engine = mg_module.get_scenario_engine()

                # 获取快照
                snapshots = st.session_state.mg_snapshots
                if snapshots and 0 <= current_hour < len(snapshots):
                    snapshot = snapshots[current_hour]

                    # 重新构造快照对象用于可视化
                    from modules.scenario_engine import HourlySnapshot, EnergyFlow, NodeState
                    snapshot_data = snapshot
                    reconstructed_nodes = {
                        name: NodeState(name, node['power'], node.get('soc'), node['color'])
                        for name, node in snapshot_data['nodes'].items()
                    }
                    reconstructed_flows = [
                        EnergyFlow(f['from'], f['to'], f['power'], f.get('cost', 0))
                        for f in snapshot_data['flows']
                    ]
                    reconstructed_snapshot = HourlySnapshot(
                        hour=snapshot_data['hour'],
                        scenario=scenario_map.get(snapshot_data['scenario'], current_scenario),
                        weather=weather_map.get(snapshot_data['weather'], current_weather),
                        nodes=reconstructed_nodes,
                        flows=reconstructed_flows,
                        metrics=snapshot_data['metrics'],
                        ai_decision=snapshot_data.get('ai_decision')
                    )

                    # 绘制能量流图
                    fig_flow = viz_engine.create_dynamic_energy_flow(reconstructed_snapshot)
                    st.plotly_chart(fig_flow, use_container_width=True, height=500)

                else:
                    st.warning("⚠️ 未找到快照数据")

            with viz_col2:
                # 实时指标面板
                st.subheader("实时指标")

                if snapshots and 0 <= current_hour < len(snapshots):
                    snapshot = snapshots[current_hour]
                    metrics_data = viz_engine.create_metrics_panel(reconstructed_snapshot)

                    for label, data in metrics_data.items():
                        delta = data.get('delta')
                        delta_color = data.get('delta_color') if delta else 'normal'
                        st.metric(
                            label,
                            data['value'],
                            delta=delta,
                            delta_color=delta_color if delta else 'normal'
                        )

                    # 场景说明
                    with st.expander("📖 场景说明"):
                        st.markdown(get_scenario_description(scenario))
                else:
                    st.info("请选择时间范围查看指标")

            st.markdown("---")

            # === 底部Sankey图和对比 ===
            bottom_col1, bottom_col2 = st.columns(2)

            with bottom_col1:
                st.subheader("能量平衡 (Sankey图)")
                if snapshots:
                    # 使用12点（正午）的快照
                    peak_hour = 12 if len(snapshots) > 12 else 0
                    peak_snapshot_data = snapshots[peak_hour]

                    reconstructed_peak_nodes = {
                        name: NodeState(name, node['power'], node.get('soc'), node['color'])
                        for name, node in peak_snapshot_data['nodes'].items()
                    }
                    reconstructed_peak_flows = [
                        EnergyFlow(f['from'], f['to'], f['power'], f.get('cost', 0))
                        for f in peak_snapshot_data['flows']
                    ]
                    reconstructed_peak = HourlySnapshot(
                        hour=peak_snapshot_data['hour'],
                        scenario=scenario_map.get(peak_snapshot_data['scenario'], current_scenario),
                        weather=weather_map.get(peak_snapshot_data['weather'], current_weather),
                        nodes=reconstructed_peak_nodes,
                        flows=reconstructed_peak_flows,
                        metrics=peak_snapshot_data['metrics'],
                        ai_decision=peak_snapshot_data.get('ai_decision')
                    )

                    fig_sankey = viz_engine.create_sankey_diagram(reconstructed_peak)
                    st.plotly_chart(fig_sankey, use_container_width=True, height=400)
                else:
                    st.warning("⚠️ 暂无数据")

            with bottom_col2:
                st.subheader("AI优化对比")
                if scenario == "AI优化对比" and "mg_result" in st.session_state:
                    result = st.session_state.mg_result
                    comparison = result.scenario_comparison

                    if comparison:
                        st.metric(
                            "AI优化节省",
                            f"¥{comparison['total_saving']:.2f}/天",
                            f"{comparison['saving_percentage']:.1f}%",
                            delta_color="normal"
                        )

                        # 绘制对比图
                        # 需要重新运行固定策略仿真
                        config = st.session_state.mg_config
                        no_ai_engine = ScenarioEngine(config)
                        no_ai_config = MicrogridConfig(ai_enabled=False)
                        no_ai_engine.config = no_ai_config
                        snapshots_no_ai = no_ai_engine.run_simulation(
                            MicrogridScenario.PEAK_VALLEY, current_weather, 24
                        )

                        ai_engine = ScenarioEngine(st.session_state.mg_config)
                        snapshots_ai = ai_engine.run_simulation(
                            MicrogridScenario.PEAK_VALLEY, current_weather, 24
                        )

                        fig_comparison = viz_engine.create_comparison_chart(snapshots_ai, snapshots_no_ai)
                        st.plotly_chart(fig_comparison, use_container_width=True, height=300)
                else:
                    st.info("选择'AI优化对比'场景查看优化前后对比")

    # --- 微电网/VPP ---
    if "🌐 微电网/VPP" in step2_tab_map:
        with step2_tab_map["🌐 微电网/VPP"]:
            st.subheader("🌐 微电网/虚拟电厂资源聚合")
            enable_vpp = st.checkbox("启用微电网调度分析", value=False)
            
            if enable_vpp:
                # 1. 资源聚合
                pv_res = st.session_state.modules_result.get("光伏")
                st_res = st.session_state.modules_result.get("储能")
                cp_res = st.session_state.modules_result.get("充电桩")
                
                pv_cap = pv_res.get("capacity", 0) if pv_res else 0
                st_cap = st_res.get("capacity", 0) if st_res else 0
                st_pow = st_res.get("power", 0) if st_res else 0
                cp_pow = cp_res.get("power", 0) if cp_res else 0
                
                if pv_cap + st_cap + cp_pow == 0:
                    st.warning("⚠️ 未检测到光伏、储能或充电桩资源，请先在对应模块进行配置。")
                else:
                    st.info("✅ 已自动聚合园区分布式资源")
                    
                    # 资源拓扑可视化
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                    res_col1.metric("☀️ 分布式光伏", f"{pv_cap:.0f} kWp", "可调出力")
                    res_col2.metric("🔋 分布式储能", f"{st_cap:.0f} kWh", f"{st_pow:.0f} kW 功率")
                    res_col3.metric("🔌 可控充电桩", f"{cp_pow:.0f} kW", "有序充电")
                    res_col4.metric("🏭 可调负荷", "50 kW", "空调/照明(估算)") # 临时估算值
                    
                    st.markdown("---")
                    
                    # 2. 调度策略与收益测算
                    st.subheader("⚙️ 运营策略与收益测算")
                    
                    vpp_col1, vpp_col2 = st.columns([1, 2])
                    
                    with vpp_col1:
                        strategy = st.radio(
                            "调度策略", 
                            ["经济优化 (峰谷套利+需量管理)", "辅助服务 (顶峰/填谷响应)", "绿色优先 (最大化消纳)"],
                            help="不同策略将影响收益构成"
                        )
                        
                        dr_price = st.number_input("需求响应补贴 (元/kWh)", value=3.0, step=0.5, help="部分地区精准响应高达5元/度")
                        dr_times = st.slider("年响应次数", 5, 50, 20)
                    
                    with vpp_col2:
                        # 收益计算模型
                        revenue_arbitrage = 0
                        revenue_dr = 0
                        revenue_aux = 0
                        
                        # A. 峰谷套利 (主要靠储能)
                        # 假设储能每天一充一放，价差0.7元
                        if strategy == "经济优化 (峰谷套利+需量管理)":
                            price_diff = 0.8  # 典型价差
                            efficiency = 0.9
                            revenue_arbitrage = st_cap * price_diff * efficiency * 330 # 330天运行
                            
                            # 需量管理收益 (假设降低5%需量电费)
                            revenue_aux = 30000 # 估算值
                            
                        elif strategy == "辅助服务 (顶峰/填谷响应)":
                            # 牺牲部分套利，参与高价响应
                            revenue_arbitrage = st_cap * 0.5 * 300 # 套利减少
                            
                            # 响应收益 = (储能功率 + 负荷削减) * 补贴 * 次数 * 时长(假设2h)
                            respond_capacity = st_pow + 50 # 储能+可调负荷
                            revenue_dr = respond_capacity * 2 * dr_times * dr_price
                            
                        else: # 绿色优先
                            # 主要是减少弃光，假设提升5%光伏收益
                            annual_gen = pv_res.get("generation", 0) if pv_res else 0
                            revenue_aux = annual_gen * 0.05 * avg_price # 减少弃光收益
                            revenue_arbitrage = st_cap * 0.4 * 300 # 仅做平衡
                        
                        total_vpp_revenue = revenue_arbitrage + revenue_dr + revenue_aux
                        
                        # 展示收益构成
                        v_c1, v_c2, v_c3 = st.columns(3)
                        v_c1.metric("峰谷套利/消纳", f"¥{revenue_arbitrage:,.0f}")
                        v_c2.metric("需求响应补贴", f"¥{revenue_dr:,.0f}")
                        v_c3.metric("需量/辅助服务", f"¥{revenue_aux:,.0f}")
                        
                        st.success(f"💰 VPP年度综合运营收益: **¥{total_vpp_revenue:,.0f}**")
                        
                        # 简单的调度示意图
                        chart_data = pd.DataFrame({
                            "收益来源": ["电价套利", "需求响应", "辅助服务"],
                            "金额": [revenue_arbitrage, revenue_dr, revenue_aux]
                        })
                        st.plotly_chart(px.bar(chart_data, x="收益来源", y="金额", title="收益构成分析"), use_container_width=True)

                    st.session_state.modules_result["微电网"] = {
                        "vpp_revenue": total_vpp_revenue,
                        "strategy": strategy
                    }
            else:
                st.session_state.modules_result["微电网"] = None

    # --- 碳资产管理 ---
    if "🌱 碳资产" in step2_tab_map:
        with step2_tab_map["🌱 碳资产"]:
            st.subheader("🌱 碳资产全生命周期管理")
            enable_carbon = st.checkbox("启用碳资产分析", value=False)
            
            if enable_carbon:
                grid_region = st.selectbox("电网区域（影响排放因子）", [
                    "华东电网（0.5366）", "华北电网（0.5810）", "南方电网（0.4267）", "西北电网（0.4912）"
                ])
                emission_factor = float(grid_region.split("（")[1].replace("）", ""))
                st.session_state.emission_factor = emission_factor
                
                # 1. 碳账本
                st.markdown("##### 1. 园区碳账本")
                
                # 计算节电量和绿电发电量
                total_kwh_saving = 0
                total_green_gen = 0
                
                for k, v in st.session_state.modules_result.items():
                    if v:
                        total_kwh_saving += v.get("saving_kwh", 0)
                        if k in ["光伏", "微电网"]: # 光伏发电
                             # 注意：光伏模块可能返回generation，也可能在saving_kwh里（如果是纯自发自用）
                             # 这里假设光伏模块的generation是发电量
                             total_green_gen += v.get("generation", 0)
                
                # 基准总用电
                baseline_kwh = st.session_state.baseline.get("annual_kwh", 5000000)
                
                # 剩余需要网购的电量 = 基准 - 节电 - 绿电 (简化计算)
                # 实际：新用电 = 基准 - 节电。 
                # 网购电 = 新用电 - 自用绿电。这里简化假设绿电全额自用。
                current_demand = max(0, baseline_kwh - total_kwh_saving)
                net_grid_purchase = max(0, current_demand - total_green_gen)
                
                # 碳排放计算
                baseline_carbon = baseline_kwh * emission_factor / 1000
                current_carbon = net_grid_purchase * emission_factor / 1000
                carbon_reduction = baseline_carbon - current_carbon
                
                c_col1, c_col2, c_col3 = st.columns(3)
                c_col1.metric("基准碳排放", f"{baseline_carbon:,.1f} tCO₂", help="改造前年排放量")
                c_col2.metric("改造后排放", f"{current_carbon:,.1f} tCO₂", help="扣除光伏抵消后的净排放")
                c_col3.metric("年碳减排量", f"{carbon_reduction:,.1f} tCO₂", f"减排率 {(carbon_reduction/baseline_carbon*100):.1f}%")
                
                st.markdown("---")
                
                # 2. 绿电/CCER交易
                st.markdown("##### 2. 绿电缺口与交易履约")
                
                if net_grid_purchase > 0:
                    st.warning(f"📉 距离【零碳园区】目标仍有 **{net_grid_purchase:,.0f} kWh** 的绿电缺口。")
                    
                    trade_col1, trade_col2 = st.columns(2)
                    with trade_col1:
                        st.markdown("**方案 A：购买绿色电力证书 (GEC)**")
                        gec_price = st.number_input("绿证价格 (元/张)", value=30.0, help="1张绿证 = 1000 kWh")
                        gec_cost = (net_grid_purchase / 1000) * gec_price
                        st.metric("绿证履约成本", f"¥{gec_cost:,.0f}")
                        
                    with trade_col2:
                        st.markdown("**方案 B：参与绿电市场交易**")
                        green_premium = st.number_input("绿电溢价 (元/kWh)", value=0.05)
                        green_power_cost = net_grid_purchase * green_premium
                        st.metric("绿电交易溢价成本", f"¥{green_power_cost:,.0f}")
                        
                else:
                    st.success(f"🌟 恭喜！园区已实现 **100% 绿电覆盖** (余量 {(total_green_gen - current_demand):,.0f} kWh)")
                    st.markdown("**收益机会：** 可将多余绿电或环境权益出售。")
                    ccer_price = st.number_input("CCER/绿证售价 (元/tCO₂)", value=50.0)
                    # 余量对应的碳减排
                    surplus_carbon = (total_green_gen - current_demand) * emission_factor / 1000
                    st.metric("潜在环境权益收益", f"¥{surplus_carbon * ccer_price:,.0f}")

                st.session_state.modules_result["碳资产"] = {
                    "reduction": carbon_reduction,
                    "carbon_after": current_carbon
                }
            else:
                st.session_state.modules_result["碳资产"] = None

# ==================== Step 3: 效益对比 ====================
if "Expert" in view_mode:
    with main_tabs[2]:
        st.header("📊 项目效益对比分析")
        
        modules = st.session_state.get("modules_result", {})
        baseline = st.session_state.get("baseline", {})
        
        # --- 各模块详细对比表 ---
        st.subheader("📋 各模块效益明细")
    
    comparison_data = []
    total_investment = 0
    total_annual_revenue = 0
    total_saving_kwh = 0
    
    for name, data in modules.items():
        if data is None:
            continue
        
        row = {"模块": name}
        
        if "old_kwh" in data:
            row["改造前(kWh)"] = f"{data['old_kwh']:,.0f}"
            row["改造后(kWh)"] = f"{data['new_kwh']:,.0f}"
            row["节电(kWh)"] = f"{data['saving_kwh']:,.0f}"
            total_saving_kwh += data["saving_kwh"]
        elif "generation" in data:
            row["改造前(kWh)"] = "-"
            row["改造后(kWh)"] = "-"
            row["节电(kWh)"] = f"{data['generation']:,.0f} (发电)"
            total_saving_kwh += data["generation"]
        else:
            row["改造前(kWh)"] = "-"
            row["改造后(kWh)"] = "-"
            row["节电(kWh)"] = "-"
        
        if "saving_rmb" in data:
            row["年收益(RMB)"] = f"{data['saving_rmb']:,.0f}"
            total_annual_revenue += data["saving_rmb"]
        elif "revenue" in data:
            row["年收益(RMB)"] = f"{data['revenue']:,.0f}"
            total_annual_revenue += data["revenue"]
        elif "net_revenue" in data:
            row["年收益(RMB)"] = f"{data['net_revenue']:,.0f}"
            total_annual_revenue += data["net_revenue"]
        
        if "investment" in data:
            row["投资(RMB)"] = f"{data['investment']:,.0f}"
            total_investment += data["investment"]
        else:
            row["投资(RMB)"] = "-"
        
        if "payback" in data:
            row["回收期(年)"] = f"{data['payback']:.1f}"
        else:
            row["回收期(年)"] = "-"
        
        comparison_data.append(row)
    
    if comparison_data:
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    
    # --- 汇总指标 ---
    st.subheader("📈 项目汇总")
    
    overall_payback = total_investment / total_annual_revenue if total_annual_revenue > 0 else 999
    carbon_reduction = total_saving_kwh * emission_factor / 1000
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("总投资", f"¥{total_investment/10000:.1f} 万")
    m2.metric("年总收益", f"¥{total_annual_revenue/10000:.1f} 万")
    m3.metric("综合回收期", f"{overall_payback:.1f} 年")
    m4.metric("年碳减排", f"{carbon_reduction:,.1f} tCO2")
    
    # ========== EMC/EPC模式收益分析 ==========
    if project_mode == "EMC（节能分成）":
        st.subheader("🤝 EMC模式收益分配分析")
        
        st.info(f"📋 **合同条款**: 投资方出资，分成{emc_sharing_years}年，投资方分成{emc_investor_ratio}%，业主分成{emc_owner_ratio}%")
        
        # 计算双方收益
        investor_annual = total_annual_revenue * emc_investor_ratio / 100
        owner_annual = total_annual_revenue * emc_owner_ratio / 100
        
        # 分成期内收益
        investor_sharing_total = investor_annual * emc_sharing_years
        owner_sharing_total = owner_annual * emc_sharing_years
        
        # 分成期后（业主获得全部收益）
        post_sharing_years = 10 - emc_sharing_years  # 假设10年分析期
        owner_post_sharing = total_annual_revenue * max(0, post_sharing_years)
        
        # 总收益（10年）
        investor_10yr = investor_sharing_total
        owner_10yr = owner_sharing_total + owner_post_sharing
        
        # 投资方回本期
        investor_payback = total_investment / investor_annual if investor_annual > 0 else 999
        
        # 展示EMC收益对比
        st.markdown("##### 📊 双方收益对比（10年分析期）")
        
        col_epc, col_owner, col_investor = st.columns(3)
        
        with col_epc:
            st.markdown("**🏢 EPC模式（对比参照）**")
            st.metric("初始投资", f"¥{total_investment/10000:.1f} 万")
            st.metric("年收益", f"¥{total_annual_revenue/10000:.1f} 万")
            st.metric("10年累计收益", f"¥{(total_annual_revenue*10 - total_investment)/10000:.1f} 万")
            st.metric("回本周期", f"{overall_payback:.1f} 年")
        
        with col_owner:
            st.markdown("**👤 EMC业主方收益**")
            st.metric("初始投资", "¥0", help="无需投资，由投资方出资")
            st.metric("分成期年收益", f"¥{owner_annual/10000:.1f} 万", f"{emc_owner_ratio}%")
            st.metric("10年累计收益", f"¥{owner_10yr/10000:.1f} 万")
            st.metric("分成期后年收益", f"¥{total_annual_revenue/10000:.1f} 万", "100%")
        
        with col_investor:
            st.markdown("**💰 EMC投资方收益**")
            st.metric("初始投资", f"¥{total_investment/10000:.1f} 万")
            st.metric("分成期年收益", f"¥{investor_annual/10000:.1f} 万", f"{emc_investor_ratio}%")
            st.metric("10年累计净收益", f"¥{(investor_10yr - total_investment)/10000:.1f} 万")
            st.metric("回本周期", f"{investor_payback:.1f} 年")
        
        # EMC详细现金流表
        with st.expander("📋 查看EMC双方详细现金流"):
            emc_cashflow_data = []
            owner_cum = 0
            investor_cum = -total_investment
            
            for year in range(1, 11):
                if year <= emc_sharing_years:
                    owner_cf = owner_annual
                    investor_cf = investor_annual
                else:
                    owner_cf = total_annual_revenue
                    investor_cf = 0
                
                owner_cum += owner_cf
                investor_cum += investor_cf
                
                emc_cashflow_data.append({
                    "年份": year,
                    "业主年收益(万)": f"{owner_cf/10000:.1f}",
                    "业主累计(万)": f"{owner_cum/10000:.1f}",
                    "投资方年收益(万)": f"{investor_cf/10000:.1f}",
                    "投资方累计(万)": f"{investor_cum/10000:.1f}",
                    "阶段": "分成期" if year <= emc_sharing_years else "分成期后"
                })
            
            st.dataframe(pd.DataFrame(emc_cashflow_data), use_container_width=True, hide_index=True)
        
        # EMC现金流对比图
        with st.expander("📈 查看EMC双方现金流趋势"):
            years = list(range(11))
            owner_cfs = [0]
            investor_cfs = [-total_investment]
            owner_c, investor_c = 0, -total_investment
            
            for year in range(1, 11):
                if year <= emc_sharing_years:
                    owner_c += owner_annual
                    investor_c += investor_annual
                else:
                    owner_c += total_annual_revenue
                owner_cfs.append(owner_c)
                investor_cfs.append(investor_c)
            
            fig_emc = go.Figure()
            fig_emc.add_trace(go.Scatter(x=years, y=[x/10000 for x in owner_cfs], 
                                         mode='lines+markers', name='业主累计收益', 
                                         line=dict(color='green')))
            fig_emc.add_trace(go.Scatter(x=years, y=[x/10000 for x in investor_cfs], 
                                         mode='lines+markers', name='投资方累计净收益', 
                                         line=dict(color='blue')))
            fig_emc.add_hline(y=0, line_dash="dash", line_color="red")
            fig_emc.add_vline(x=emc_sharing_years, line_dash="dot", 
                              annotation_text=f"分成期结束(第{emc_sharing_years}年)")
            fig_emc.update_layout(
                title="EMC模式双方累计收益对比",
                xaxis_title="年份", 
                yaxis_title="累计收益(万元)",
                height=350
            )
            st.plotly_chart(fig_emc, use_container_width=True)
    
    # --- 收益构成图 ---
    st.subheader("💰 收益来源构成")
    
    revenue_data = []
    for name, data in modules.items():
        if data is None:
            continue
        if "saving_rmb" in data:
            revenue_data.append({"模块": name, "年收益": data["saving_rmb"]})
        elif "revenue" in data:
            revenue_data.append({"模块": name, "年收益": data["revenue"]})
        elif "net_revenue" in data:
            revenue_data.append({"模块": name, "年收益": data["net_revenue"]})
    
    if revenue_data:
        fig_pie = px.pie(pd.DataFrame(revenue_data), values="年收益", names="模块", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # --- 10年现金流 ---
    st.subheader("📊 10年累计现金流")
    
    years = list(range(11))
    cashflows = [-total_investment]
    current = -total_investment
    for _ in range(1, 11):
        current += total_annual_revenue
        cashflows.append(current)
    
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(x=years, y=cashflows, marker_color=['red' if x<0 else 'green' for x in cashflows]))
    fig_cf.update_layout(xaxis_title="年份", yaxis_title="累计净现金流 (RMB)")
    st.plotly_chart(fig_cf, use_container_width=True)
    
    # --- 前后对比 ---
    st.subheader("⚡ 能耗前后对比")
    
    old_total_kwh = baseline.get("annual_kwh", 0)
    new_total_kwh = old_total_kwh - total_saving_kwh
    
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(name='改造前', x=['年用电量'], y=[old_total_kwh], marker_color='red'))
    fig_compare.add_trace(go.Bar(name='改造后', x=['年用电量'], y=[max(0, new_total_kwh)], marker_color='green'))
    fig_compare.update_layout(barmode='group', yaxis_title='kWh')
    st.plotly_chart(fig_compare, use_container_width=True)
    
    # --- 报告导出 ---
    st.subheader("📥 下载报告")
    if st.button("生成详细分析报告 (Excel)"):
        report_file = generate_excel_report(baseline, modules, pricing_config)
        st.download_button(
            label="⬇️ 点击下载 Excel 报告",
            data=report_file,
            file_name="零碳项目收益估值报告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


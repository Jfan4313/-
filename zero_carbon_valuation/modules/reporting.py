import pandas as pd
from io import BytesIO
from typing import Dict, Any, List

def generate_excel_report(
    baseline: Dict[str, Any],
    modules_result: Dict[str, Any],
    pricing_config: Any
) -> BytesIO:
    """生成Excel格式的计算报告"""
    
    # 创建BytesIO对象
    output = BytesIO()
    
    # 1. 汇总表 (Overview)
    overview_data = {
        "项目年总用电量 (kWh)": baseline.get("annual_kwh", 0),
        "项目年总电费 (RMB)": baseline.get("annual_bill", 0),
        "改造后用电量 (kWh)": baseline.get("annual_kwh", 0) - sum([
            m.get("saving_kwh", 0) for m in modules_result.values() if m and "saving_kwh" in m
        ]) - sum([
            m.get("generation", 0) for m in modules_result.values() if m and "generation" in m
        ]),
        "年总收益 (RMB)": sum([
            (m.get("saving_rmb", 0) or m.get("revenue", 0) or m.get("net_revenue", 0)) 
            for m in modules_result.values() if m
        ]),
        "总投资 (RMB)": sum([
            (m.get("investment", 0)) for m in modules_result.values() if m
        ]),
    }
    overview_data["综合回收期 (年)"] = overview_data["总投资 (RMB)"] / overview_data["年总收益 (RMB)"] if overview_data["年总收益 (RMB)"] > 0 else 999
    
    df_overview = pd.DataFrame(list(overview_data.items()), columns=["指标", "数值"])
    
    # 2. 模块详细表 (Modules Detail)
    detail_rows = []
    headers = ["模块", "年节电/发电(kWh)", "年收益(RMB)", "投资(RMB)", "回收期(年)"]
    
    for name, data in modules_result.items():
        if not data:
            continue
            
        kwh = data.get("saving_kwh", 0) or data.get("generation", 0) or 0
        revenue = data.get("saving_rmb", 0) or data.get("revenue", 0) or data.get("net_revenue", 0) or 0
        inv = data.get("investment", 0) or 0
        payback = data.get("payback", 999)
        
        detail_rows.append([name, kwh, revenue, inv, payback])
        
    df_detail = pd.DataFrame(detail_rows, columns=headers)
    
    # 3. 写入Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_overview.to_excel(writer, sheet_name='项目总览', index=False)
        df_detail.to_excel(writer, sheet_name='模块详细', index=False)
        
        # 添加电费单数据 (如果存在)
        if "monthly_data" in baseline and isinstance(baseline["monthly_data"], pd.DataFrame):
            baseline["monthly_data"].to_excel(writer, sheet_name='电费单原始数据', index=False)
        elif "monthly_totals" in baseline:
            df_monthly = pd.DataFrame({"月份": list(range(1, 13)), "用电量": baseline["monthly_totals"]})
            df_monthly.to_excel(writer, sheet_name='月度用电', index=False)
            
    output.seek(0)
    return output

def save_report_to_disk(
    baseline: Dict[str, Any],
    modules_result: Dict[str, Any],
    pricing_config: Any,
    filename: str = "Zero_Carbon_Project_Report.xlsx"
):
    """保存Excel报告到磁盘"""
    excel_file = generate_excel_report(baseline, modules_result, pricing_config)
    with open(filename, "wb") as f:
        f.write(excel_file.getvalue())
    return filename

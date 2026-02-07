from .base import BaseModule, SimulationResult

class PVModule(BaseModule):
    def __init__(self):
        super().__init__("Photovoltaic System")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        Inputs:
        - capacity_kw: float
        - annual_yield_hours: float (e.g. 1100 hours/year)
        - self_use_ratio: float (0.0 to 1.0)
        - electricity_price_buy: float (Avoided cost)
        - electricity_price_sell: float (Feed-in tariff)
        - total_investment_per_w: float (e.g. 3.5 RMB/W)
        """
        capacity = inputs.get("capacity_kw", 0)
        yield_hours = inputs.get("annual_yield_hours", 1000)
        self_use = inputs.get("self_use_ratio", 0.8)
        p_buy = inputs.get("electricity_price_buy", 0.8)
        p_sell = inputs.get("electricity_price_sell", 0.4)
        cost_per_w = inputs.get("total_investment_per_w", 3.0)
        
        # Generation
        total_generation_kwh = capacity * yield_hours
        
        # Revenue Streams
        revenue_self_use = total_generation_kwh * self_use * p_buy
        revenue_feed_in = total_generation_kwh * (1 - self_use) * p_sell
        total_revenue = revenue_self_use + revenue_feed_in
        
        # Financials
        investment = capacity * 1000 * cost_per_w
        annual_maintenance = investment * 0.01
        net_cashflow = total_revenue - annual_maintenance
        
        emission_factor = inputs.get("emission_factor", 0.5703)
        carbon_reduction = total_generation_kwh * emission_factor / 1000.0

        metrics = self.calculate_financials(investment, net_cashflow, lifespan_years=25)

        return SimulationResult(
            module_name=self.name,
            annual_revenue=total_revenue,
            total_investment=investment,
            annual_maintenance_cost=annual_maintenance,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=carbon_reduction
        )

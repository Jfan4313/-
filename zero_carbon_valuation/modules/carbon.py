from .base import BaseModule, SimulationResult

class CarbonAssetModule(BaseModule):
    def __init__(self):
        super().__init__("Carbon Assets (CCER/Greencert)")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        Inputs:
        - total_carbon_reduction_tons: float
        - carbon_price_per_ton: float
        - transaction_cost_pct: float
        """
        tons = inputs.get("total_carbon_reduction_tons", 0)
        price = inputs.get("carbon_price_per_ton", 50.0) # e.g. 50 RMB/ton
        cost_pct = inputs.get("transaction_cost_pct", 0.10) # Verification fees etc.
        
        gross_revenue = tons * price
        transaction_cost = gross_revenue * cost_pct
        
        net_revenue = gross_revenue - transaction_cost
        
        # Investment is usually low (Verification fee), treat as 0 or small op-ex
        # We put transaction cost as maintenance/opex
        investment = inputs.get("initial_setup_cost", 20000) # Consulting usage
        
        metrics = self.calculate_financials(investment, net_revenue, lifespan_years=5)

        return SimulationResult(
            module_name=self.name,
            annual_revenue=gross_revenue,
            total_investment=investment,
            annual_maintenance_cost=transaction_cost,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=0 # This allows monetization, doesn't create new reduction
        )

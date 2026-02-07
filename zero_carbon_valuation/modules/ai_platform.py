from .base import BaseModule, SimulationResult

class AIPlatformModule(BaseModule):
    def __init__(self):
        super().__init__("AI Energy Mgmt Platform")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        Inputs:
        - baseline_annual_energy_cost: float (Total bill without AI)
        - efficiency_improvement_pct: float (e.g. 0.05 for 5%)
        - load_shift_savings_pct: float (e.g. 0.03 for 3% bill reduction via optimization)
        - software_implementation_cost: float
        - annual_saas_fee: float
        - hardware_integration_cost: float (Sensors, gateways)
        """
        baseline_cost = inputs.get("baseline_annual_energy_cost", 0)
        eff_pct = inputs.get("efficiency_improvement_pct", 0.03)
        shift_pct = inputs.get("load_shift_savings_pct", 0.02)
        
        total_saving_pct = eff_pct + shift_pct
        annual_savings = baseline_cost * total_saving_pct
        
        investment = inputs.get("software_implementation_cost", 100000) + \
                     inputs.get("hardware_integration_cost", 50000)
        
        annual_saas = inputs.get("annual_saas_fee", 20000)
        
        net_cashflow = annual_savings - annual_saas
        
        # Carbon: AI reduces energy usage, so it reduces carbon directly.
        # We need annual kWh to calc tons.
        # Approximate from cost if kWh not given?
        # Let's assume avg price 0.8 to back-calculate kWh.
        avg_price = 0.8
        saved_kwh = annual_savings / avg_price
        emission_factor = inputs.get("emission_factor", 0.5703)
        carbon_reduction = saved_kwh * emission_factor / 1000.0

        metrics = self.calculate_financials(investment, net_cashflow, lifespan_years=10)

        return SimulationResult(
            module_name=self.name,
            annual_revenue=annual_savings,
            total_investment=investment,
            annual_maintenance_cost=annual_saas,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=carbon_reduction
        )

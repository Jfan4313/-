from .base import BaseModule, SimulationResult

class ChargingModule(BaseModule):
    def __init__(self):
        super().__init__("EV Charging System")

    def calculate(self, inputs: dict) -> SimulationResult:
        """
        Inputs:
        - num_chargers: int
        - power_per_charger_kw: float
        - daily_utilization_hours: float
        - service_fee_per_kwh: float (e.g. 0.6 RMB)
        - electricity_price_grid: float (Cost)
        - electricity_price_user: float (Price charged to user, often Grid + Service)
        - investment_per_charger: float
        """
        count = inputs.get("num_chargers", 0)
        power = inputs.get("power_per_charger_kw", 7)
        hours = inputs.get("daily_utilization_hours", 4)
        service_fee = inputs.get("service_fee_per_kwh", 0.5)
        # Often user pays RealTimePrice + ServiceFee.
        # So Revenue = ServiceFee.
        # If operator pays flat and charges TOU, there is spread revenue.
        # We assume pass-through + service fee model for simplicity unless specified.
        
        daily_kwh = count * power * hours
        annual_kwh = daily_kwh * 365
        
        annual_service_revenue = annual_kwh * service_fee
        
        # Financials
        investment = count * inputs.get("investment_per_charger", 5000)
        annual_maint = investment * 0.03 # Higher maintenance for public chargers
        
        net_cashflow = annual_service_revenue - annual_maint
        
        # Carbon reduction accounts for switching Gas -> EV?
        # Usually standard is: 1 kWh EV = ~0.3-0.5 L Petrol saved? 
        # Or we leave that to the Transport sector.
        # For a building project, usually charging piles don't claim the carbon credit of the cars.
        carbon_reduction = 0.0 

        metrics = self.calculate_financials(investment, net_cashflow, lifespan_years=8)

        return SimulationResult(
            module_name=self.name,
            annual_revenue=annual_service_revenue,
            total_investment=investment,
            annual_maintenance_cost=annual_maint,
            payback_period_years=metrics["payback_years"],
            roi=metrics["roi"],
            irr=metrics["irr"],
            carbon_reduction_tons=carbon_reduction
        )

# EVolve: Assumptions, Boundaries & Limitations

## 1. System Scope & Engineering Boundaries
EVolve is designed strictly as an engineering computational learning platform and decision-support prototype. It is explicitly **not**:
- A certified automotive Battery Management System (BMS).
- An On-Board Diagnostics (OBD-II) vehicle scanner.
- A vehicle controller or physical charging station supervisor.

---

## 2. Core Mathematical Assumptions

### 2.1 State of Charge (SoC) Linearity
- **Assumption:** EVolve models available energy as $E = C_u \cdot (S / 100)$, implying a linear relationship between open-circuit voltage / SoC percentage and usable kilowatt-hours.
- **Physical Reality:** Real Lithium-Ion batteries exhibit nonlinear open-circuit voltage curves (e.g. flat voltage plateaus in Lithium Iron Phosphate / LFP chemistries). The linear model serves as a practical, explainable approximation for macro-level energy accounting.

### 2.2 Charging Efficiency & Losses
- **Assumption:** Delivered energy calculated by integrating power measurements $\int P(t) dt$ represents energy provided at the charger interface.
- **Physical Reality:** Charger conversion losses, onboard AC-DC rectifier losses (typically 85-92% efficient), battery internal resistance heat generation ($I^2 R$), and active thermal conditioning (fans, coolant pumps) mean energy stored in cells is slightly less than energy drawn from the grid.

### 2.3 Constant-Power vs Variable-Power Tapering
- **Assumption:** Baseline charging time estimates use $T = \Delta E / P$.
- **Correction:** EVolve provides the variable-power model $T = \int (C_u / 100) / P(S) dS$ to account for charging taper above 80% SoC, where BMS transitions from Constant Current (CC) to Constant Voltage (CV).

### 2.4 Driving Consumption Determinants
- **Assumption:** Range predictions assume a steady consumption rate $c$ ($\text{kWh/km}$).
- **Physical Reality:** Real driving consumption varies dynamically based on:
  - Aerodynamic drag ($F_d \propto v^2$)
  - Ambient temperature (cabin heating/cooling and battery internal resistance)
  - Elevation and road topography
  - Tire rolling resistance and vehicle cargo weight
  - Driver aggression and regenerative braking habits
- **Mitigation:** EVolve provides Conservative (+15%) and Optimistic (-15%) scenario bounds to reflect operational variance.

---

## 3. Battery Health (SOH) Limitations
- **Boundary:** SOH cannot be inferred from a single daily drive or superficial charge cycle.
- **Requirement:** Reliable SOH calculation requires standardized full charge-discharge capacity tests conducted at controlled ambient temperatures.
- **Disclaimer:** EVolve estimates SOH from user-entered or lab-measured usable capacity readings and makes no claims to override OEM manufacturer diagnostic tools.

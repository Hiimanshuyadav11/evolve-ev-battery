# EVolve: Mathematical & Computational Methodology

## 1. Overview
EVolve is an engineering analytics and decision-support prototype applying numerical methods to electric-vehicle (EV) energy data. This document formalizes the governing equations, numerical algorithms, input/output boundary conditions, and mathematical derivations implemented in the system.

---

## 2. Fundamental System Definitions
Let:
- $C_n$: Nominal battery capacity ($\text{kWh}$)
- $C_u$: Usable battery capacity ($\text{kWh}$), where $0 < C_u \le C_n$
- $S$: State of Charge ($\% \text{ SoC}$), where $0 \le S \le 100$
- $P(t)$: Instantaneous charging power ($\text{kW}$) at time $t$
- $E$: Energy delivered or consumed ($\text{kWh}$)
- $d$: Driving distance ($\text{km}$)
- $c$: Energy consumption rate ($\text{kWh/km}$) or $c_{100} = 100 \times c$ ($\text{kWh/100 km}$)
- $R$: Estimated driving range ($\text{km}$)

### Available Battery Energy
Assuming linear mapping between SoC percentage and usable energy:
$$E_{\text{available}} = C_u \left( \frac{S}{100} \right)$$

---

## 3. Interpolation of Missing Sensor Telemetry

### 3.1 Linear Interpolation
Given known telemetry coordinates $(x_0, y_0)$ and $(x_1, y_1)$ where $x_0 \ne x_1$:
$$y(x) = y_0 + \frac{x - x_0}{x_1 - x_0} (y_1 - y_0)$$
Slope:
$$m = \frac{y_1 - y_0}{x_1 - x_0}$$

### 3.2 Newton's Divided-Difference Polynomial Interpolation
For $n+1$ distinct points $(x_0, y_0), (x_1, y_1), \dots, (x_n, y_n)$:
$$P_n(x) = f[x_0] + \sum_{k=1}^n f[x_0, x_1, \dots, x_k] \prod_{j=0}^{k-1} (x - x_j)$$
Divided differences are computed recursively:
$$f[x_i] = y_i$$
$$f[x_i, \dots, x_{i+k}] = \frac{f[x_{i+1}, \dots, x_{i+k}] - f[x_i, \dots, x_{i+k-1}]}{x_{i+k} - x_i}$$

---

## 4. Numerical Integration of Delivered Charging Energy

### 4.1 Composite Trapezoidal Rule
Charging energy is the time-integral of electric power $E = \int P(t) dt$. For discrete timestamps in minutes $\{t_0, t_1, \dots, t_n\}$ and power $\{P_0, P_1, \dots, P_n\}$:
$$E \approx \sum_{i=0}^{n-1} \frac{P_i + P_{i+1}}{2} \left( \frac{t_{i+1} - t_i}{60} \right) \quad [\text{kWh}]$$

### 4.2 Simpson's 1/3 Rule
When sample intervals are uniformly spaced ($h = \Delta t_{\text{hours}} = \text{constant}$) and the number of subintervals $n$ is even (odd number of points):
$$E \approx \frac{h}{3} \left[ P_0 + P_n + 4 \sum_{i \in \text{odd}} P_i + 2 \sum_{i \in \text{even}, i \ne 0, n} P_i \right]$$

---

## 5. Charging Time Estimation

### 5.1 Constant-Power Baseline
$$\Delta E = C_u \left( \frac{S_{\text{target}} - S_{\text{current}}}{100} \right)$$
$$T_{\text{hours}} = \frac{\Delta E}{P_{\text{constant}}}$$

### 5.2 Variable-Power Curve Integration
As battery saturation increases, charging power tapers. The infinitesimal time $dt$ to deposit charge $dS$ is:
$$dt = \frac{C_u / 100}{P(S)} dS \implies T = \int_{S_{\text{current}}}^{S_{\text{target}}} \frac{C_u / 100}{P(S)} dS$$
EVolve solves this integral numerically using composite trapezoidal quadrature over piecewise-interpolated power curves $P(S)$.

---

## 6. Driving Consumption & Least Squares Linear Regression
Using historical trip observations $(d_i, E_i)$:
$$\hat{E}(d) = a + b \cdot d$$
Where:
$$b = \frac{n \sum (d_i E_i) - (\sum d_i)(\sum E_i)}{n \sum d_i^2 - (\sum d_i)^2} \quad [\text{kWh/km}]$$
$$a = \bar{E} - b \bar{d} \quad [\text{kWh}]$$

---

## 7. Journey Feasibility & Numerical Root Finding
For journey distance $d$, consumption $c$, usable capacity $C_u$, and arrival reserve $S_r$, the residual function is:
$$f(S) = C_u \left( \frac{S}{100} \right) - (d \cdot c) - C_u \left( \frac{S_r}{100} \right) = 0$$

### 7.1 Bisection Method
$$m = \frac{a + b}{2}$$

### 7.2 Newton-Raphson Method
$$x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}$$
$$f'(S) = \frac{C_u}{100}$$

---

## 8. Battery State of Health (SOH)
$$\text{SOH} (\%) = \frac{C_{\text{usable, current}}}{C_{\text{usable, original}}} \times 100$$
$$\text{Capacity Loss } L = C_{\text{original}} - C_{\text{current}} \quad [\text{kWh}]$$

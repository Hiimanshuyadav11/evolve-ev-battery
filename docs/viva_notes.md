# EVolve: Viva Voce Defense & Examination Notes

**Subject:** Computational Methods / Numerical Analysis Lab  
**Application:** EVolve — Intelligent EV Battery Analytics & Predictive System  
**Category:** B.Tech Second-Year Engineering Project  

---

## 1. Frequently Asked Viva Questions & Model Answers

### Q1: Why do we use numerical integration for charging sessions instead of multiplying power by time?
**Answer:** Charging power is rarely constant in the real world. In DC Fast Charging, stations deliver peak power (e.g., 50 kW or 150 kW) until approximately 60–80% SoC, after which the vehicle BMS tapers power down to 10–15 kW to protect cell chemistry. In AC charging, grid voltage fluctuations cause minor power variations. Because power $P(t)$ is a time-varying function observed at discrete timestamps, delivered energy is the definite integral:
$$E = \int_{t_0}^{t_n} P(t) dt$$
We employ the **Composite Trapezoidal Rule** for arbitrary time intervals, and **Simpson's 1/3 Rule** for uniformly spaced intervals to accurately calculate kilowatt-hours delivered.

---

### Q2: Why can't Simpson's 1/3 Rule be applied to every charging session?
**Answer:** Simpson's 1/3 Rule has two strict mathematical prerequisites:
1. **Uniform Step Size:** Subintervals must be equally spaced ($\Delta t_i = h = \text{constant}$). Real telemetry often arrives irregularly.
2. **Even Number of Subintervals:** Because each parabolic segment connects three adjacent points (spanning two subintervals), the total interval count $n$ must be even (meaning an odd number of data points $N = n + 1$).
If either condition is violated, EVolve rejects Simpson's 1/3 Rule and transparently falls back to the **Trapezoidal Rule**.

---

### Q3: What is the truncation error comparison between Trapezoidal and Simpson's 1/3 Rule?
**Answer:**
- **Trapezoidal Rule:** Approximates $f(x)$ with straight-line segments.
  - Local error: $O(h^3)$
  - Global error: $O(h^2)$
- **Simpson's 1/3 Rule:** Approximates $f(x)$ with second-order parabolas.
  - Local error: $O(h^5)$
  - Global error: $O(h^4)$
On smooth nonlinear curves with uniform steps, Simpson's 1/3 Rule converges significantly faster and provides higher numerical precision.

---

### Q4: When should we use Newton Divided-Difference vs Linear Interpolation?
**Answer:**
- **Linear Interpolation:** Connects two immediate bounding samples $(x_0, y_0)$ and $(x_1, y_1)$. It is robust, localized, and immune to global polynomial instability.
- **Newton Divided-Difference:** Constructs a global polynomial of degree $n$ through all $n+1$ distinct points using a divided-difference table. It provides smooth curvature across multiple points.
- **Limitation / Caution:** If the polynomial degree exceeds 4 or 5 ($n > 4$), high-degree polynomials can experience **Runge's Phenomenon** (wild oscillations near interval edges). EVolve explicitly warns the user whenever $n > 4$.

---

### Q5: How is linear regression used in driving consumption?
**Answer:** We model energy consumption as a linear function of distance: $E = a + b \cdot d$.
- The **slope $b$** represents the marginal consumption rate ($\text{kWh/km}$).
- The **intercept $a$** accounts for baseline overhead energy (such as pre-conditioning, idling, cabin heating/air conditioning, and computer electronics).
- We evaluate goodness-of-fit via the coefficient of determination $R^2$, Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE).

---

### Q6: How does EVolve demonstrate numerical root-finding?
**Answer:** In the Trip Simulator and Methods Lab, we determine the minimum starting SoC $S_{\min}$ needed to complete a journey of distance $d$ at consumption $c$ while arriving with reserve $S_r$.
The residual function is:
$$f(S) = C_u \left( \frac{S}{100} \right) - (d \cdot c) - C_u \left( \frac{S_r}{100} \right) = 0$$
While this equation has an exact linear algebraic solution $S_{\min} = \frac{100(d \cdot c)}{C_u} + S_r$, EVolve formulates it as $f(S) = 0$ to demonstrate and compare:
1. **Bisection Method:** Bracket halving, linear convergence, guaranteed to converge when $f(a) \cdot f(b) < 0$.
2. **Newton-Raphson Method:** Tangent projection, quadratic convergence $O(\epsilon^2)$, requiring $x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}$ with safeguards against near-zero derivatives.

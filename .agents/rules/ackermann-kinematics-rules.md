# Reglas Cinemáticas y de Control Ackermann para UGV Voyager 3

Este conjunto de reglas gobierna el modelado cinemático, las transformaciones de velocidad y las restricciones físicas del chasis Ackermann del Voyager 3:

---

## 1. Modelo Cinemático Bicicleta (Bicycle Model)

El vehículo se modela en el plano $2D$ tomando como referencia el centro del eje motriz trasero (`base_link`):

$$\dot{x} = v \cos(\theta)$$
$$\dot{y} = v \sin(\theta)$$
$$\dot{\theta} = \omega = \frac{v}{L} \tan(\delta)$$

Donde:
* $v$: Velocidad lineal longitudinal del vehículo.
* $\theta$: Orientación (yaw) en el plano.
* $\omega$: Velocidad angular de rotación sobre el eje $z$.
* $\delta$: Ángulo de viraje de las ruedas directrices delanteras.
* $L$: Batalla o distancia entre ejes delantero y trasero (aproximadamente $0.35\text{ m}$).

---

## 2. Restricciones Físicas y Guardas Numéricas No Negociables

1. **Protección Contra Singularidad en Parada ($v \to 0$):**
   - Para calcular el ángulo de viraje $\delta$ a partir de un comando deseado de $(\omega, v)$:
     $$\delta = \arctan\left(\frac{L \cdot \omega}{v + \text{sign}(v) \cdot \epsilon}\right)$$
   - $\epsilon = 10^{-7}$ debe sumarse siempre en el denominador cuando $|v| < \epsilon$.
   - Si $|v| < 10^{-4}\text{ m/s}$, el cálculo debe conmutar a $\delta = 0$ o mantener el último ángulo válido sin intentar calcular curvaturas infinitas.

2. **Límite Físico de Giro ($\delta_{\max}$):**
   - El varillaje del servo de dirección y la mecánica del chasis imponen un límite angular mecánico estricto:
     $$\delta \in [-\delta_{\max}, \delta_{\max}], \quad \delta_{\max} \approx 0.436\text{ rad} \ (25^\circ)$$
   - Prohibido comandar ángulos mayores que provocarían bloqueo mecánico o esfuerzo excesivo en el servo `MAIN OUT 1`.

3. **Radio de Giro Mínimo ($R_{\min}$):**
   - El radio de giro mínimo posible es:
     $$R_{\min} = \frac{L}{\tan(\delta_{\max})} \approx \frac{0.35}{\tan(25^\circ)} \approx 0.75\text{ m}$$
   - Cualquier algoritmo de planificación local (como Nearness Diagram o TEB) debe considerar que el vehículo **no puede rotar sobre su propio eje** ($\omega \neq 0$ con $v = 0$ es físicamente imposible en cinemática Ackermann).

---

## 3. Rampas de Aceleración y Prevención de Deslizamiento

1. **Filtro de Rampa en Tracción:**
   - Para proteger la transmisión por piñón/corona y evitar patinaje de las ruedas motrices, la tasa de cambio de velocidad debe estar limitada:
     $$\left|\frac{dv}{dt}\right| \le a_{\max} \quad (a_{\max} \approx 1.5\text{ m/s}^2)$$
2. **Dirección Suavizada:**
   - La velocidad angular del servo no debe exceder la capacidad del actuador:
     $$\left|\frac{d\delta}{dt}\right| \le \dot{\delta}_{\max} \quad (\dot{\delta}_{\max} \approx 1.2\text{ rad/s})$$

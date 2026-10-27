# Reglas de Revisión Adversarial de Código (UGV Voyager 3)

Todo código desarrollado para el autopiloto, nodos ROS 2, algoritmos de evasión o puentes de telemetría debe superar esta auditoría previa a su integración o ejecución:

---

## 1. Revisión en Contexto Fresco (Fresh-Context Check)
* Analizar el código asumiendo que el vehículo opera en un entorno físico no controlado con obstáculos inesperados y pérdida potencial de señal de radio.
* Preguntarse siempre: *¿Qué ocurre si el LiDAR envía un frame corrupto o vacío? ¿Qué pasa si la velocidad se anula súbitamente? ¿Qué pasa si el actuador se atasca?*

---

## 2. Auditoría de Casos Límite Físicos y Matemáticos

1. **Guardas Epsilon en Geometría y Cinemática:**
   - Comprobar que en cualquier cálculo de curvatura $\kappa = \frac{\tan(\delta)}{L}$ o ángulo $\delta = \arctan(\frac{L \omega}{v})$ exista la guarda $\epsilon = 10^{-7}$ para evitar división por cero cuando $v \to 0$ o $L \to 0$.
2. **Saturación Incondicional de Actuadores:**
   - Comprobar que el ángulo de dirección esté acotado entre $[-\delta_{\max}, \delta_{\max}]$ ($25^\circ$).
   - Comprobar que la velocidad lineal esté limitada al rango seguro del chasis ($[-v_{\max}, v_{\max}]$).
3. **Manejo de Rangos Inválidos en el LiDAR (`sensor_msgs/LaserScan`):**
   - El código debe filtrar explícitamente valores `range < range_min`, `range > range_max`, `inf` y `NaN` antes de alimentar el cálculo del Nearness Diagram o campos de fuerza.

---

## 3. Eficiencia en Sistemas Embebidos (Raspberry Pi 3)
* **Gestión de Memoria y CPU:**
  - Evitar asignaciones masivas de memoria o creación repetitiva de objetos dentro de callbacks de alta frecuencia ($> 20\text{ Hz}$).
  - Reutilizar listas o arrays de cálculo siempre que sea posible.
* **Políticas de QoS Adecuadas:**
  - Verificar que no se use `ReliabilityPolicy.RELIABLE` en tópicos sensoriales de alto ancho de banda que puedan saturar el bus DDS en la RPi.

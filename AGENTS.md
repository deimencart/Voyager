# Workspace Guidelines: UGV Voyager 3 Autonomy & ROS 2 (Voyager)

Directrices de desarrollo, arquitectura de software y estándares de ingeniería para el workspace `D:\Voyager`.
Este entorno de desarrollo y operación adopta con el máximo rigor las directrices de robótica autónoma, sistemas embebidos en tiempo real, arquitectura **ROS 2**, cinemática vehicular **Ackermann**, telemetría **MAVLink / MAVROS**, complementadas con la filosofía **Ponytail++ (Senior Minimalist Engineer)** y el **Protocolo Feynman de Verificación**.

---

## 🚜 1. Identidad de la Plataforma y Especificaciones Físicas

* **Plataforma:** UGV Voyager 3 (Fible ALTU - Proyecto Europeo H2020 RAWFIE).
* **Cinemática:** Vehículo terrestre no tripulado con dirección tipo **Ackermann** (eje delantero directriz con servo PWM, tracción trasera con ESC/motor brushless).
* **Autopiloto:** Pixhawk 1 con firmware **ArduPilot (APM:Rover / ArduRover v3.4.2+)**.
* **Computadora de Misión (Companion Computer):** Raspberry Pi 3 Model B (UART de alta velocidad en `/dev/serial0` a 921.600 bps).
* **Percepción Principal:** LiDAR rotativo 360° **LightWare SF40/C** (12V DC, UART a 115.200 bps en Pixhawk `SERIAL 4/5` o RPi).
* **Navegación Global:** GPS U-blox Neo-M8N + Brújula externa I2C (`SERIAL 3`).
* **Comunicaciones:**
  * Red de Corto Alcance / Laboratorio: Wi-Fi integrado 2.4 GHz (Hotspot directo `DroneLab` / `192.168.137.x` o router MikroTik `192.168.1.1`).
  * Telemetría Remota / BVLOS: Módem celular 4G LTE Huawei HiLink (`192.168.8.1`) + túnel VPN seguro hacia GCS / Cloud.
  * Puerto de Telemetría MAVLink: UDP `14550` (hacia QGroundControl y Mission Planner).

---

## 🏗️ 2. Estructura del Workspace

```
D:\Voyager/
├── ros2_ws/                       # Workspace principal de ROS 2
│   └── src/
│       ├── voyager_bringup/       # Launch files, configuración MAVROS y orquestación
│       └── voyager_navigation/    # Nodos de control reactivo (Nearness Diagram, Ackermann)
├── repos/                         # Repositorios y submódulos clonados (ardupilot, mavros, pymavlink)
├── analisis_sistema/              # Documentación técnica, pinouts, extracciones de RPi y bitácoras
│   ├── MANUAL_SISTEMA_VOYAGER3.md # Especificaciones eléctricas y de conexionado
│   ├── BITACORA_SESION_*.md       # Hitos de pruebas y validaciones experimentales
│   └── CONFIGURACION_PARAMETROS_PIXHAWK.parm # Parámetros volcados de ArduRover
├── sdbackup/ & backup_sdbackup/   # Imagen forense .img (~32 GB) de la tarjeta SD original
├── .agents/                       # Reglas modulares de ingeniería y catálogo de skills
│   ├── rules/                     # Reglas de ROS 2, cinemática, hardware y revisión
│   └── skills/                    # Habilidades operativas del agente
├── AGENTS.md & GEMINI.md          # Directrices generales del agente
├── CODING_GUIDELINES.md           # Estándares de programación y estilo para ROS 2
└── ROADMAP.md                     # Estado de fases, hitos y tareas activas
```

---

## 🛠️ 3. Filosofía Ponytail++ (Simplicidad Radical y Robustez Crítica)

1. **YAGNI Estricto (You Aren't Gonna Need It):** No crear wrappers innecesarios para APIs directas de `rclpy` o `pymavlink`.
2. **Inlining sobre Fragmentación:** Si una transformación matemática o cálculo cinemático tiene menos de 10 líneas y se ejecuta en un solo lugar del callback, mantenerla en línea.
3. **Cero Código Muerto:** Prohibido código comentado, bloques de prueba abandonados o prints temporales.
4. **Ediciones Quirúrgicas:** Tocar únicamente las líneas necesarias para el objetivo actual; no reescribir código adyacente sin justificación técnica.
5. **Biblioteca Estándar y ROS Canónico:** Priorizar paquetes estándar de ROS (`geometry_msgs`, `sensor_msgs`, `nav_msgs`, `tf2_ros`) y la biblioteca estándar de Python antes de introducir nuevas dependencias.

---

## 🤖 4. Convenciones de Desarrollo en Robótica y ROS 2

### A. Nomenclatura y Tópicos Canónicos
* **Tópicos de Entrada de Sensores:**
  * Escaneo LiDAR: `/scan` (`sensor_msgs/msg/LaserScan`).
  * Odometría: `/odom` o `/mavros/local_position/odom` (`nav_msgs/msg/Odometry`).
  * Telemetría IMU: `/mavros/imu/data` (`sensor_msgs/msg/Imu`).
* **Tópicos de Comando de Actuación:**
  * Velocidad y Giro Twist: `/cmd_vel` (`geometry_msgs/msg/Twist`).
  * Comando Específico Ackermann: `/cmd_ackermann` (`ackermann_msgs/msg/AckermannDriveStamped`).
  * Modo de Operación y Failsafe: `/voyager/safety_state` (`std_msgs/msg/String` o mensaje personalizado).
* **Frames de Coordenadas (REP 105):**
  * `base_link`: Centro del eje trasero del UGV.
  * `odom`: Origen de odometría local continua.
  * `map`: Coordenadas globales absolutas (fijadas por GPS/SLAM).
  * `laser_frame`: Centro del emisor óptico del LiDAR LightWare SF40/C.

### B. Estabilidad Numérica y Guardas Epsilon
* **Cálculo de Curvatura y Radio de Giro:**
  $$\kappa = \frac{\tan(\delta)}{L}, \quad R = \frac{1}{\kappa + \text{sign}(\kappa) \cdot \epsilon}$$
  donde $\delta$ es el ángulo de las ruedas delanteras, $L$ es la batalla (wheelbase) y $\epsilon = 10^{-7}$ previene división por cero cuando las ruedas están rectas ($\delta = 0$).
* **Saturación Física Incondicional:**
  * Todo ángulo de dirección solicitado debe ser acotado estrictamente a $[-\delta_{\max}, \delta_{\max}]$ (máx. $25^\circ \approx 0.436\text{ rad}$).
  * La velocidad lineal $v$ debe acotarse a $[v_{\min}, v_{\max}]$ (nunca saturar bruscamente el ESC sin rampas de aceleración).

---

## 🔒 5. Reglas Críticas de Seguridad Eléctrica y Operacional

1. **Aislamiento de Voltajes:**
   * El LiDAR LightWare SF40/C **DEBE alimentarse exclusivamente a 12V DC** desde el rail de potencia PDB. Jamás conectar su línea de alimentación a los buses de 5V de la Raspberry Pi o la Pixhawk.
   * La Raspberry Pi se alimenta con 5.0V regulados (mínimo 2.5A).
   * El rail `MAIN OUT` de la Pixhawk recibe 5.57V desde el BEC auxiliar para mover el servo de dirección.
2. **Heartbeat y Watchdog de Seguridad:**
   * Todo nodo de control que publique en `/cmd_vel` o hacia MAVROS debe incluir un watchdog de seguridad. Si el ciclo de control se interrumpe durante más de $300\text{ ms}$, la velocidad del vehículo debe caer inmediatamente a cero ($v = 0$).
3. **Cero Comandos a Vehículos Desarmados:**
   * Verificar siempre el estado de armado (`/mavros/state -> armed`) antes de enviar comandos de velocidad reactiva.

---

## 📐 6. Protocolo Feynman Obligatorio

Para cualquier explicación teórica, diseño de controladores cinemáticos, algoritmos de navegación reactiva o análisis de fallas:
1. **Deconstrucción Desnuda:** Explicar el fenómeno físico o la limitación cinemática sin jerga vacía ni razonamientos circulares.
2. **Formalismo Matemático en LaTeX:** Describir ecuaciones con KaTeX completo ($$...$$) con verificación de dimensiones.
3. **Grafos Visuales Mermaid:** Diagramas de flujo de datos, árboles de estados o mapas de modos de falla.
4. **Mini-Tests Unitarios:** Aserción o prueba unitaria reproducible en cada implementación de control.

---

## ⛔ 7. Canarios de Contexto y Tripwires Anti-Alucinaciones

* Tienes **ESTRICTAMENTE PROHIBIDO** inventar que el rover tiene tracción diferencial tipo Skid-Steer. El Voyager 3 tiene dirección tipo **Ackermann**.
* Tienes **ESTRICTAMENTE PROHIBIDO** sugerir alimentar el LiDAR SF40/C con los 5V de la Raspberry Pi.
* Si violas estas premisas, es señal inequívoca de pérdida de contexto crítico.

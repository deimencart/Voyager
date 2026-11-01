# Roadmap Técnico del UGV Voyager 3 (ROADMAP.md)

Estado de avance, planificación de fases y bitácora de desarrollo para el vehículo autónomo Voyager 3.

---

## 🧭 Resumen de Fases y Estado Actual

| Fase | Título | Estado | Progreso |
| :--- | :--- | :---: | :---: |
| **Fase 0** | Auditoría Eléctrica, Seguridad y Respaldo Forense | **Completado** | 100% |
| **Fase 1** | Conectividad Inalámbrica y Telemetría MAVLink | **Completado** | 100% |
| **Fase 2** | Stack Base ROS 2, Puente MAVROS y Visión | **Completado** | 90% |
| **Fase 3** | Percepción LiDAR 360°, Teleoperación y Evasión Reactiva | **En Progreso** | 75% |
| **Fase 4** | Mapeo 2D, Localización y Navegación Global (Nav2 / SLAM) | **Planificado** | 10% |
| **Fase 5** | Trabajo Futuro: Migración ROS 2 On-Board y Bypass LiDAR denso | **Planificado** | 0% |
| **Fase 6** | Autonomía Jerárquica y Supervisión Agentica (I+D Futuro) | **Planificado** | 15% |

---

## 📌 Detalle por Fases

### Fase 0: Auditoría Eléctrica, Seguridad y Respaldo Forense
- [x] Extracción y respaldo bit a bit de la tarjeta micro-SD original de la Raspberry Pi 3 (`sd.img`, 31.9 GB).
- [x] Auditoría eléctrica del sensor LiDAR LightWare SF40/C: corrección del mito de 5V y fijación de la línea nominal de **12V DC**.
- [x] Identificación de pinouts y conexionado de la controladora Pixhawk 1:
  - `MAIN OUT 1`: Servo de dirección delantera (Función 26 - GroundSteering).
  - `MAIN OUT 3`: ESC y motor de tracción trasera (Función 70 - Throttle).
  - `SERIAL 4/5`: Conexión serial LiDAR SF40/C a 115.200 bps.
  - `TELEM 2`: Conexión de alta velocidad con Raspberry Pi 3 (`/dev/serial0` a 921.600 bps).
- [x] Respaldo de parámetros de vuelo y navegación de ArduRover (`CONFIGURACION_PARAMETROS_PIXHAWK.parm`).

### Fase 1: Conectividad Inalámbrica y Telemetría MAVLink
- [x] Conexión inalámbrica autónoma mediante Wi-Fi Directo / Hotspot de laboratorio (`DroneLab`, `192.168.137.153`), eliminando colisiones de routing del MikroTik.
- [x] Validación de flujo bidireccional MAVLink por UDP `14550` hacia **QGroundControl** (v5.1.5) y **Mission Planner**.
- [x] Desmitificación del script heredado `runDrone.sh` y el mensaje `"RPI is OFFLINE"` (debido al ping extinto al servidor de Atenas `195.134.71.99`).
- [x] Definición de la estrategia de comunicaciones: Wi-Fi para laboratorio/taller vs. módem 4G LTE Huawei para BVLOS.

### Fase 2: Stack Base ROS 2, Puente MAVROS y Visión
- [x] Creación del espacio de trabajo ROS 2: `ros2_ws/src/`.
- [x] Configuración de `voyager_bringup`:
  - Archivo de parámetros MAVROS (`mavros_config.yaml`).
  - Launch file orquestador (`voyager_bringup.launch.py`).
- [x] Streaming de vídeo H.264 RTP en tiempo real (1024x768 @ 30 FPS) desde cámara CSI Raspberry Pi hacia ROS 2 (`camera_receiver_node.py` en `/camera/image_raw`).
- [x] Implementación de transformadas estáticas (`tf2_ros`) para `base_link` $\to$ `laser_frame` y `camera_optical_frame`.

### Fase 3: Percepción LiDAR 360°, Teleoperación y Evasión Reactiva
- [x] Decodificación en tiempo real de LiDAR SF40/C (MAVLink `DISTANCE_SENSOR` ID 132) con interpolación Arc-Cloud 3D a 10 Hz (`sf40_scan_node.py`).
- [x] Teleoperación cinemática Ackermann validada en hardware real (`ackermann_steering_teleop_node.py` y `voyager_teleop_key_node.py`).
- [x] Implementación de Parada de Emergencia (E-STOP) con desarme forzado Pixhawk e inhibición de actuadores en menos de 50 ms.
- [x] Mitigación de picos de corriente inductiva (*inrush current brownout*) mediante software *Slew-Rate Limiter* ($300\,\mu\text{s/s}$).
- [x] Aumento del envolvente de velocidad punta ($1750\,\mu\text{s}$ PWM / $1.2\,\text{m/s}$).
- [ ] Conexión en bucle cerrado de `/scan` con `nearness_diagram_ackermann_node.py` para evasión de obstáculos autónoma.
- [x] Adaptación de la cinemática vehicular Ackermann:
  - Transformación de velocidades angulares a ángulos de giro $\delta = \arctan(L \cdot \omega / v)$.
  - Inclusión de guarda numérica contra división por cero ($\epsilon = 10^{-7}$).
- [ ] Sintonización de sectores de seguridad del algoritmo Nearness Diagram según la envolvente de giro del vehículo.
- [ ] Pruebas en bucle cerrado (SITL en ArduPilot + Gazebo/simulador y posterior validación en hardware real).

### Fase 4: Mapeo 2D, Localización y Navegación Global (Nav2 / SLAM)
- [x] Arquitectura y plantilla base del nodo de guiado por waypoints GPS Ackermann ([`gps_waypoint_follower_node.py`](file:///d:/Voyager/ros2_ws/src/voyager_navigation/voyager_navigation/gps_waypoint_follower_node.py)): proyección geodésica WGS-84 a ENU y control Pure Pursuit acotado a $\pm 25^\circ$.
- [ ] Integración de SLAM 2D (`slam_toolbox` o `cartographer_ros`) a partir del escaneo `/scan` y odometría de ruedas.
- [ ] Configuración del stack de navegación Nav2 con plugins específicos para cinemática Ackermann (e.g. `RegulatedPurePursuitController` o `TEB Local Planner`).
- [ ] Misiones de navegación por waypoints GPS en exteriores y telemetría por túnel 4G LTE celular.

### Fase 5: Trabajo Futuro — Migración de ROS 2 On-Board y Modernización del LiDAR
> **Contexto de Operación:** Actualmente el robot no ejecuta ROS 2 a bordo; la Raspberry Pi 3 opera como pasarela ligera MAVLink UDP hacia la estación de ingeniería (PC/WSL2). El objetivo de esta fase es trasladar la pila completa de ROS 2 directamente a la computadora de misión a bordo.

- [ ] **Despliegue de ROS 2 On-Board:**
  - Instalar distribución de 64 bits (`Ubuntu Server 22.04 LTS arm64`) en nueva microSD para la Raspberry Pi 3B (o migración a SBC de mayor rendimiento como Raspberry Pi 5 / Jetson Orin Nano).
  - Ejecutar ROS 2 Humble de forma local y autónoma a bordo, eliminando la dependencia del enlace Wi-Fi para bucles de control reactivos.
- [ ] **Modernización de la Percepción LiDAR (Superación del cuello de botella de 8 puntos):**
  - **Opción A (Fase intermedia):** Actualizar Pixhawk a ArduRover 4.x para habilitar el mensaje MAVLink `OBSTACLE_DISTANCE` (ID 330), escalando de 8 a **72 sectores discretos** ($5^\circ$ por sector).
  - **Opción B (Fase definitiva para SLAM):** Desconectar líneas de datos serie (TX/RX) del SF40/C de la Pixhawk (`SERIAL 4/5`) y conectarlas directamente a la SBC vía adaptador USB-UART industrial (FTDI).
  - **Garantía Eléctrica:** Preservar la alimentación obligatoria de **12V DC desde la PDB** para el SF40/C (prohibido alimentar desde pines de 5V de la SBC).
  - Desarrollar/ejecutar el nodo nativo ROS 2 en la SBC para leer el protocolo binario LightWare, publicando la nube densa completa (**1.024 a 2.048 puntos por vuelta** a 10 Hz / $\Delta\theta \approx 0.25^\circ$) para mapeo SLAM de alta fidelidad.

### Fase 6: Autonomía Jerárquica y Supervisión Agentica (I+D Futuro)
- [ ] Integración de agente supervisor en estación terrena (GCS) para síntesis de misiones y políticas de navegación en lenguaje natural / código.
- [x] Evaluación técnica de modelos generativos de acción de mundo (**Agentic WAM / AW-0**, arXiv:2610.30136): registro formal en [`analisis_sistema/EVALUACION_TECNICA_AGENTIC_WAM_AW0.md`](file:///d:/Voyager/analisis_sistema/EVALUACION_TECNICA_AGENTIC_WAM_AW0.md). Conclusión de inviabilidad on-board en Raspberry Pi 3B (1 GB RAM) y adopción del modelo jerárquico deliberativo GCS + control determinista Ackermann local.

---

## 📝 Registro de Sesiones
* **2026-10-18:** Auditoría inicial del sistema operativo Stretch, clonación forense y volcado de parámetros.
* **2026-10-24:** Validación del enlace Hotspot, telemetría QGC/Mission Planner, corrección eléctrica 12V del LiDAR SF40/C.
* **2026-10-26:** Creación del entorno agentico integral (.agents, reglas, skills, guidelines y roadmap).
* **2026-10-26:** Definición de la estrategia de portabilidad y replicabilidad para docencia e investigación (`analisis_sistema/GUIA_REPRODUCIBILIDAD_DOCENCIA.md`).
* **2026-10-28:** Ingesta bibliográfica y auditoría exhaustiva de *Agentic World Action Models (AW-0)*. Creación del informe técnico y actualización del corpus de investigación en `candidate_papers.json`.
* **2026-10-28:** Elaboración de propuestas de modernización de hardware, GAP Analysis comparativo y plan de migración para Pixhawk y Raspberry Pi ([`documentation/hardware_description/11_hardware_upgrade_and_gap_analysis.md`](file:///d:/Voyager/documentation/hardware_description/11_hardware_upgrade_and_gap_analysis.md)).

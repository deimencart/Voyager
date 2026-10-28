# Roadmap Técnico del UGV Voyager 3 (ROADMAP.md)

Estado de avance, planificación de fases y bitácora de desarrollo para el vehículo autónomo Voyager 3.

---

## 🧭 Resumen de Fases y Estado Actual

| Fase | Título | Estado | Progreso |
| :--- | :--- | :---: | :---: |
| **Fase 0** | Auditoría Eléctrica, Seguridad y Respaldo Forense | **Completado** | 100% |
| **Fase 1** | Conectividad Inalámbrica y Telemetría MAVLink | **Completado** | 100% |
| **Fase 2** | Stack Base ROS 2 y Puente MAVROS | **En Progreso** | 75% |
| **Fase 3** | Percepción LiDAR 360° y Evasión Reactiva (Nearness Diagram) | **En Progreso** | 60% |
| **Fase 4** | Mapeo 2D, Localización y Navegación Global (Nav2 / SLAM) | **Planificado** | 10% |

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

### Fase 2: Stack Base ROS 2 y Puente MAVROS
- [x] Creación del espacio de trabajo ROS 2: `ros2_ws/src/`.
- [x] Configuración de `voyager_bringup`:
  - Archivo de parámetros MAVROS (`mavros_config.yaml`).
  - Launch file orquestador (`voyager_bringup.launch.py`).
- [ ] Validación de enlace MAVROS activo en la Raspberry Pi 3 con autopiloto armado.
- [ ] Implementación de nodo de publicación de transformadas estáticas (`tf2_ros`) para los frames `base_link`, `laser_frame` y `base_footprint`.

### Fase 3: Percepción LiDAR 360° y Evasión Reactiva (Nearness Diagram)
- [x] Estructura inicial del nodo de evasión reactiva: [`nearness_diagram_ackermann_node.py`](file:///d:/Voyager/ros2_ws/src/voyager_navigation/voyager_navigation/nearness_diagram_ackermann_node.py).
- [x] Adaptación de la cinemática vehicular Ackermann:
  - Transformación de velocidades angulares a ángulos de giro $\delta = \arctan(L \cdot \omega / v)$.
  - Inclusión de guarda numérica contra división por cero ($\epsilon = 10^{-7}$).
- [ ] Sintonización de sectores de seguridad del algoritmo Nearness Diagram según la envolvente de giro del vehículo.
- [ ] Pruebas en bucle cerrado (SITL en ArduPilot + Gazebo/simulador y posterior validación en hardware real).

### Fase 4: Mapeo 2D, Localización y Navegación Global (Nav2 / SLAM)
- [ ] Integración de SLAM 2D (`slam_toolbox` o `cartographer_ros`) a partir del escaneo `/scan` y odometría de ruedas.
- [ ] Configuración del stack de navegación Nav2 con plugins específicos para cinemática Ackermann (e.g. `RegulatedPurePursuitController` o `TEB Local Planner`).
- [ ] Misiones de navegación por waypoints GPS en exteriores y telemetría por túnel 4G LTE celular.

### Fase 5: Autonomía Jerárquica y Supervisión Agentica (I+D Futuro)
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

# GEMINI.md — Directrices del Asistente y Agente de Ingeniería (Voyager 3)

Este archivo actúa como guía rectora complementaria para Gemini y los agentes de IA que operen en `D:\Voyager`.

Consulta los siguientes documentos de referencia obligatoria antes de emprender tareas en este repositorio:

1. **[`AGENTS.md`](file:///d:/Voyager/AGENTS.md)**: Manifiesto general de arquitectura, filosofía Ponytail++, hardware y tripwires.
2. **[`CODING_GUIDELINES.md`](file:///d:/Voyager/CODING_GUIDELINES.md)**: Convenciones de estilo de código, interfaces ROS 2 y MAVROS.
3. **[`ROADMAP.md`](file:///d:/Voyager/ROADMAP.md)**: Estado actual del proyecto, fases y backlog técnico.
4. **[`.agents/rules/`](file:///d:/Voyager/.agents/rules)**: Reglas modulares de cinemática, ROS 2, hardware y revisión adversarial de código.
5. **[`analisis_sistema/MANUAL_SISTEMA_VOYAGER3.md`](file:///d:/Voyager/analisis_sistema/MANUAL_SISTEMA_VOYAGER3.md)**: Manual del fabricante (Fible ALTU / RAWFIE), pinouts y mapa eléctrico.

---

## ⚡ Reglas Resumidas para Gemini en este Workspace

* **Plataforma:** Rover terrestre todoterreno con cinemática **Ackermann** (giro frontal con servo en `MAIN OUT 1`, acelerador/tracción en `MAIN OUT 3`).
* **Companion Computer:** Raspberry Pi 3 Model B comunicada por UART `/dev/serial0` (921.600 bps) con Pixhawk 1 (ArduRover v3.4.2).
* **Percepción:** LiDAR rotativo 360° LightWare SF40/C alimentado **exclusivamente a 12V DC**.
* **Comunicaciones:** Wi-Fi Hotspot `DroneLab` (`192.168.137.x`), MAVLink UDP `14550`, túnel 4G LTE Huawei para BVLOS.
* **Stack Objetivo:** ROS 2 (`voyager_bringup`, `voyager_navigation` con Nearness Diagram Navigation para Ackermann).
* **Protocolo Feynman:** Fórmulas explícitas en LaTeX, diagramas en Mermaid, manejo riguroso de guardas numéricas ($\epsilon = 10^{-7}$) y pruebas unitarias.

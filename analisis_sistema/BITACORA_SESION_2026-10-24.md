# BITÁCORA DE TRABAJO TÉCNICO — ROVER VOYAGER 3 (FIBLE ALTU)
**Fecha:** 2026-10-24  
**Plataforma:** UGV Voyager 3 / Consorcio Europeo H2020 RAWFIE  
**Ubicación:** Laboratorio / Makerspace  
**Sistemas:** Pixhawk 1 (ArduRover V3.4.2), Raspberry Pi 3 Model B, LiDAR LightWare SF40/C, GPS U-blox Neo-M8N, GCS (QGroundControl v5.1.5 & Mission Planner 1.3.x)

---

## 1. Resumen Ejecutivo de la Sesión
Durante la sesión se consolidó la conexión inalámbrica autónoma del UGV Voyager 3, se validó la telemetría en tiempo real tanto en **QGroundControl** como en **Mission Planner**, se auditaron los sensores inerciales y de posicionamiento, se esclareció la arquitectura de red y el rol del módem celular, se realizó la auditoría eléctrica crítica del sensor LiDAR LightWare SF40/C (desmintiendo la alimentación a 5V y fijando los 12V requeridos) y se definieron los pipelines de vídeo y control de los servos de la cámara.

```mermaid
flowchart TD
    subgraph Potencia ["Alimentación y Potencia"]
        BAT["Batería LiPo / Fuente Lab"] --> PDB["Placa Distribución (PDB)"]
        PDB -->|12V DC nominal| LIDAR["LiDAR SF40/C (Motor 360°)"]
        PDB -->|5.57V BEC| SERVOR["Rail MAIN OUT Pixhawk"]
        PDB -->|5.0V BEC| RPI["Raspberry Pi 3B"]
    end

    subgraph Control_Telemetria ["Autopiloto y Telemetría"]
        RPI <-->|UART /dev/serial0 @ 921.600 bps| PIX["Pixhawk 1 (ArduRover V3.4.2)"]
        LIDAR -->|UART SERIAL 4/5 @ 115.200 bps| PIX
        GPS["GPS U-blox Neo-M8N"] -->|UART SERIAL 3 + I2C| PIX
        CAM["Cámara CSI v2"] -->|Cinta CSI| RPI
    end

    subgraph Estacion_Tierra ["GCS / Laptop"]
        RPI <-->|WiFi Hotspot DroneLab (192.168.137.x)| PC["Laptop Windows 11"]
        PC --> MP["Mission Planner (UDP 14550 / Radar Ctrl+F)"]
        PC --> QGC["QGroundControl (UDP 14550 / GStreamer 5600)"]
    end
```

---

## 2. Hitos y Pruebas Realizadas

### A. Conectividad Inalámbrica y Topología de Red
1. **Enlace WiFi Directo sin Cable Ethernet:**
   - Se prescindió del cable Ethernet conectado al router MikroTik, evitando la colisión de puertas de enlace (`0.0.0.0/0 via 192.168.1.1`) que bloqueaba la salida a Internet de la laptop.
   - La Raspberry Pi 3 se asoció automáticamente a la zona con cobertura móvil de Windows (**SSID:** `DroneLab`, **PSK:** `stavrospapas`) en la dirección IP **`192.168.137.153`** (MAC `B8-27-EB-6E-25-63`).
   - Latencia de enlace: $3 - 8\text{ ms}$, puerto SSH `22` abierto y enlace MAVLink activo por UDP `14550`.
2. **Auditoría de Topologías de Red (Swarm vs. AP Autónomo):**
   - **Modo Cliente (Actual):** Óptimo para enjambres multi-robot. Todos los robots y la GCS coexisten en la misma subred (`192.168.137.0/24` o red de laboratorio), permitiendo comunicación V2V (Robot-to-Robot) y descubrimiento dinámico de nodos DDS en ROS 2.
   - **Modo AP Autónomo (MikroTik / Red `Voyager_3`):** Crea una burbuja inalámbrica aislada para operar en campo sin infraestructura, pero segmenta cada robot en una red diferente impidiendo el control centralizado de enjambres sin hardware de puente.
   - **Desmitificación del mensaje `RPI is OFFLINE`:** Se comprobó que la advertencia del script `runDrone.sh` (*"RPI is OFFLINE, please check Mikrotik..."*) se debe exclusivamente al intento de ping hacia el servidor extinto del consorcio RAWFIE en Grecia (`195.134.71.99`), sin ningún impacto en la telemetría local.
3. **Dicotomía de Comunicaciones: Corto Alcance (Wi-Fi) vs. Misiones Largas (GSM / BVLOS):**
   - **Operaciones de Corto Alcance ($< 50-80\text{ m}$ / Laboratorio / Taller):** El enlace es **100% directo por Wi-Fi** ($2.4\text{ GHz}$). No requiere GSM, ni tarjeta SIM, ni conexión a Internet. Si la laptop no tiene Internet, la conexión se realiza conectándose al router MikroTik del propio robot (`Voyager_3`) o al Hotspot del móvil (incluso sin datos).
   - **Misiones Largas y BVLOS ($> 100\text{ m}$ a kilómetros):** Debido a la atenuación de Friis en $2.4\text{ GHz}$, el Wi-Fi se extingue. En este escenario **SÍ es necesario el módem GSM / 4G con tarjeta SIM**:
     - El robot transmite su telemetría a través de las antenas de telefonía móvil hacia un servidor VPN / Cloud.
     - El operador conecta su laptop a Internet (por ejemplo compartiendo datos de su móvil).
     - Ambos se comunican por IP global sin importar si la distancia es de $500\text{ m}$ o $50\text{ km}$.
   - **Alternativas sin SIM para Misiones Largas:**
     - Radios de telemetría RF punto a punto (SiK 433/915 MHz o RFD900) conectadas al puerto `TELEM 1` de la Pixhawk ($1 - 15\text{ km}$ sin Internet ni SIM).
     - Misión autónoma pregrabada en la EEPROM de la Pixhawk (el rover ejecuta los waypoints GPS y se reconecta al Wi-Fi al retornar).

### B. Validación de Telemetría en QGroundControl (v5.1.5)
- El autopiloto fue reconocido instantáneamente como vehículo terrestre:
  - `type: 10` $\to$ **Ground Rover**.
  - `autopilot: 3` $\to$ **ArduPilot / APM**.
  - `system_status: 4` $\to$ **Active**.
- Se desplegaron los modos de navegación exclusivos de ArduRover: **`Manual`**, **`Acro`**, **`Steering`**, **`Hold`**, **`Loiter`**, **`Follow`**, **`Simple`**, **`Dock`**, **`Circle`**, **`Auto`**, **`RTL`**, **`Smart RTL`** y **`Guided`**.
- El rover se mantuvo desarmado en modo **`Manual`** / **`Hold`** por seguridad para evitar el giro imprevisto de los actuadores mecánicos.

### C. Validación de Sensores en Mission Planner
1. **Subsistema Inercial (IMU Triple Redundancia):**
   - Lectura dinámica de giróscopos tri-redundantes:
     - Primaria: $g_x = 2$, $g_y = 18$, $\text{gyrosq} = 26.24$.
     - Secundaria: $g_{x2} = -17$, $g_{y2} = 58$, $\text{gyrosq2} = 60.47$.
     - Terciaria: $g_{x3} = 2$, $g_{y3} = 4$, $\text{gyrosq3} = 4.89$.
   - Filtro de actitud (EKF) operativo con ángulo de balanceo $\text{roll} = -0.59471^\circ$.
2. **Subsistema GNSS / GPS:**
   - Detección física confirmada: `gpsstatus = 1` (u-blox Neo-M8N sincronizado con la Pixhawk por UART en `SERIAL 3` a $38.400\text{ bps}$).
   - `satcount = 0` y `gpshdop = 99.99`: Comportamiento nominal en interiores debido a la atenuación de las ondas de $1575.42\text{ MHz}$ por el forjado de hormigón. Se confirmó que no requiere tarjeta SIM ni red celular para obtener *3D Fix* en exteriores.
   - Independencia del módem Huawei: Se clarificó que el dongle USB 4G solo servía para el enlace VPN en campos de prueba remotos; el GPS es un receptor orbital totalmente autónomo.
3. **Alimentación del Rail de Actuadores:**
   - La telemetría reportó **`servovoltage = 5576` ($5.57\text{ V}$)**.
   - Confirmación física: El BEC / regulador del chasis está encendido y alimenta correctamente las líneas de $5\text{ V}$ de los servos (`MAIN OUT`), garantizando potencia motriz para la dirección delantera.

---

## 3. Auditoría Eléctrica y Mecánica del LiDAR LightWare SF40/C

### Deconstrucción de Primeros Principios y Requisitos Eléctricos
Se detectó y corrigió a tiempo una confusión de seguridad sobre la tensión del sensor:

| Parámetro | Valor Datasheet Oficial | Consecuencia de Conexión Errónea |
| :--- | :--- | :--- |
| **Tensión Motor/Alimentación ($V_{in}$)** | **$6.5\text{ V}$ a $30.0\text{ V}$ DC** (Nominal **$12.0\text{ V}$**) | A $5\text{ V}$, el motor rotativo carece de par y provoca caídas de tensión bruscas. |
| **Consumo de Corriente** | Pico de $0.5\text{ A}$ a $1.0\text{ A}$ | Sobrecarga el regulador interno si se alimenta de la Pixhawk. |
| **Nivel Lógico UART** | $3.3\text{ V}$ TTL (tolerante a $5\text{ V}$) | Si se conectan $12\text{ V}$ al pin RX de la Pixhawk, se destruye el microcontrolador STM32. |

> [!CAUTION]
> **REGLA DE ORO DE INSTALACIÓN:**
> 1. La alimentación de $12\text{ V}$ debe provenir de la toma del circuito de potencia/batería (cable rojo a $+12\text{ V}$, cable negro a GND común).
> 2. Al conector `SERIAL 4/5` de la Pixhawk **SOLO se conectan las señales lógicas: TX, RX y GND**.
> 3. El pin rojo ($+5\text{ V}$) del conector `SERIAL 4/5` de la Pixhawk **DEBE QUEDAR VACÍO/DESCONECTADO**.

### Visualización del Radar 360° en Mission Planner
- Con el parámetro `SERIAL4_PROTOCOL = 11` (Proximity) y `PRX_TYPE = 1` (SF40C):
- En Mission Planner $\to$ Pantalla `Flight Data` $\to$ Pulsar **`Ctrl + F`** $\to$ Botón **`Proximity`**.
- Se despliega el radar de 360° mostrando arcos y vectores de distancia a obstáculos en metros.

---

## 4. Subsistema de Cámara y Servos Pan/Tilt

1. **Cámara Raspberry Pi v2 (Sensor Sony IMX219):**
   - Transmisión por GStreamer RTP H.264 hacia puerto UDP `5600`:
     ```bash
     raspivid -n -w 1024 -h 768 -b 1000000 -fps 30 -t 0 -o - \
       | gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=10 pt=96 \
       ! udpsink host=192.168.137.1 port=5600
     ```
   - En Mission Planner: HUD $\to$ Clic derecho $\to$ `Video` $\to$ `Set MJPEG Source` o `Set GStreamer Source` $\to$ `Start Video`.
2. **Servos del Gimbal de la Cámara:**
   - La Pixhawk cuenta con soporte de control de cámara mediante parámetros `MNT_` y comandos de MAVLink (`MAV_CMD_DO_MOUNT_CONTROL`).
   - Control directo en Mission Planner mediante `Flight Data` $\to$ pestaña **`Actions`** $\to$ **`Set Mount`** (Roll, Pitch, Yaw).

---

## 5. Protocolo de Apagado Seguro y Estado Final

1. **Apagado Lógico de Linux:**
   ```bash
   sudo poweroff
   ```
2. **Verificación de LEDs:** Se aguarda hasta la extinción del parpadeo del LED verde (tarjeta microSD en reposo sin escrituras pendientes).
3. **Corte Eléctrico:** Desconexión de la fuente de alimentación / batería de $12\text{ V}$.
4. **Cierre de Estación de Control:** Cierre de Mission Planner y desactivación de la zona móvil de Windows.

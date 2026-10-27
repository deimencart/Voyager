# Manual Técnico y de Operación: UGV Voyager 3 (Fible ALTU - RAWFIE)

---

## 1. Ficha Técnica y Resumen Ejecutivo

* **Nombre del Vehículo:** Voyager 3 (Nombre de red: `rtart.fible.voyager.ugv.3`).
* **Tipo de Plataforma:** UGV (*Unmanned Ground Vehicle*) con chasis todoterreno y dirección tipo Ackermann (ruedas directrices delanteras y tracción motriz).
* **Fabricante / Integrador:** **Fible Technologies I.K.E.** (Atrina Center, 32 Kifisias Avenue, Marousi, Atenas, Grecia — [fible.gr](https://fible.gr)).
* **Proyecto Matriz:** **RAWFIE** (*Road-, Air- and Water-based Future Internet Experimentation*, iniciativa europea Horizon 2020).
* **Equipo de Desarrollo:** Nasos (Athanasios) Grigoropoulos (Software/UoA) y Stavros Papas (Comunicaciones/Fible).
* **Computadora de Misión (Companion Computer):** Raspberry Pi 3 Model B (Raspbian GNU/Linux 9 Stretch, Kernel 4.14).
* **Controladora de Vuelo / Navegación:** Pixhawk 1 con firmware **ArduPilot APM:Rover**.
* **Sensores de Percepción:** LiDAR rotativo 360° **LightWare SF40** (antiguo LW20), GPS/Brújula externa y barómetro MS5611.
* **Comunicaciones a Bordo:** Router **MikroTik RouterBOARD** (`192.168.1.1`), módem 4G/LTE **Huawei** (`192.168.8.1`), Wi-Fi integrada y túnel OpenVPN seguro.
* **Protocolo de Control y Telemetría:** **MAVLink 1.0 / 2.0** (puerto UDP `14550` hacia Mission Planner / QGroundControl) y **Apache Kafka + Apache Avro** hacia el servidor central RAWFIE.

---

## 2. Arquitectura de Hardware y Conexiones Físicas

```
+-----------------------------------------------------------------------------------+
|                              UGV VOYAGER 3 (FIBLE ALTU)                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +--------------------+        UART (115.200 bps)        +---------------------+  |
|  | LiDAR LightWare    | -------------------------------- | Pixhawk: SERIAL 4/5 |  |
|  | SF40 (360 grados)  |                                  +---------------------+  |
|  +--------------------+                                             |             |
|                                                                     |             |
|  +--------------------+        UART (38.400 bps)                    |             |
|  | Antena GPS +       | --------------------------------------------+             |
|  | Brújula Externa    | (Pixhawk: SERIAL 3)                         |             |
|  +--------------------+                                             |             |
|                                                                     |             |
|  +--------------------+        MAIN OUT 1 (PWM)                     |             |
|  | Servo Dirección    | --------------------------------------------+             |
|  | Delantera          | (GroundSteering - Función 26)               |             |
|  +--------------------+                                             |             |
|                                                                     |             |
|  +--------------------+        MAIN OUT 3 (PWM)                     |             |
|  | Variador ESC /     | --------------------------------------------+             |
|  | Motor de Tracción  | (Throttle - Función 70)                     |             |
|  +--------------------+                                             |             |
|                                                                     |             |
|  +--------------------+        Puerto TELEM 1 (57.600 bps)          |             |
|  | Radio RF 433/915   | --------------------------------------------+             |
|  | MHz (Opcional)     | (Telemetría de largo alcance)               |             |
|  +--------------------+                                             |             |
|                                                                     |             |
|  +--------------------+        Puerto RC IN (PPM / SBUS)            |             |
|  | Receptor RC 2.4GHz | --------------------------------------------+             |
|  | (Manual Override)  | (Canal 1: Giro, Canal 3: Gas, Canal 8: Modo)|             |
|  +--------------------+                                             |             |
|                                                                     |             |
|                               UART TELEM 2 (921.600 bps)            |             |
|                 +---------------------------------------------------+             |
|                 |                                                                 |
|                 v                                                                 |
|  +-----------------------------+                                                  |
|  | Raspberry Pi 3 (GPIO 14/15) |                                                  |
|  | /dev/serial0                |                                                  |
|  +-----------------------------+                                                  |
|         |                |                      |                                 |
|     CSI |           RJ45 | Ethernet         USB |                                 |
|         v                v                      v                                 |
|  +------------+   +--------------------+  +------------------------------------+  |
|  | Cámara RPi |   | Router MikroTik    |  | Módem 4G/LTE Huawei HiLink         |  |
|  | HD H.264   |   | (192.168.1.1)      |  | (192.168.8.1 - Tarjeta SIM celular)|  |
|  +------------+   +--------------------+  +------------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Tabla de Asignación de Pines y Puertos (Pinout)

| Dispositivo | Conexión en Pixhawk | Conexión en Raspberry Pi | Parámetros / Configuración |
| :--- | :--- | :--- | :--- |
| **Servo Dirección** | `MAIN OUT 1` | — | `SERVO1_FUNCTION = 26` (GroundSteering), Trim: 1470 us, Reverse: 1 |
| **Motor / ESC** | `MAIN OUT 3` | — | `SERVO3_FUNCTION = 70` (Throttle), Min: 900 us, Max: 2000 us |
| **Enlace Raspberry Pi**| `TELEM 2` | `GPIO 14` (TXD) y `GPIO 15` (RXD) | `SERIAL2_PROTOCOL = 1` (MAVLink), `SERIAL2_BAUD = 921` (921.600 bps) |
| **LiDAR SF40** | `SERIAL 4/5` | — | `SERIAL4_PROTOCOL = 11` (Proximity), `SERIAL4_BAUD = 115` (115.200 bps) |
| **GPS / Magnetómetro** | `SERIAL 3` | — | `SERIAL3_PROTOCOL = 5` (GPS), `SERIAL3_BAUD = 38` (38.400 bps) |
| **Radio RF Telemetría**| `TELEM 1` | — | `SERIAL1_PROTOCOL = 1` (MAVLink), `SERIAL1_BAUD = 57` (57.600 bps) |
| **Receptor RC** | `RC IN` | — | Canales mapeados: `RC1` (Dirección), `RC3` (Gas), `RC8` (Modo) |
| **Cámara de Vídeo** | — | Conector cinta `CSI` | `raspivid` @ 1024x768 30fps H.264 |
| **Router de Red** | — | Puerto `eth0` (Ethernet) | IP Gateway: `192.168.1.1` (o `192.168.3.1`) |
| **Módem Celular** | — | Puerto `USB` | IP Gateway HiLink: `192.168.8.1` |

---

## 3. Arquitectura de Software y Telemetría

El software de la Raspberry Pi orquesta la telemetría, el control autónomo y la transmisión de vídeo a través de tres procesos concurrentes:

### A. Multiplexado MAVLink (`MAVProxy`)
MAVProxy toma el flujo serie del autopiloto a 921.600 baudios y lo divide en dos canales UDP:
```bash
mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=127.0.0.1:1234 --out=$GCS_IP:14550 --aircraft Voyager_3
```
1. **Canal Local (`127.0.0.1:1234`):** Permite que el demonio Python de a bordo (`adapter.py`) controle el vehículo.
2. **Canal Remoto (`UDP 14550`):** Permite que tu PC con **Mission Planner** o **QGroundControl** reciba la telemetría gráfica en tiempo real.

### B. Demonio de Telemetría e IoT (`adapter-rover`)
Ubicación: `/home/pi/adapter-rover/adapter/adapter.py`.
* Utiliza **DroneKit-Python** para suscribirse a los eventos del autopiloto (`RAW_IMU`, `SCALED_IMU2`, `SCALED_PRESSURE`, `GLOBAL_POSITION_INT`, `SYS_STATUS`).
* Serializa las lecturas con esquemas **Apache Avro** ubicados en `/home/pi/adapter-rover/Avro_Schemas/`.
* Publica las métricas en un clúster de **Apache Kafka** (`172.19.0.18:9092` / Schema Registry: `http://172.19.0.18:8081`):
  * `rtart_Attitude`: Orientación espacial (Roll, Pitch, Yaw).
  * `rtart_LinearVelocity`: Vector de velocidad lineal en 3 ejes.
  * `rtart_LinearAcceleration`: Lecturas de acelerómetros en mg.
  * `rtart_Location`: Coordenadas GPS (Latitud, Longitud, Altitud).
  * `rtart_BatteryState`: Voltaje y consumo de corriente.
  * `rtart_ObjectDistance`: Distancias de obstáculos reportadas por el LiDAR SF40.
  * `rtart_CpuUsage`: Carga de CPU y almacenamiento de la Raspberry Pi.

### C. Transmisión de Vídeo en Directo (`GStreamer`)
Captura la señal del sensor de cámara mediante `raspivid` y la empaqueta en RTP H.264 por UDP:
```bash
raspivid -n -w 1024 -h 768 -b 500000 -fps 30 -t 0 -o - \
  | gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=10 pt=96 \
  ! udpsink host=$Stream_IP port=5600
```
La estación de tierra o cualquier reproductor como **VLC** recibe el vídeo en el puerto UDP `5600`.

---

## 4. Credenciales de Acceso, Redes y Contraseñas

### Redes Wi-Fi Memorizadas (`/etc/wpa_supplicant/wpa_supplicant.conf`)
* **SSID Principal:** `DroneLab` | **Contraseña (PSK):** `stavrospapas`
* **SSID Alternativo 1:** `Stavros iPhone 7` | **Contraseña (PSK):** `stavrospapas`
* **SSID Alternativo 2:** `7bpm-WiFi` | **Contraseña (PSK):** `stavrospapas`

### Acceso a la Consola Linux (SSH)
* **Usuario:** `pi`
* **Contraseñas válidas:**
  1. `raspberry` (Contraseña original del sistema base Raspbian).
  2. `stavrospapas` (Contraseña de campo utilizada por el equipo de DroneLab).
* **Privilegios:** `pi` tiene permisos `sudo` completos sin solicitud de clave (`NOPASSWD: ALL`).
* **Comando de conexión:**
  ```powershell
  ssh pi@<IP_DEL_ROBOT>
  ```

### Red Privada Virtual (OpenVPN RAWFIE)
* **Servidor Remoto:** `195.134.71.99:1194` (UDP).
* **Certificados del Cliente:** `/home/pi/Rawfie_OpenVPN/`
  * `ca.crt` (Certificado de la Autoridad de Certificación).
  * `rtart.fible.voyager.ugv.3.crt` (Certificado del vehículo).
  * `rtart.fible.voyager.ugv.3.key` (Clave privada RSA).

---

## 5. El Sistema LiDAR y Evitación de Colisiones

El vehículo cuenta con un escáner láser rotativo **LightWare SF40** conectado a la Pixhawk en el puerto `SERIAL 4/5`:

* **Protocolo:** `SERIAL4_PROTOCOL = 11` (Proximity sensor).
* **Velocidad de datos:** `SERIAL4_BAUD = 115` (115.200 bps).
* **Evasión autónoma (`AVOID_ENABLE = 3`):**
  * La Pixhawk ejecuta internamente el algoritmo de evitación de obstáculos con proximidad.
  * **Distancia máxima de reacción (`AVOID_DIST_MAX = 5.0` m):** Si un obstáculo entra en el radio de 5 metros, el rover calcula trayectorias de desvío.
  * **Margen mínimo de seguridad (`AVOID_MARGIN = 2.0` m):** El rover mantiene al menos 2 metros de separación.
  * **Comportamiento (`AVOID_BEHAVE = 1`):** El rover frena o bordea el obstáculo automáticamente según el modo de navegación activo.

---

## 6. Señales Acústicas, Luminosas y Mensajes del Robot

El robot comunica su estado en tres capas independientes:

### A. Zumbador Piezoeléctrico (Buzzer de la Pixhawk)
* **Tono ascendente alegre (3 notas):** Inicialización y calibración de sensores completada con éxito.
* **Un pitido largo:** Robot **ARMADO** (motores activos; peligro de movimiento).
* **Dos pitidos cortos:** Robot **DESARMADO** (modo seguro; motores desconectados).
* **Pitidos graves intermitentes:** Error o bloqueo de seguridad (ej. batería baja o fallo en la brújula).

### B. LED RGB Central de la Pixhawk
* **Azul parpadeante:** Sistema listo, esperando fijación de satélites GPS.
* **Verde parpadeante:** Señal GPS bloqueada (Fix 3D); listo para ser armado.
* **Verde fijo:** **ARMADO y en funcionamiento.**
* **Ámbar / Amarillo parpadeante rápido:** Modo de emergencia (*Failsafe*).

### C. Avisos de Voz en Mission Planner
Al conectar Mission Planner por el puerto UDP 14550, el software reproduce alertas de voz por los altavoces de tu computadora:
* *"Armed"* / *"Disarmed"*.
* *"Manual mode"* / *"Hold mode"* / *"Auto mode"*.
* *"GPS 3D Fix, 12 satellites"*.
* *"Warning: Low battery"*.

---

## 7. Instrucciones Paso a Paso para Conectar y Operar el Robot

### Paso 1: Establecer la Conexión de Red
El método más sencillo sin conectar cables es aprovechar la red memorizada en la Raspberry Pi:
1. En tu teléfono móvil o en tu laptop activa la **Zona Wi-Fi portátil / Compartir Internet** (*Hotspot*).
2. Configura los datos exactos:
   * **Nombre de red (SSID):** `DroneLab`
   * **Contraseña:** `stavrospapas`
3. Enciende el robot alimentando la Raspberry Pi y la Pixhawk.
4. En 30-40 segundos, la Raspberry Pi se conectará automáticamente a tu punto de acceso.
5. Revisa la lista de dispositivos conectados en tu móvil/PC y anota la dirección IP asignada (por ejemplo `192.168.43.50`).

### Paso 2: Conectar con Mission Planner
1. Abre **Mission Planner** en tu computadora.
2. En la esquina superior derecha:
   * Selecciona **`UDP`** en el desplegable de puertos.
   * Deja el baudrate en **`115200`**.
3. Haz clic en el botón **Connect**.
4. En la ventana emergente que solicita el puerto, escribe **`14550`** y presiona *OK*.
5. Verás cómo Mission Planner descarga los parámetros y muestra el vehículo en el mapa.

### Paso 3: Visualizar la Cámara de Vídeo (Opcional)
* **En VLC Media Player:**
  1. Abre VLC.
  2. Ve a *Medio* $\to$ *Abrir emisión de red*.
  3. Introduce la URL: `udp://@:5600` y haz clic en *Reproducir*.

### Paso 4: Acceder a la Terminal de la Raspberry Pi
* Abre PowerShell o PuTTY en Windows y ejecuta:
  ```powershell
  ssh pi@192.168.43.50
  ```
  Introduce la clave `raspberry` o `stavrospapas`.

---

## 8. Guía de Solución de Problemas (Troubleshooting)

### Problema: La Raspberry Pi arranca pero no envía telemetría a Mission Planner
* **Causa:** El script `runDrone.sh` espera por defecto detectar el router MikroTik (`192.168.1.1`) y el módem 4G Huawei (`192.168.8.1`). Si estás probando la placa en una mesa sin estos equipos conectados, el script se detiene en las comprobaciones de ping.
* **Solución en banco de pruebas:**
  1. Conéctate por SSH a la Raspberry Pi.
  2. Lanza MAVProxy manualmente hacia la IP de tu computadora:
     ```bash
     mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=udp:TU_IP_PC:14550 --aircraft Voyager_3
     ```
  3. O edita `/home/pi/runDrone.sh` con `nano /home/pi/runDrone.sh` y cambia las líneas 30 y 31 a:
     ```bash
     StartMikrotik=0
     StartLTE=0
     ```

### Problema: La Pixhawk no arma los motores
* **Causa 1 (Seguridad física):** En los parámetros originales `BRD_SAFETYENABLE = 0` (el botón físico está anulado para permitir el armado por software). Si fue reactivado, mantén pulsado el interruptor de seguridad de la Pixhawk hasta que el LED rojo quede fijo.
* **Causa 2 (Pre-arm checks):** La Pixhawk bloquea el armado si no tiene señal GPS en modos asistidos (`AUTO` o `GUIDED`). Cambia el modo a `MANUAL` desde Mission Planner para probar los motores en interiores.

### Problema: Restauración de Parámetros de Fábrica de la Pixhawk
Si la Pixhawk pierde su configuración, dispones de la copia de seguridad completa extraída en:
📁 `D:\Voyager\analisis_sistema\Voyager_3_root\logs\2025-03-04\flight1\mav.parm`
* En Mission Planner: Ve a *CONFIG* $\to$ *Full Parameter Tree* $\to$ *Load from file* $\to$ selecciona `mav.parm` $\to$ *Write Params*.
Esto restaurará instantáneamente todas las ganancias PID, asignación de servos, calibración del LiDAR y velocidades originales.

---

## 9. Arquitectura de Red y Operación en Enjambre (Swarm Robotics)

### Dilema Técnico: Modo Cliente (Actual) vs. Modo Punto de Acceso (AP)
El router de a bordo (MikroTik RouterBOARD mAP, `192.168.1.1`) puede configurarse en dos modalidades de red mutuamente excluyentes, cada una con implicaciones directas en la viabilidad de enjambres multi-robot:

#### A. Modo Cliente / Station (Configuración Actual de Fábrica)
* **Topología:** Todos los robots se asocian como clientes a una red inalámbrica centralizada (ej. SSID `DroneLab` provista por un router de base en el laboratorio o un router móvil en maletín).
* **Impacto en Swarms:** **Óptimo.** Todos los vehículos y la estación de control comparten la misma subred física y lógica (`192.168.1.0/24`). Permite comunicación directa Robot-a-Robot (V2V), descubrimiento dinámico de nodos en ROS 2 mediante DDS (FastDDS/CycloneDDS multicast) y supervisión centralizada en una única pantalla de Mission Planner discriminando por `SYSID`.
* **Desventaja:** Requiere la presencia de un router central encendido.

#### B. Modo Punto de Acceso / Home AP (Configuración Autónoma Individual)
* **Topología:** Cada robot emite su propia red inalámbrica (`Voyager_3_WiFi`) y ejecuta su propio servidor DHCP (`192.168.1.10 - 192.168.1.200`).
* **Impacto en Swarms:** **Inviable como islas aisladas.** Un ordenador portátil solo puede conectarse a una red WiFi a la vez. Los robots no pueden comunicarse entre sí por el aire porque ambos operan como emisores (AP) no asociados.
* **Ventaja:** Ideal para el desarrollo, banco de pruebas y calibración de un único robot de forma 100% independiente de infraestructuras externas.

#### C. Topología Híbrida Recomendada para Enjambre en Campo (Maestro-Esclavo)
Para operar un enjambre en exteriores sin router de pared:
1. **Robot Líder (Master):** Su MikroTik se configura en **Modo AP** emitiendo la red del enjambre (`Swarm_Base`).
2. **Robots Seguidores (Slaves) y GCS:** Se configuran en **Modo Cliente (Station)** conectándose a la WiFi del Robot Líder.
3. Se obtiene un enjambre completamente coordinado y autónomo sin necesidad de infraestructura externa adicional.

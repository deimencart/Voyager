# PROTOCOLO DE CIERRE SEGURO, CONFIGURACIONES Y HOJA DE RUTA
**Vehículo:** UGV Voyager 3 (Fible ALTU)  
**Fecha de registro:** 18 de octubre de 2026 (Actualizado 19 de octubre de 2026)  
**Archivo de parámetros respaldado:** [`CONFIGURACION_PARAMETROS_PIXHAWK.parm`](file:///D:/Voyager/analisis_sistema/CONFIGURACION_PARAMETROS_PIXHAWK.parm)

---

## 1. PROCEDIMIENTO DE APAGADO SEGURO (PASO A PASO)

Dado que la Raspberry Pi no cuenta con botón físico de apagado por hardware, **nunca desconectes la alimentación en caliente** para evitar la corrupción del sistema de archivos en la microSD:

### Paso 1: Detener MAVProxy
En la ventana de terminal donde está corriendo MAVProxy:
* Pulsa **`Ctrl + C`** para cerrar MAVProxy ordenadamente.
* Volverás al prompt del sistema: `pi@Voyager_3_RPi:~ $`.

### Paso 2: Ordenar el apagado del sistema operativo
Ejecuta el siguiente comando en la terminal SSH:
```bash
sudo poweroff
```
*(Opcionalmente también sirve `sudo shutdown -h now`).*

### Paso 3: Esperar el reposo de disco (LED Verde)
1. Observa los LEDs de la placa de la Raspberry Pi:
   * El **LED verde (ACT / Actividad)** empezará a parpadear intensamente durante unos 5 a 10 segundos mientras vuelca la caché de memoria a la tarjeta SD.
   * Tras parpadear, el **LED verde se apagará por completo** (o dará 10 parpadeos regulares y quedará apagado).
   * Solo quedará encendido el **LED rojo fijo (PWR / Alimentación)**.
2. En ese momento, el sistema operativo está 100% desmontado y a salvo.

### Paso 4: Desconectar la alimentación física
1. Desconecta el cable de alimentación o la batería principal del chasis.
2. Desconecta el cable Ethernet de tu ordenador.
3. Cierra **Mission Planner** en Windows.

---

## 2. CONFIGURACIONES TÉCNICAS CONSOLIDADAS Y REGISTRADAS

Todos los parámetros operativos han quedado archivados para su restauración o replicación en cualquier momento:

### A. Parámetros del Autopiloto (Pixhawk / ArduRover 3.4.2)
* **Dirección Ackermann (`SERVO1`):**
  * Función: `26` (GroundSteering)
  * Mínimo / Máximo: `1100` $\mu$s / `1900` $\mu$s
  * Centro (Trim): `1470` $\mu$s
  * Sentido de giro: `SERVO1_REVERSED = 1`
* **Tracción (`SERVO3`):**
  * Función: `70` (Throttle)
  * Mínimo / Máximo: `900` $\mu$s / `2000` $\mu$s
  * Neutro (Trim): `1300` $\mu$s
  * Sentido de giro: `SERVO3_REVERSED = 1`
* **Sensor LiDAR 360° (LightWare SF40):**
  * Puerto serie: `SERIAL4_PROTOCOL = 11` (Prover SF40/C) @ 115.200 bps
  * Evitación de obstáculos: `AVOID_ENABLE = 3`, margen de frenado = 2.0 m, distancia máxima = 5.0 m
* **Enlace de Telemetría Principal:**
  * `SERIAL2_PROTOCOL = 1` (MAVLink 1) @ **921.600 baudios** hacia GPIO 14/15 de la Raspberry Pi.

### B. Direcciones y Puertos de Red
* **WiFi Hotspot Portátil (Provisional):** SSID `DroneLab`, Clave `stavrospapas`, IP Gateway `192.168.137.1`.
* **IP Asignada al Robot (WiFi):** `192.168.137.145`.
* **Enlace Cable Ethernet Directo:** APIPA `169.254.174.253` (Robot) $\longleftrightarrow$ `169.254.80.227` (Portátil), latencia $< 1$ ms.
* **Puerto UDP de Telemetría:** `14550` (Mission Planner).
* **Streaming de Vídeo Cámara CSI:** UDP puerto `5600` (GStreamer RTP H.264).
* **Credenciales SSH:** Usuario `pi`, Contraseña `raspberry`.

---

## 3. CHECKLIST Y HOJA DE RUTA PARA LA PRÓXIMA SESIÓN (NEXT STEPS)

### Fase 1: Convertir el Router MikroTik a Punto de Acceso (AP)
1. Conectar el portátil por cable de red al puerto libre del router MikroTik.
2. Abrir **WinBox** en Windows y conectar al MikroTik (`admin` sin clave o `stavrospapas`).
3. En **Quick Set**, seleccionar modo **`Home AP`**:
   * SSID: `Voyager_3`.
   * Seguridad: WPA2 PSK.
   * IP del router: `192.168.1.1` con **DHCP Server activo** (`192.168.1.10 - 192.168.1.200`).
4. Conectar el portátil por WiFi a la nueva red del rover.

### Fase 2: Parchear el Script de Inicio de la Raspberry Pi
En `/home/pi/runDrone.sh`:
* Cambiar `UseMaintenanceIP=1` y `Maintenance_GCS_IP="192.168.1.255"` (broadcast) o la IP del PC.
* Anular `CheckInternet` (el ping a Grecia `195.134.71.99`) para que MAVProxy arranque automáticamente siempre.

### Fase 3: Alimentación de Potencia del Chasis y Prueba de Actuadores
1. Conectar la batería LiPo principal del coche.
2. Encender el interruptor del variador ESC (verificar que en Mission Planner `Bat1` marque $> 7.4\,\text{V}$).
3. Verificar que el servo opone resistencia mecánica dura con la mano.
4. En MAVProxy, desbloquear el failsafe de radio:
   ```text
   param set ARMING_REQUIRE 0
   param set FS_THR_ENABLE 0
   mode MANUAL
   rc 1 1650
   ```
5. Probar giro izquierda (`rc 1 1350`), centro (`rc 1 1500`) y avance suave (`rc 3 1560`).

### Fase 4: Rodadura en Suelo y Teleoperación
1. Bajar el coche del soporte.
2. Enlazar un mando en Mission Planner (sección `Joystick`) o manejarlo mediante teclado inalámbricamente vía WiFi del MikroTik.

### Fase 5: Migración a ROS 2 y Mapeo SLAM
1. Conservar la microSD actual como respaldo histórico.
2. Flashear en una nueva microSD: **Ubuntu Server 22.04 LTS (64-bit `arm64`)** + **ROS 2 Humble**.
3. Instalar **MAVROS 2** para control por `/cmd_vel` y mapeo SLAM con el LiDAR LightWare SF40.

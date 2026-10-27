# PLAN DE MIGRACIÓN Y CONTROL DEL ROVER VOYAGER_3 (ROS 2 & SIMULACIÓN)

**Fecha:** Octubre 2026  
**Vehículo:** Fible ALTU / Voyager_3  
**Chasis:** Rover Ackermann (1/10 RC modificado)  
**Estado:** Backup completado (`sd.img` 31.9 GB), enlace Pixhawk validado a 921.600 bps.

---

## 1. INVENTARIO COMPLETO DEL HARDWARE IDENTIFICADO

| Subsistema | Componente Físico | Conexión / Puerto | Especificaciones Clave |
| :--- | :--- | :--- | :--- |
| **Companion Computer** | Raspberry Pi 3 Model B | Alimentación 5V BEC | CPU Cortex-A53 quad-core 1.2 GHz, 1 GB LPDDR2, WiFi 2.4 GHz, Ethernet 100M. |
| **Autopiloto** | Pixhawk 1 (PX4v3) | `TELEM 2` $\to$ RPi `/dev/serial0` | STM32F427 @ 168 MHz, 2MB Flash, NuttX OS, ArduRover V3.4.2. Enlace serie a **921.600 baudios**. |
| **Sensor LiDAR** | LightWare SF40/C 360° | Pixhawk `SERIAL 4/5` | Telémetro láser rotatorio 360°, alcance hasta 100 m, UART @ 115.200 bps. Parámetros: `AVOID_ENABLE=3`. |
| **Navegación / GNSS** | U-blox Neo-M8N + Brújula | Pixhawk `SERIAL 3` + I2C | GPS/GLONASS concurrente, brújula digital HMC5883L/LSM303D externa sobre mástil elevado. |
| **Actuador Dirección** | Servo digital RC | Pixhawk `MAIN OUT 1` | Cinemática Ackermann. `SERVO1_FUNCTION=26` (GroundSteering), Trim: 1470 $\mu$s, Min: 1100, Max: 1900. |
| **Actuador Tracción** | Variador electrónico (ESC) + Motor DC/Brushless | Pixhawk `MAIN OUT 3` | `SERVO3_FUNCTION=70` (Throttle), Min: 900, Max: 2000, Trim: 1300 $\mu$s. |
| **Cámara** | Raspberry Pi Camera v2 | Conector CSI de cinta | Sensor Sony IMX219 (8 MP), GStreamer H.264 RTP stream por UDP 5600. |
| **Comunicaciones Legacy** | Router MikroTik mAP + Módem 4G Huawei | `eth0` (192.168.1.1) + USB (192.168.8.1) | Módulos del proyecto RAWFIE (opcionales para operación en laboratorio/taller). |

---

## 2. DIAGNÓSTICO DEL SISTEMA OPERATIVO ACTUAL

* **OS:** Raspbian GNU/Linux 9.4 (Stretch).
* **Kernel:** Linux 4.14.34-v7+ (32-bit `armv7l`).
* **Python:** 2.7.13 (Python 3.5.3 legado).
* **Stack de Control Legacy:** MAVProxy multiplexando a puerto UDP 1234 (`DroneKit`) y demonio `adapter-rover` publicando telemetría Apache Avro hacia Kafka remoto en Grecia (`172.19.0.18:9092`).
* **Limitación Crítica:** Raspbian Stretch es un sistema operativo descatalogado (End-of-Life). **No admite ROS 2 nativo** (ROS 2 Humble / Iron requiere arquitectura de 64 bits `aarch64` y Ubuntu 22.04 LTS).

---

## 3. HOJA DE RUTA PARA INTEGRACIÓN DE ROS 2 (MÉTODO RECOMENDADO)

### Fase A: Independencia de Tarjeta SD
1. Mantener la tarjeta SD actual como reliquia / backup histórico (está clonada de forma idéntica en `D:\Voyager\backup_sdbackup\sd.img`).
2. Utilizar una **nueva tarjeta microSD de 32 o 64 GB** (Clase 10 / U3).

### Fase B: Instalación del Stack Moderno
1. Flashear **Ubuntu Server 22.04.4 LTS (64-bit `arm64`)** para Raspberry Pi.
2. Instalar **ROS 2 Humble Hawksbill**.
3. Instalar **MAVROS 2**:
   ```bash
   sudo apt install ros-humble-mavros ros-humble-mavros-msgs
   ```
4. Configurar el puerto UART `/dev/ttyAMA0` (GPIO 14/15) a 921.600 baudios en `/boot/firmware/config.txt`.
5. Lanzar el nodo de enlace:
   ```bash
   ros2 launch mavros apm.launch fcu_url:=serial:///dev/ttyAMA0:921600
   ```

### Fase C: Arquitectura de Tópicos y Control en ROS 2

```mermaid
flowchart LR
    A["Pixhawk (ArduRover)"] <-->|UART 921.600 bps| B["MAVROS 2 (RPi)"]
    B -->|/mavros/imu/data| C["Navegación / SLAM (Nav2)"]
    B -->|/mavros/global_position/global| C
    D["Teleoperación / Joy / Twist"] -->|/cmd_vel| B
    B -->|RC Override / MANUAL| A
    E["LiDAR LightWare SF40"] -->|LaserScan /scan| C
```

1. **Lectura de Sensores:** MAVROS publica automáticamente:
   * `/mavros/imu/data` (Giroscopios y acelerómetros @ 50 Hz).
   * `/mavros/battery` (Voltaje y consumo en tiempo real).
   * `/mavros/global_position/raw/fix` (Coordenadas satelitales GPS).
   * `/mavros/state` (Modo actual, armado/desarmado, conexión).
2. **Control de Conducción:** El robot se conduce publicando mensajes estándar `geometry_msgs/msg/Twist` en `/mavros/setpoint_velocity/cmd_vel_unstamped` (velocidad lineal $v$ y velocidad angular $\omega$).

---

## 4. INTEGRACIÓN CON GEMELO DIGITAL Y SIMULACIÓN
* El chasis Ackermann con sus límites ($1100-1900\,\mu\text{s}$) y el LiDAR 360° pueden ser modelados en simulación física para validar trayectorias, control de trayectoria y algoritmos de evitación antes de transferir las políticas de control al vehículo real (*Sim-to-Real*).

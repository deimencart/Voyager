---
name: mavlink-pixhawk-telemetry
description: Diagnostic, configuration, and stream routing protocol for Pixhawk 1, ArduRover firmware, MAVLink 1.0/2.0, MAVROS, and GCS telemetry on the UGV Voyager 3. Use when diagnosing UDP 14550 stream drops, configuring serial baudrates on /dev/serial0, analyzing ArduPilot .parm parameters, or setting up multi-client MAVLink routing.
---

# MAVLink & Pixhawk Telemetry Diagnostics Skill (UGV Voyager 3)

Este skill define los procedimientos de diagnóstico, enlace de telemetría y configuración del protocolo MAVLink entre la controladora de vuelo **Pixhawk 1**, la computadora de a bordo **Raspberry Pi 3**, y las estaciones de control en tierra (**QGroundControl** / **Mission Planner**).

---

## 🎯 ¿Cuándo Activar Este Skill?
Activa este skill cuando:
1. Se configure o diagnostique el puente MAVROS en ROS 2 (`voyager_bringup`).
2. Se pierda o degrade la tasa de refresco del flujo MAVLink por UDP `14550`.
3. Se auditen parámetros del autopiloto ArduRover (`CONFIGURACION_PARAMETROS_PIXHAWK.parm`).
4. Se requiera enrutar telemetría simultánea hacia múltiples clientes (GCS local, red celular y nodos de a bordo) usando `mavlink-router` o `mavproxy`.

---

## 📡 Arquitectura de Comunicaciones y Enrutamiento MAVLink

```mermaid
flowchart TD
    PIX["Pixhawk 1 (ArduRover v3.4.2)"] <-->|UART TELEM 2 (921.600 bps)| RPI["Raspberry Pi 3 (/dev/serial0)"]
    
    subgraph RPI_Stack ["Companion Computer (RPI 3B)"]
        ROUTER["mavlink-router / mavproxy"]
        MAVROS["Nodo ROS 2 MAVROS"]
        ROUTER <-->|UDP 127.0.0.1:14551| MAVROS
    end
    
    RPI <--> ROUTER
    
    ROUTER <-->|UDP 192.168.137.x:14550 (Wi-Fi DroneLab)| GCS1["Laptop GCS (QGroundControl / Mission Planner)"]
    ROUTER <-->|Túnel VPN / Módem 4G 192.168.8.1| GCS2["Servidor Cloud / GCS Remota BVLOS"]
```

---

## ⚙️ Parámetros Clave de ArduRover en Pixhawk (`.parm`)

| Parámetro | Valor Configurado | Significado y Función |
| :--- | :--- | :--- |
| `SERIAL2_PROTOCOL` | `1` o `2` | Protocolo MAVLink en puerto TELEM 2 hacia RPi. |
| `SERIAL2_BAUD` | `921` | Tasa de baudios de 921.600 bps para telemetría sin latencia. |
| `SERVO1_FUNCTION` | `26` | Salida `MAIN OUT 1` configurada como `GroundSteering` (dirección delantera). |
| `SERVO3_FUNCTION` | `70` | Salida `MAIN OUT 3` configurada como `Throttle` (acelerador tracción). |
| `SERVO1_TRIM` | `1470` | Trim de punto medio (posición recta de ruedas directrices). |
| `FS_ACTION` | `0` o `1` | Acción de seguridad por pérdida de señal de radio / telemetría (`Hold` o parada). |

---

## 🔍 Protocolo de Verificación Rápida de Conexión

1. **Prueba de Ping a la RPi desde la GCS (Laptop):**
   ```powershell
   ping 192.168.137.153
   ```
2. **Comprobar recepción de paquetes MAVLink en el puerto UDP 14550:**
   ```powershell
   Get-NetUDPEndpoint -LocalPort 14550
   ```
3. **Comprobar estado del puerto serie en la Raspberry Pi:**
   ```bash
   ls -la /dev/serial0
   # Debe apuntar a /dev/ttyAMA0 con permisos para el grupo dialout
   ```

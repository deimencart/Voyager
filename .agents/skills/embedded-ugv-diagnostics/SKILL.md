---
name: embedded-ugv-diagnostics
description: Diagnostics, CPU/memory profiling, thermal throttling mitigation, and network benchmarking for Raspberry Pi 3 Model B and embedded Linux stacks on the UGV Voyager 3. Use when diagnosing high system load, dropped serial bytes, Wi-Fi latency spikes, or optimizing ROS 2 background daemons.
---

# Embedded UGV Diagnostics Skill (Raspberry Pi 3 & Linux)

Este skill proporciona guías y scripts de diagnóstico para supervisar la salud térmica, uso de recursos, estabilidad de red y latencias de comunicación en la computadora de a bordo **Raspberry Pi 3 Model B** del Voyager 3.

---

## 🎯 ¿Cuándo Activar Este Skill?
Activa este skill cuando:
1. Se observen saltos temporales o pérdida de paquetes en el escaneo LiDAR o en la telemetría MAVROS.
2. La Raspberry Pi 3 experimente sobrecalentamiento ($T > 75^\circ\text{C}$) o caídas de tensión (*undervoltage*).
3. Se analice la latencia del enlace Wi-Fi con la GCS (`192.168.137.x`).
4. Se optimicen los servicios de inicio en Linux (`systemd`).

---

## 💻 Comandos de Diagnóstico en la Raspberry Pi 3 (vía SSH)

```bash
# 1. Monitoreo de Temperatura y Frecuencia de CPU
vcgencmd measure_temp
vcgencmd get_throttled
# Si 'get_throttled' devuelve distinto de 0x0, ha habido caida de voltaje o estrangulamiento termico

# 2. Uso de Memoria y Swap (critico en la RPi3 con solo 1GB de RAM)
free -m
vmstat 1 5

# 3. Rendimiento y saturacion de nucleos (4x Cortex-A53)
top -b -n 1 | head -n 20

# 4. Comprobacion de errores en la interfaz serie de telemetria
dmesg | grep -i tty
stty -F /dev/serial0 -a
```

---

## 🚦 Tabla de Códigos de `get_throttled` (Failsafes de Alimentación)

| Bit Hexadecimal | Significado | Causa y Acción Correctiva |
| :--- | :--- | :--- |
| `0x1` | Caída de tensión por debajo de 4.63V (*Under-voltage detected*). | Revisar el convertidor BEC de 5V y el cable micro-USB. |
| `0x2` | Límite de frecuencia de CPU activado por temperatura. | Mejorar disipación pasiva/ventilador en el chasis. |
| `0x4` | Estrangulamiento térmico activo (*Throttling active*). | La CPU baja a 600 MHz; peligro de pérdida de ciclo en ROS 2. |
| `0x50000` | Ha ocurrido una caída de tensión previa durante la sesión. | La fuente es inestable bajo picos de corriente del módem 4G. |

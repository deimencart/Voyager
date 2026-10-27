# Reglas de Seguridad Eléctrica y Hardware Embebido (UGV Voyager 3)

Reglas de estricto cumplimiento para proteger la electrónica de potencia, computación y sensores del Voyager 3:

---

## 1. Distribución de Alimentación y Tensiones

```
[BATERÍA LiPo / FUENTE DE LAB (11.1V - 12.6V)]
       |
       +---> [LÍNEA NOMINAL 12V PDB] --------------> LiDAR LightWare SF40/C (12V DC)
       |
       +---> [BEC STEP-DOWN 5.57V] ----------------> Rail MAIN OUT Pixhawk 1 (Servo Dirección)
       |
       +---> [BEC STEP-DOWN 5.0V / 3A] -----------> Raspberry Pi 3 Model B (Micro-USB / 5V GPIO)
```

1. **Sensor LiDAR LightWare SF40/C:**
   - **Tensión de Trabajo Nominal:** **12V DC**.
   - **PROHIBIDO:** Conectar la alimentación del motor rotativo del SF40/C a la salida de 5V de la Raspberry Pi o de la Pixhawk. Una tensión de 5V provoca caída de revoluciones, cuelgues del procesador óptico y daños por sobreconsumo en reguladores lógicos.
2. **Servo de Dirección (MAIN OUT 1):**
   - El rail de salida de la Pixhawk no entrega corriente a los servos por sí mismo; se alimenta mediante el BEC dedicado de 5.57V conectado al rail de pines `MAIN OUT`.
3. **Raspberry Pi 3 Model B:**
   - Alimentada a 5.0V con fuente o convertidor capaz de suministrar al menos 2.5A sostenidos para evitar el icono del rayo amarillo (*undervoltage alert*).

---

## 2. Comunicaciones y Failsafe de Hardware

1. **Enlace Serie RPi <-> Pixhawk (`/dev/serial0`):**
   - Baudrate configurado en la Pixhawk (`SERIAL2_BAUD = 921`) a 921.600 bps.
   - En la Raspberry Pi, el puerto UART debe estar desvinculado de la consola serie Linux (`console=serial0,115200` deshabilitado en `/boot/cmdline.txt`) para uso exclusivo del puente MAVLink/MAVROS.
2. **Watchdog de Enlace y Parada de Emergencia:**
   - Si se pierde la comunicación MAVLink durante más de $1.0\text{ s}$, el autopiloto ArduRover conmuta automáticamente a modo `HOLD` o `MANUAL` de seguridad según la configuración de failsafe (`FS_ACTION`).
3. **Control Manual de Emergencia (RC Override):**
   - El receptor de radio control tradicional de 2.4 GHz en el puerto `RC IN` de la Pixhawk siempre tiene prioridad de intervención manual sobre el software de la Raspberry Pi.

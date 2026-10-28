# Autopilot: The Cube / Pixhawk 2.1 (Cube Black) & Standard Carrier Board

This document provides technical specifications, pinout mappings, mechanical vibration isolation details, carrier board interfaces, and reference documentation for the **Cube Black** autopilot powering the **UGV Voyager 3**.

---

## 1. System Identification & Core Architecture

* **Model:** The Cube Black (Pixhawk 2.1) by CubePilot / ProfiCNC.
* **Firmware:** ArduPilot (APM:Rover v3.4.2).
* **Firmware Board Type:** `BRD_TYPE = 3` (Identifies Cube Black / Pixhawk 2.1 hardware).
* **Interconnect:** 80-pin Hirose DF17 high-density connector interfacing the Cube to the Standard Carrier Board.

### Processing Units
* **Main Flight Management Unit (FMU):**
  * **Processor:** STMicroelectronics STM32F427VIT6.
  * **Core:** 32-bit ARM Cortex-M4 with hardware Floating Point Unit (FPU).
  * **Clock Speed:** 168 MHz.
  * **Memory:** 256 KB RAM, 2 MB Flash.
* **I/O Fail-Safe Co-processor:**
  * **Processor:** STMicroelectronics STM32F100C8T6.
  * **Core:** 32-bit ARM Cortex-M0/M3 @ 24 MHz.
  * **Function:** Dedicated fail-safe hardware supervisor, handles `MAIN OUT 1-8` PWM generation, safety switch logic, and direct RC receiver overrides.

---

## 2. Sensor Subsystem & Thermal Stabilization

The Cube Black integrates triple redundant Inertial Measurement Units (IMUs) and dual barometers:

| Sensor | Chipset | Bus | Placement | Function |
| :--- | :--- | :---: | :--- | :--- |
| **IMU 1** | InvenSense MPU9250 | SPI | Isolated Suspended Board | 3-axis Accel, 3-axis Gyro, 3-axis Mag |
| **IMU 2** | InvenSense ICM20608 / ICM20948 | SPI | Isolated Suspended Board | 3-axis Accel, 3-axis Gyro |
| **IMU 3** | STMicroelectronics L3GD20 + LSM303D | SPI | Fixed Mainboard | 3-axis Accel, 3-axis Gyro, 3-axis Mag |
| **Barometer 1** | MEAS MS5611-01BA03 | SPI | Internal | High-precision atmospheric pressure |
| **Barometer 2** | MEAS MS5611-01BA03 | SPI | Internal | Redundant barometric pressure |

### Vibration Isolation & Active Heating Chamber
* **Mechanical Isolation:** IMU 1 and IMU 2 are suspended on a dedicated internal damping platform supported by precision silicone/foam dampers, isolating the sensors from high-frequency acoustic and structural chassis vibrations.
* **Thermal Heating Loop:** The internal sensor chamber features built-in resistive heating elements monitored by a closed-loop PID controller.
  * **Target Temperature:** **45.0 °C** (`BRD_IMU_TARGTEMP = 45.000000`).
  * **Operational Value:** Eliminates thermal zero-bias drift during outdoor cold-starts or changing ambient field conditions.

---

## 3. Standard Carrier Board Connector Pinouts

The Standard Carrier Board breaks out the 80-pin Hirose DF17 bus into keyed JST-GH (1.25 mm pitch) and 0.1" (2.54 mm) header connectors.

### 3.1. TELEM 1 & TELEM 2 Ports (JST-GH 6-Pin)
* Used for telemetry radios and companion computer UART bridge.

```text
Pin 1 (Red)    : +5.0V DC (Shared VCC, max 1.5A)
Pin 2 (Yellow) : TX (3.3V TTL Output)
Pin 3 (Green)  : RX (3.3V TTL Input)
Pin 4 (Gray)   : CTS (Clear To Send)
Pin 5 (Gray)   : RTS (Request To Send)
Pin 6 (Black)  : GND (0.0V Reference)
```

#### Voyager 3 TELEM 2 Connection (Companion Bridge):
| Pin | Signal | Target Pin on Raspberry Pi 3B | Note |
| :---: | :--- | :--- | :--- |
| **1** | VCC (+5V) | **NOT CONNECTED** | Left disconnected to prevent voltage backfeeding |
| **2** | TX (OUT) | Pin 10 (GPIO 15 / RXD) | 3.3V TTL serial data to companion gateway |
| **3** | RX (IN) | Pin 8 (GPIO 14 / TXD) | 3.3V TTL serial data from companion gateway |
| **4** | CTS | Unused | Hardware flow control disabled |
| **5** | RTS | Unused | Hardware flow control disabled |
| **6** | GND | Pin 6 (GND) | Common signal ground |

*Parameters:* `SERIAL2_BAUD = 921` (921,600 bps), `SERIAL2_PROTOCOL = 1` (MAVLink 1.0/2.0).

---

### 3.2. GPS 1 Port (JST-GH 8-Pin)
* Interfaces the primary GNSS receiver and the external mast-mounted magnetometer.

| Pin | Signal | Voltage / Logic | Description |
| :---: | :--- | :---: | :--- |
| **1** | VCC | +5.0 V DC | Power to external GPS module |
| **2** | TX (OUT) | 3.3V TTL | Serial output from autopilot to GPS |
| **3** | RX (IN) | 3.3V TTL | Serial input from GPS to autopilot (`SERIAL3`) |
| **4** | SCL (I2C1) | 3.3V (Pull-up) | I2C Clock for external compass |
| **5** | SDA (I2C1) | 3.3V (Pull-up) | I2C Data for external compass |
| **6** | BUTTON | Active Low | Physical safety switch line |
| **7** | SAFETY_LED | Output | Safety switch status LED |
| **8** | GND | 0.0 V | Common ground |

*Parameters:* `SERIAL3_BAUD = 38` (38,400 bps), `SERIAL3_PROTOCOL = 5` (GPS NMEA/UBX).

---

### 3.3. GPS 2 / SERIAL 4 Port (JST-GH 6-Pin)
* Interfaces secondary GNSS or serial rangefinder sensors. On Voyager 3, it interfaces the **LightWare SF40/C 360° LiDAR**.

| Pin | Signal | Logic Level | Connection to LightWare SF40/C |
| :---: | :--- | :---: | :--- |
| **1** | VCC (+5V) | +5.0 V DC | **DISCONNECTED** (LiDAR motor requires 12V from PDB) |
| **2** | TX (OUT) | 3.3V TTL | Connected to SF40/C RX line |
| **3** | RX (IN) | 3.3V TTL | Connected to SF40/C TX line |
| **4** | SCL (I2C2) | 3.3V | Unused |
| **5** | SDA (I2C2) | 3.3V | Unused |
| **6** | GND | 0.0 V | Common ground with SF40/C and PDB |

*Parameters:* `SERIAL4_BAUD = 115` (115,200 bps), `SERIAL4_PROTOCOL = 11` (Proximity Sensor).

---

### 3.4. MAIN OUT (1–8) & AUX OUT (1–6) Header Rails (0.1" / 2.54mm)
* Standard 3-pin headers arranged in three rows:
  * **Top Row:** Signal (PWM, 3.3V logic level).
  * **Middle Row:** `VDD_SERVO` positive rail.
  * **Bottom Row:** GND (Common ground).

> [!IMPORTANT]
> **Servo Rail Isolation:**  
> The middle positive rail (`VDD_SERVO`) is **isolated** from the autopilot's internal 5.3V power regulator. The Cube cannot power servos from its power ports.  
> On the Voyager 3, the servo rail is powered at **5.57V DC** by an auxiliary BEC connected to `MAIN OUT 7/8`.

* **Channel Mapping:**
  * **MAIN OUT 1:** Front Ackermann Steering Servo (`SERVO1_FUNCTION = 26`, Min: 1100 µs, Max: 1900 µs, Trim: 1470 µs).
  * **MAIN OUT 3:** Rear Traction Motor ESC (`SERVO3_FUNCTION = 70`, Min: 900 µs, Max: 2000 µs, Trim: 1300 µs).
  * **MAIN OUT 2, 4–8:** Auxiliary PWM channels.
  * **AUX OUT 1–6:** Dedicated FMU auxiliary lines (camera pan/tilt, relay outputs).

---

### 3.5. POWER 1 & POWER 2 Ports (Molex Clik-Mate 2.0mm 6-Pin)
* Receives regulated power and analog current/voltage sensor readings from the power module:

| Pin | Signal | Voltage Level | Function |
| :---: | :--- | :---: | :--- |
| **1** | VDD_5V_BRICK | +5.3 V DC | Primary power input from 3DR Power Module |
| **2** | VDD_5V_BRICK | +5.3 V DC | Redundant parallel power contact |
| **3** | CURRENT_SENS | 0.0 – 3.3 V Analog | Battery current shunt signal (`BATT_CURR_PIN = 3`, 17.0 A/V) |
| **4** | VOLTAGE_SENS | 0.0 – 3.3 V Analog | Battery voltage divider signal (`BATT_VOLT_PIN = 2`, mult: 12.10696) |
| **5** | GND | 0.0 V | Power ground reference |
| **6** | GND | 0.0 V | Redundant ground contact |

---

## 4. References & Documentation

* [CubePilot Interface Specifications & Mechanical Dimensions](https://docs.cubepilot.org/autopilot/the-cube/introduction/interface-specifications)
* [ArduPilot Cube Black Official Hardware Overview](https://ardupilot.org/copter/docs/common-thecube-overview.html)
* [ProfiCNC The Cube GitHub Hardware Repository & Schematics](https://github.com/proficnc/The-Cube)
* [ArduPilot Official Hardware Schematics (ProfiCNC / The Cube)](https://github.com/ArduPilot/Schematics/tree/master/ProfiCNC)
* [Cube Black Carrier Board Mechanical & Pinout Drawings](https://docs.cubepilot.org/autopilot/the-cube/the-cube-user-guide)

# Hardware Overview & Component Wiki

This document provides the high-level Bill of Materials (BOM), the four-domain decoupled power tree, and the navigation index for the complete hardware documentation of the **UGV Voyager 3**.

---

## 1. Bill of Materials (BOM) & Component Index

Click on any subsystem link in the table below to access its detailed pinout, wiring schematics, datasheets, and official documentation:

| Subsystem | Component | Specifications & Details | Interface | Operating Voltage | Dedicated Wiki Page |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Autopilot Unit** | **The Cube Black** (Pixhawk 2.1) | STM32F427 + STM32F100, Heated Triple IMU (45°C) | Direct Sensor / Actuator Lines | $5.3\text{ V}$ DC (from Power Module) | [01 — The Cube Black Autopilot](01_the_cube_black_autopilot.md) |
| **Primary Perception** | **LightWare SF40/C** | 360° Scanning Laser Rangefinder (0.2 m – 100 m) | UART to Pixhawk `SERIAL 4/5` | **$12.0\text{ V}$ DC nominal** *(Strict)* | [02 — LightWare SF40/C LiDAR](02_lightware_sf40c_lidar.md) |
| **Companion Gateway** | **Raspberry Pi 3 Model B** | Quad-Core Cortex-A53 1.2 GHz, 1 GB RAM | UART (`/dev/serial0`) & Ethernet | $5.0\text{ V}$ DC (Turnigy SBEC 5A) | [03 — Raspberry Pi 3B Gateway](03_raspberry_pi_3b.md) |
| **Vision Camera** | **RPi Camera Module v2** | Sony IMX219 (8.08 MP, 1080p, f/2.0 lens) | 15-pin MIPI CSI-2 Ribbon | $3.3\text{ V}$ DC (from RPi bus) | [04 — RPi Camera Module v2](04_rpi_camera_v2.md) |
| **Global Navigation** | **U-blox Neo-M8N** | Concurrent GNSS + External Magnetometer on Mast | UART (`SERIAL 3`) + I2C1 Bus | $5.0\text{ V}$ DC (from Pixhawk) | [05 — U-blox Neo-M8N GNSS](05_ublox_m8n_gps_compass.md) |
| **Wireless Router** | **MikroTik mAP 2nD** | Dual Fast Ethernet + 2.4 GHz Wi-Fi + USB Host | RJ45 Ethernet & micro-USB | $12.0\text{ V}$ DC (from PDB) | [06 — MikroTik mAP 2nD Router](06_mikrotik_map_2nd_router.md) |
| **Cellular Modem** | **Huawei E3372h** | 4G LTE Cat4 USB Dongle (HiLink Mode, 150 Mbps) | USB on MikroTik Router | $5.0\text{ V}$ DC (via USB) | [07 — Huawei 4G LTE Modem](07_huawei_e3372h_lte_modem.md) |
| **Chassis & Steering** | **Fible ALTU Ackermann** | Front Steering Servo + Rear Brushless ESC Motor | PWM 50 Hz on `MAIN OUT 1 & 3` | Servo: $5.57\text{ V}$ / Motor: $14.8\text{ V}$ | [08 — Ackermann & Actuators](08_ackermann_actuators_chassis.md) |
| **Power Distribution** | **4-Domain Decoupled Tree** | 4S LiPo + 3DR Module + Turnigy SBEC + Servo BEC | XT60 Heavy Bus & Regulators | $14.8\text{ V} - 16.8\text{ V}$ DC Pack | [09 — Power Distribution Tree](09_power_distribution_tree.md) |
| **Autopilot Config** | **ArduRover Parameters** | Complete verified parameter reference dump | EEPROM / Flash Memory | N/A | [10 — ArduRover Parameters](10_ardurover_parameters_master.md) |

---

## 2. Power Tree & Voltage Domains

The platform uses **four decoupled voltage domains** to avoid ground loops and protect delicate digital electronics from motor electrical noise:

```text
4S LiPo Battery (14.8V – 16.8V DC) via XT60
  │
  ├──► [Domain 1: Direct PDB Rail] ────────► Traction Motor ESC (Direct Battery Power)
  │                                ────────► LightWare SF40/C LiDAR Motor (12.0V DC)
  │                                ────────► MikroTik mAP 2nD Router (12.0V DC Jack)
  │
  ├──► [Domain 2: 3DR Power Module] ──────► The Cube POWER 1 (5.3V DC / 2.25A Regulated)
  │                                           ├──► STM32F427 FMU & Co-processor
  │                                           ├──► Triple IMUs Heated at 45.0 °C
  │                                           └──► U-blox Neo-M8N GNSS (via GPS 1 port)
  │
  ├──► [Domain 3: Turnigy SBEC] ──────────► Raspberry Pi 3B Power IN (5.0V DC / 5A Dedicated)
  │                                           └──► Sony IMX219 Camera Module (via CSI)
  │
  └──► [Domain 4: Auxiliary Servo BEC] ───► Pixhawk Servo Rail MAIN OUT 1–8 (5.57V DC)
                                              └──► Front Ackermann Steering Servo
```

---

## 3. Critical Electrical Safety Rules

> [!CAUTION]
> **RULE 1: LiDAR SF40/C 12V Power Line**  
> The LightWare SF40/C sensor **must be powered directly by 12V DC** from the battery distribution line. Never power it from the 5V pins of the Pixhawk or Raspberry Pi (5V lacks the current to start the internal spinning motor). Only logic lines (`TX`, `RX`, and `GND`) are connected to the Pixhawk's `SERIAL 4/5` port.

> [!CAUTION]
> **RULE 2: TELEM 2 Isolation (No +5V Shared Line)**  
> The Raspberry Pi 3B receives its own dedicated power from the Turnigy SBEC ($5.0\text{ V}$ / $5\text{ A}$). The serial connection between the RPi (`GPIO 14/15`) and Pixhawk (`TELEM 2`) **must not connect the +5V pin**. Only `TX`, `RX`, and common `GND` are wired to prevent voltage backfeeding.

> [!IMPORTANT]
> **RULE 3: Servo Rail Power Requirement**  
> Pixhawk's servo output rail (`MAIN OUT 1-8`) does not receive power from the Pixhawk power port. It is powered independently at **5.57V DC** by the auxiliary BEC to provide mechanical torque to the steering servo without causing voltage drops to the flight controller.

> [!WARNING]
> **RULE 4: Bench Power Supply vs. 4S LiPo Battery**  
> Do not use standard PC (ATX) power supplies for testing. When the motor accelerates or the steering servo turns, sharp current spikes trip the power supply's over-current protection (OCP), causing an immediate shutdown.  
> The rover is powered by a **4S LiPo battery** ($14.8\text{ V}$ – $16.8\text{ V}$), which delivers high peak discharge currents without voltage collapse.

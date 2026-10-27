# Hardware Overview & Power Distribution

This document details the physical components (Bill of Materials) and the power distribution architecture of the **UGV Voyager 3**.

---

## 1. Bill of Materials (BOM)

| Subsystem | Component | Model / Specs | Interface | Operating Voltage |
| :--- | :--- | :--- | :--- | :---: |
| **Autopilot Unit** | Pixhawk 1 (PX4v3) | STM32F427 + STM32F100 Co-processor | Direct Sensor / Actuator Lines | $5.3\text{ V}$ DC (from Power Module) |
| **Companion Gateway** | Raspberry Pi 3 Model B | Quad-Core Cortex-A53 1.2 GHz, 1GB RAM | UART (`/dev/serial0`) & Ethernet | $5.0\text{ V}$ DC (Turnigy SBEC 5A) |
| **Wireless Router** | MikroTik RouterBOARD | Model mAP 2nD (Dual Ethernet + Wi-Fi) | RJ45 Ethernet & USB Port | $12.0\text{ V}$ DC (from PDB) |
| **Cellular Modem** | Huawei HiLink 4G/LTE | USB Dongle with Cellular SIM Slot | USB on MikroTik Router | $5.0\text{ V}$ DC (via USB) |
| **Primary Perception** | 360° Laser Rangefinder | LightWare SF40/C (Range: 0.2m – 100m) | UART to Pixhawk `SERIAL 4/5` | **$12.0\text{ V}$ DC nominal** *(Strict)* |
| **Global Navigation** | GNSS + Digital Compass | U-blox Neo-M8N + External Magnetometer | UART (`SERIAL 3`) + I2C Bus | $5.0\text{ V}$ DC (from Pixhawk) |
| **Front Steering** | High-Torque Servo Motor | Standard RC Servo (Ackermann Linkage) | PWM 50 Hz on `MAIN OUT 1` | $5.57\text{ V}$ DC (from Servo BEC) |
| **Rear Traction** | Electronic Speed Controller | Brushless/Brushed RC Car ESC + Motor | PWM Throttle on `MAIN OUT 3` | $11.1 - 12.6\text{ V}$ DC (Direct LiPo) |
| **Manual Override** | 2.4 GHz RC Receiver | PPM / S.BUS Safety Receiver | `RC IN` on Pixhawk | $5.0\text{ V}$ DC (from Pixhawk) |
| **Vision Camera** | HD Camera Module | Raspberry Pi Camera v2 (Sony IMX219) | 15-pin MIPI CSI-2 Ribbon | $3.3\text{ V}$ DC (from RPi bus) |
| **Main Battery** | 3S LiPo Battery Pack | 11.1V – 12.6V DC, ~3300 mAh, XT60 | Power Distribution Board (PDB) | Nominal $11.1\text{ V} - 12.6\text{ V}$ |

---

## 2. Power Tree & Voltage Domains

The platform uses **four decoupled voltage domains** to avoid ground loops and protect delicate digital electronics from motor electrical noise:

```text
3S LiPo Battery (11.1V - 12.6V DC) via XT60
  │
  ├──► [Direct 12V PDB Rail] ──────► LightWare SF40/C LiDAR (Motor & Laser)
  │                          ──────► Electronic Speed Controller (ESC Traction Power)
  │                          ──────► MikroTik mAP Router
  │
  ├──► [3DR Power Module] ────────► Pixhawk 1 VCC (5.3V DC regulated + Current/Voltage Shunt)
  │
  ├──► [Turnigy SBEC (Step-Down)] ─► Raspberry Pi 3B Power IN (5.0V DC / 5A dedicated)
  │
  └──► [Auxiliary BEC 2] ─────────► Pixhawk Servo Rail MAIN OUT 1-8 (5.57V DC)
                                     └──► Front Steering Servo Power
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

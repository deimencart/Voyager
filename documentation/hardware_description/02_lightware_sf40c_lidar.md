# LiDAR: LightWare SF40/C 360-Degree Laser Rangefinder

This document details the optical, electrical, and communication specifications, wiring rules, and ArduPilot integration parameters for the **LightWare SF40/C** scanning LiDAR on the **UGV Voyager 3**.

---

## 1. Operating Principle & Optical Specifications

The LightWare SF40/C is a rotating 360° laser rangefinder designed for autonomous obstacle detection and proximity navigation. It utilizes an internal optical slip-ring and a continuous brushless motor to rotate the laser optical assembly.

| Parameter | Specification | Details |
| :--- | :--- | :--- |
| **Manufacturer** | LightWare Optoelectronics (Pty) Ltd | Model: SF40/C |
| **Measurement Principle** | Pulsed Time-of-Flight (ToF) | Direct photon time flight measurement |
| **Laser Diode** | 905 nm Infrared Semiconductor | Class 1M eye-safe (IEC 60825-1:2014) |
| **Operating Range** | **0.2 m to 100 m** | On standard natural reflective surfaces |
| **Update Rate** | Up to **20,010 readings/sec** | 20 kHz sampling frequency |
| **Rotational Scan Rate** | **0.5 Hz to 5.5 Hz** | 30 to 330 RPM (user configurable) |
| **Resolution** | 1 cm (0.01 m) | Raw measurement granularity |
| **Distance Accuracy** | $\pm 0.03\text{ m}$ (3 cm) | Independent of range under nominal reflection |
| **Angular Resolution** | ~0.2° to 1.0° | Dependent on rotation speed and point density |
| **Dimensions** | 70 mm (Height) × 79 mm (Diameter) | Anodized aluminum base with polycarbonate dome |
| **Weight** | 256 grams | Compact cylindrical chassis |

---

## 2. Electrical Specifications & Wiring Rules

> [!CAUTION]
> **CRITICAL ELECTRICAL SAFETY RULE: 12V DC POWER INPUT**  
> The LightWare SF40/C internal motor and optical transmitter **require a supply voltage between 6.5 V and 30.0 V DC (Nominal 12.0 V DC)**.  
> * **Never** connect the LiDAR power leads to the 5V rail of the Pixhawk or Raspberry Pi. 5V lacks the electrical power to spin up the motor, causing sensor stall and brownout resets.  
> * The SF40/C must receive **12.0V DC directly from the Power Distribution Board (PDB)**.

### Power & Consumption
* **Input Voltage Range:** 6.5 V to 30.0 V DC.
* **Nominal Supply:** **12.0 V DC** from the main PDB bus.
* **Power Draw:** 3.5 W typical; up to 7.0 W during rotational motor acceleration.

### Physical Wiring Table

The SF40/C connects to the autopilot via the **SERIAL 4 / GPS 2** port on the Cube carrier board:

| SF40/C Lead | Signal / Function | Target Connection | Operating Level |
| :--- | :--- | :--- | :--- |
| **V+ (Power)** | Motor & Logic Supply | **PDB +12V DC Rail** | **+12.0 V DC** |
| **GND (Power)** | Power Return | **PDB Ground** | 0.0 V (Ground) |
| **TX (Data)** | LiDAR Serial Out | Pixhawk `SERIAL 4` Pin 3 (RXD) | 3.3V TTL |
| **RX (Data)** | LiDAR Serial In | Pixhawk `SERIAL 4` Pin 2 (TXD) | 3.3V TTL |
| **Signal GND** | Logic Ground | Pixhawk `SERIAL 4` Pin 6 (GND) | 0.0 V (Common GND) |
| *None* | *Empty* | Pixhawk `SERIAL 4` Pin 1 (+5V) | **LEAVE EMPTY / UNWIRED** |

---

## 3. ArduPilot Configuration Parameters

The autopilot receives continuous distance and bearing packets from the SF40/C over UART and populates the 360-degree obstacle proximity buffer:

| Parameter | Configured Value | Description |
| :--- | :---: | :--- |
| `SERIAL4_PROTOCOL` | `11` | Protocol type: Proximity Sensor / Rangefinder 360 |
| `SERIAL4_BAUD` | `115` | Baudrate: 115,200 bps |
| `PRX_TYPE` | `1` | Sensor driver: LightWare SF40/C legacy protocol |
| `AVOID_ENABLE` | `3` | Obstacle avoidance enabled in autonomous and manual modes |
| `AVOID_DIST_MAX` | `5.0` | Maximum distance (meters) to track obstacles for avoidance |
| `AVOID_MARGIN` | `2.0` | Minimum clearance margin (meters) maintained from obstacles |
| `AVOID_BEHAVE` | `1` | Vehicle behavior: Slide around obstacle or stop |

### Verifying Radar Proximity in Mission Planner
1. Connect Mission Planner to the vehicle via UDP port `14550`.
2. Press **`Ctrl + F`** on the keyboard to bring up the Advanced Function Window.
3. Click on the **`Proximity`** button.
4. A polar radar window appears displaying live 360-degree obstacle detection ranges in real time.

---

## 4. References & Documentation

* [LightWare SF40/C Product Manual Rev 7 (Official PDF)](https://www.documents.lightware.co.za/SF40%20-%20Laser%20Scanner%20Manual%20-%20Rev%207.pdf)
* [LightWare SF40/C Mouser Technical Datasheet](https://www.mouser.com/datasheet/2/811/SF40___Laser_Scanner_Manual___Rev_7-1510427.pdf)
* [ArduPilot LightWare SF40/C Proximity & Avoidance Guide](https://ardupilot.org/rover/docs/common-lightware-sf40c-objectavoidance.html)
* [LightWare Studio Configuration Tool & Firmware Updates](https://lightwarelidar.com/)

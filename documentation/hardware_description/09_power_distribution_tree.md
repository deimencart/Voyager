# Power Distribution Architecture & Electrical Safety

This document details the four-domain decoupled power distribution system, voltage regulators, battery specifications, bench testing guidelines, and electrical safety rules for the **UGV Voyager 3**.

---

## 1. Four-Domain Decoupled Power Tree

Robotic ground vehicles experience intense electrical disturbances from motor inductive switching and steering servo mechanical stall currents. To prevent brownouts, sensor drift, and flight controller resets, the Voyager 3 divides its electrical system into **four electrically isolated voltage domains**:

```text
4S LiPo Battery (14.8V – 16.8V DC) via XT60
  │
  ├──► [Domain 1: High-Current PDB Rail] ──────► Traction Motor ESC (Direct Battery Power)
  │                                      ──────► LightWare SF40/C LiDAR Motor (12.0V DC)
  │                                      ──────► MikroTik mAP 2nD Router (12.0V DC Jack)
  │
  ├──► [Domain 2: 3DR Power Module] ──────────► Pixhawk POWER 1 (5.3V DC / 2.25A Regulated)
  │                                               ├──► STM32F427 FMU & Co-processor
  │                                               ├──► Triple IMUs & Heating Element (45°C)
  │                                               ├──► Barometers MS5611
  │                                               └──► U-blox Neo-M8N GNSS (via GPS 1 port)
  │
  ├──► [Domain 3: Turnigy MultiStar SBEC] ─────► Raspberry Pi 3B (5.0V DC / 5A Dedicated)
  │                                               ├──► Sony IMX219 Camera Module (via CSI)
  │                                               └──► USB Bus & Diagnostics
  │
  └──► [Domain 4: Auxiliary Servo BEC] ────────► Pixhawk MAIN OUT 1–8 Servo Rail (5.57V DC)
                                                  └──► Front Ackermann Steering Servo
```

---

## 2. Voltage Domains Specification

### Domain 1: Unregulated & High-Current Distribution (PDB)
* **Voltage Source:** Direct 4S LiPo battery terminal ($14.8\text{ V} - 16.8\text{ V}$ DC).
* **Power Distribution Board (PDB):** Heavy copper bus with XT60 main connector.
* **Connected Devices:**
  * **Traction ESC:** Directly powered from battery bus for maximum torque delivery.
  * **LightWare SF40/C LiDAR:** Dedicated 12.0V DC line powering the continuous optical motor and pulsed laser transmitter.
  * **MikroTik mAP 2nD Router:** Powered via standard 2.1mm DC barrel jack (accepts 8V – 57V DC).

---

### Domain 2: Autopilot & Core Sensors (3DR Power Module)
* **Voltage Source:** 3DR Power Module buck regulator.
* **Output Voltage:** **5.30 V DC** (up to 2.25 A) delivered to the Cube carrier board **`POWER 1`** port.
* **Integrated Telemetry Sensors:**
  * **Current Shunt Sensor:** Monitors battery current draw via ADC Pin 3 (`BATT_AMP_PERVLT = 17.000000`).
  * **Voltage Divider Sensor:** Monitors total battery voltage via ADC Pin 2 (`BATT_VOLT_MULT = 12.106960`).
* **Protected Loads:**
  * STM32F427 FMU and STM32F100 failsafe co-processor.
  * Triple internal IMUs and precision 45.0 °C resistive heating element.
  * Redundant MS5611 barometers.
  * U-blox Neo-M8N GNSS receiver and compass puck (powered via `GPS 1` port).

---

### Domain 3: Companion Computer (Turnigy MultiStar SBEC)
* **Regulator Type:** High-efficiency switching buck regulator (SBEC).
* **Input Voltage:** Main battery bus ($14.8\text{ V} - 16.8\text{ V}$).
* **Output Voltage & Current:** **5.0 V DC @ 5.0 A continuous** (7.5 A peak).
* **Connected Devices:**
  * Raspberry Pi 3 Model B (via 40-pin GPIO Pins 2, 4, 6, 9).
  * Sony IMX219 Camera Module (via 15-pin MIPI CSI-2 bus).

> [!CAUTION]
> **ISOLATION RULE: TELEM 2 PIN 1 (+5V) MUST REMAIN UNCONNECTED**  
> The Raspberry Pi receives power exclusively from the Turnigy SBEC.  
> The serial cable between the RPi and the Cube `TELEM 2` port connects **only TX, RX, and common GND**.  
> The +5V pin (Pin 1) must remain strictly disconnected to prevent current backfeeding between independent switching regulators.

---

### Domain 4: Servo Actuator Rail (Auxiliary Servo BEC)
* **Regulator Type:** Auxiliary Switching BEC.
* **Output Voltage:** **5.57 V DC** (`servovoltage = 5576 mV` in Mission Planner telemetry).
* **Connection:** Injected into `MAIN OUT 7` or `MAIN OUT 8` on the servo header rail.
* **Connected Devices:**
  * Front steering high-torque RC servo motor.
* **Electrical Safety:**
  * The Cube's internal power module is decoupled from the `MAIN OUT 1-8` positive rail by internal diode isolation circuitry.
  * Servos draw high inductive stall currents (up to 2A–3A when wheels encounter obstacles). Powering the servo rail from a dedicated external BEC ensures that servo stalls never drop the voltage on the flight controller.

---

## 3. Battery System & Bench Power Supply Guidelines

### 3.1. Main Flight Battery (4S LiPo)
* **Chemistry:** Lithium Polymer (LiPo) 4S1P.
* **Nominal Voltage:** $4 \times 3.7\text{ V} = \mathbf{14.8\text{ V}}$ DC.
* **Full Charge Voltage:** $4 \times 4.2\text{ V} = \mathbf{16.8\text{ V}}$ DC.
* **Capacity:** 3300 mAh (`BATT_CAPACITY = 3300.0`).
* **Discharge Capability:** Continuous 30C / Burst 60C rating provides rapid transient current delivery without voltage sag.

---

### 3.2. Bench Testing Warning: ATX / PC Power Supplies

> [!WARNING]
> **DO NOT USE STANDARD PC / ATX POWER SUPPLIES FOR DRIVE TESTING**  
> During initial bench testing, technicians often attempt to power the vehicle using a repurposed computer ATX power supply.  
> * **Failure Mode:** When the steering servo snaps direction or the propulsion motor accelerates from standstill, the instantaneous current rate of change ($\frac{di}{dt}$) and inductive back-EMF trigger the power supply's internal Over-Current Protection (OCP) or Over-Voltage Protection (OVP).  
> * **Result:** The power supply instantly trips and shuts down, dropping all power to the vehicle mid-operation.  
> * **Standard Procedure:** Perform all drive and actuator tests using the **4S LiPo battery** or an industrial lab power supply with adjustable current limiting rated for at least **15A–20A**.

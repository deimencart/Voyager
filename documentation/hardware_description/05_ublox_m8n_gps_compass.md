# GNSS & Digital Compass: U-blox Neo-M8N with External Magnetometer

This document covers the technical specifications, serial protocol, elevated mast mounting, and configuration for the **U-blox Neo-M8N GNSS & Compass** module on the **UGV Voyager 3**.

---

## 1. Receiver Specifications

The vehicle utilizes a multi-constellation u-blox NEO-M8N receiver module engineered for high-precision autonomous positioning:

| Parameter | Specification | Details |
| :--- | :--- | :--- |
| **GNSS Engine** | 72-channel u-blox M8 | Concurrent reception of GPS/QZSS, GLONASS, and BeiDou (Galileo ready) |
| **Position Accuracy** | **2.5 m CEP** (Autonomous) | **2.0 m CEP** with SBAS (EGNOS / WAAS) |
| **Velocity Accuracy** | 0.05 m/s | True ground speed tracking |
| **Heading Accuracy** | 0.3° | Motion vector calculation |
| **Sensitivity** | Tracking & Nav: –167 dBm<br>Cold start: –148 dBm<br>Hot start: –157 dBm | High-sensitivity RF front-end |
| **Update Rate** | Up to 18 Hz (Single GNSS)<br>10 Hz (Concurrent GPS+GLONASS) | Configured to **5 Hz** nominal in ArduPilot |
| **Time to First Fix (TTFF)** | Cold Start: 26 s<br>Hot Start: 1 s | Aided by onboard lithium backup battery |

---

## 2. Interface & Carrier Board Pinouts

The module connects to the **GPS 1** port on the Cube carrier board via an 8-pin JST-GH cable:

| Pin | Signal | Voltage / Logic | Function |
| :---: | :--- | :---: | :--- |
| **1** | VCC | +5.0 V DC | Power to GNSS module & compass |
| **2** | TX (OUT) | 3.3V TTL | Autopilot transmit to GPS module |
| **3** | RX (IN) | 3.3V TTL | GPS module serial data into autopilot (`SERIAL 3`) |
| **4** | SCL (I2C1) | 3.3V (Pull-up) | Primary I2C clock line for magnetometer |
| **5** | SDA (I2C1) | 3.3V (Pull-up) | Primary I2C data line for magnetometer |
| **6** | BUTTON | Active Low | Arming safety switch input |
| **7** | SAFETY_LED | Output | Arming safety switch LED indicator |
| **8** | GND | 0.0 V | Common ground |

*ArduPilot Parameters:*  
* `SERIAL3_PROTOCOL = 5` (GPS NMEA/UBX auto-detect).  
* `SERIAL3_BAUD = 38` (38,400 bps).  
* `GPS_TYPE = 1` (AUTO detect UBX binary format).

---

## 3. External Magnetometer & Elevated Mast Mount

### 3.1. Magnetometer Chipset
The puck module houses an external 3-axis digital compass (Honeywell **HMC5883L** / **IST8310**) connected directly to the primary hardware I2C bus (`I2C 1`). ArduPilot assigns this external sensor as **Compass 1 (Primary)**:
* `COMPASS_USE = 1`
* `COMPASS_EXTERNAL = 1`

### 3.2. Why the Mast Mount is Critical (EMI Isolation)
On electric ground rovers, the propulsion drivetrain draws massive current pulses:
* The 4S LiPo battery leads carry up to **30A–40A** during motor acceleration.
* The Electronic Speed Controller (ESC) generates severe high-frequency magnetic fields due to PWM switching (8 kHz – 16 kHz).
* The steel chassis bolts and traction motor magnets produce significant permanent magnetic offsets.

> [!IMPORTANT]
> **ELECTROMAGNETIC ISOLATION (CARBON FIBER MAST):**  
> Mounting the compass directly on the chassis leads to severe compass calibration failures, heading divergence, and "Toilet Bowling" during autonomous navigation.  
> The Voyager 3 mounts the GPS/Compass puck on a **15 cm – 20 cm elevated carbon fiber mast**, moving the sensitive magnetic sensors outside the high-current field envelope of the battery, ESC, and motor.

---

## 4. References & Documentation

* [u-blox NEO-M8 Series Official Data Sheet (PDF)](https://content.u-blox.com/sites/default/files/NEO-M8-FW3_DataSheet_UBX-15031086.pdf)
* [u-blox 8 / M8 Receiver Description & Protocol Specification (PDF)](https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf)
* [ArduPilot GPS & Compass Module Integration Guide](https://ardupilot.org/rover/docs/common-installing-3dr-ublox-gps-compass-module.html)
* [ArduPilot Advanced Compass Calibration Protocol](https://ardupilot.org/rover/docs/common-compass-calibration-in-mission-planner.html)

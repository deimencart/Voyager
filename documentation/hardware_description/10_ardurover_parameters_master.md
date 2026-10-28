# ArduRover Configuration Parameters Master Reference

This document provides a reference table of the calibrated configuration parameters loaded into the **The Cube Black** flight controller on the **UGV Voyager 3**, verified against the hardware parameter dump (`CONFIGURACION_PARAMETROS_PIXHAWK.parm`).

---

## 1. Autopilot Core & Sensor Thermal Management

| Parameter | Calibrated Value | Default | Engineering Function |
| :--- | :---: | :---: | :--- |
| `BRD_TYPE` | `3` | `0` | Identifies board as Pixhawk 2.1 / The Cube (Cube Black) |
| `BRD_IMU_TARGTEMP`| `45.0` | `-1` | Thermostatically heats isolated IMU module to 45.0 °C |
| `BRD_PWM_COUNT` | `4` | `4` | Number of auxiliary PWM outputs enabled |
| `INS_GYR_ID` | `2162698` | — | Primary gyroscope sensor identifier (MPU9250 on SPI) |
| `INS_GYR2_ID` | `2228234` | — | Secondary gyroscope sensor identifier (ICM20608 on SPI) |
| `INS_GYR3_ID` | `2359306` | — | Tertiary gyroscope sensor identifier (L3GD20 on SPI) |

---

## 2. Serial Communication Ports

| Parameter | Calibrated Value | Protocol / Baud | Description |
| :--- | :---: | :---: | :--- |
| `SERIAL1_PROTOCOL` | `1` | MAVLink 1.0/2.0 | Primary external telemetry radio port |
| `SERIAL1_BAUD` | `57` | 57,600 bps | Telemetry radio transmission speed |
| `SERIAL2_PROTOCOL` | `1` | MAVLink 1.0/2.0 | **Companion gateway UART port** (Raspberry Pi 3B) |
| `SERIAL2_BAUD` | `921` | **921,600 bps** | High-speed link to `/dev/serial0` on companion RPi |
| `SERIAL3_PROTOCOL` | `5` | GPS NMEA / UBX | Dedicated GNSS serial receiver port |
| `SERIAL3_BAUD` | `38` | 38,400 bps | U-blox Neo-M8N receiver default communication speed |
| `SERIAL4_PROTOCOL` | `11` | Proximity / Lidar | **LightWare SF40/C 360° laser rangefinder port** |
| `SERIAL4_BAUD` | `115` | 115,200 bps | SF40/C rotational scanner binary telemetry speed |

---

## 3. Actuator Servo Calibration (Ackermann & ESC)

| Parameter | Calibrated Value | Units | Engineering Function |
| :--- | :---: | :---: | :--- |
| `SERVO1_FUNCTION` | `26` | Enum | GroundSteering (Front Ackermann Servo on `MAIN OUT 1`) |
| `SERVO1_MIN` | `1100` | µs | Maximum right steering PWM pulse width |
| `SERVO1_MAX` | `1900` | µs | Maximum left steering PWM pulse width |
| `SERVO1_TRIM` | `1470` | µs | Neutral steering center alignment |
| `SERVO1_REVERSED` | `1` | Boolean | Inverted steering polarity to match bellcrank linkage |
| `SERVO3_FUNCTION` | `70` | Enum | Throttle (Rear Traction Motor ESC on `MAIN OUT 3`) |
| `SERVO3_MIN` | `900` | µs | Maximum reverse / brake PWM pulse width |
| `SERVO3_MAX` | `2000` | µs | Maximum forward throttle PWM pulse width |
| `SERVO3_TRIM` | `1300` | µs | Stationary motor stop PWM pulse width |
| `SERVO3_REVERSED` | `1` | Boolean | Inverted motor polarity for forward motion |

---

## 4. Obstacle Avoidance & 360° Proximity Parameters

| Parameter | Calibrated Value | Units | Engineering Function |
| :--- | :---: | :---: | :--- |
| `PRX_TYPE` | `1` | Enum | Sensor driver: LightWare SF40/C legacy protocol |
| `AVOID_ENABLE` | `3` | Bitmask | Avoidance enabled in Autonomous and Guided modes |
| `AVOID_DIST_MAX` | `5.0` | meters | Maximum obstacle detection and tracking distance |
| `AVOID_MARGIN` | `2.0` | meters | Minimum vehicle clearance envelope from obstacles |
| `AVOID_BEHAVE` | `1` | Enum | Avoidance behavior: Slide around obstacle / Stop |

---

## 5. Battery Monitor Calibration (3DR Power Module)

| Parameter | Calibrated Value | Units | Engineering Function |
| :--- | :---: | :---: | :--- |
| `BATT_MONITOR` | `3` | Enum | Analog Voltage and Current monitoring |
| `BATT_VOLT_PIN` | `2` | ADC Pin | Autopilot ADC Pin 2 (Voltage divider input) |
| `BATT_CURR_PIN` | `3` | ADC Pin | Autopilot ADC Pin 3 (Current shunt input) |
| `BATT_VOLT_MULT`| `12.10696` | Multiplier | Calibrated voltage scaling factor |
| `BATT_AMP_PERVLT`| `17.0` | Amps/Volt | Calibrated current shunt scaling (17 Amps per Volt) |
| `BATT_CAPACITY` | `3300` | mAh | Nominal capacity of 4S LiPo battery pack |

---

## 6. System Safety & Arming Controls

| Parameter | Calibrated Value | Operational Setting | Engineering Function |
| :--- | :---: | :---: | :--- |
| `ARMING_REQUIRE` | `1` | Enforced | Inhibit all motor/steering PWM until vehicle is armed |
| `BRD_SAFETYENABLE`| `0` | Bypassed | Disables physical push-button switch requirement |
| `FS_THR_ENABLE` | `1` (Field) / `0` (Bench) | Selectable | Radio failsafe (1 = RC link required; 0 = bench test) |
| `MOT_PWM_TYPE` | `0` | Normal PWM | Standard 50 Hz PWM output generation |

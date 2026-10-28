# Initial Setup & Manual Operation Guide

This section describes the step-by-step procedures to power up the **UGV Voyager 3**, establish network communication, bridge MAVLink telemetry, and operate the rover using standard Ground Control Station (GCS) software without needing ROS onboard.

---

## Guide Index

| Step | Guide Document | Objective |
| :---: | :--- | :--- |
| **01** | [01 — Network & Telemetry Setup](01_network_and_telemetry.md) | Connect to the rover via mobile hotspot (`DroneLab`), verify IP, SSH login, and launch MAVProxy serial-to-UDP telemetry forwarding |
| **02** | [02 — Mission Planner & Manual Drive](02_mission_planner_and_drive.md) | Connect Mission Planner via UDP port `14550`, verify sensor heartbeats, perform pre-arm checks, software arm, test steering/throttle, and shutdown |

---

## Operating Pre-requisites
* Mobile phone or laptop configured as a **2.4 GHz Wi-Fi hotspot**:
  * **SSID:** `DroneLab`
  * **Password:** `stavrospapas`
* Charged **4S LiPo battery** ($14.8\text{ V} - 16.8\text{ V}$) with XT60 connector.
* Mission Planner or QGroundControl installed on the GCS computer.

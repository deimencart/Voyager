# Technical Documentation Suite

This directory contains the complete technical documentation for the **UGV Voyager 3**, structured into modular sections covering hardware specifications, first-time vehicle setup, and the ROS 2 software environment.

---

## Documentation Sections

### 1. Hardware Description & Specifications
Detailed technical specifications, pinout tables, schematics, electrical power distribution, and official datasheets for all 9 vehicle subsystems.
* **Master Index:** [Hardware Documentation Index](hardware_description/README.md)
* **Overview & BOM:** [Hardware Overview](hardware_description/hardware_overview.md)
* **Communication Buses:** [Communication Architecture](hardware_description/communication_architecture.md)
* **Components:**
  * [01 — The Cube Black Autopilot](hardware_description/01_the_cube_black_autopilot.md)
  * [02 — LightWare SF40/C LiDAR](hardware_description/02_lightware_sf40c_lidar.md)
  * [03 — Raspberry Pi 3B Gateway](hardware_description/03_raspberry_pi_3b.md)
  * [04 — RPi Camera Module v2](hardware_description/04_rpi_camera_v2.md)
  * [05 — U-blox Neo-M8N GNSS & Compass](hardware_description/05_ublox_m8n_gps_compass.md)
  * [06 — MikroTik mAP 2nD Router](hardware_description/06_mikrotik_map_2nd_router.md)
  * [07 — Huawei 4G LTE Modem](hardware_description/07_huawei_e3372h_lte_modem.md)
  * [08 — Ackermann Steering & Actuators](hardware_description/08_ackermann_actuators_chassis.md)
  * [09 — Power Distribution Tree](hardware_description/09_power_distribution_tree.md)
  * [10 — ArduRover Parameters Master Table](hardware_description/10_ardurover_parameters_master.md)

---

### 2. Initial Setup (Manual Drive without ROS)
Step-by-step procedures to power the rover, connect to network telemetry, configure ground control software, and perform first movement tests.
* [01 — Network & Telemetry Setup](initial_setup/01_network_and_telemetry.md): Hotspot configuration (`DroneLab`), SSH access, and MAVProxy forwarding.
* [02 — Mission Planner & Manual Drive](initial_setup/02_mission_planner_and_drive.md): UDP connection, pre-arm checks, manual arming, steering/throttle tests, and shutdown.

---

### 3. ROS 2 Software Environment
Installation instructions and workspace setup for controlling the vehicle using the Robot Operating System (ROS 2 Humble).
* [01 — ROS 2 Installation Guide](ros2_setup/01_ros2_installation.md): Step-by-step installation for Linux (Ubuntu 22.04 LTS native) and Windows (WSL2), MAVROS integration, and UDP network verification.

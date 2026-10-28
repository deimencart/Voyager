# ROS 2 Software Environment Setup

This section provides the complete environment setup guides for controlling the **UGV Voyager 3** using **ROS 2 Humble Hawksbill**.

---

## Guide Index

| Step | Guide Document | Target Platforms | Description |
| :---: | :--- | :--- | :--- |
| **01** | [01 — ROS 2 Installation Guide](01_ros2_installation.md) | Ubuntu 22.04 LTS (Native) / Windows 11 (WSL2) | Binary package installation, MAVROS setup, GeographicLib datasets, workspace compilation, and UDP telemetry verification |

---

## Architecture Note
The rover's onboard Raspberry Pi 3B acts solely as a lightweight serial-to-UDP telemetry gateway (running `MAVProxy`).  
The ROS 2 stack and MAVROS nodes run on your development computer (Linux workstation or Windows PC with WSL2), communicating with the rover over UDP port `14550`.

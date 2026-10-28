# Onboard Wireless Router: MikroTik RouterBOARD mAP 2nD (RBmAP2nD)

This document details the hardware specifications, network interfaces, power input, and operational routing modes for the **MikroTik RouterBOARD mAP 2nD** router on the **UGV Voyager 3**.

---

## 1. Technical Specifications

* **Model:** MikroTik RouterBOARD mAP 2nD (Product code: `RBmAP2nD`).
* **Processor / SoC:** Qualcomm Atheros **QCA9531** (MIPSBE architecture @ 650 MHz).
* **RAM:** 64 MB DDR2 400 MHz.
* **Storage:** 16 MB onboard SPI Flash.
* **Operating System:** MikroTik RouterOS (License Level 4).
* **Wireless Subsystem:**
  * 2.4 GHz 802.11b/g/n dual-chain (2x2 MIMO).
  * Built-in omnidirectional antenna with 1.2 dBi gain.
  * Transmission speeds up to 300 Mbps.
* **Power Supply Flexibility:**
  * **DC Barrel Jack:** Accepts **8 V to 57 V DC** (connected to the **12.0 V DC** battery rail from the PDB).
  * **Micro-USB:** 5.0 V DC power input.
  * **Passive PoE-In:** 10 V to 57 V DC on `Ether1`.
  * **Maximum Power Consumption:** ~5 W without USB devices.
* **Dimensions:** 68 mm × 68 mm × 19 mm.

---

## 2. Network Physical Interfaces

```text
               ┌────────────────────────────────────────────────────────┐
               │              MikroTik RouterBOARD mAP 2nD              │
               │                                                        │
12V DC (PDB) ─►│ [DC Jack: 8-57V]                                       │
               │                                                        │
RPi 3B eth0  ◄─┤ [Ether 1: PoE In]           [micro-USB Host] ◄─────────┼─► Huawei 4G LTE
               │                                                        │   (E3372h HiLink)
Field Laptop ◄─┤ [Ether 2: PoE Out]          [2.4 GHz Wi-Fi AP/STA] ◄───┼─► DroneLab Hotspot
               └────────────────────────────────────────────────────────┘
```

1. **Ether 1 (Fast Ethernet 10/100 Mbps):**
   * Connected directly to the Raspberry Pi 3B onboard Ethernet port (`eth0`).
   * Configured within the vehicle internal LAN (`192.168.1.0/24`).
2. **Ether 2 (Fast Ethernet 10/100 Mbps with Passive PoE Out):**
   * Accessible externally on the vehicle chassis.
   * Enables field engineers to connect a laptop via a standard RJ45 cable for direct diagnostics without relying on Wi-Fi.
3. **Micro-USB 2.0 Host Port:**
   * Equipped with automated USB power reset support.
   * Hosts the **Huawei E3372h 4G/LTE USB cellular modem** in HiLink hostless mode.

---

## 3. Critical Difference: mAP 2nD vs. mAP lite

| Feature | MikroTik mAP 2nD (RBmAP2nD) | MikroTik mAP lite (RBmAPL-2nD) |
| :--- | :---: | :---: |
| **Ethernet Ports** | **2x 10/100 Fast Ethernet** | 1x 10/100 Fast Ethernet |
| **USB Host Port** | **Yes (micro-USB type AB)** | **No (None)** |
| **4G Cellular Dongle Support** | **Full USB support** | Unsupported |
| **Simultaneous Laptop + RPi Cable** | **Supported** (`Ether1` + `Ether2`) | Impossible (Single port) |
| **DC Power Jack** | **8V – 57V DC** | Only PoE or microUSB |

The **Voyager 3 specifically requires the mAP 2nD** because it provides both independent wired connections (to the Raspberry Pi and technician port) and hosts the 4G LTE cellular dongle simultaneously.

---

## 4. Wireless Operational Modes: Hotspot vs. Direct AP

The router is configured to support two modes of wireless connectivity:

### Mode A: Station Client Mode (`DroneLab` Hotspot) — Recommended
* The router scans for a predefined 2.4 GHz Wi-Fi network and associates with it automatically on boot.
* **Target Network (SSID):** `DroneLab`
* **Password:** `stavrospapas`
* **Band:** 2.4 GHz
* **Advantage:** Bypasses local IP conflicts and assigns standard DHCP addresses to all vehicle components.

### Mode B: Direct Access Point Mode (`Voyager 3`)
* If no hotspot is detected, the router emits an SSID named `Voyager 3`.
* Direct connection can occasionally encounter DHCP handshake issues depending on the operating system of the ground station; the `DroneLab` hotspot mode is the proven reliable field method.

---

## 5. References & Documentation

* [MikroTik mAP 2nD Official Product Brochure (PDF)](https://i.mt.lv/product_files/mAP-qg_191149.pdf)
* [MikroTik RouterBOARD mAP User Manual (Official Documentation)](https://help.mikrotik.com/docs/display/UM/mAP)
* [MikroTik mAP 2nD Specifications & Firmware Downloads](https://mikrotik.com/product/RBmAP2nD)
* [MikroTik RouterOS 4G/LTE Interface Configuration Guide](https://help.mikrotik.com/docs/display/ROS/LTE)

# Cellular Modem: Huawei HiLink 4G/LTE USB Dongle (E3372h)

This document covers the radio specifications, hostless architecture, web administration interface, and network routing for the **Huawei E3372h 4G/LTE** cellular modem on the **UGV Voyager 3**.

---

## 1. Cellular Standards & Radio Frequency Specifications

The Huawei E3372h USB dongle provides Beyond Visual Line of Sight (BVLOS) long-range connectivity, bridging telemetry and video over cellular cellular networks:

| Parameter | Specification | Details |
| :--- | :--- | :--- |
| **Model** | Huawei **E3372h-153** / E3372s | USB 2.0 High-Speed Stick |
| **Cellular Standard** | 3GPP LTE Release 9, Category 4 (Cat4) | Downlink: Up to **150 Mbps**<br>Uplink: Up to **50 Mbps** |
| **4G LTE Frequency Bands** | FDD: Bands 1, 3, 7, 8, 20 | 2100 / 1800 / 2600 / 900 / 800 MHz |
| **3G UMTS / DC-HSPA+ Bands** | 900 / 2100 MHz | Up to 42.2 Mbps downlink |
| **2G GSM / GPRS / EDGE Bands** | 850 / 900 / 1800 / 1900 MHz | Quad-band fallback |
| **RF Connectors** | 2x **CRC9** External Antenna Ports | Supports 2x2 MIMO external high-gain antennas |
| **Operating Voltage** | 5.0 V DC (from USB bus) | Power consumption: < 3.5 W (~500–700 mA peak) |
| **SIM Card Slot** | Standard Mini-SIM (2FF) | Directly under sliding cover |

---

## 2. HiLink Hostless Architecture vs. Legacy Stick Mode

The Voyager 3 utilizes the modem in **HiLink Mode** rather than legacy serial stick mode:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Huawei HiLink Architecture                       │
│                                                                        │
│   Cellular Tower ◄──► [LTE Baseband Modem]                             │
│                              │                                         │
│                       [Internal Router]                                │
│                   (NAT + DHCP: 192.168.8.1)                            │
│                              │                                         │
│                     [CDC-Ether / RNDIS]                                │
│                              │                                         │
│               USB Port ◄─────┴─────► MikroTik mAP 2nD (lte1 Interface) │
└────────────────────────────────────────────────────────────────────────┘
```

### Why HiLink Mode is Superior for Autonomous Robotics:
1. **Hostless Autonomous Reconnection:**  
   The modem firmware manages the radio link autonomously. If cellular coverage drops in a valley and returns, the modem reconnects automatically without requiring AT command reconnection scripts on the host.
2. **Virtual Ethernet Interface (CDC-Ether):**  
   The MikroTik router recognizes the modem instantly as a native virtual Ethernet card (`lte1`). No USB serial dialers (`wvdial` or `chat`) are required.
3. **Dedicated Subnet Separation:**  
   The modem assigns itself as an independent gateway on the `192.168.8.0/24` subnet, keeping the cellular WAN isolated from the rover's internal LAN (`192.168.1.0/24`).

---

## 3. Web Administration Interface (`192.168.8.1`)

When connected through the vehicle network or directly into a laptop:
* **Admin URL:** `http://192.168.8.1/`
* **Features:**
  * **APN Configuration:** Allows setting custom cellular carrier Access Point Names (APNs) and credentials.
  * **Radio Signal Diagnostics:** Real-time metrics including:
    * **RSSI:** Received Signal Strength Indicator (dBm).
    * **RSRP:** Reference Signal Received Power (dBm).
    * **RSRQ:** Reference Signal Received Quality (dB).
    * **SINR:** Signal-to-Interference-plus-Noise Ratio (dB).
  * **SMS Console:** Send and receive carrier text messages directly.

---

## 4. References & Documentation

* [Huawei Official Consumer Portal](https://consumer.huawei.com/en/)
* [OpenWrt Hardware Documentation for Huawei E3372 (HiLink / CDC-Ether)](https://openwrt.org/toh/huawei/e3372)
* [MikroTik RouterOS LTE Interface Setup Guide](https://help.mikrotik.com/docs/spaces/ROS/pages/328114/LTE)

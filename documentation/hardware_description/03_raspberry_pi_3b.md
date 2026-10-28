# Companion Gateway: Raspberry Pi 3 Model B

This document covers the technical specifications, serial UART bridge configuration, power requirements, and pinout connections for the **Raspberry Pi 3 Model B** serving as the companion computer on the **UGV Voyager 3**.

---

## 1. Technical Specifications

* **Model:** Raspberry Pi 3 Model B (Rev 1.2).
* **System-on-Chip (SoC):** Broadcom **BCM2837**.
* **CPU:** Quad-Core 64-bit ARM Cortex-A53 @ 1.2 GHz.
* **GPU:** Broadcom VideoCore IV @ 400 MHz (H.264 high-profile hardware video encode/decode at 1080p30).
* **RAM:** 1 GB LPDDR2 SDRAM (900 MHz shared with GPU).
* **Storage:** 32 GB MicroSD Class 10 (SanDisk / Kingston).
* **Operating System:** Raspbian GNU/Linux 9 (Stretch) / Debian derivative, Linux Kernel 4.14.
* **Connectivity:**
  * 10/100 Mbps Fast Ethernet (SMSC LAN9514 controller via internal USB 2.0).
  * 2.4 GHz 802.11 b/g/n Wi-Fi & Bluetooth 4.1 Classic / BLE (Broadcom BCM43438).
  * 4x USB 2.0 Type-A ports.
  * 15-pin MIPI CSI-2 camera connector.
  * Full-size HDMI 1.4 port.

---

## 2. Power Supply & Thermal Domain

The Raspberry Pi 3B is powered independently by a **Turnigy MultiStar SBEC** (Switching Battery Elimination Circuit):
* **Input Voltage:** Main 4S LiPo battery (14.8V – 16.8V DC).
* **Regulated Output:** **5.0 V DC @ 5.0 A continuous** (7.5 A peak).
* **Connection Point:** Connected directly to the 40-pin GPIO header:
  * Positive (+5.0V): **Pin 2** and **Pin 4**.
  * Ground (0.0V): **Pin 6** and **Pin 9**.

> [!CAUTION]
> **ELECTRICAL ISOLATION RULE (TELEM 2 +5V DISCONNECTED):**  
> Because the Raspberry Pi has its own dedicated 5V/5A power supply, the **+5.0V line of Pixhawk TELEM 2 (Pin 1) must remain disconnected**.  
> Connecting +5V between the Pixhawk and the Raspberry Pi would create a parallel power loop, potentially backfeeding current, burning traces, or causing unpredictable resets.

---

## 3. High-Speed Serial UART Interconnect (`/dev/serial0`)

The companion computer bridges MAVLink telemetry between the autopilot and the IP network using its primary hardware UART (PL011):

```text
Raspberry Pi 40-Pin Header            Pixhawk 2.1 Carrier (TELEM 2)
───────────────────────────            ──────────────────────────────
Pin 8  (GPIO 14 - TXD) ──────────────► Pin 3 (RXD - Green wire)
Pin 10 (GPIO 15 - RXD) ◄────────────── Pin 2 (TXD - Yellow wire)
Pin 6  (Ground)        ◄─────────────► Pin 6 (GND - Black wire)
Pin 2/4 (5V Supply)    [Turnigy SBEC]  Pin 1 (+5V) [LEFT EMPTY]
```

### UART Configuration in `/boot/config.txt`
To achieve maximum communication throughput without packet drops at **921,600 bps**, the onboard Bluetooth is decoupled and the primary ARM PL011 UART (`/dev/ttyAMA0`) is assigned to the physical GPIO pins:

```ini
# /boot/config.txt
enable_uart=1
dtoverlay=pi3-disable-bt
core_freq=250
```

* The serial device alias `/dev/serial0` points directly to `/dev/ttyAMA0`.
* The Linux serial console login prompt (`serial-getty@ttyAMA0.service`) is disabled to prevent terminal data from corrupting MAVLink streams.

---

## 4. Network Integration & Telemetry Routing

* **Wired Ethernet Interface (`eth0`):** Configured with static IP `192.168.1.100/24` (or DHCP from MikroTik router). Connects via standard RJ45 cable to port `Ether1` on the MikroTik mAP 2nD router.
* **MAVProxy Telemetry Daemon:**  
  On system boot, a systemd service executes MAVProxy to read binary MAVLink packets from `/dev/serial0` at 921,600 bps and broadcast them over UDP to the ground station:
  ```bash
  mavproxy.py --master=/dev/serial0,921600 --out=udpbcast:192.168.137.255:14550
  ```

---

## 5. References & Documentation

* [Raspberry Pi 3 Model B Official Product Brief (PDF)](https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-product-brief.pdf)
* [Raspberry Pi 3 Model B Reduced Schematics (PDF)](https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-reduced-schematics.pdf)
* [Raspberry Pi Official Hardware & UART Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts)
* [Broadcom BCM2837 ARM Peripherals Architecture](https://datasheets.raspberrypi.com/bcm2835/bcm2835-peripherals.pdf)

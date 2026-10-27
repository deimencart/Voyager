# Step 1: Network Setup & MAVLink Telemetry Bridge

This guide explains how to establish the network connection between your Ground Control Station (laptop) and the **UGV Voyager 3**, log into the companion computer via SSH, and start the MAVLink telemetry forwarder **without running ROS**.

---

## Prerequisites

* UGV Voyager 3 powered via its main 3S LiPo battery.
* Operator Laptop running Windows 10/11 or Linux with Wi-Fi enabled.
* An SSH client installed (Windows Terminal, PowerShell, or standard bash).

---

## Step 1.1: Connect the Rover via Hotspot

> **Note on Wi-Fi Networks:**  
> The onboard MikroTik router broadcasts its own Wi-Fi named `Voyager 3`. However, connecting directly to it is often unreliable due to DHCP/IP conflicts.  
> The tested and hassle-free method is to create a mobile hotspot on your phone or laptop. The rover is pre-configured to look for this hotspot and join it automatically.

To connect with the rover:

1. **Turn on Mobile Hotspot** on your phone or laptop.
2. **Configure the exact credentials** expected by the rover:
   * **Hotspot Name (SSID):** `DroneLab`
   * **Password:** `stavrospapas`
   * **Band:** 2.4 GHz
3. **Turn on the rover** by plugging in the 4S LiPo battery. It connects to your hotspot automatically within ~30–45 seconds.
4. **Find the rover's IP address** in your hotspot's connected devices list (e.g. `192.168.137.153`).

*(Optional field alternative: You can also connect a direct Ethernet cable from your laptop to the onboard MikroTik router at `192.168.1.1`)*

---

## Step 1.2: Verify SSH Access to Raspberry Pi

Open PowerShell or a terminal on your laptop and run:

```bash
ssh pi@192.168.137.153
```
*(Replace `192.168.137.153` with the actual IP address assigned to the rover)*

* **Default Username:** `pi`
* **Default Password:** `stavrospapas` *(or `raspberry` on clean images)*

Once logged in, verify serial communication with the Pixhawk:

```bash
ls -l /dev/serial0
```
*You should see `/dev/serial0 -> ttyAMA0` or `ttyS0`.*

---

## Step 1.3: Start MAVProxy Telemetry Forwarding

The Pixhawk sends telemetry out of its `TELEM 2` port at **921,600 baud**. The Raspberry Pi uses **`MAVProxy`** to read this serial stream and forward it over Ethernet/Wi-Fi to your laptop's UDP port `14550`.

Run the following command on the Raspberry Pi:

```bash
mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=udp:192.168.137.1:14550 --aircraft Voyager_3
```

> [!NOTE]
> Replace `192.168.137.1` with the **IP address of your laptop** (the GCS IP).  
> If using broadcast on your local subnet, you can also use:
> ```bash
> mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=udp:192.168.137.255:14550 --aircraft Voyager_3
> ```

### Expected Console Output:

```text
Connect /dev/serial0,921600 source_system=255
Loaded module console
Loaded module map
MAV: Heartbeat from system 1 component 1
Flight mode: HOLD
APM: ArduRover v3.4.2 (82c65fe3)
Received 679 parameters
```

When you see `Heartbeat from system 1` and `Received 679 parameters`, the telemetry stream is active and broadcasting to your laptop.

---

### Next Step:
Proceed to [**Step 2: Mission Planner Setup & First Movement**](02_mission_planner_and_drive.md) to connect the graphical interface and drive the rover.

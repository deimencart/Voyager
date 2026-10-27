# Step 2: Mission Planner Setup & First Movement (No ROS)

This guide covers connecting **Mission Planner** (or **QGroundControl**) to the live telemetry stream, running pre-arm safety checks, arming the autopilot, and testing steering and motor motion **without ROS**.

---

## 2.1: Connect Mission Planner via UDP

1. Open **Mission Planner** on your laptop.
2. In the top-right corner of the window:
   * Select **`UDP`** from the communication port dropdown (do not select a COM port).
   * Leave the baudrate dropdown at **`115200`** (baudrate is ignored for UDP sockets).
3. Click the **Connect** button.
4. A popup will prompt for the UDP port:
   * Enter **`14550`** and click **OK**.
5. Mission Planner will begin loading parameters from the Pixhawk:
   * The progress bar will count up to 679 parameters.
   * The artificial horizon will level, showing active pitch, roll, and heading.

---

## 2.2: Pre-Arming Checks & Telemetry Verification

Before arming the vehicle, verify the following indicators in the **Flight Data** screen:

| Telemetry Item | Nominal Value | What It Confirms |
| :--- | :--- | :--- |
| **Flight Mode** | `HOLD` or `MANUAL` | Vehicle will not attempt autonomous movement upon arming. |
| **Battery Voltage** | `11.1V - 12.6V` | Main LiPo battery is connected and healthy. |
| **Servo Voltage (`servovoltage`)** | `~5.57V` ($5570\text{ mV}$) | Auxiliary BEC is powering the `MAIN OUT` servo rail for steering. |
| **GPS Status** | `GPS: No Fix` (Indoor) / `3D Fix` (Outdoor) | GPS unit is communicating with Pixhawk via `SERIAL 3`. |
| **Proximity Radar (Ctrl+F)** | 360° obstacle vectors | LightWare SF40/C is streaming distances via `SERIAL 4/5`. |

> [!WARNING]
> **Safety Switch Check:**  
> If the physical safety switch on the Pixhawk is blinking red, press and hold it for 3 seconds until the LED turns **solid red**. The default parameter set in this rover has `BRD_SAFETYENABLE = 0` (software arming allowed), but physical verification is always recommended.

---

## 2.3: Radio Failsafe Considerations (Bench Testing)

By default, ArduRover enforces a safety failsafe if no handheld RC transmitter signal is detected (`FS_THR_ENABLE = 1`), preventing arming over telemetry.

If you are bench-testing the rover **without an RC transmitter turned on**:
1. In Mission Planner, go to **Config/Tuning** $\to$ **Full Parameter Tree**.
2. Search for `FS_THR_ENABLE`.
3. Note its original value (`1`) and temporarily set it to **`0`** (Disabled).
4. Click **Write Params**.
5. Ensure the flight mode is set to **`MANUAL`**.

> [!IMPORTANT]
> Always restore `FS_THR_ENABLE = 1` before taking the vehicle outdoors for autonomous or high-speed testing!

---

## 2.4: Arming the Rover

Once the mode is `MANUAL` and pre-arm checks pass:

### Method A: Arming via Mission Planner Interface
1. Go to **Flight Data** $\to$ click the **Actions** tab (under the artificial horizon).
2. Look for the **Arm/Disarm** button.
3. Click **Arm**.
4. **Auditory Confirmation:** The Pixhawk buzzer will emit **one long solid beep**, and the main RGB LED will stay solid green.

### Method B: Arming via MAVProxy Terminal
In the SSH terminal where MAVProxy is running:
```text
MAV> mode manual
MAV> arm throttle
```
*Output: `ARMED`*

---

## 2.5: Testing Actuator Motion

### A. Testing Front Steering (Ackermann Linkage)
* In the **Actions** tab or via RC Channel 1 override:
  * Steering trim is centered at **$1470\text{ }\mu\text{s}$**.
  * Increasing PWM towards **$1900\text{ }\mu\text{s}$** turns wheels in one direction.
  * Decreasing PWM towards **$1100\text{ }\mu\text{s}$** turns wheels in the opposite direction.
  * Mechanically, the steering angle $\delta$ must saturate at $\pm 25^\circ$.

### B. Testing Rear Traction Motor
* Elevate the rear wheels off the ground on a test bench.
* Move channel 3 (Throttle) slightly above neutral ($1300\text{ }\mu\text{s}$ trim):
  * The rear wheels will begin turning forward smoothly.
* Move channel 3 slightly below neutral to test reverse and regenerative brake.

---

## 2.6: Safe Shutdown Procedure

1. **Disarm the Vehicle:**
   * In Mission Planner: Click **Disarm** in the Actions tab.
   * The buzzer will emit **two short beeps** (*DISARMED*).
2. **Switch Flight Mode to HOLD:**
   * Set mode to `HOLD` to lock all actuator PWM lines.
3. **Shutdown Linux Companion Gracefully:**
   * In the SSH session, run:
     ```bash
     sudo poweroff
     ```
   * Wait 15 seconds until the green activity LED on the Raspberry Pi stops blinking completely.
4. **Disconnect Power:**
   * Unplug the main XT60 battery connector.

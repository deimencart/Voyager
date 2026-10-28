# Vision Camera: Raspberry Pi Camera Module v2

This document covers the optical specifications, physical interface, video streaming pipeline, and configuration for the **Raspberry Pi Camera Module v2** mounted on the **UGV Voyager 3**.

---

## 1. Optical & Sensor Specifications

The Camera Module v2 replaces the original OmniVision OV5647 sensor with a high-definition Sony IMX219 sensor:

| Parameter | Specification | Details |
| :--- | :--- | :--- |
| **Image Sensor** | Sony **IMX219PQ** Exmor R | Back-illuminated CMOS color sensor |
| **Still Resolution** | **8.08 Megapixels** | 3280 × 2464 effective active pixels |
| **Optical Format** | 1/4.0" | Sensor diagonal: 4.60 mm |
| **Pixel Dimensions** | 1.12 µm × 1.12 µm | High-sensitivity OmniBSI architecture |
| **Lens Focal Length** | 3.04 mm | ~29 mm equivalent in 35mm photography |
| **Aperture** | $f/2.0$ | Fixed focal plane |
| **Horizontal Field of View (H-FoV)** | **62.2°** | Wide-angle forward vision |
| **Vertical Field of View (V-FoV)** | **48.8°** | Ground and obstacle clearance view |
| **Video Modes Supported** | 1080p @ 30 fps<br>720p @ 60 fps<br>VGA (640x480) @ 90 fps | Hardware H.264 encoder on VideoCore IV |

---

## 2. Physical Interconnect (MIPI CSI-2)

* **Cable:** 15-pin Flat Flexible Cable (FFC), 1.0 mm pitch ribbon cable.
* **Interface:** Direct connection to the Raspberry Pi 3B **CAMERA** port.
* **Bus Architecture:** 2-lane MIPI CSI-2 (Camera Serial Interface 2) carrying raw uncompressed Bayer data directly to the Broadcom VideoCore IV Image Sensor Processor (ISP).
* **Hardware Acceleration:** The VideoCore IV GPU handles debayering, automatic white balance (AWB), auto-exposure (AE), and real-time H.264 video compression in silicon with virtually zero CPU utilization.

---

## 3. Video Streaming Pipeline (Voyager 3)

The vehicle captures video for real-time remote driving and teleoperation using the `raspivid` utility piped through GStreamer into an RTP H.264 UDP network stream.

### Operational Parameters
* **Resolution:** 1024 × 768 pixels.
* **Framerate:** 30 frames per second (fps).
* **Bitrate:** 1,000,000 bps (1.0 Mbps), optimized for reliable low-latency wireless transmission.
* **Network Protocol:** RTP (Real-time Transport Protocol) payload type 96 over UDP.
* **Target Port:** **5600** on the GCS laptop.

### Pipeline Execution Command (Raspberry Pi):
```bash
raspivid -n -w 1024 -h 768 -b 1000000 -fps 30 -t 0 -o - \
  | gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=10 pt=96 \
  ! udpsink host=192.168.137.1 port=5600
```

### Receiving Stream on Ground Control Station (GCS):
* **Using GStreamer:**
  ```bash
  gst-launch-1.0 -v udpsrc port=5600 caps="application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264" \
    ! rtph264depay ! avdec_h264 ! autovideosink sync=false
  ```
* **Using Mission Planner / QGroundControl:**
  * In QGroundControl: Video Settings $\to$ Source: **`UDP h.264 Video Stream`**, Port: **`5600`**.

---

## 4. References & Documentation

* [eLinux Raspberry Pi Camera Module Hardware Guide](https://elinux.org/Rpi_Camera_Module)
* [Raspberry Pi Hardware Documentation Repository](https://github.com/raspberrypi/documentation)

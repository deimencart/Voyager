# ROS 2 Environment Setup & Installation Guide

This guide provides the complete, step-by-step instructions to replicate our **ROS 2 Humble** development and control environment on both **Linux (Native Ubuntu 22.04)** and **Windows (WSL2)** to communicate with the UGV Voyager 3.

---

## 1. System Requirements & Compatibility

| Platform | Recommended Setup | Supported ROS 2 Distribution |
| :--- | :--- | :--- |
| **Linux** | Ubuntu 22.04 LTS (*Jammy Jellyfish*) 64-bit | **ROS 2 Humble Hawksbill** (Desktop) |
| **Windows** | Windows 10/11 with **WSL2** (Ubuntu 22.04 distro) | **ROS 2 Humble Hawksbill** inside WSL2 |

---

## 2. Operating System Preparation

### Option A: Windows (WSL2 Setup)

If you are using Windows 10 or 11, install WSL2 with Ubuntu 22.04:

1. Open PowerShell as Administrator and run:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```
2. Restart your computer if prompted.
3. Launch Ubuntu 22.04 from the Start menu and set up your Linux username and password.
4. **UDP Networking Tip (WSL2):** To ensure MAVLink UDP packets from the rover (port 14550) reach WSL2 smoothly, create or edit `%USERPROFILE%\.wslconfig` in Windows with:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
   *(Or ensure your Windows Firewall allows inbound UDP traffic on port 14550).*

### Option B: Linux (Native Ubuntu 22.04)

Open a standard terminal (`Ctrl+Alt+T`) and ensure your system is up to date:
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 3. Install ROS 2 Humble Hawksbill

Run the following commands inside your Ubuntu 22.04 terminal (native or WSL2):

### Step 3.1: Set Locale
```bash
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Step 3.2: Add ROS 2 GPG Key & Repository
```bash
sudo apt install software-properties-common curl -y
sudo add-apt-repository universe -y

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### Step 3.3: Install ROS 2 Desktop Packages
```bash
sudo apt update
sudo apt install ros-humble-desktop -y
```

### Step 3.4: Configure Shell Environment
Add ROS 2 to your bash profile so it loads on every new terminal:
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 4. Install Build Tools & Package Managers

Install `colcon` (the ROS 2 build system), `rosdep`, and Python utilities:

```bash
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    git

# Initialize rosdep
sudo rosdep init
rosdep update
```

---

## 5. Install Robotics Dependencies & Message Definitions

Our setup requires MAVROS (MAVLink bridge), Ackermann message interfaces, and TF2 transform libraries:

### Step 5.1: Install MAVROS and Message Packages
```bash
sudo apt install -y \
    ros-humble-mavros \
    ros-humble-mavros-msgs \
    ros-humble-ackermann-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs
```

### Step 5.2: Install GeographicLib Datasets (Mandatory for MAVROS)
MAVROS requires GeographicLib coordinate datasets to compute GPS geodetic transformations. Without these, MAVROS nodes fail to initialize:
```bash
sudo /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh
```

### Step 5.3: Install Python Dependencies
```bash
pip3 install pymavlink
```

---

## 6. Clone & Build the Voyager Workspace

With all prerequisites installed, clone the repository and build the workspace:

### Step 6.1: Clone the Repository
```bash
git clone https://github.com/deimencart/Voyager.git
cd Voyager/ros2_ws
```

### Step 6.2: Install Workspace Dependencies via rosdep
```bash
rosdep install --from-paths src --ignore-src -r -y
```

### Step 6.3: Build the Packages
Compile the ROS 2 packages using symlink installs (enables rapid development without recompiling Python scripts):
```bash
colcon build --symlink-install
```

### Step 6.4: Source the Workspace Overlay
```bash
source install/setup.bash

# Optional: Add to ~/.bashrc for automatic loading
echo "source $(pwd)/install/setup.bash" >> ~/.bashrc
```

---

## 7. Verification & Sanity Checks

Verify that your system recognizes the Voyager packages:

```bash
ros2 pkg list | grep voyager
```
**Expected Output:**
```text
voyager_bringup
voyager_navigation
```

Verify that the Nearness Diagram node and launch files can be located:
```bash
ros2 pkg executables voyager_navigation
```
**Expected Output:**
```text
voyager_navigation nearness_diagram_node
```

Your environment is now fully configured and ready to communicate with the rover via ROS 2.

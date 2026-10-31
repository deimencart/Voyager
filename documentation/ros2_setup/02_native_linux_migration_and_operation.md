# Guía de Migración y Operación en Linux Nativo (Ubuntu 22.04 LTS)

Esta guía detalla el procedimiento paso a paso para desplegar, compilar y operar la plataforma autónoma **UGV Voyager 3** directamente en una estación de trabajo o portátil con **Linux nativo (Ubuntu 22.04 LTS Jammy Jellyfish)**, prescindiendo por completo de la capa de virtualización de Windows y WSL2.

---

## 🚀 1. Ventajas de la Arquitectura en Linux Nativo

Al migrar a Linux nativo se eliminan los cuellos de botella de red y rendimiento presentes en entornos virtualizados:

| Característica | Windows 11 + WSL2 | Linux Nativo (Ubuntu 22.04) |
| :--- | :--- | :--- |
| **Pila de red** | Switch virtual Hyper-V (Subred NAT `172.29.x.x`) | Acceso directo a interfaces físicas (`wlan0`, `eth0`) |
| **Daemon de reenvío** | Requiere [`udp_mavlink_relay.py`](file:///d:/Voyager/repos/udp_mavlink_relay.py) | **Innecesario**. Los sockets UDP se abren directamente |
| **Rendimiento RViz 2** | Virtualizado por WSLg (~30 FPS, emulación OpenGL) | **Aceleración GPU directa por hardware** (60+ FPS nativo) |
| **DDS / Multicast ROS 2** | Aislado por el cortafuegos y el adaptador Hyper-V | Descubrimiento automático de nodos en toda la subred local |
| **Orquestación** | Requiere 3 terminales (PowerShell + 2 WSL2) | **Un solo comando central** (`voyager_bringup.launch.py`) |

---

## 📦 2. Requisitos Previos e Instalación de Dependencias

Ejecuta los siguientes comandos en tu terminal de Ubuntu 22.04:

### 2.1. Actualizar el sistema e instalar ROS 2 Humble Desktop
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common curl locales git

# Configurar locales en UTF-8
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Añadir repositorio de ROS 2 Humble
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop
```

### 2.2. Instalar herramientas de compilación y librerías de robótica
```bash
# Herramientas de build
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip

# Paquetes de ROS 2 (MAVROS, Ackermann, Visión y TF)
sudo apt install -y \
    ros-humble-mavros \
    ros-humble-mavros-msgs \
    ros-humble-ackermann-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-sensor-msgs-py \
    ros-humble-nav-msgs \
    ros-humble-rviz2

# Inicializar rosdep (si no se ha hecho previamente)
sudo rosdep init || true
rosdep update

# Datasets geodésicos obligatorios para MAVROS (GPS / WGS-84)
sudo /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh
```

### 2.3. Instalar librerías de vídeo GStreamer y Python MAVLink
```bash
# GStreamer con soporte H.264 para decodificar la cámara CSI de la Raspberry Pi
sudo apt install -y \
    python3-opencv \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev

# Dependencias Python
pip3 install pymavlink
```

---

## 🛠️ 3. Clonado del Repositorio y Compilación

```bash
# 1. Clonar el repositorio
git clone https://github.com/deimencart/Voyager.git ~/Voyager
cd ~/Voyager/ros2_ws

# 2. Instalar dependencias del workspace con rosdep
rosdep install --from-paths src --ignore-src -r -y

# 3. Compilar paquetes con symlinks (desarrollo rápido en Python)
colcon build --symlink-install

# 4. Configurar el entorno en tu sesión bash
source install/setup.bash
```

> [!TIP]
> Para no tener que hacer `source` manualmente cada vez que abras una terminal, añade las siguientes líneas a tu `~/.bashrc`:
> ```bash
> echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
> echo "source ~/Voyager/ros2_ws/install/setup.bash" >> ~/.bashrc
> source ~/.bashrc
> ```

---

## 📶 4. Configuración del Enlace de Red en Linux

La Raspberry Pi 3B a bordo del Voyager 3 viene preconfigurada para conectarse automáticamente a un punto de acceso con los siguientes parámetros:
* **SSID:** `DroneLab`
* **Contraseña:** `stavrospapas`
* **Banda:** $2.4\text{ GHz}$

### Opción A: Crear el Hotspot directamente desde la terminal de Ubuntu (Recomendada)
```bash
# 1. Crear y levantar el punto de acceso inalámbrico
nmcli dev wifi hotspot ssid DroneLab password stavrospapas ifname wlan0

# 2. Verificar la IP asignada a tu interfaz Wi-Fi (normalmente 10.42.0.1 o 192.168.137.1)
ip addr show wlan0
```

> [!NOTE]
> Si la Raspberry Pi ya tiene fijada la IP de destino de telemetría a `192.168.137.1`, puedes añadir dicha IP como alias secundario a tu tarjeta Wi-Fi de Linux con:
> ```bash
> sudo ip addr add 192.168.137.1/24 dev wlan0
> ```

### Opción B: Conexión mediante el Router MikroTik (`Voyager_3`)
Si enciendes el router MikroTik del rover, simplemente conecta tu portátil por Wi-Fi al SSID `Voyager_3`. Tu ordenador recibirá una IP dentro del rango `192.168.1.x` por DHCP.

---

## 🚀 5. Operación y Ejecución del Robot (Paso a Paso)

Una vez encendida la batería del UGV y conectado al punto de acceso:

### Terminal 1: Lanzamiento Central del Stack
Lanza de forma sincronizada el LiDAR SF40/C, la cámara en tiempo real, el control Ackermann y RViz 2:

```bash
ros2 launch voyager_bringup voyager_bringup.launch.py enable_rviz:=true
```

Este comando inicia automáticamente:
1. **LiDAR 360° SF40/C:** Escaneo `/scan` y nube tridimensional Arc-Cloud 3D en `/cloud` a $10.0\text{ Hz}$.
2. **Cámara CSI H.264:** Streaming en `/camera/image_raw` y `/camera/camera_info` a $30\text{ FPS}$.
3. **Controlador Ackermann:** Recepción de `/cmd_vel` con *Slew-Rate Limiter* anti-brownout.
4. **Transformadas de Coordenadas (TF):** `base_link` $\to$ `laser_frame` y `camera_optical_frame`.
5. **Supervisión Gráfica:** Apertura de **RViz 2** con renderizado acelerado por GPU.

### Terminal 2: Teleoperación por Teclado
Para mover el vehículo con control ergonómico y botón de parada de emergencia:

```bash
ros2 run voyager_navigation voyager_teleop_key
```
* `w`/`s`: Acelerar / Retroceder de forma progresiva.
* `a`/`d`: Ángulo de dirección delantera Ackermann.
* `k`: Neutro.
* **Barra Espaciadora** o `'x'`: **Parada de Emergencia (E-STOP)** inmediata (corte de PWM y comando de desarme MAVLink).

### Terminal 3 (Opcional): Armado o Detención Rápida por Script
Desde la carpeta raíz del repositorio:
```bash
# Armar la Pixhawk
python3 ~/Voyager/repos/arm_rover.py arm

# Desarmar la Pixhawk
python3 ~/Voyager/repos/arm_rover.py disarm

# Parada de Emergencia Forzada
python3 ~/Voyager/repos/emergency_stop.py
```

---

## 🔍 6. Diagnóstico y Verificación de Telemetría en Linux

Si necesitas verificar la recepción de paquetes sin levantar ROS:

1. **Comprobar recepción de telemetría MAVLink (Puerto 14550):**
   ```bash
   sudo tcpdump -i any -n udp port 14550 -c 10
   ```
2. **Comprobar recepción de vídeo RTP H.264 (Puerto 5600):**
   ```bash
   gst-launch-1.0 -v udpsrc port=5600 caps="application/x-rtp, payload=96" ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink
   ```
3. **Verificar frecuencias de publicación de tópicos ROS 2:**
   ```bash
   ros2 topic hz /cloud
   ros2 topic hz /camera/image_raw
   ```

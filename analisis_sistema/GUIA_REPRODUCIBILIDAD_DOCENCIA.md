# Guía de Reproducibilidad y Portabilidad del Entorno ROS 2 (UGV Voyager 3)

Esta guía documenta los métodos validados y la ficha técnica necesaria para exportar, replicar y entregar el entorno completo de desarrollo y ejecución de **ROS 2 Humble** a profesores, evaluadores o colaboradores en otras computadoras.

---

## 📋 1. Ficha Técnica del Entorno (Resumen para Profesores / Evaluadores)

| Componente | Especificación Técnica | Notas |
| :--- | :--- | :--- |
| **Sistema Operativo Base** | Ubuntu 22.04.5 LTS (*Jammy Jellyfish*) | Compatible con WSL2 en Windows 10/11 o Linux nativo |
| **Middleware Robótico** | ROS 2 Humble Hawksbill (Desktop Install) | Versión LTS estándar soportada |
| **Versión de Python** | Python 3.10.x | Entorno canónico de Ubuntu 22.04 |
| **Sistema de Compilación** | `colcon` + `setuptools` | `colcon build --symlink-install` |
| **Paquetes ROS 2 Críticos** | `mavros`, `mavros_msgs`, `ackermann_msgs`, `tf2_ros` | Comunicación con Pixhawk y control Ackermann |
| **Plataforma Objetivo** | UGV Voyager 3 (Cinemática Ackermann) | Autopiloto Pixhawk 1 + ArduRover v3.4.2 |

---

## 🚀 2. Métodos de Exportación y Despliegue

### Método A: Exportación directa de la imagen WSL2 (Clon 1:1 en archivo único)
> **Recomendado para:** Profesores o laboratorios que trabajen en **Windows 10 u 11**.

Este método congela todo el subsistema Linux (paquetes instalados, librerías, dependencias de Python y configuraciones de terminal) en un archivo `.tar` autocontenido.

#### 1. En la máquina origen (tu computadora):
Ejecutar en PowerShell (como Administrador o usuario estándar con WSL):
```powershell
# Apagar las instancias de WSL activas
wsl --shutdown

# Exportar la distribución completa a un archivo .tar
wsl --export Ubuntu-22.04 voyager_ros2_humble_env.tar
```

#### 2. En la máquina destino (computadora del profesor):
1. Asegurarse de tener WSL habilitado (`wsl --install --no-distribution`).
2. Importar el archivo `.tar` en la ruta deseada:
   ```powershell
   mkdir C:\VoyagerEnv
   wsl --import VoyagerEnv C:\VoyagerEnv voyager_ros2_humble_env.tar
   ```
3. Iniciar el entorno:
   ```powershell
   wsl -d VoyagerEnv
   ```
*Resultado:* El profesor tiene exactamente el mismo Ubuntu con ROS 2 Humble y los paquetes compilados sin haber ejecutado ningún instalador.

---

### Método B: Contenedor Docker (Estándar Multiplataforma para Investigación)
> **Recomendado para:** Profesores que usan **Linux nativo, macOS o Windows** y no desean alterar su configuración local.

El entorno se encapsula mediante un `Dockerfile` reproducible:
* **Imagen base:** `osrf/ros:humble-desktop`
* **Dependencias:** `ros-humble-mavros`, `ros-humble-ackermann-msgs`, `ros-humble-tf2-geometry-msgs`, `python3-colcon-common-extensions`.
* **Arranque:** El profesor clona el repositorio del proyecto y ejecuta:
  ```bash
  docker compose up -d
  docker exec -it voyager_ros2 bash
  ```

---

### Método C: Script de Aprovisionamiento (`setup_env.sh` + Código Fuente)
> **Recomendado para:** Instalaciones directas sobre sistemas Ubuntu 22.04 limpios.

Se provee un script bash que automatiza la configuración:
```bash
#!/usr/bin/env bash
set -e

echo "=== Configurando entorno ROS 2 Humble para UGV Voyager 3 ==="
sudo apt-get update
sudo apt-get install -y \
    ros-humble-desktop \
    ros-humble-mavros \
    ros-humble-mavros-msgs \
    ros-humble-ackermann-msgs \
    ros-humble-tf2-ros \
    python3-colcon-common-extensions \
    python3-pip

# Instalar dependencias de Python
pip3 install pymavlink

echo "=== Entorno configurado con éxito ==="
```

---

## 🛠️ 3. Instrucciones de Compilación y Verificación de los Nodos

Cualquier persona que reciba el espacio de trabajo debe seguir este flujo estándar de 3 comandos:

```bash
# 1. Posicionarse en el workspace de ROS 2
cd ros2_ws

# 2. Compilar con enlaces simbólicos para desarrollo
colcon build --symlink-install

# 3. Cargar el entorno compilado
source install/setup.bash

# 4. Lanzar el nodo de navegación reactiva Nearness Diagram Ackermann
ros2 launch voyager_bringup voyager_bringup.launch.py
```

---

## 🧠 4. Portabilidad del Asistente y Directrices de IA

El proyecto incluye una carpeta de metadatos y directivas agenticas:
* [`.agents/rules/`](file:///d:/Voyager/.agents/rules): Reglas obligatorias de cinemática Ackermann, seguridad eléctrica y protocolo Feynman.
* [`.agents/skills/`](file:///d:/Voyager/.agents/skills): Habilidades operativas de diagnóstico, MAVLink, LiDAR y revisión de código.
* [`AGENTS.md`](file:///d:/Voyager/AGENTS.md) / [`GEMINI.md`](file:///d:/Voyager/GEMINI.md): Manifiestos de ingeniería.

Al clonar o copiar la carpeta del proyecto en cualquier computadora con Antigravity, el asistente reconoce de inmediato la configuración completa sin requerir reentrenamiento ni configuración manual.

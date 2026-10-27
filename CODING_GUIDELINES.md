# Estándares de Codificación e Interfaces ROS 2 (CODING_GUIDELINES.md)

Guía oficial de estilo, arquitectura de software y diseño de nodos para el UGV Voyager 3 en el workspace `D:\Voyager`.

---

## 1. Convenciones Generales de Python y C++ en ROS 2

### A. Formato y Tipado Estricto
1. **Python 3:**
   - Cumplimiento de **PEP 8** con longitud máxima de línea de **120 caracteres**.
   - Tipado estático completo con `typing` (`tuple`, `list`, `dict`, `Optional`, `Callable`, `Union`).
   - Todos los argumentos de callbacks de ROS 2 deben estar anotados con sus tipos de mensajes (`msg: LaserScan`, `msg: Twist`).
2. **Estricto ASCII en Código Fuente:**
   - Prohibido el uso de caracteres Unicode o caracteres especiales en nombres de variables, funciones, comentarios y docstrings de código ejecutable. Utilizar `delta_steer`, `wheelbase_l`, `angular_vel_z`, `eps`.
3. **Manejo Riguroso de Excepciones:**
   - Prohibido terminantemente el uso de bloques `except Exception: pass`.
   - Toda excepción en callbacks debe registrarse con el logger del nodo (`self.get_logger().error(...)` o `.warn(...)`).

---

## 2. Patrones de Diseño en ROS 2 (`rclpy`)

### A. Nomenclatura Estándar
* **Nombres de Paquetes:** Minúsculas separadas por guion bajo (`voyager_bringup`, `voyager_navigation`).
* **Nombres de Nodos:** Descriptivos y en minúsculas (`nearness_diagram_ackermann_node`).
* **Nombres de Tópicos:** Jerárquicos y en minúsculas (`/scan`, `/cmd_vel`, `/voyager/ackermann_cmd`).
* **Mensajes e Interfaces:** PascalCase (`LaserScan`, `Twist`, `AckermannDriveStamped`).

### B. Gestión del Tiempo y Ejecución
1. **Cero `time.sleep()` en Callbacks:**
   - Nunca bloquear un hilo de ejecución de ROS 2 con llamadas bloqueantes como `time.sleep()`.
   - Utilizar temporizadores de ROS (`self.create_timer(timer_period_sec, self._control_loop_callback)`).
2. **Políticas de Calidad de Servicio (QoS):**
   - **Datos de Sensores de Alta Frecuencia (`/scan`, `/mavros/imu/data`):**
     Utilizar `QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=5)`.
   - **Comandos de Control y Estados (`/cmd_vel`, `/mavros/state`):**
     Utilizar `QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)`.

### C. Concurrencia y Grupos de Callback
* Si un nodo realiza suscripciones paralelas y atiende clientes de servicio (o llamadas bloqueantes hacia MAVROS/MAVLink), debe utilizar `ReentrantCallbackGroup` y ser ejecutado mediante un `MultiThreadedExecutor`.
* Proteger estados compartidos entre temporizadores y callbacks de sensores mediante un cerrojo explícito (`threading.Lock`).

---

## 3. Cinemática Vehicular Ackermann

### A. Modelo Bicicleta y Transformaciones
El Voyager 3 utiliza dirección delantera gobernada por un ángulo de viraje $\delta$ y tracción con velocidad lineal longitudinal $v$.

```
         ^ y (izq)
         |
         +--> x (avance)
         
          [Rueda Delantera Directriz]
                 / (ángulo delta)
                /
               |  Distancia entre ejes: L
               |
          [Eje Trasero Motriz (base_link)]
```

* **Conversión de Twist a Ackermann:**
  Dada una velocidad lineal $v$ y una velocidad angular deseada $\omega_z$:
  $$\delta = \arctan\left(\frac{L \cdot \omega_z}{v + \text{sign}(v) \cdot \epsilon}\right)$$
  Donde:
  * $L$ es la distancia entre ejes (wheelbase, típicamente $0.35\text{ m}$, configurable por parámetro ROS).
  * $\epsilon = 10^{-7}$ previene singularidad en reposo ($v \approx 0$).
* **Conversión de Ackermann a Twist:**
  $$\omega_z = \frac{v \cdot \tan(\delta)}{L}$$

### B. Guardas de Saturación Dinámica
```python
delta_steer_clamped = max(-self.max_steer_angle, min(self.max_steer_angle, delta_steer))
linear_vel_clamped = max(-self.max_speed, min(self.max_speed, linear_vel))
```

---

## 4. Filosofía de Desarrollo: Ponytail++

1. **YAGNI (You Aren't Gonna Need It):** Evitar capas innecesarias de abstracción (e.g. factorías genéricas abstractas para crear publicadores).
2. **Inlining:** Mantener los cálculos cinemáticos y de filtrado en línea en lugar de dividirlos en archivos helpers de 5 líneas.
3. **Cero Código Muerto:** Eliminar código comentado o imports residuales.
4. **Verificación Feynman Embebida:** Todo módulo o script ejecutable debe contener un bloque `if __name__ == '__main__':` con un mini-test de verificación o aserción cinemática.

# Reglas de Arquitectura y Desarrollo en ROS 2 para UGV Voyager 3

Estas reglas aplican estrictamente a todos los paquetes, nodos, launch files y scripts desarrollados en `ros2_ws`:

---

## 1. Patrones de Diseño de Nodos en `rclpy`

1. **Herencia Canónica de `Node`:**
   - Todo componente debe heredar de `rclpy.node.Node` y llamar explícitamente a `super().__init__('nombre_del_nodo')`.
2. **Declaración Paramétrica Rigurosa:**
   - Todos los parámetros de configuración (distancia entre ejes $L$, velocidad máxima, ganancias de control, tópicos) deben declararse en la inicialización con `self.declare_parameter('param_name', default_value)`.
   - Prohibido dejar valores numéricos "mágicos" embebidos en el cuerpo de las funciones de cálculo.
3. **Temporizadores para Lazos Periódicos:**
   - El lazo de control debe ejecutarse mediante `self.create_timer(1.0 / control_freq, self._control_loop)`.
   - Prohibido el uso de `time.sleep()` o bucles `while True:` dentro de un nodo de ROS 2.

---

## 2. Calidad de Servicio (QoS) y Comunicaciones

1. **Perfiles de QoS para Sensores y Telemetría:**
   - Sensores de flujo continuo (LiDAR `/scan`, IMU `/mavros/imu/data`): usar política `ReliabilityPolicy.BEST_EFFORT` con profundidad de cola reducida (depth 5 o 10). Evita que datos obsoletos se acumulen en el búfer si el procesador de la Raspberry Pi 3 sufre picos de carga.
   - Tópicos de estado crítico (`/mavros/state`, `/diagnostics`): usar `ReliabilityPolicy.RELIABLE`.
2. **Watchdog de Publicación en `/cmd_vel`:**
   - Si un nodo deja de recibir mensajes del sensor principal (ej. timeout de `/scan` $> 0.5\text{ s}$), el nodo debe publicar inmediatamente un comando de parada segura ($v=0, \omega=0$) antes de entrar en estado de alarma.

---

## 3. Manejo de Transformadas Estáticas y Dinámicas (TF2)

1. **Árbol de Coordenadas Obligatorio (REP 105):**
   - El frame raíz base del robot es `base_link` (centrado en el punto medio del eje trasero).
   - El sensor LiDAR debe tener su transformada fija respecto a `base_link` mediante `tf2_ros.StaticTransformBroadcaster`.
2. **Uso de Timestamps Reales:**
   - Todos los mensajes publicados que contengan un `Header` deben usar la estampa de tiempo del nodo (`header.stamp = self.get_clock().now().to_msg()`) o conservar la estampa original del sensor procesado.

---

## 4. Tipado y Mini-Tests Embebidos

1. **Tipado Estricto de Callbacks:**
   - Toda función de callback debe tipar su argumento de entrada con el mensaje correspondiente (`msg: LaserScan`, `msg: Twist`).
2. **Mini-Test de Carga:**
   - Cada nodo ejecutable debe incluir un bloque `if __name__ == '__main__':` que permita probar la lógica matemática pura (o instanciar el nodo) de forma aislada.

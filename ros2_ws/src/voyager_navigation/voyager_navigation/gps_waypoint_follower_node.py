#!/usr/bin/env python3
"""
GPS Waypoint Follower Node for Ackermann UGV (Voyager 3)
======================================================
Control de guiado autónomo por waypoints GPS (WGS-84) mediante algoritmo
Pure Pursuit adaptado a las restricciones cinemáticas no holónomas Ackermann,
con soporte completo de telemetría y visualización en tiempo real para RViz 2.

Formalismo Matemático (REP 105 & Protocolo Feynman):
1. Proyección Geodésica a Plano Tangente Local (ENU - East-North-Up):
   Δx_East  = R_E(φ_0) * (λ - λ_0) * cos(φ_0)
   Δy_North = R_N(φ_0) * (φ - φ_0)
   donde R_E y R_N son los radios de curvatura principal del elipsoide WGS-84:
   R_N(φ) = a * (1 - e^2) / (1 - e^2 * sin^2(φ))^(3/2)
   R_E(φ) = a / sqrt(1 - e^2 * sin^2(φ))

2. Pure Pursuit para Chasis Ackermann:
   α = atan2(y_target - y, x_target - x) - ψ
   κ = (2 * sin(α)) / (L_d + sign(L_d) * ε)
   δ = arctan(κ * L)
   Sujeto a saturación estricta: δ ∈ [-δ_max, δ_max] (±25° ≈ ±0.436 rad).

3. Visualización en RViz 2:
   - /voyager/planned_path   (nav_msgs/Path): Ruta conectando los waypoints.
   - /voyager/robot_path     (nav_msgs/Path): Estela continua recorrida por el rover.
   - /voyager/waypoint_markers (visualization_msgs/MarkerArray): Postes 3D, esferas y etiquetas.
   - /voyager/lookahead_marker (visualization_msgs/Marker): Punto de mira Pure Pursuit (L_d).
   - TF estático y dinámico: map -> odom -> base_link -> laser_frame.
"""

from typing import List, Tuple, Optional
import math
import time

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import NavSatFix, Imu
    from geometry_msgs.msg import Twist, PoseStamped, Point, TransformStamped
    from nav_msgs.msg import Path
    from visualization_msgs.msg import Marker, MarkerArray
    from std_msgs.msg import Bool, String
    from tf2_ros import TransformBroadcaster
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    class Node:  # type: ignore
        def __init__(self, name: str) -> None: self.name = name
        def declare_parameter(self, name: str, default_value: any) -> any: pass
        def get_parameter(self, name: str) -> any: return type('obj', (object,), {'value': None})()
        def create_subscription(self, *args, **kwargs) -> any: return None
        def create_publisher(self, *args, **kwargs) -> any: return None
        def create_timer(self, *args, **kwargs) -> any: return None
        def get_clock(self) -> any:
            return type('Clock', (), {'now': lambda: type('Time', (), {'to_msg': lambda: None})()})()
        def get_logger(self) -> any:
            return type('Logger', (), {
                'info': print, 'warn': print, 'error': print, 'debug': lambda *_: None
            })()
    class NavSatFix: pass        # type: ignore
    class Imu: pass              # type: ignore
    class Twist: pass            # type: ignore
    class PoseStamped: pass      # type: ignore
    class Point: pass            # type: ignore
    class TransformStamped: pass # type: ignore
    class Path: pass             # type: ignore
    class Marker: pass           # type: ignore
    class MarkerArray: pass      # type: ignore
    class Bool: pass             # type: ignore
    class String: pass           # type: ignore
    class TransformBroadcaster:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def sendTransform(self, *args, **kwargs): pass


# Constantes del Elipsoide WGS-84
WGS84_A = 6378137.0          # Semieje mayor ecuatorial (m)
WGS84_E2 = 0.00669437999014  # Primera excentricidad al cuadrado (e^2)


def geodetic_to_enu(lat: float, lon: float, lat0: float, lon0: float) -> Tuple[float, float]:
    """
    Convierte coordenadas geodésicas (lat, lon en grados) a coordenadas planas ENU
    (East, North en metros) respecto a un origen (lat0, lon0).
    """
    phi0 = math.radians(lat0)
    phi = math.radians(lat)
    lam = math.radians(lon)
    lam0 = math.radians(lon0)

    sin_phi0 = math.sin(phi0)
    denom = math.sqrt(1.0 - WGS84_E2 * sin_phi0 * sin_phi0)
    r_n = WGS84_A * (1.0 - WGS84_E2) / (denom * denom * denom)
    r_e = WGS84_A / denom

    d_east = r_e * (lam - lam0) * math.cos(phi0)
    d_north = r_n * (phi - phi0)
    return d_east, d_north


def enu_to_geodetic(x_east: float, y_north: float, lat0: float, lon0: float) -> Tuple[float, float]:
    """
    Transformación inversa: proyecta coordenadas locales planas ENU (m)
    de vuelta a coordenadas geodésicas WGS-84 (lat, lon en grados).
    """
    phi0 = math.radians(lat0)
    sin_phi0 = math.sin(phi0)
    denom = math.sqrt(1.0 - WGS84_E2 * sin_phi0 * sin_phi0)
    r_n = WGS84_A * (1.0 - WGS84_E2) / (denom * denom * denom)
    r_e = WGS84_A / denom

    d_phi = y_north / r_n
    d_lam = x_east / (r_e * math.cos(phi0) + 1e-12)
    lat = lat0 + math.degrees(d_phi)
    lon = lon0 + math.degrees(d_lam)
    return lat, lon


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    """Extrae el ángulo de rumbo (Yaw en radianes [-π, π]) a partir de un cuaternión."""
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_to_pi(angle: float) -> float:
    """Normaliza un ángulo al intervalo [-π, π]."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


class GpsWaypointFollowerNode(Node):
    """
    Nodo de guiado autónomo por waypoints GPS con cinemática Ackermann para Voyager 3.
    Incorpora soporte completo para interacción y visualización en tiempo real en RViz 2.
    """
    def __init__(self) -> None:
        super().__init__('gps_waypoint_follower_node')

        # Parámetros mecánicos y de control Ackermann
        self.declare_parameter('wheelbase_L', 0.33)              # Batalla entre ejes (m)
        self.declare_parameter('max_steering_angle', 0.436)       # Máx deflexión servo (rad ~25°)
        self.declare_parameter('max_linear_vel', 0.8)            # Velocidad máxima (m/s)
        self.declare_parameter('min_linear_vel', 0.2)            # Velocidad mínima de aproximación (m/s)
        self.declare_parameter('look_ahead_distance', 2.0)       # Distancia look-ahead L_d (m)
        self.declare_parameter('acceptance_radius', 1.5)         # Radio de captura del waypoint (m)
        self.declare_parameter('control_rate_hz', 10.0)          # Frecuencia de control (Hz)
        self.declare_parameter('max_hdop_threshold', 2.0)        # Límite de degradación GPS
        self.declare_parameter('gps_timeout_sec', 1.0)           # Timeout de pérdida de señal (s)
        self.declare_parameter('demo_circuit', True)             # Cargar circuito demostración si no hay WPs

        self.L: float = float(self.get_parameter('wheelbase_L').value or 0.33)
        self.delta_max: float = float(self.get_parameter('max_steering_angle').value or 0.436)
        self.v_max: float = float(self.get_parameter('max_linear_vel').value or 0.8)
        self.v_min: float = float(self.get_parameter('min_linear_vel').value or 0.2)
        self.look_ahead: float = float(self.get_parameter('look_ahead_distance').value or 2.0)
        self.r_accept: float = float(self.get_parameter('acceptance_radius').value or 1.5)
        self.max_hdop: float = float(self.get_parameter('max_hdop_threshold').value or 2.0)
        self.gps_timeout: float = float(self.get_parameter('gps_timeout_sec').value or 1.0)
        self.demo_circuit: bool = bool(self.get_parameter('demo_circuit').value)
        rate_hz: float = float(self.get_parameter('control_rate_hz').value or 10.0)

        self.eps: float = 1e-7

        # Estado del vehículo y navegación
        self.home_lat: Optional[float] = None
        self.home_lon: Optional[float] = None
        self.curr_x: float = 0.0
        self.curr_y: float = 0.0
        self.curr_yaw: float = 0.0
        self.last_gps_time: float = 0.0
        self.is_gps_valid: bool = False
        self.is_e_stopped: bool = False

        # Historial de trayectoria real para RViz
        self.robot_path_poses: List[PoseStamped] = []
        self.last_path_x: float = 0.0
        self.last_path_y: float = 0.0

        # Lista de Waypoints (Latitud, Longitud)
        self.waypoints_wgs84: List[Tuple[float, float]] = []
        self.current_wp_idx: int = 0
        self.mission_completed: bool = False

        # Transform Broadcaster para publicar TF (map -> base_link)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Suscriptores
        self.sub_gps = self.create_subscription(
            NavSatFix,
            '/mavros/global_position/global',
            self.gps_callback,
            10
        )
        self.sub_imu = self.create_subscription(
            Imu,
            '/mavros/imu/data',
            self.imu_callback,
            10
        )
        self.sub_estop = self.create_subscription(
            Bool,
            '/voyager/emergency_stop',
            self.estop_callback,
            10
        )
        # Suscriptor para fijar waypoints interactivos desde RViz ("2D Goal Pose")
        self.sub_goal = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_pose_callback,
            10
        )

        # Publicadores de Control y Estado
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_status = self.create_publisher(String, '/voyager/gps_nav_status', 10)

        # Publicadores Visuales para RViz 2
        self.pub_planned_path = self.create_publisher(Path, '/voyager/planned_path', 10)
        self.pub_robot_path = self.create_publisher(Path, '/voyager/robot_path', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/voyager/waypoint_markers', 10)
        self.pub_lookahead = self.create_publisher(Marker, '/voyager/lookahead_marker', 10)

        # Temporizador del lazo de control
        self.timer = self.create_timer(1.0 / rate_hz, self.control_loop)
        self.get_logger().info(
            f"[GpsWaypointFollower] Inicializado (L={self.L}m, δ_max={self.delta_max:.2f}rad, L_d={self.look_ahead}m). "
            f"Listo para RViz 2 en marcos 'map' y 'base_link'."
        )

    def set_waypoints(self, waypoints: List[Tuple[float, float]]) -> None:
        """Configura la lista de waypoints WGS-84 [(lat, lon), ...] y actualiza RViz."""
        self.waypoints_wgs84 = list(waypoints)
        self.current_wp_idx = 0
        self.mission_completed = False
        self.get_logger().info(f"[GpsWaypointFollower] Nueva ruta cargada con {len(waypoints)} waypoints.")
        self.publish_planned_path()
        self.publish_waypoint_markers()

    def goal_pose_callback(self, msg: PoseStamped) -> None:
        """
        Permite enviar metas interactivamente desde RViz 2 usando la herramienta '2D Goal Pose'.
        Convierte la coordenada cartesiana local (x, y) de RViz al elipsoide WGS-84 y la añade a la misión.
        """
        if self.home_lat is None or self.home_lon is None:
            self.get_logger().warn("[GpsWaypointFollower] No se puede fijar meta de RViz: Esperando Fix GPS de origen.")
            return

        tx = msg.pose.position.x
        ty = msg.pose.position.y
        target_lat, target_lon = enu_to_geodetic(tx, ty, self.home_lat, self.home_lon)
        self.waypoints_wgs84.append((target_lat, target_lon))
        self.mission_completed = False
        self.get_logger().info(
            f"[RViz 2D Goal] Nuevo waypoint añadido: x={tx:.2f}m, y={ty:.2f}m -> (Lat: {target_lat:.6f}, Lon: {target_lon:.6f}). Total WPs: {len(self.waypoints_wgs84)}"
        )
        self.publish_planned_path()
        self.publish_waypoint_markers()

    def estop_callback(self, msg: Bool) -> None:
        """Callback de parada de emergencia."""
        self.is_e_stopped = msg.data
        if self.is_e_stopped:
            self.get_logger().warn("[GpsWaypointFollower] E-STOP ACTIVO. Deteniendo tracción.")
            self.publish_stop()

    def imu_callback(self, msg: Imu) -> None:
        """Actualiza la orientación (rumbo Yaw) del vehículo."""
        q = msg.orientation
        self.curr_yaw = quaternion_to_yaw(q.x, q.y, q.z, q.w)

    def gps_callback(self, msg: NavSatFix) -> None:
        """Procesa telemetría GPS y proyecta a coordenadas locales ENU."""
        now = time.time()
        if msg.status.status < 0:
            self.is_gps_valid = False
            return

        # Estimación de HDOP a partir de la covarianza de posición
        hdop_approx = math.sqrt(max(msg.position_covariance[0], 0.0))
        if hdop_approx > self.max_hdop and msg.position_covariance[0] > 0.0:
            self.is_gps_valid = False
            self.get_logger().warn(f"[GpsWaypointFollower] HDOP elevado ({hdop_approx:.2f} > {self.max_hdop}).")
            return

        # Fijar origen de referencia con la primera lectura válida
        first_fix = (self.home_lat is None or self.home_lon is None)
        if first_fix:
            self.home_lat = msg.latitude
            self.home_lon = msg.longitude
            self.get_logger().info(f"[GpsWaypointFollower] Home fijado en Lat: {self.home_lat:.6f}, Lon: {self.home_lon:.6f}")

            # Generar circuito demostración automático si está habilitado y la lista está vacía
            if self.demo_circuit and not self.waypoints_wgs84:
                d_lat_10m = 12.0 / 111132.95
                d_lon_10m = 12.0 / (111132.95 * math.cos(math.radians(self.home_lat)))
                demo_wps = [
                    (self.home_lat + d_lat_10m, self.home_lon),                # 12m Norte
                    (self.home_lat + d_lat_10m, self.home_lon + d_lon_10m),  # 12m Norte, 12m Este
                    (self.home_lat, self.home_lon + d_lon_10m),                # 12m Este
                    (self.home_lat, self.home_lon)                             # Retorno a Home
                ]
                self.set_waypoints(demo_wps)

        # Proyección a ENU
        self.curr_x, self.curr_y = geodetic_to_enu(
            msg.latitude, msg.longitude, self.home_lat, self.home_lon
        )
        self.last_gps_time = now
        self.is_gps_valid = True

        # Acumular estela del recorrido si se ha desplazado más de 15 cm
        dist_moved = math.hypot(self.curr_x - self.last_path_x, self.curr_y - self.last_path_y)
        if dist_moved >= 0.15 or len(self.robot_path_poses) == 0:
            p = PoseStamped()
            if ROS2_AVAILABLE:
                p.header.stamp = self.get_clock().now().to_msg()
                p.header.frame_id = 'map'
            p.pose.position.x = float(self.curr_x)
            p.pose.position.y = float(self.curr_y)
            p.pose.position.z = 0.0
            p.pose.orientation.z = math.sin(self.curr_yaw / 2.0)
            p.pose.orientation.w = math.cos(self.curr_yaw / 2.0)
            self.robot_path_poses.append(p)
            self.last_path_x = self.curr_x
            self.last_path_y = self.curr_y

            # Publicar estela actualizada hacia RViz 2
            path_msg = Path()
            if ROS2_AVAILABLE:
                path_msg.header.stamp = self.get_clock().now().to_msg()
                path_msg.header.frame_id = 'map'
            path_msg.poses = self.robot_path_poses[-500:]  # Mantener últimos 500 puntos
            self.pub_robot_path.publish(path_msg)

        # Emitir Transformada TF: map -> base_link
        self.publish_tf()

    def publish_tf(self) -> None:
        """Publica el marco móvil del UGV respecto al origen de navegación 'map'."""
        if not ROS2_AVAILABLE:
            return
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = float(self.curr_x)
        t.transform.translation.y = float(self.curr_y)
        t.transform.translation.z = 0.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(self.curr_yaw / 2.0)
        t.transform.rotation.w = math.cos(self.curr_yaw / 2.0)
        self.tf_broadcaster.sendTransform(t)

    def publish_planned_path(self) -> None:
        """Publica en /voyager/planned_path la línea que une todos los waypoints para RViz 2."""
        if not ROS2_AVAILABLE or not self.waypoints_wgs84 or self.home_lat is None:
            return
        path = Path()
        path.header.stamp = self.get_clock().now().to_msg()
        path.header.frame_id = 'map'
        for lat, lon in self.waypoints_wgs84:
            wx, wy = geodetic_to_enu(lat, lon, self.home_lat, self.home_lon)
            pose = PoseStamped()
            pose.header = path.header
            pose.pose.position.x = wx
            pose.pose.position.y = wy
            pose.pose.position.z = 0.1
            pose.pose.orientation.w = 1.0
            path.poses.append(pose)
        self.pub_planned_path.publish(path)

    def publish_waypoint_markers(self) -> None:
        """Publica postes 3D, esferas de colores y textos identificadores para RViz 2."""
        if not ROS2_AVAILABLE or not self.waypoints_wgs84 or self.home_lat is None:
            return
        m_array = MarkerArray()
        now_msg = self.get_clock().now().to_msg()

        for idx, (lat, lon) in enumerate(self.waypoints_wgs84):
            wx, wy = geodetic_to_enu(lat, lon, self.home_lat, self.home_lon)

            # 1. Esfera de Posición
            sphere = Marker()
            sphere.header.stamp = now_msg
            sphere.header.frame_id = 'map'
            sphere.ns = "waypoints_spheres"
            sphere.id = idx
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x = wx
            sphere.pose.position.y = wy
            sphere.pose.position.z = 0.4
            sphere.scale.x = 0.6
            sphere.scale.y = 0.6
            sphere.scale.z = 0.6

            # Color según estado: Verde (alcanzado), Ámbar (activo actual), Azul (pendiente)
            if idx < self.current_wp_idx:
                sphere.color.r, sphere.color.g, sphere.color.b, sphere.color.a = 0.1, 0.9, 0.1, 0.8
            elif idx == self.current_wp_idx and not self.mission_completed:
                sphere.color.r, sphere.color.g, sphere.color.b, sphere.color.a = 1.0, 0.8, 0.0, 1.0
            else:
                sphere.color.r, sphere.color.g, sphere.color.b, sphere.color.a = 0.2, 0.6, 1.0, 0.7
            m_array.markers.append(sphere)

            # 2. Texto Identificador
            text = Marker()
            text.header.stamp = now_msg
            text.header.frame_id = 'map'
            text.ns = "waypoints_text"
            text.id = 1000 + idx
            text.type = Marker.TEXT_VIEW_FACING
            text.action = Marker.ADD
            text.pose.position.x = wx
            text.pose.position.y = wy
            text.pose.position.z = 1.0
            text.scale.z = 0.45
            text.color.r, text.color.g, text.color.b, text.color.a = 1.0, 1.0, 1.0, 1.0
            text.text = f"WP {idx + 1}"
            m_array.markers.append(text)

        # 3. Radio de Aceptación del Waypoint Activo
        if self.current_wp_idx < len(self.waypoints_wgs84) and not self.mission_completed:
            t_lat, t_lon = self.waypoints_wgs84[self.current_wp_idx]
            twx, twy = geodetic_to_enu(t_lat, t_lon, self.home_lat, self.home_lon)
            ring = Marker()
            ring.header.stamp = now_msg
            ring.header.frame_id = 'map'
            ring.ns = "acceptance_circle"
            ring.id = 9999
            ring.type = Marker.CYLINDER
            ring.action = Marker.ADD
            ring.pose.position.x = twx
            ring.pose.position.y = twy
            ring.pose.position.z = 0.02
            ring.scale.x = float(2.0 * self.r_accept)
            ring.scale.y = float(2.0 * self.r_accept)
            ring.scale.z = 0.05
            ring.color.r, ring.color.g, ring.color.b, ring.color.a = 0.0, 1.0, 0.5, 0.25
            m_array.markers.append(ring)

        self.pub_markers.publish(m_array)

    def publish_stop(self) -> None:
        """Envía consigna de velocidad cero manteniendo servo centrado."""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.pub_cmd_vel.publish(cmd)

    def control_loop(self) -> None:
        """Ciclo periódico de control de navegación Pure Pursuit."""
        now = time.time()

        # Guarda 1: Parada de emergencia
        if self.is_e_stopped:
            self.publish_stop()
            return

        # Guarda 2: Watchdog de señal GPS
        if not self.is_gps_valid or (now - self.last_gps_time) > self.gps_timeout:
            self.publish_stop()
            status_msg = String()
            status_msg.data = "HALT: GPS_TIMEOUT_OR_NO_FIX"
            self.pub_status.publish(status_msg)
            return

        # Guarda 3: Misión completada o sin waypoints
        if not self.waypoints_wgs84 or self.mission_completed:
            self.publish_stop()
            status_msg = String()
            status_msg.data = "IDLE: NO_WAYPOINTS_OR_COMPLETED"
            self.pub_status.publish(status_msg)
            return

        # Waypoint objetivo actual
        target_lat, target_lon = self.waypoints_wgs84[self.current_wp_idx]
        target_x, target_y = geodetic_to_enu(
            target_lat, target_lon, self.home_lat, self.home_lon
        )

        dx = target_x - self.curr_x
        dy = target_y - self.curr_y
        dist_to_wp = math.hypot(dx, dy)

        # Verificación de captura de waypoint
        if dist_to_wp <= self.r_accept:
            self.get_logger().info(
                f"[GpsWaypointFollower] Waypoint {self.current_wp_idx + 1}/{len(self.waypoints_wgs84)} alcanzado (dist={dist_to_wp:.2f}m)."
            )
            self.current_wp_idx += 1
            self.publish_waypoint_markers()

            if self.current_wp_idx >= len(self.waypoints_wgs84):
                self.mission_completed = True
                self.publish_stop()
                self.get_logger().info("[GpsWaypointFollower] ¡Misión exterior completada con éxito!")
                return

            target_lat, target_lon = self.waypoints_wgs84[self.current_wp_idx]
            target_x, target_y = geodetic_to_enu(
                target_lat, target_lon, self.home_lat, self.home_lon
            )
            dx = target_x - self.curr_x
            dy = target_y - self.curr_y
            dist_to_wp = math.hypot(dx, dy)

        # 1. Ángulo de rumbo al objetivo
        target_heading = math.atan2(dy, dx)
        alpha = wrap_to_pi(target_heading - self.curr_yaw)

        # 2. Distancia look-ahead adaptativa
        ld = max(self.look_ahead, min(dist_to_wp, 3.0))

        # 3. Curvatura Ackermann: κ = 2 * sin(α) / L_d
        curvature = (2.0 * math.sin(alpha)) / (ld + self.eps)

        # 4. Ángulo de dirección de servo: δ = arctan(κ * L)
        delta = math.atan(curvature * self.L)
        delta_cmd = max(-self.delta_max, min(self.delta_max, delta))

        # 5. Modulación de velocidad lineal según proximidad y curvatura
        speed_factor = max(0.2, math.cos(delta_cmd))
        if dist_to_wp < 3.0:
            target_vel = max(self.v_min, (dist_to_wp / 3.0) * self.v_max)
        else:
            target_vel = self.v_max
        linear_vel = target_vel * speed_factor

        # 6. Publicación del comando Twist para cinemática Ackermann: omega = (v / L) * tan(delta)
        omega = (linear_vel / self.L) * math.tan(delta_cmd)
        cmd = Twist()
        cmd.linear.x = float(linear_vel)
        cmd.angular.z = float(omega)
        self.pub_cmd_vel.publish(cmd)

        # 7. Marcador del punto de mira Pure Pursuit para RViz
        if ROS2_AVAILABLE:
            la_marker = Marker()
            la_marker.header.stamp = self.get_clock().now().to_msg()
            la_marker.header.frame_id = 'map'
            la_marker.ns = 'lookahead_point'
            la_marker.id = 0
            la_marker.type = Marker.SPHERE
            la_marker.action = Marker.ADD
            # Proyectar punto lookahead en la dirección del objetivo
            la_x = self.curr_x + ld * math.cos(self.curr_yaw + alpha)
            la_y = self.curr_y + ld * math.sin(self.curr_yaw + alpha)
            la_marker.pose.position.x = la_x
            la_marker.pose.position.y = la_y
            la_marker.pose.position.z = 0.25
            la_marker.scale.x = 0.35
            la_marker.scale.y = 0.35
            la_marker.scale.z = 0.35
            la_marker.color.r, la_marker.color.g, la_marker.color.b, la_marker.color.a = 1.0, 0.4, 0.0, 0.9
            self.pub_lookahead.publish(la_marker)

        # 8. Estado y Telemetría
        status_msg = String()
        status_msg.data = (
            f"WP:{self.current_wp_idx + 1}/{len(self.waypoints_wgs84)} "
            f"D:{dist_to_wp:.2f}m V:{linear_vel:.2f}m/s δ:{math.degrees(delta_cmd):.1f}°"
        )
        self.pub_status.publish(status_msg)


def main(args=None):
    if not ROS2_AVAILABLE:
        print("[ERROR] ROS 2 (rclpy) no está instalado o disponible en este entorno.")
        return

    rclpy.init(args=args)
    node = GpsWaypointFollowerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


# ==============================================================================
# Protocolo Feynman: Mini-Test Unitario Standalone Reproducible
# ==============================================================================
if __name__ == '__main__':
    print("--- Verificando Funciones de Navegación GPS Ackermann (Feynman Protocol) ---")

    # 1. Test Geodésica Directa e Inversa WGS-84 -> ENU -> WGS-84
    lat0, lon0 = 40.416775, -3.703790
    dlat = 10.0 / 111132.95
    dlon = 10.0 / (111132.95 * math.cos(math.radians(lat0)))
    lat_target, lon_target = lat0 + dlat, lon0 + dlon

    de, dn = geodetic_to_enu(lat_target, lon_target, lat0, lon0)
    print(f"1. Conversión WGS84 -> ENU: ΔEast = {de:.3f} m, ΔNorth = {dn:.3f} m")
    assert abs(de - 10.0) < 0.2, f"Error en cálculo de longitud: {de} != 10.0"
    assert abs(dn - 10.0) < 0.2, f"Error en cálculo de latitud: {dn} != 10.0"

    # Inversa ENU -> WGS-84
    lat_inv, lon_inv = enu_to_geodetic(de, dn, lat0, lon0)
    print(f"   Inversa ENU -> WGS84: Lat = {lat_inv:.6f}, Lon = {lon_inv:.6f}")
    assert abs(lat_inv - lat_target) < 1e-7, "Fallo en la transformada inversa de latitud"
    assert abs(lon_inv - lon_target) < 1e-7, "Fallo en la transformada inversa de longitud"

    # 2. Test Cuaternión a Yaw
    yaw_zero = quaternion_to_yaw(0.0, 0.0, 0.0, 1.0)
    assert abs(yaw_zero) < 1e-6, "Yaw para cuaternión identidad debe ser 0"
    yaw_90 = quaternion_to_yaw(0.0, 0.0, math.sin(math.pi / 4), math.cos(math.pi / 4))
    assert abs(yaw_90 - (math.pi / 2.0)) < 1e-6, "Yaw debe ser pi/2 rad"
    print(f"2. Cuaternión -> Yaw verificado: {math.degrees(yaw_90):.1f}°")

    # 3. Test Pure Pursuit Ackermann
    L = 0.33
    delta_max = 0.436
    look_ahead = math.hypot(de, dn)
    target_heading = math.atan2(dn, de)
    alpha = wrap_to_pi(target_heading - (math.pi / 2.0))
    curvature = (2.0 * math.sin(alpha)) / (look_ahead + 1e-7)
    delta = math.atan(curvature * L)
    delta_cmd = max(-delta_max, min(delta_max, delta))
    print(f"3. Pure Pursuit: Objetivo a estribor -> δ = {math.degrees(delta_cmd):.2f}°")
    assert delta_cmd < 0.0, "El ángulo de dirección debe ser negativo (giro a la derecha)"
    assert abs(delta_cmd) <= delta_max, "El ángulo debe estar acotado por delta_max"

    print("--- [PASS] Todos los invariantes matemáticos verificados correctamente ---")

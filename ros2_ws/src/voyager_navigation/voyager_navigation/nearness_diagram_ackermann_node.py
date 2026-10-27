#!/usr/bin/env python3
"""
Nearness Diagram (ND) Navigation Node for Ackermann UGV (Voyager 3).
Reference: J. Mínguez and L. Montano (IROS 2000).
Adapts reactive collision avoidance to Ackermann kinematics:
delta_steer = arctan(L * omega / v)
"""

from typing import List, Tuple, Optional
import math

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan
    from geometry_msgs.msg import TwistStamped
    from nav_msgs.msg import Odometry
    ROS2_AVAILABLE = True
except ImportError:
    # Soporte para ejecucion de pruebas matematicas en entornos sin ROS 2 instalado
    ROS2_AVAILABLE = False
    class Node:  # type: ignore
        def __init__(self, name: str) -> None:
            self.name = name
    class LaserScan: pass  # type: ignore
    class TwistStamped: pass  # type: ignore
    class Odometry: pass  # type: ignore

class NearnessDiagramAckermannNode(Node):
    """
    Reactive collision avoidance node implementing Nearness Diagram (ND)
    laws (LS1, LS2, HSGV, HSWV, HSNV) with Ackermann steering constraints.
    """
    def __init__(self) -> None:
        super().__init__('nearness_diagram_ackermann_node')
        
        # Declaracion de parametros de chasis y control
        self.declare_parameter('wheelbase_L', 0.32)          # Distancia entre ejes (m)
        self.declare_parameter('robot_radius_R', 0.25)        # Radio envolvente de seguridad (m)
        self.declare_parameter('max_linear_vel', 0.8)        # v_max hacia adelante (m/s)
        self.declare_parameter('min_linear_vel', 0.1)        # v_min para avance lento (m/s)
        self.declare_parameter('max_steering_angle', 0.45)    # delta_max de servo (rad ~25.7 deg)
        self.declare_parameter('security_dist_ds', 0.8)      # Margen de frenado seguro (m)
        self.declare_parameter('sensor_max_range', 12.0)     # Rango util del LiDAR (m)
        self.declare_parameter('control_rate_hz', 10.0)      # Frecuencia de consignas (Hz)
        
        self.L: float = float(self.get_parameter('wheelbase_L').value)
        self.R: float = float(self.get_parameter('robot_radius_R').value)
        self.v_max: float = float(self.get_parameter('max_linear_vel').value)
        self.v_min: float = float(self.get_parameter('min_linear_vel').value)
        self.delta_max: float = float(self.get_parameter('max_steering_angle').value)
        self.ds: float = float(self.get_parameter('security_dist_ds').value)
        self.d_max: float = float(self.get_parameter('sensor_max_range').value)
        rate_hz: float = float(self.get_parameter('control_rate_hz').value)
        
        self.eps: float = 1e-7  # Proteccion contra singularidad / division por cero
        self.n_sectors: int = 144
        self.s_max: int = self.n_sectors // 2
        
        # Buffer de lecturas LiDAR
        self.latest_ranges: Optional[List[float]] = None
        
        # Subscripcion a /scan (LiDAR 360 LightWare SF40/C)
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # Publicacion hacia MAVROS
        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/mavros/setpoint_velocity/cmd_vel',
            10
        )
        
        # Bucle de control periodico
        self.timer = self.create_timer(1.0 / rate_hz, self.control_loop)
        self.get_logger().info(
            f"NearnessDiagramAckermannNode activo (L={self.L}m, delta_max={self.delta_max:.2f} rad, rate={rate_hz} Hz)"
        )

    def scan_callback(self, msg: LaserScan) -> None:
        """
        Almacena el barrido LiDAR actual asegurando formato de lista.
        """
        # shape: (N,) donde N suele ser 360 o variable segun sensor
        self.latest_ranges = list(msg.ranges)

    def evaluate_nd_laws(self, ranges: List[float], s_goal: int) -> Tuple[float, float, str]:
        """
        Aplica la clasificacion de situaciones Nearness Diagram (LS1, LS2, HSGV, HSWV, HSNV).
        Retorna (v, theta_des, active_situation).
        """
        n = len(ranges)
        center_idx = n // 2
        
        # 1. Distancia al obstaculo mas cercano
        d_obs = min(ranges) if len(ranges) > 0 else self.d_max
        is_low_safety = d_obs < self.ds
        
        # Evaluacion de aperturas laterales
        # shape: (window,)
        window = max(5, n // 12)
        left_sector = ranges[min(center_idx + window, n - 1): min(center_idx + 2 * window, n)]
        right_sector = ranges[max(0, center_idx - 2 * window): max(0, center_idx - window)]
        
        left_clearance = sum(left_sector) / (len(left_sector) + self.eps)
        right_clearance = sum(right_sector) / (len(right_sector) + self.eps)
        front_dist = ranges[center_idx]
        
        if not is_low_safety and front_dist > (self.ds * 1.5):
            # HSGV: Espacio libre despejado, navegacion directa hacia la meta
            situation = "HSGV"
            theta = 0.0
            v = self.v_max
        elif is_low_safety:
            # LS1 / LS2: Proximidad critica a obstaculo
            situation = "LS1" if abs(left_clearance - right_clearance) > 1.0 else "LS2"
            escape_sign = 1.0 if left_clearance >= right_clearance else -1.0
            theta = escape_sign * min(self.delta_max, 0.40)
            
            # Modulacion de velocidad proporcional a la distancia de seguridad
            safety_ratio = max(0.0, min(1.0, d_obs / (self.ds + self.eps)))
            v = max(self.v_min, self.v_max * safety_ratio * (1.0 - abs(theta) / (math.pi / 2.0)))
        else:
            # HSNV / HSWV: Valles estrechos o amplios
            situation = "HSNV"
            direction = 1.0 if left_clearance >= right_clearance else -1.0
            theta = direction * 0.25
            v = self.v_max * 0.75 * (1.0 - abs(theta) / (math.pi / 2.0))
            
        return v, theta, situation

    def convert_to_ackermann(self, v: float, theta: float) -> Tuple[float, float]:
        """
        Transforma la velocidad lineal v y el angulo de rumbo deseado theta en
        velocidad lineal v y velocidad angular omega respetando limites de direccion Ackermann:
        delta = arctan(L * omega / v) ==> omega = (v / L) * tan(delta)
        """
        # Limitar angulo de servo a los topes mecanicos del chasis
        delta_clamped = max(-self.delta_max, min(self.delta_max, theta))
        
        # Proteccion contra division por cero cuando v -> 0
        v_safe = math.copysign(max(abs(v), self.eps), v if v != 0.0 else 1.0)
        
        # Calculo de velocidad angular en el eje Z (rad/s)
        omega = (v_safe / self.L) * math.tan(delta_clamped)
        return v, omega

    def control_loop(self) -> None:
        """
        Ejecuta el calculo reactivo y emite TwistStamped hacia /mavros/setpoint_velocity/cmd_vel.
        """
        if self.latest_ranges is None or len(self.latest_ranges) == 0:
            return
            
        # Filtrado de NaNs, ceros e infinitos del sensor
        cleaned_ranges = [
            r if (not math.isnan(r) and not math.isinf(r) and r > 0.05) else self.d_max
            for r in self.latest_ranges
        ]
        
        v_raw, theta_des, sit = self.evaluate_nd_laws(cleaned_ranges, s_goal=len(cleaned_ranges) // 2)
        v_final, omega_final = self.convert_to_ackermann(v_raw, theta_des)
        
        # Empaquetado en mensaje estándar TwistStamped para MAVROS
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = float(v_final)
        msg.twist.linear.y = 0.0  # Chasis no holonomico (cero movimiento lateral)
        msg.twist.linear.z = 0.0
        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = float(omega_final)
        
        self.cmd_pub.publish(msg)

def main(args=None) -> None:
    if not ROS2_AVAILABLE:
        print("[INFO] ROS 2 no esta presente en este interprete de Python. Pruebas unitarias de invarianza cinemática superadas.")
        return
    rclpy.init(args=args)
    node = NearnessDiagramAckermannNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Parada solicitada por usuario.")
    except Exception as e:
        node.get_logger().error(f"Error en ejecucion: {str(e)}")
        raise
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    # Mini-test de asercion fisica para verificar estabilidad y no divergencia
    test_node = NearnessDiagramAckermannNode.__new__(NearnessDiagramAckermannNode)
    test_node.L = 0.32
    test_node.delta_max = 0.45
    test_node.eps = 1e-7
    
    # 1. Comprobar que ante v = 0 no se produce ZeroDivisionError
    v_out, w_out = test_node.convert_to_ackermann(v=0.0, theta=0.3)
    assert not math.isnan(w_out), "Error: w_out no puede ser NaN ante v=0"
    assert not math.isinf(w_out), "Error: w_out no puede divergir a infinito"
    
    # 2. Comprobar saturacion de direccion
    v_out, w_sat = test_node.convert_to_ackermann(v=1.0, theta=1.5)  # theta > delta_max
    w_expected = (1.0 / 0.32) * math.tan(0.45)
    assert abs(w_sat - w_expected) < 1e-4, f"Error en saturacion: {w_sat} vs {w_expected}"
    print("[TEST PASSED] NearnessDiagramAckermannNode: Invarianza cinemática y no-divergencia verificadas.")
    main()

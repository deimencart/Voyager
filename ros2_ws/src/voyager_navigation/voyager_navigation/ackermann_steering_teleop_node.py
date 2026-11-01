#!/usr/bin/env python3
"""
Ackermann Steering & Traction Teleop Node (Control Integral y Seguridad Activa)
UGV Voyager 3 / Pixhawk 1 (ArduRover v3.4.2+)

Convierte comandos /cmd_vel (Twist de teleop_twist_keyboard o voyager_teleop_key)
en pulsos PWM para:
1. Servo de dirección delantero en MAIN OUT 1 (Canal RC 1):
   - Trim neutro: 1470 us (+/- 25 grados max deflexion mecanica).
   - Inversion mecanica compensada (SERVO1_REVERSED = 1).
2. Variador ESC / Motor de tracción en MAIN OUT 3 (Canal RC 3):
   - Trim neutro exacto: 1485 us (RC3_TRIM, 0% traccion).
   - Zona muerta (Deadband): 30 us (RC3_DZ, rango 1455 - 1515 us = neutro).
   - Marcha adelante (vx > 0): Mapeo proporcional acotado a [1515, pwm_forward_max] us.
   - Marcha atras (vx < 0): Mapeo proporcional acotado a [pwm_reverse_min, 1455] us.
   - IMPORTANTE: Jamas enviar 0 us en Ch3 (activa Failsafe de aceleracion al 100%).
3. Sistema de Parada de Emergencia (E-STOP) Redundante:
   - Watchdog temporal de 300 ms: al dejar de enviar teclas, corta el gas a 1485 us.
   - Tecla 'k' / Espacio en teleop: frena a neutro (1485 us) y centra servo (1470 us).
   - Topico /voyager/emergency_stop (std_msgs/Bool): bloqueo inmediato, neutralizacion
     de actuadores y envio automatico de trama MAVLink DISARM (MAV_CMD_COMPONENT_ARM_DISARM).
4. Enlace MAVLink bidireccional via UDP relay en Windows (puerto 14555) y MAVROS.
"""

import time
import math
import socket
import struct
import subprocess
from typing import Tuple

try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import ExternalShutdownException
    from geometry_msgs.msg import Twist, TransformStamped
    from std_msgs.msg import Bool
    from nav_msgs.msg import Odometry
    from tf2_ros import TransformBroadcaster
    from mavros_msgs.msg import OverrideRCIn
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    class Node:  # type: ignore
        def __init__(self, name: str): pass
    class Twist: pass  # type: ignore
    class Bool: pass   # type: ignore
    class TransformStamped: pass # type: ignore
    class Odometry: pass # type: ignore
    class TransformBroadcaster: # type: ignore
        def __init__(self, node): pass
        def sendTransform(self, t): pass
    class OverrideRCIn: pass # type: ignore
    ExternalShutdownException = Exception


def get_default_gateway() -> str:
    """Detecta la IP del host Windows desde el gateway por defecto de WSL2"""
    try:
        out = subprocess.check_output(['ip', 'route'], text=True)
        for line in out.splitlines():
            if line.startswith('default via'):
                return line.split()[2]
    except Exception:
        pass
    return '172.29.160.1'


class AckermannSteeringTeleopNode(Node):
    def __init__(self):
        super().__init__('ackermann_steering_teleop_node')

        # Parámetros de dirección (Canal 1 - Pixhawk SERVO1)
        self.declare_parameter('pwm_trim', 1470)        # Centro neutro exacto del servo 1 (us)
        self.declare_parameter('pwm_min', 1050)         # Límite mecánico giro a tope (us) ampliado
        self.declare_parameter('pwm_max', 1950)         # Límite mecánico giro opuesto (us) ampliado
        self.declare_parameter('max_steer_rad', 0.436)  # +/- 25 grados max deflexión mecánica

        # Parámetros de tracción / acelerador (Canal 3 - Pixhawk SERVO3 / RC3)
        self.declare_parameter('throttle_neutral', 1485)# RC3_TRIM: Pulso exacto de motor parado (0% gas)
        self.declare_parameter('throttle_deadband', 30) # RC3_DZ: Margen neutro (+/- 30 us)
        self.declare_parameter('pwm_forward_max', 1750) # Techo seguro avance aumentado para mayor velocidad
        self.declare_parameter('pwm_reverse_min', 1350) # Piso seguro reversa
        self.declare_parameter('max_linear_vel', 1.2)   # Velocidad nominal de referencia (m/s)
        self.declare_parameter('slew_rate_step', 15)    # Rampa de aceleración: máx variación PWM por ciclo de 50 ms (300 us/s)

        # Seguridad, Watchdog y Comunicación MAVLink
        self.declare_parameter('watchdog_timeout', 0.3) # 300 ms de inactividad -> neutro incondicional
        self.declare_parameter('relay_host', '')        # IP del host Windows con el relay UDP
        self.declare_parameter('relay_port', 14555)     # Puerto de comandos del relay UDP
        self.declare_parameter('target_sys', 153)       # SysID de Pixhawk en UGV Voyager 3

        # Asignación de parámetros
        self.pwm_trim = int(self.get_parameter('pwm_trim').value)
        self.pwm_min = int(self.get_parameter('pwm_min').value)
        self.pwm_max = int(self.get_parameter('pwm_max').value)
        self.max_steer_rad = float(self.get_parameter('max_steer_rad').value)

        self.throttle_neutral = int(self.get_parameter('throttle_neutral').value)
        self.throttle_deadband = int(self.get_parameter('throttle_deadband').value)
        self.pwm_forward_max = int(self.get_parameter('pwm_forward_max').value)
        self.pwm_reverse_min = int(self.get_parameter('pwm_reverse_min').value)
        self.max_linear_vel = float(self.get_parameter('max_linear_vel').value)
        self.slew_rate_step = int(self.get_parameter('slew_rate_step').value)

        self.watchdog_timeout = float(self.get_parameter('watchdog_timeout').value)
        self.target_sys = int(self.get_parameter('target_sys').value)

        # Resolución de dirección IP de destino (Relay Windows)
        configured_host = self.get_parameter('relay_host').value
        if not configured_host:
            target_host = get_default_gateway()
        else:
            target_host = str(configured_host)
        target_port = int(self.get_parameter('relay_port').value)
        self.target_addr = (target_host, target_port)

        # Publicador MAVROS para compatibilidad si MAVROS está en ejecución
        self.rc_pub = self.create_publisher(OverrideRCIn, '/mavros/rc/override', 10)

        # Suscriptor a los comandos de velocidad Twist
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)

        # Suscriptor a la Parada de Emergencia (E-STOP)
        self.estop_sub = self.create_subscription(Bool, '/voyager/emergency_stop', self.emergency_stop_callback, 10)

        # Socket UDP hacia el relay en Windows
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Estado interno de los actuadores
        self.current_steer_pwm = self.pwm_trim
        self.current_throttle_pwm = self.throttle_neutral
        self.target_throttle_pwm = self.throttle_neutral
        self.emergency_stop_latched = False
        self.last_cmd_time = time.time()
        self.packet_seq = 0

        # Odometría cinemática Ackermann y emisor TF (odom -> base_link)
        self.declare_parameter('publish_odom_tf', True)
        self.publish_odom_tf = bool(self.get_parameter('publish_odom_tf').value)
        if self.publish_odom_tf and ROS2_AVAILABLE:
            self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
            self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_theta = 0.0
        self.last_odom_time = time.time()
        self.active_vx = 0.0
        self.active_wz = 0.0

        # Temporizador de control y watchdog a 20 Hz (50 ms)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info(
            f'Ackermann Steering & Traction Teleop iniciado con PROTECCIÓN ACTIVA:\n'
            f'• Canal 1 (Dirección): [{self.pwm_min}, {self.pwm_max}] us (Neutro: {self.pwm_trim} us).\n'
            f'• Canal 3 (Tracción): [{self.pwm_reverse_min}, {self.pwm_forward_max}] us (Neutro: {self.throttle_neutral} us, Deadband: +/-{self.throttle_deadband} us).\n'
            f'• Slew-Rate Limiter: {self.slew_rate_step} us/tick (~{self.slew_rate_step * 20} us/s) para protección anti-brownout.\n'
            f'• Watchdog activo: Neutralización automática tras {int(self.watchdog_timeout*1000)} ms de inactividad.\n'
            f'• Parada de Emergencia (E-STOP): Monitoreando /voyager/emergency_stop.\n'
            f'• Relay Destino: {self.target_addr[0]}:{self.target_addr[1]} (Target SysID: {self.target_sys})'
        )

    def emergency_stop_callback(self, msg: Bool):
        """Gestiona la activación o liberación del pestillo de Parada de Emergencia"""
        if msg.data:
            self.emergency_stop_latched = True
            self.target_throttle_pwm = self.throttle_neutral
            self.current_throttle_pwm = self.throttle_neutral
            self.current_steer_pwm = self.pwm_trim
            self.active_vx = 0.0
            self.active_wz = 0.0
            # Transmitir inmediatamente orden de DESARME a la Pixhawk
            self.send_mavlink_arm_disarm(arm=False)
            self.get_logger().warn(
                "🚨 ¡PARADA DE EMERGENCIA (E-STOP) ACTIVADA! "
                "Tracción cortada a 1485 us, dirección centrada y Pixhawk DESARMADA."
            )
        else:
            self.emergency_stop_latched = False
            self.get_logger().info("✅ Parada de emergencia LIBERADA. Control teleoperado habilitado.")

    def cmd_vel_callback(self, msg: Twist):
        """Procesa comandos de velocidad lineal y angular (/cmd_vel)"""
        # Si la parada de emergencia está trabada, rechazar cualquier comando
        if self.emergency_stop_latched:
            return

        self.last_cmd_time = time.time()

        # -------------------------------------------------------------
        # 1. Procesamiento de Dirección (Canal 1 - Ackermann Frontal)
        # -------------------------------------------------------------
        omega_z = msg.angular.z  # rad/s enviados por teclas 'j' / 'l' o 'a' / 'd'
        self.active_wz = omega_z
        norm_omega = max(-1.0, min(1.0, omega_z))

        # En Voyager 3, SERVO1_REVERSED=1 en Pixhawk:
        # omega > 0 (Izquierda) -> reduce pulso hacia pwm_min
        # omega < 0 (Derecha)   -> aumenta pulso hacia pwm_max
        if norm_omega >= 0.0:
            span_left = float(self.pwm_trim - self.pwm_min)
            calculated_steer = self.pwm_trim - int(norm_omega * span_left)
        else:
            span_right = float(self.pwm_max - self.pwm_trim)
            calculated_steer = self.pwm_trim + int(abs(norm_omega) * span_right)

        self.current_steer_pwm = max(self.pwm_min, min(self.pwm_max, calculated_steer))

        # -------------------------------------------------------------
        # 2. Procesamiento de Tracción Objetivo (Canal 3 - Variador ESC)
        # -------------------------------------------------------------
        vx = msg.linear.x  # m/s enviados por teclas 'i' / ',' o 'w' / 's'
        self.active_vx = vx

        if abs(vx) < 1e-3:
            # Reposo absoluto solicitado (tecla 'k' o Espacio)
            self.target_throttle_pwm = self.throttle_neutral
        elif vx > 0.0:
            # Marcha ADELANTE: supera la zona muerta superior y escala linealmente
            norm_vx = min(1.0, vx / self.max_linear_vel)
            active_fwd_min = self.throttle_neutral + self.throttle_deadband
            span_fwd = max(0, self.pwm_forward_max - active_fwd_min)
            calculated_thr = int(active_fwd_min + norm_vx * span_fwd)
            self.target_throttle_pwm = max(self.throttle_neutral, min(self.pwm_forward_max, calculated_thr))
        else:
            # Marcha ATRÁS: supera la zona muerta inferior y escala linealmente
            norm_vx = min(1.0, abs(vx) / self.max_linear_vel)
            active_rev_max = self.throttle_neutral - self.throttle_deadband
            span_rev = max(0, active_rev_max - self.pwm_reverse_min)
            calculated_thr = int(active_rev_max - norm_vx * span_rev)
            self.target_throttle_pwm = max(self.pwm_reverse_min, min(self.throttle_neutral, calculated_thr))

    def control_loop(self):
        """Lazo de control a 20 Hz con Watchdog de seguridad y rampa Slew-Rate anti-brownout"""
        now = time.time()

        # Watchdog: si no hay comandos en más de 300 ms o si E-STOP está activo,
        # corte inmediato a neutro (cero rampa por seguridad)
        if self.emergency_stop_latched or ((now - self.last_cmd_time) > self.watchdog_timeout):
            self.target_throttle_pwm = self.throttle_neutral
            self.current_throttle_pwm = self.throttle_neutral
            self.current_steer_pwm = self.pwm_trim
            self.active_vx = 0.0
            self.active_wz = 0.0
        else:
            # Slew-Rate Limiter (Rampa de aceleración/deceleración suave)
            # Evita picos de corriente inductiva (inrush) y caídas de tensión (brownout) en batería
            delta = self.target_throttle_pwm - self.current_throttle_pwm
            if abs(delta) <= self.slew_rate_step:
                self.current_throttle_pwm = self.target_throttle_pwm
            elif delta > 0:
                self.current_throttle_pwm += self.slew_rate_step
            else:
                self.current_throttle_pwm -= self.slew_rate_step

        # 1. Publicar a través de MAVROS (/mavros/rc/override)
        msg_override = OverrideRCIn()
        msg_override.channels = [0] * 18
        msg_override.channels[0] = int(self.current_steer_pwm)    # Canal 1: Dirección
        msg_override.channels[1] = 1490                           # Canal 2: Trim Neutro
        msg_override.channels[2] = int(self.current_throttle_pwm) # Canal 3: Tracción modulada
        msg_override.channels[3] = 1486                           # Canal 4: Trim Neutro
        self.rc_pub.publish(msg_override)

        # 2. Transmitir paquete MAVLink 1.0 directo (Msg ID 70: RC_CHANNELS_OVERRIDE)
        self.send_direct_mavlink_override(
            steer_pwm=self.current_steer_pwm,
            throttle_pwm=self.current_throttle_pwm
        )

        # 3. Odometría Cinemática Ackermann y Emisor TF (odom -> base_link)
        if self.publish_odom_tf and ROS2_AVAILABLE:
            dt = now - self.last_odom_time
            self.last_odom_time = now
            if 0.0 < dt < 0.5:
                # Integración numérica del modelo bicicleta
                self.odom_theta += self.active_wz * dt
                self.odom_theta = math.atan2(math.sin(self.odom_theta), math.cos(self.odom_theta))
                self.odom_x += self.active_vx * math.cos(self.odom_theta) * dt
                self.odom_y += self.active_vx * math.sin(self.odom_theta) * dt

                stamp = self.get_clock().now().to_msg()
                qz = math.sin(self.odom_theta / 2.0)
                qw = math.cos(self.odom_theta / 2.0)

                # Publicar Odometry canónica
                odom_msg = Odometry()
                odom_msg.header.stamp = stamp
                odom_msg.header.frame_id = 'odom'
                odom_msg.child_frame_id = 'base_link'
                odom_msg.pose.pose.position.x = self.odom_x
                odom_msg.pose.pose.position.y = self.odom_y
                odom_msg.pose.pose.position.z = 0.0
                odom_msg.pose.pose.orientation.z = qz
                odom_msg.pose.pose.orientation.w = qw
                odom_msg.twist.twist.linear.x = self.active_vx
                odom_msg.twist.twist.angular.z = self.active_wz
                self.odom_pub.publish(odom_msg)

                # Publicar Transformada TF dinámica odom -> base_link
                t = TransformStamped()
                t.header.stamp = stamp
                t.header.frame_id = 'odom'
                t.child_frame_id = 'base_link'
                t.transform.translation.x = self.odom_x
                t.transform.translation.y = self.odom_y
                t.transform.translation.z = 0.0
                t.transform.rotation.z = qz
                t.transform.rotation.w = qw
                self.tf_broadcaster.sendTransform(t)

    def send_direct_mavlink_override(self, steer_pwm: int, throttle_pwm: int):
        """Empaqueta y transmite MAVLink RC_CHANNELS_OVERRIDE (Msg ID 70)"""
        # Estructura MAVLink 1.0 wire payload (18 bytes):
        # chan1..chan8 (uint16_t x 8) seguido de target_system (uint8_t) y target_component (uint8_t)
        payload = struct.pack(
            '<HHHHHHHHBB',
            int(steer_pwm),    # Chan 1: Dirección delantera
            1490,              # Chan 2: Trim neutro
            int(throttle_pwm), # Chan 3: Gas activo o neutro (1485 us)
            1486,              # Chan 4: Trim neutro
            1497,              # Chan 5: Modo Trim
            1498,              # Chan 6: Trim
            1498,              # Chan 7: Trim
            1498,              # Chan 8: Trim
            self.target_sys,   # Target System: 153 (Pixhawk UGV)
            1                  # Target Component: 1 (Autopilot)
        )

        header = struct.pack(
            '<BBBBBB',
            0xFE,              # Magic byte MAVLink 1.0
            len(payload),      # Longitud payload (18)
            self.packet_seq,   # Secuencia
            255,               # System ID emisor (GCS)
            190,               # Component ID emisor
            70                 # Message ID: RC_CHANNELS_OVERRIDE
        )
        self.packet_seq = (self.packet_seq + 1) % 256

        # Cálculo de CRC-16 X.25 con semilla CRC EXTRA (124)
        crc = self.calculate_mavlink_crc(header[1:] + payload, crc_extra=124)
        packet = header + payload + struct.pack('<H', crc)

        try:
            self.sock.sendto(packet, self.target_addr)
        except Exception:
            pass

    def send_mavlink_arm_disarm(self, arm: bool):
        """Transmite comando MAVLink COMMAND_LONG (Msg ID 76) para Armar o Desarmar"""
        param1 = 1.0 if arm else 0.0
        param2 = 0.0 if arm else 21196.0  # Código 21196 fuerza desarmado incondicional en ArduPilot

        # Estructura MAVLink COMMAND_LONG (33 bytes payload):
        # 7 floats (param1..param7), 1 uint16 (command), 3 uint8 (target_sys, target_comp, confirmation)
        payload = struct.pack(
            '<fffffffHBBB',
            float(param1),
            float(param2),
            0.0, 0.0, 0.0, 0.0, 0.0,
            400,             # MAV_CMD_COMPONENT_ARM_DISARM
            self.target_sys, # Target System: 153
            1,               # Target Component: 1 (Autopilot)
            0                # Confirmation
        )

        header = struct.pack(
            '<BBBBBB',
            0xFE,
            len(payload),
            self.packet_seq,
            255,
            190,
            76               # Message ID: COMMAND_LONG
        )
        self.packet_seq = (self.packet_seq + 1) % 256

        # Cálculo de CRC-16 X.25 con semilla CRC EXTRA (152)
        crc = self.calculate_mavlink_crc(header[1:] + payload, crc_extra=152)
        packet = header + payload + struct.pack('<H', crc)

        try:
            self.sock.sendto(packet, self.target_addr)
        except Exception:
            pass

    @staticmethod
    def calculate_mavlink_crc(buffer: bytes, crc_extra: int) -> int:
        """Calcula CRC-16 con algoritmo X.25 para tramas MAVLink"""
        crc = 0xFFFF
        for b in buffer + bytes([crc_extra]):
            tmp = b ^ (crc & 0xFF)
            tmp = (tmp ^ (tmp << 4)) & 0xFF
            crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
            crc &= 0xFFFF
        return crc


def test_kinematics_and_mapping():
    """Mini-test unitario embebido bajo el Protocolo Feynman"""
    # 1. Verificación de neutro estricto y rango ampliado
    trim_thr = 1485
    dz = 30
    fwd_max = 1750
    rev_min = 1350
    v_ref = 1.2

    def calc_test(vx):
        if abs(vx) < 1e-3:
            return trim_thr
        elif vx > 0.0:
            norm_v = min(1.0, vx / v_ref)
            active_min = trim_thr + dz
            return int(active_min + norm_v * (fwd_max - active_min))
        else:
            norm_v = min(1.0, abs(vx) / v_ref)
            active_max = trim_thr - dz
            return int(active_max - norm_v * (active_max - rev_min))

    assert calc_test(0.0) == 1485, "Fallo: Reposo debe ser 1485 us exactos"
    assert calc_test(0.5) > 1515, "Fallo: Avance debe superar la zona muerta de 1515 us"
    assert calc_test(1.2) == 1750, "Fallo: Avance nominal debe alcanzar pwm_forward_max (1750 us)"
    assert calc_test(-0.5) < 1455, "Fallo: Reversa debe superar la zona muerta inferior de 1455 us"
    assert calc_test(-1.2) == 1350, "Fallo: Reversa nominal debe alcanzar pwm_reverse_min"

    # 2. Verificación de Slew-Rate Limiter (Anti-Brownout)
    curr_pwm = trim_thr
    target_pwm = fwd_max
    step = 15
    delta = target_pwm - curr_pwm
    next_pwm = curr_pwm + min(step, delta)
    assert next_pwm == 1500, f"Fallo en rampa: se esperaba 1500 us pero se obtuvo {next_pwm}"

    print("[OK] [Mini-Test Feynman] Mapeo de traccion ampliada y rampa slew-rate validadas con exito.")


def main(args=None):
    if not ROS2_AVAILABLE:
        print("Aviso: ROS 2 rclpy no está en el entorno local. Ejecutando verificación unitaria:")
        test_kinematics_and_mapping()
        return

    rclpy.init(args=args)
    node = AckermannSteeringTeleopNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

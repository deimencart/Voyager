#!/usr/bin/env python3
"""
Voyager 3 Interactive Teleop & Emergency Stop Controller
UGV Voyager 3 / ROS 2 Humble

Interfaz de control por teclado con botón/tecla de Parada de Emergencia (E-STOP)
integrada y visualización de estado en tiempo real.
"""

import sys
import time
import os

try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from std_msgs.msg import Bool
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False

if os.name == 'nt':
    import msvcrt
    def get_key():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                return msvcrt.getch().decode('latin1', errors='ignore')
            return ch.decode('latin1', errors='ignore')
        return None
else:
    import select
    import termios
    import tty
    def get_key():
        fd = sys.stdin.fileno()
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if rlist:
            return sys.stdin.read(1)
        return None

BANNER = """
====================================================================
 🚜 UGV VOYAGER 3 — CONTROL DE TELEOPERACIÓN Y PARADA DE EMERGENCIA
====================================================================
  [w] / [i] : Avanzar (+0.1 m/s)      [s] / [,] : Retroceder (-0.1 m/s)
  [a] / [D] : Girar Izquierda (+0.2)  [d] / [l] : Girar Derecha (-0.2)
  [k]       : Frenar a Neutro (0.0)

  >>> [BARRA ESPACIADORA] o [x] : 🚨 PARADA DE EMERGENCIA (E-STOP) 🚨 <<<
  [r]       : Liberar E-STOP / Reactivar Control
  [q]       : Salir limpiamente
--------------------------------------------------------------------
"""

def main(args=None):
    if not ROS2_AVAILABLE:
        print("Error: ROS 2 rclpy no está disponible.")
        return

    rclpy.init(args=args)
    node = rclpy.create_node('voyager_teleop_key')
    cmd_pub = node.create_publisher(Twist, '/cmd_vel', 10)
    estop_pub = node.create_publisher(Bool, '/voyager/emergency_stop', 10)

    # Configuración de terminal en POSIX
    old_settings = None
    if os.name != 'nt':
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    linear_v = 0.0
    angular_w = 0.0
    estop_active = False

    max_v = 1.2       # m/s tope dinámico ampliado (con rampa slew-rate anti-brownout)
    max_w = 1.0       # rad/s
    v_step = 0.1
    w_step = 0.35      # Incremento de dirección ampliado para giros más vivos (3 toques = 100% deflexión)

    print(BANNER)

    try:
        while rclpy.ok():
            key = get_key()
            if key:
                key_l = key.lower()

                # --- PARADA DE EMERGENCIA INMEDIATA ---
                if key == ' ' or key_l == 'x':
                    estop_active = True
                    linear_v = 0.0
                    angular_w = 0.0
                    # Publicar E-STOP a /voyager/emergency_stop
                    msg_estop = Bool()
                    msg_estop.data = True
                    estop_pub.publish(msg_estop)
                    # Publicar parada a /cmd_vel
                    msg_twist = Twist()
                    cmd_pub.publish(msg_twist)
                    print("\r\n🚨 [E-STOP] ¡PARADA DE EMERGENCIA ACTIVADA! Motores cortados y Pixhawk desarmada.   ", flush=True)

                # --- LIBERAR PARADA DE EMERGENCIA ---
                elif key_l == 'r':
                    estop_active = False
                    msg_estop = Bool()
                    msg_estop.data = False
                    estop_pub.publish(msg_estop)
                    print("\r\n✅ [E-STOP] Parada de emergencia LIBERADA. Control habilitado.                       ", flush=True)

                # --- CONTROL DE MOVIMIENTO (Solo si E-STOP no está trabado) ---
                elif not estop_active:
                    if key_l in ('w', 'i'):
                        linear_v = min(max_v, linear_v + v_step)
                    elif key_l in ('s', ','):
                        linear_v = max(-max_v, linear_v - v_step)
                    elif key_l in ('a', 'j'):
                        angular_w = min(max_w, angular_w + w_step)
                    elif key_l in ('d', 'l'):
                        angular_w = max(-max_w, angular_w - w_step)
                    elif key_l == 'k':
                        linear_v = 0.0
                        angular_w = 0.0
                    elif key_l == 'q':
                        break

                    msg_twist = Twist()
                    msg_twist.linear.x = float(linear_v)
                    msg_twist.angular.z = float(angular_w)
                    cmd_pub.publish(msg_twist)

                elif key_l == 'q':
                    break

            # Publicar periódicamente para mantener vivo el watchdog mientras el rover rueda
            if not estop_active and (abs(linear_v) > 1e-3 or abs(angular_w) > 1e-3):
                msg_twist = Twist()
                msg_twist.linear.x = float(linear_v)
                msg_twist.angular.z = float(angular_w)
                cmd_pub.publish(msg_twist)

            # Imprimir estado en línea única
            status_estop = "🚨 E-STOP BLOQUEADO (Pulsa 'r' para liberar)" if estop_active else "🟢 OPERATIVO"
            sys.stdout.write(
                f"\rVel Lineal: {linear_v:+.2f} m/s | Dirección: {angular_w:+.2f} rad/s | Estado: {status_estop}   "
            )
            sys.stdout.flush()
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        # Freno de seguridad final al salir
        msg_twist = Twist()
        cmd_pub.publish(msg_twist)
        if old_settings is not None and os.name != 'nt':
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        rclpy.shutdown()
        print("\n[Teleop] Cerrado en modo seguro.")

if __name__ == '__main__':
    main()

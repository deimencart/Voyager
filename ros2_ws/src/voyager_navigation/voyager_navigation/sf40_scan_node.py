#!/usr/bin/env python3
"""
ROS 2 SF40/C LiDAR LaserScan & Arc-Cloud Publisher Node
Decodes MAVLink DISTANCE_SENSOR messages (ID 132) received over UDP
and generates:
  1. /scan: Canonical sensor_msgs/msg/LaserScan
  2. /cloud: High-density 3D Arc-Cloud sensor_msgs/msg/PointCloud2
"""

import socket
import struct
import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import Header
from sensor_msgs.msg import LaserScan, PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster

class SF40ScanNode(Node):
    def __init__(self):
        super().__init__('sf40_scan_node')
        
        # Publicadores
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.cloud_pub = self.create_publisher(PointCloud2, '/cloud', 10)
        
        # Emisor de TF estática: base_link -> laser_frame
        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_tf()
        
        # Socket UDP escuchando el flujo MAVLink
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', 14550))
        self.sock.setblocking(False)
        
        # Almacén de distancias para los 8 sectores (en metros)
        # 0=Frente, 1=Frente-Der, 2=Der, 3=Atras-Der, 4=Atras, 5=Atras-Izq, 6=Izq, 7=Frente-Izq
        self.distances = [float('inf')] * 8
        
        # Mapeo de orientación MAVLink a ángulo central en coordenadas ROS (REP 103)
        self.angle_map = {
            0: 0.0,                 # 0° (Frente, +X)
            7: math.pi / 4.0,       # +45° (Frente-Izquierda)
            6: math.pi / 2.0,       # +90° (Izquierda, +Y)
            5: 3.0 * math.pi / 4.0, # +135° (Atrás-Izquierda)
            4: math.pi,             # 180° (Atrás, -X)
            3: -3.0 * math.pi / 4.0,# -135° (Atrás-Derecha)
            2: -math.pi / 2.0,      # -90° (Derecha, -Y)
            1: -math.pi / 4.0       # -45° (Frente-Derecha)
        }
        
        self.timer = self.create_timer(0.1, self.loop)  # 10 Hz
        self.get_logger().info('SF40 LiDAR Arc-Cloud Node iniciado en UDP 14550')

    def publish_static_tf(self):
        """Publica la transformada base_link -> laser_frame"""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'laser_frame'
        t.transform.translation.x = 0.15
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.20
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def loop(self):
        # Drenar paquetes UDP
        while True:
            try:
                data, _ = self.sock.recvfrom(2048)
                # MAVLink 1.0 (0xFE)
                if len(data) >= 20 and data[0] == 254 and data[5] == 132:
                    payload = data[6:6 + data[1]]
                    if len(payload) >= 14:
                        _, _, _, cur_dist_cm, _, _, orientation, _ = struct.unpack('<IHHHBBBB', payload[:14])
                        if orientation < 8:
                            dist_m = cur_dist_cm / 100.0
                            self.distances[orientation] = dist_m if (0.05 <= dist_m <= 20.0) else float('inf')
                # MAVLink 2.0 (0xFD)
                elif len(data) >= 25 and data[0] == 253:
                    msg_id = data[7] | (data[8] << 8) | (data[9] << 16)
                    if msg_id == 132:
                        payload = data[10:10 + data[1]]
                        if len(payload) >= 14:
                            _, _, _, cur_dist_cm, _, _, orientation, _ = struct.unpack('<IHHHBBBB', payload[:14])
                            if orientation < 8:
                                dist_m = cur_dist_cm / 100.0
                                self.distances[orientation] = dist_m if (0.05 <= dist_m <= 20.0) else float('inf')
            except (BlockingIOError, socket.error):
                break
            except Exception:
                break

        now = self.get_clock().now().to_msg()

        # 1. Publicar LaserScan estándar
        scan = LaserScan()
        scan.header.stamp = now
        scan.header.frame_id = 'laser_frame'
        scan.angle_min = -math.pi
        scan.angle_max = math.pi - (math.pi / 4.0)
        scan.angle_increment = math.pi / 4.0
        scan.range_min = 0.10
        scan.range_max = 20.0
        scan.ranges = [
            float(self.distances[4]), float(self.distances[3]),
            float(self.distances[2]), float(self.distances[1]),
            float(self.distances[0]), float(self.distances[7]),
            float(self.distances[6]), float(self.distances[5])
        ]
        self.scan_pub.publish(scan)

        # 2. Generar Nube de Puntos Densa (Arc-Cloud)
        # Para cada sector válido, se genera un abanico continuo de puntos en 3D
        points_3d = []
        samples_per_sector = 25  # Puntos por arco angular
        half_sector_span = (math.pi / 4.0) / 2.0  # +/- 22.5 grados
        z_layers = [-0.03, 0.0, 0.03]  # 3 capas de espesor volumétrico

        for ori, center_angle in self.angle_map.items():
            r = self.distances[ori]
            if 0.10 <= r <= 20.0:
                for step in range(samples_per_sector):
                    # Interpolar ángulo de -22.5° a +22.5° alrededor del centro
                    frac = (step / (samples_per_sector - 1)) - 0.5
                    angle = center_angle + (frac * 2.0 * half_sector_span)
                    px = r * math.cos(angle)
                    py = r * math.sin(angle)
                    for pz in z_layers:
                        points_3d.append([px, py, pz])

        if points_3d:
            cloud_header = Header()
            cloud_header.stamp = now
            cloud_header.frame_id = 'laser_frame'
            cloud_msg = pc2.create_cloud_xyz32(cloud_header, points_3d)
            self.cloud_pub.publish(cloud_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SF40ScanNode()
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

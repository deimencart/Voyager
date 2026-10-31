#!/usr/bin/env python3
"""
Voyager 3 Camera Receiver Node (H.264 UDP -> ROS 2 Image)
UGV Voyager 3 / Raspberry Pi Camera Module v2 (Sony IMX219)

Recibe el flujo de vídeo H.264 emitido por GStreamer desde la Raspberry Pi (puerto UDP 5600)
y lo publica como tópico estándar sensor_msgs/msg/Image (/camera/image_raw).
"""

import sys
import time

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image, CameraInfo
    from geometry_msgs.msg import TransformStamped
    from tf2_ros import StaticTransformBroadcaster
    import cv2
    import numpy as np
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    class Node:  # type: ignore
        def __init__(self, name: str): pass

class CameraReceiverNode(Node):
    def __init__(self):
        super().__init__('camera_receiver_node')

        self.declare_parameter('port', 5600)
        self.declare_parameter('width', 1024)
        self.declare_parameter('height', 768)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('frame_id', 'camera_optical_frame')

        self.port = int(self.get_parameter('port').value)
        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.fps = float(self.get_parameter('fps').value)
        self.frame_id = str(self.get_parameter('frame_id').value)

        # Publicador de imágenes
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)

        # Emisor de TF estática para la cámara
        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self.publish_camera_tf()

        # Pipeline de GStreamer para decodificar H.264 RTP en OpenCV
        gst_pipeline = (
            f"udpsrc port={self.port} caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96\" "
            f"! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1"
        )
        self.get_logger().info(
            f"Iniciando receptor de cámara en UDP :{self.port}...\n"
            f"Esperando flujo de vídeo H.264 desde la Raspberry Pi (se desbloqueará en cuanto comience la transmisión)..."
        )

        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            # Intento de fallback mediante backend estándar de OpenCV
            fallback_url = f"udp://0.0.0.0:{self.port}"
            self.cap = cv2.VideoCapture(fallback_url)

        if self.cap.isOpened():
            self.get_logger().info(f"¡Flujo de vídeo H.264 detectado y enlazado en UDP :{self.port}!")

        # Temporizador a la frecuencia de fotogramas objetivo
        period = 1.0 / max(1.0, self.fps)
        self.timer = self.create_timer(period, self.capture_loop)
        self.frame_count = 0

    def publish_camera_tf(self):
        """Publica transformada base_link -> camera_link"""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = self.frame_id
        # La cámara está montada en el mástil delantero del Voyager 3
        t.transform.translation.x = 0.20
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.28
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def capture_loop(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        # Construcción directa de sensor_msgs/msg/Image (sin dependencia de cv_bridge)
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.height = frame.shape[0]
        msg.width = frame.shape[1]
        msg.encoding = 'bgr8'
        msg.is_bigendian = False
        msg.step = frame.shape[1] * 3
        msg.data = frame.tobytes()

        self.image_pub.publish(msg)
        self.frame_count += 1
        if self.frame_count % 150 == 1:
            self.get_logger().info(f"Cámara transmitiendo: {frame.shape[1]}x{frame.shape[0]} @ ~{int(self.fps)} FPS")

    def destroy_node(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    if not ROS2_AVAILABLE:
        print("Error: ROS 2 o OpenCV no están disponibles.")
        return
    rclpy.init(args=args)
    node = CameraReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()

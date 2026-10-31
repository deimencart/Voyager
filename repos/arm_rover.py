#!/usr/bin/env python3
"""
Voyager 3 Rover Arming Tool (Windows/Linux Standalone)
UGV Voyager 3 / Pixhawk 1

Envía comando MAVLink COMMAND_LONG (Msg 76) con MAV_CMD_COMPONENT_ARM_DISARM (400)
para ARMAR la Pixhawk (param1=1.0).
Requiere que el vehículo esté en modo MANUAL y con el interruptor del ESC encendido.
"""

import socket
import struct
import sys
import time

def calculate_mavlink_crc(buffer: bytes, crc_extra: int) -> int:
    crc = 0xFFFF
    for b in buffer + bytes([crc_extra]):
        tmp = b ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    return crc

def send_arm(target_ip="127.0.0.1", target_port=14555, target_sys=153):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"\n[ARM] Solicitando ARMADO de Pixhawk a {target_ip}:{target_port} (SysID {target_sys})...")

    # Enviar MAV_CMD_COMPONENT_ARM_DISARM (param1=1.0)
    payload_arm = struct.pack(
        '<fffffffHBBB',
        1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        400, target_sys, 1, 0
    )
    header_arm = struct.pack('<BBBBBB', 0xFE, len(payload_arm), 0, 255, 190, 76)
    crc_arm = calculate_mavlink_crc(header_arm[1:] + payload_arm, crc_extra=152)
    packet_arm = header_arm + payload_arm + struct.pack('<H', crc_arm)

    for i in range(3):
        try:
            sock.sendto(packet_arm, (target_ip, target_port))
            time.sleep(0.02)
        except Exception as e:
            print(f"Error al enviar: {e}")
            break

    sock.close()
    print("[OK] Comando de ARMADO enviado a Pixhawk.\n")

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 14555
    send_arm(target_ip=host, target_port=port)

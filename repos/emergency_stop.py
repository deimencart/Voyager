#!/usr/bin/env python3
"""
Voyager 3 Instant E-STOP & Disarm (Windows/Linux Standalone Kill-Switch)
UGV Voyager 3 / Pixhawk 1

Envía de forma inmediata e incondicional:
1. RC_CHANNELS_OVERRIDE (Msg 70) con Gas en 1485 us (Neutro estricto) y Dirección en 1470 us.
2. COMMAND_LONG (Msg 76) con MAV_CMD_COMPONENT_ARM_DISARM (400) para forzar el DESARME de Pixhawk.
Funciona directamente por UDP hacia el relay de Windows (127.0.0.1:14555) o hacia el rover.
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

def send_stop(target_ip="127.0.0.1", target_port=14555, target_sys=153):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"\n[EMERGENCY STOP] Enviando parada inmediata a {target_ip}:{target_port} (Pixhawk SysID {target_sys})...")

    # 1. Enviar Override a Neutro (1485 us en gas, 1470 us en direccion)
    payload_override = struct.pack(
        '<HHHHHHHHBB',
        1470, 1490, 1485, 1486, 1497, 1498, 1498, 1498,
        target_sys, 1
    )
    header_override = struct.pack('<BBBBBB', 0xFE, len(payload_override), 0, 255, 190, 70)
    crc_override = calculate_mavlink_crc(header_override[1:] + payload_override, crc_extra=124)
    packet_override = header_override + payload_override + struct.pack('<H', crc_override)

    # 2. Enviar Disarm Forzado (param1=0.0, param2=21196.0)
    payload_disarm = struct.pack(
        '<fffffffHBBB',
        0.0, 21196.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        400, target_sys, 1, 0
    )
    header_disarm = struct.pack('<BBBBBB', 0xFE, len(payload_disarm), 1, 255, 190, 76)
    crc_disarm = calculate_mavlink_crc(header_disarm[1:] + payload_disarm, crc_extra=152)
    packet_disarm = header_disarm + payload_disarm + struct.pack('<H', crc_disarm)

    # Enviar ráfaga triple para garantizar recepción por UDP
    for i in range(3):
        try:
            sock.sendto(packet_override, (target_ip, target_port))
            sock.sendto(packet_disarm, (target_ip, target_port))
            time.sleep(0.02)
        except Exception as e:
            print(f"Error al enviar: {e}")
            break

    sock.close()
    print("[OK] Parada enviada: Gas en 1485 us (Neutro), Servo en 1470 us (Centro) y orden de DESARME transmitida.\n")

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 14555
    send_stop(target_ip=host, target_port=port)

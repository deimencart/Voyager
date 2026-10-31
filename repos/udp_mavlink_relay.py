import socket
import subprocess
import select
import time
import sys

def get_wsl_ip():
    try:
        out = subprocess.check_output(["wsl", "-d", "Ubuntu-22.04", "--", "hostname", "-I"], text=True)
        return out.strip().split()[0]
    except Exception:
        return "172.29.174.114"

def main():
    wsl_ip = get_wsl_ip()
    print(f"[UDP Relay Bidireccional] Iniciando puente de telemetria, control y video:", flush=True)
    print(f"  • Enlace Rover (Inbound Telemetria): 192.168.137.1:14550", flush=True)
    print(f"  • Enlace Rover (Inbound Video):      192.168.137.1:5600", flush=True)
    print(f"  • Destino WSL2:                      {wsl_ip} (:14550 y :5600)", flush=True)
    print(f"  • Enlace Comandos WSL2 (Outbound):   0.0.0.0:14555 -> Rover", flush=True)

    # 1. Socket para telemetría MAVLink (Pi -> Windows)
    sock_rover = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_rover.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_rover.bind(('192.168.137.1', 14550))
    sock_rover.setblocking(False)

    # 2. Socket para streaming de vídeo H.264 (Pi -> Windows)
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_video.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    video_bound = False
    try:
        sock_video.bind(('192.168.137.1', 5600))
        sock_video.setblocking(False)
        video_bound = True
    except Exception as e:
        print(f"  [AVISO Video] No se pudo vincular puerto 5600 ({e}). El visor local de Windows puede estar usándolo.")

    # 3. Socket para comandos de control desde WSL2 (WSL2 -> Windows)
    sock_wsl_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_wsl_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_wsl_in.bind(('0.0.0.0', 14555))
    sock_wsl_in.setblocking(False)

    # 4. Socket para reenviar hacia WSL2 (Windows -> WSL2)
    sock_wsl_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    last_rover_addr = None
    inbound_count = 0
    video_count = 0
    outbound_count = 0
    last_warn_time = 0

    listen_sockets = [sock_rover, sock_wsl_in]
    if video_bound:
        listen_sockets.append(sock_video)

    while True:
        rlist, _, _ = select.select(listen_sockets, [], [], 0.5)

        for s in rlist:
            if s is sock_rover:
                try:
                    data, addr = sock_rover.recvfrom(4096)
                    last_rover_addr = addr
                    sock_wsl_out.sendto(data, (wsl_ip, 14550))
                    inbound_count += 1
                    if inbound_count % 200 == 0:
                        print(f"[Relay] {inbound_count} paquetes telemetria hacia WSL2 (Rover: {addr})", flush=True)
                except Exception:
                    pass

            elif s is sock_video:
                try:
                    data, addr = sock_video.recvfrom(65535)
                    sock_wsl_out.sendto(data, (wsl_ip, 5600))
                    video_count += 1
                    if video_count % 300 == 1:
                        print(f"[Relay] Transmitiendo video de camara hacia WSL2 ({video_count} paquetes)", flush=True)
                except Exception:
                    pass

            elif s is sock_wsl_in:
                try:
                    data, addr = sock_wsl_in.recvfrom(4096)
                    if last_rover_addr is not None:
                        sock_rover.sendto(data, last_rover_addr)
                        outbound_count += 1
                        if outbound_count % 20 == 1:
                            print(f"[Relay] ---> Reenviado comando de control {outbound_count} hacia Rover {last_rover_addr} ({len(data)} bytes)", flush=True)
                except Exception:
                    pass

if __name__ == '__main__':
    main()

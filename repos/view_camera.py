#!/usr/bin/env python3
"""
Voyager 3 Live Camera Viewer (Standalone Window)
UGV Voyager 3 / Raspberry Pi Camera Module v2

Abre una ventana gráfica en tiempo real que muestra el vídeo H.264
transmitido por el rover a través del puerto UDP 5600.
Pulsa 'q' o 'ESC' para cerrar la ventana.
"""

import cv2
import sys
import time

def main(port=5600):
    print(f"\n=======================================================")
    print(f" 📷 UGV VOYAGER 3 — VISOR DE CÁMARA EN VIVO (UDP :{port})")
    print(f"=======================================================")
    print("Conectando con el flujo de vídeo de la Raspberry Pi...")
    print("Pulsa [q] o [ESC] en la ventana de vídeo para salir.\n")

    # Pipeline GStreamer optimizado para decodificación hardware / software fluida
    pipeline = (
        f"udpsrc port={port} caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96\" "
        f"! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1"
    )

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        # Fallback a captura UDP directa por FFMPEG
        fallback = f"udp://0.0.0.0:{port}"
        cap = cv2.VideoCapture(fallback)

    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir el flujo de vídeo en el puerto UDP {port}.")
        print("Verifica que el rover esté encendido y transmitiendo vídeo.")
        return

    fps_count = 0
    t0 = time.time()
    fps_display = 0.0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        fps_count += 1
        elapsed = time.time() - t0
        if elapsed >= 1.0:
            fps_display = fps_count / elapsed
            fps_count = 0
            t0 = time.time()

        # Añadir HUD informativo
        h, w = frame.shape[:2]
        hud_text = f"VOYAGER 3 | {w}x{h} | {fps_display:.1f} FPS"
        cv2.putText(frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "Pulsa [q] para salir", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow("Voyager 3 - Camara en Vivo (Sony IMX219)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n[OK] Visor de cámara cerrado.")

if __name__ == '__main__':
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 5600
    main(port=p)

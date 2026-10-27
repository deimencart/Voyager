import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = Document()

# Set page margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

COLOR_PRIMARY = RGBColor(31, 73, 125)    # Navy Blue
COLOR_SECONDARY = RGBColor(89, 89, 89)  # Dark Gray
COLOR_TEXT = RGBColor(38, 38, 38)        # Off-black

def set_para_font(p, name='Calibri', size=11, color=COLOR_TEXT, bold=False, italic=False):
    for run in p.runs:
        run.font.name = name
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.bold = bold
        run.italic = italic

def add_styled_heading(text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(6)
    if level == 1:
        set_para_font(h, 'Calibri', 18, COLOR_PRIMARY, bold=True)
    elif level == 2:
        set_para_font(h, 'Calibri', 14, COLOR_PRIMARY, bold=True)
    elif level == 3:
        set_para_font(h, 'Calibri', 12, COLOR_SECONDARY, bold=True)
    return h

def add_code_block(text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    shd = parse_xml(r'<w:shd {} w:fill="F2F4F7"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shd)
    borders = parse_xml(r'<w:tcBorders {}><w:top w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/><w:left w:val="single" w:sz="24" w:space="0" w:color="1F497D"/><w:right w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/></w:tcBorders>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(33, 37, 41)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ----------------- COVER / TITLE -----------------
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(24)
title_p.paragraph_format.space_after = Pt(4)
title_run = title_p.add_run('Manual Técnico y de Operación')
title_run.font.name = 'Calibri'
title_run.font.size = Pt(26)
title_run.font.color.rgb = COLOR_PRIMARY
title_run.bold = True

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(14)
sub_run = sub_p.add_run('UGV Voyager 3 — Fible ALTU (Consorcio Europeo RAWFIE H2020)')
sub_run.font.name = 'Calibri'
sub_run.font.size = Pt(14)
sub_run.font.color.rgb = COLOR_SECONDARY
sub_run.italic = True

div_p = doc.add_paragraph()
div_p.paragraph_format.space_after = Pt(18)
div_run = div_p.add_run('Auditoría Integral de Hardware, Software, Red, Telemetría y Guía de Conexión')
div_run.font.name = 'Calibri'
div_run.font.size = Pt(11)
div_run.bold = True

# ----------------- SECTION 1 -----------------
add_styled_heading('1. Ficha Técnica y Resumen Ejecutivo', 1)
p = doc.add_paragraph()
p.add_run('El vehículo objeto de este manual es una plataforma robótica terrestre todoterreno (UGV — Unmanned Ground Vehicle) integrada originalmente para el consorcio de investigación europeo RAWFIE (Road-, Air- and Water-based Future Internet Experimentation, programa Horizon 2020 de la Unión Europea).')

items_sec1 = [
    ('Nombre del Vehículo', 'Voyager 3 (Identificador de red: rtart.fible.voyager.ugv.3).'),
    ('Fabricante / Integrador', 'Fible Technologies I.K.E. (Atrina Center, 32 Kifisias Avenue, Marousi, Atenas, Grecia — fible.gr).'),
    ('Equipo de Desarrollo', 'Nasos (Athanasios) Grigoropoulos (Software/UoA) y Stavros Papas (Comunicaciones/Fible).'),
    ('Chasis y Mecánica', 'Plataforma todoterreno con cinemática Ackermann (servo de dirección delantero y variador ESC con motor de tracción).'),
    ('Computadora de Misión', 'Raspberry Pi 3 Model B (Raspbian GNU/Linux 9 Stretch, Kernel 4.14 armv7l).'),
    ('Autopiloto de Control', 'Pixhawk 1 con firmware ArduPilot APM:Rover.'),
    ('Sensores Principales', 'LiDAR 360° LightWare SF40 (puerto SERIAL 4/5 a 115.200 bps), antena GPS/Brújula externa y barómetro barométrico MS5611.'),
    ('Comunicaciones', 'Router MikroTik RouterBOARD (192.168.1.1 en eth0), módem celular 4G/LTE Huawei HiLink (192.168.8.1 en USB) y túnel seguro OpenVPN.'),
    ('Telemetría', 'MAVLink 1.0/2.0 en puerto UDP 14550 para Mission Planner / QGroundControl y bus Apache Kafka con esquemas Apache Avro.')
]
for k, v in items_sec1:
    bp = doc.add_paragraph(style='List Bullet')
    r1 = bp.add_run(k + ': ')
    r1.bold = True
    bp.add_run(v)

# ----------------- SECTION 2 -----------------
add_styled_heading('2. Arquitectura de Hardware y Asignación de Pines', 1)
p = doc.add_paragraph()
p.add_run('A continuación se detalla la asignación física de puertos de la controladora Pixhawk y la computadora Raspberry Pi 3 extraída de los archivos de parámetros de vuelo (mav.parm) y scripts de arranque:')

table_data = [
    ['Dispositivo / Función', 'Puerto en Pixhawk', 'Puerto en Raspberry Pi', 'Parámetros y Velocidad'],
    ['Servo de Dirección', 'MAIN OUT 1 (PWM)', '—', 'SERVO1_FUNCTION = 26 (GroundSteering), Trim: 1470 us, Rev: 1'],
    ['Motor de Tracción / ESC', 'MAIN OUT 3 (PWM)', '—', 'SERVO3_FUNCTION = 70 (Throttle), Min: 900 us, Max: 2000 us'],
    ['Enlace RPi - Pixhawk', 'TELEM 2 (UART)', 'GPIO 14 (TX) / 15 (RX)', 'SERIAL2_PROTOCOL = 1 (MAVLink), Baud: 921.600 bps'],
    ['LiDAR 360° LightWare SF40', 'SERIAL 4/5 (UART)', '—', 'SERIAL4_PROTOCOL = 11 (Proximity), Baud: 115.200 bps'],
    ['GPS + Brújula Externa', 'SERIAL 3 (UART)', '—', 'SERIAL3_PROTOCOL = 5 (GPS), Baud: 38.400 bps'],
    ['Radio Telemetría RF 433/915', 'TELEM 1 (UART)', '—', 'SERIAL1_PROTOCOL = 1 (MAVLink), Baud: 57.600 bps'],
    ['Receptor RC Manual 2.4GHz', 'RC IN (PPM/SBUS)', '—', 'Canal 1: Dirección, Canal 3: Gas, Canal 8: Modo de vuelo'],
    ['Cámara HD Raspberry Pi', '—', 'Conector Cinta CSI', 'raspivid @ 1024x768 30 fps H.264'],
    ['Router a Bordo MikroTik', '—', 'Ethernet eth0', 'IP Gateway fija: 192.168.1.1 (o 192.168.3.1)'],
    ['Módem 4G/LTE Celular', '—', 'Puerto USB', 'Huawei HiLink Gateway: 192.168.8.1 (con tarjeta SIM)']
]

tbl = doc.add_table(rows=len(table_data), cols=4)
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(table_data):
    for c_idx, val in enumerate(row):
        cell = tbl.cell(r_idx, c_idx)
        cell.text = val
        cell_p = cell.paragraphs[0]
        cell_p.paragraph_format.space_before = Pt(3)
        cell_p.paragraph_format.space_after = Pt(3)
        if r_idx == 0:
            shd = parse_xml(r'<w:shd {} w:fill="1F497D"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shd)
            set_para_font(cell_p, 'Calibri', 9.5, RGBColor(255, 255, 255), bold=True)
        else:
            if r_idx % 2 == 1:
                shd = parse_xml(r'<w:shd {} w:fill="F8F9FA"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shd)
            set_para_font(cell_p, 'Calibri', 9, COLOR_TEXT)

doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ----------------- SECTION 3 -----------------
add_styled_heading('3. Arquitectura de Software y Telemetría', 1)
doc.add_paragraph('El sistema se autoarranca al recibir alimentación mediante /etc/rc.local, el cual ejecuta /home/pi/runDrone.sh en segundo plano. La pila de software se compone de tres módulos coordinados:')

add_styled_heading('A. MAVProxy (Multiplexado MAVLink a 921.600 bps)', 2)
doc.add_paragraph('MAVProxy toma el flujo serie del autopiloto y lo divide en dos canales UDP simultáneos:')
add_code_block('mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=127.0.0.1:1234 --out=$GCS_IP:14550 --aircraft Voyager_3')
doc.add_paragraph('1. Canal Local (127.0.0.1:1234): Permite que el demonio de navegación en Python (adapter.py) interactúe con el autopiloto via DroneKit.\n2. Canal Remoto (UDP 14550): Permite que tu PC con Mission Planner o QGroundControl reciba la telemetría en tiempo real.')

add_styled_heading('B. Demonio de Telemetría IoT (adapter-rover)', 2)
doc.add_paragraph('Ubicado en /home/pi/adapter-rover/adapter/adapter.py. Utiliza DroneKit-Python para escuchar eventos de IMU, GPS, batería y presión, los serializa usando esquemas Apache Avro y los envía al broker Apache Kafka (172.19.0.18:9092) en tópicos como rtart_Attitude, rtart_LinearVelocity, rtart_Location y rtart_ObjectDistance.')

add_styled_heading('C. Streaming de Vídeo GStreamer (UDP 5600)', 2)
doc.add_paragraph('La cámara emite vídeo H.264 en tiempo real empaquetado en RTP hacia la estación de control:')
add_code_block('raspivid -n -w 1024 -h 768 -b 500000 -fps 30 -t 0 -o - | gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=10 pt=96 ! udpsink host=$Stream_IP port=5600')

# ----------------- SECTION 4 -----------------
add_styled_heading('4. Credenciales de Red y Acceso', 1)
doc.add_paragraph('Todos los accesos y credenciales recuperados de la imagen:')

wifi_items = [
    ('SSID Principal', 'DroneLab | Clave PSK: stavrospapas'),
    ('SSID Alternativo 1', 'Stavros iPhone 7 | Clave PSK: stavrospapas'),
    ('SSID Alternativo 2', '7bpm-WiFi | Clave PSK: stavrospapas'),
    ('Usuario SSH (Linux)', 'pi | Contraseñas: raspberry o stavrospapas (Sudo NOPASSWD habilitado)'),
    ('OpenVPN RAWFIE', 'Servidor: 195.134.71.99:1194 UDP | Certificado: rtart.fible.voyager.ugv.3.crt')
]
for k, v in wifi_items:
    bp = doc.add_paragraph(style='List Bullet')
    r = bp.add_run(k + ': ')
    r.bold = True
    bp.add_run(v)

# ----------------- SECTION 5 -----------------
add_styled_heading('5. El Sistema LiDAR y Evitación de Obstáculos', 1)
doc.add_paragraph('El vehículo equipa un escáner láser LightWare SF40 conectado en SERIAL 4/5 (115.200 bps):')
lidar_items = [
    ('Evasión autónoma (AVOID_ENABLE = 3)', 'La Pixhawk frena o desvía el rover automáticamente si detecta obstáculos.'),
    ('Distancia máxima de reacción (AVOID_DIST_MAX = 5.0 m)', 'El cálculo de trayectoria de desvío comienza a 5 metros del objeto.'),
    ('Margen de seguridad (AVOID_MARGIN = 2.0 m)', 'El rover mantiene un espacio de seguridad mínimo de 2 metros con cualquier obstáculo.'),
    ('Comportamiento de evasión (AVOID_BEHAVE = 1)', 'Detención o deslizamiento lateral según el modo de conducción activo.')
]
for k, v in lidar_items:
    bp = doc.add_paragraph(style='List Bullet')
    r = bp.add_run(k + ': ')
    r.bold = True
    bp.add_run(v)

# ----------------- SECTION 6 -----------------
add_styled_heading('6. Señales Acústicas y Avisos del Robot', 1)
doc.add_paragraph('El robot se comunica a través de tres vías simultáneas:')
sound_items = [
    ('Zumbador (Buzzer de la Pixhawk)', 'Melodía alegre de 3 notas = Arranque y calibración OK. Pitido largo = ARMADO (motores con corriente). Dos pitidos cortos = DESARMADO. Pitidos graves repetitivos = Alarma de batería baja o falta de señal GPS.'),
    ('LED RGB de la Pixhawk', 'Azul parpadeante = Buscando satélites. Verde parpadeante = GPS Fix 3D listo para armar. Verde fijo = ARMADO y en marcha. Ámbar parpadeante = Modo Failsafe / Emergencia.'),
    ('Voz en Mission Planner', 'Al conectar Mission Planner al puerto UDP 14550, tu PC habla por los altavoces anunciando: Armed, Disarmed, Manual Mode, Auto Mode, Warning: Low battery, etc.')
]
for k, v in sound_items:
    bp = doc.add_paragraph(style='List Bullet')
    r = bp.add_run(k + ': ')
    r.bold = True
    bp.add_run(v)

# ----------------- SECTION 7 -----------------
add_styled_heading('7. Guía Paso a Paso para Conectar y Operar', 1)
doc.add_paragraph('Instrucciones para enlazar el vehículo con tu PC:')
steps = [
    ('Paso 1: Activar Zona Wi-Fi en tu Móvil o Laptop', 'Crea una zona Wi-Fi compartida con Nombre: DroneLab y Contraseña: stavrospapas. Enciende el robot. En 30-40 segundos se conectará solo y verás su dirección IP (ej. 192.168.43.50).'),
    ('Paso 2: Conectar con Mission Planner', 'Abre Mission Planner. En la esquina superior derecha selecciona UDP (baudrate 115200). Pulsa Connect. Escribe el puerto 14550 y pulsa OK. Se conectará y verás el vehículo en el mapa.'),
    ('Paso 3: Ver la Cámara con VLC (Opcional)', 'Abre VLC Media Player -> Medio -> Abrir emisión de red -> introduce udp://@:5600 y pulsa Reproducir.'),
    ('Paso 4: Entrar a la Terminal por SSH', 'En PowerShell o PuTTY escribe: ssh pi@192.168.43.50 con contraseña raspberry o stavrospapas.')
]
for k, v in steps:
    bp = doc.add_paragraph(style='List Bullet')
    r = bp.add_run(k + ': ')
    r.bold = True
    bp.add_run(v)

# ----------------- SECTION 8 -----------------
add_styled_heading('8. Guía de Solución de Problemas (Troubleshooting)', 1)
tb_items = [
    ('La Raspberry Pi arranca pero no envía telemetría', 'Si estás probando en una mesa sin el router MikroTik ni el módem Huawei conectados, el script runDrone.sh se pausa en los pings de red. Solución: conéctate por SSH y ejecuta mavproxy.py --master=/dev/serial0 --baudrate 921600 --out=udp:TU_IP_PC:14550 o edita runDrone.sh poniendo StartMikrotik=0 y StartLTE=0.'),
    ('La Pixhawk no permite armar los motores', 'En interiores la Pixhawk bloquea el armado en modos automáticos por falta de GPS. Cambia el modo a MANUAL en Mission Planner para probar los motores en el banco de trabajo.'),
    ('Restauración de parámetros de fábrica', 'Dispones del archivo mav.parm extraído en Voyager_3_root/logs/2025-03-04/flight1/mav.parm. En Mission Planner puedes cargarlo desde CONFIG -> Full Parameter Tree -> Load from file -> Write Params para restaurar el 100% de la configuración original.')
]
for k, v in tb_items:
    bp = doc.add_paragraph(style='List Bullet')
    r = bp.add_run(k + ': ')
    r.bold = True
    bp.add_run(v)

out_file = r'D:\Voyager\analisis_sistema\MANUAL_SISTEMA_VOYAGER3.docx'
doc.save(out_file)
print('DOCX successfully generated at:', out_file)

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

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

def add_styled_heading(doc, text, level):
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

def format_table(tbl, col_widths, headers, data):
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_para_font(p, 'Calibri', 10, RGBColor(255, 255, 255), bold=True)
        shd = parse_xml(r'<w:shd {} w:fill="1F497D"/>'.format(nsdecls('w')))
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)
        
    for row_idx, row_data in enumerate(data):
        row_cells = tbl.add_row().cells
        fill_color = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate(row_data):
            row_cells[i].text = str(val)
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_para_font(p, 'Calibri', 9.5, COLOR_TEXT)
            shd = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), fill_color))
            row_cells[i]._tc.get_or_add_tcPr().append(shd)

    for row in tbl.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def generate_bitacora():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)

    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(20)
    title_run = title_p.add_run('Bitácora de Trabajo Técnico')
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = COLOR_PRIMARY
    title_run.bold = True

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run('Sesión de Conexión, Auditoría de Telemetría, Diagnóstico y Planificación de Modo AP — UGV Voyager 3')
    sub_run.font.name = 'Calibri'
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = COLOR_SECONDARY
    sub_run.italic = True

    p_meta = doc.add_paragraph()
    p_meta.add_run('Fecha: 18 de octubre de 2026 (Actualizado: 19 de octubre de 2026) | Entorno: Makerspace / Laboratorio').italic = True
    
    add_styled_heading(doc, '1. Resumen Ejecutivo de la Jornada', 1)
    p = doc.add_paragraph()
    p.add_run('Durante la sesión de trabajo se logró reactivar y enlazar el rover Voyager 3 (Fible ALTU / Consorcio H2020 RAWFIE) tras años de inactividad técnica. Se obtuvo acceso directo por consola SSH como superusuario a la Raspberry Pi 3 Model B, se estableció la comunicación MAVLink a 921.600 baudios con el autopiloto Pixhawk (ArduRover V3.4.2), se descargaron los 679 parámetros y se transmitió la telemetría viva a Mission Planner por UDP 14550. Se aisló la causa raíz por la cual los actuadores no respondieron y se definió la arquitectura de red definitiva mediante la conversión del router MikroTik RouterBOARD a modo Punto de Acceso (AP).')

    add_styled_heading(doc, '2. Hitos Técnicos Alcanzados', 1)
    headers = ['Hito Técnico', 'Estado', 'Detalle y Observaciones']
    widths = [Inches(1.8), Inches(1.2), Inches(3.5)]
    data = [
        ['Copia de Seguridad Física', 'COMPLETADO', 'Imagen bit a bit sd.img (31.9 GB) creada y write-protected en D:\\Voyager\\backup_sdbackup\\.'],
        ['Credenciales del Sistema', 'VALIDADO', 'Usuario pi / Contraseña raspberry (verificado contra hash SHA-512 crypt de /etc/shadow). Permisos sudo íntegros.'],
        ['Enlace WiFi Hotspot', 'LOGRADO', 'Asociación a red DroneLab (2.4 GHz) con IP asignada 192.168.137.145.'],
        ['Enlace Ethernet Físico', 'LOGRADO', 'Enlace directo por cable a 100 Mbps. IPv6 link-local fe80::ad8c:6f66:3d82:3bb4%15 e IPv4 APIPA 169.254.174.253 (< 1 ms latencia).'],
        ['Enlace MAVLink Pixhawk', 'LOGRADO', 'MAVProxy comunicando por /dev/serial0 a 921.600 bps. Heartbeat de ArduRover V3.4.2 activo y 679 parámetros archivados.'],
        ['Interfaz Mission Planner', 'LOGRADO', 'Recepción de telemetría por UDP puerto 14550: horizonte artificial, brújula, orientación e interfaz gráfica operativas.']
    ]
    t = doc.add_table(rows=1, cols=3)
    format_table(t, widths, headers, data)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_styled_heading(doc, '3. Diagnóstico: ¿Por qué no se movieron los actuadores?', 1)
    doc.add_paragraph().add_run('A pesar de que el software de control recibió las órdenes enviadas por consola, las ruedas y el motor no respondieron físicamente debido a dos causas concurrentes:')

    add_styled_heading(doc, '3.1. Causas de Software en el Autopiloto (ArduPilot)', 2)
    items_sw = [
        ('Requisito de Armado Obligatorio (ARMING_REQUIRE = 1): ', 'En ArduRover, las salidas PWM hacia el servo de dirección (MAIN OUT 1) y hacia el variador ESC (MAIN OUT 3) están inhibidas electrónicamente hasta que el vehículo se encuentra en estado ARMED. Al estar desarmado, los comandos de radio virtual rc 1 1650 son descartados por seguridad.'),
        ('Bloqueo por Failsafe de Radio (FS_THR_ENABLE = 1): ', 'El autopiloto tiene configurada la parada de seguridad si no detecta una señal válida de radiofrecuencia (emisora física RC de 2.4 GHz). Al no haber un transmisor RC encendido, ArduRover fuerza el modo HOLD e impide el armado (provocando el error COMMAND_ACK {command: 400, result: 4}).'),
        ('Rechazo de DO_SET_SERVO en Canales Principales: ', 'El intento de forzar el servo con servo set 1 1650 devolvió COMMAND_ACK {command: 183, result: 4} (FAILED). En el firmware ArduPilot, MAV_CMD_DO_SET_SERVO está prohibido en canales asignados a conducción primaria (k_ground_steering / Canal 1).')
    ]
    for b, t_text in items_sw:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(b).bold = True
        p.add_run(t_text)

    add_styled_heading(doc, '3.2. Causa Eléctrica / Alimentación de Potencia del Chasis', 2)
    doc.add_paragraph().add_run('En la pantalla de Mission Planner se registró arriba en rojo: Bat1: 0.00v 0.0 A. En la arquitectura de la Pixhawk, el conector POWER alimenta la CPU interna y la Raspberry Pi, pero el rail de servos (MAIN OUT 1 a 8) requiere alimentación externa de 5V–6V proporcionada por el variador electrónico (ESC) del coche o por un BEC dedicado. Al marcar 0.00V, la batería de tracción del coche estaba desconectada o el interruptor general del variador (ESC) del chasis estaba apagado, dejando el servo sin energía mecánica para ejercer fuerza.')

    add_styled_heading(doc, '4. Diagnóstico de Red LAN y Solución Definitiva: MikroTik en Modo AP', 1)
    doc.add_paragraph().add_run('En el diseño original del consorcio RAWFIE, el router MikroTik funcionaba en modo Cliente (Station), buscando asociarse a redes exteriores o enrutar por el módem 4G hacia Grecia (195.134.71.99). La solución definitiva de ingeniería consiste en configurar el MikroTik RouterBOARD integrado como Punto de Acceso (AP / Home AP):')
    
    items_lan = [
        ('Emisión de Burbuja WiFi Autónoma: ', 'El coche emitirá su propia red inalámbrica (SSID: Voyager_3). No dependerá de zonas móviles ni de la infraestructura del edificio.'),
        ('Servidor DHCP a Bordo: ', 'El MikroTik asignará automáticamente direcciones IP válidas tanto a la Raspberry Pi (192.168.1.100) como a cualquier portátil o estación de tierra conectada (192.168.1.150).'),
        ('Eliminación del Cable y Caídas: ', 'Se erradica el problema de timeout del Hotspot de Windows 11, las direcciones APIPA provisionales (169.254.x.x) y la necesidad de arrastrar un cable Ethernet físico.')
    ]
    for b, t_text in items_lan:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(b).bold = True
        p.add_run(t_text)

    add_styled_heading(doc, '5. Plan de Acción y Próximos Pasos (Next Steps)', 1)
    doc.add_paragraph().add_run('La hoja de ruta estructurada para la siguiente fase de desarrollo comprende 5 fases:')
    steps = [
        ('Fase 1: Conversión del MikroTik a Modo AP (WinBox): ', 'Conectar cable Ethernet al MikroTik, abrir WinBox en Windows (admin / stavrospapas), seleccionar Quick Set -> Home AP, asignar SSID Voyager_3, activar DHCP Server (192.168.1.10 - 192.168.1.200) y verificar la conexión inalámbrica del portátil.'),
        ('Fase 2: Parche del Script runDrone.sh: ', 'En la Raspberry Pi, fijar UseMaintenanceIP=1, establecer Maintenance_GCS_IP="192.168.1.255" (broadcast) y anular la función CheckInternet para que MAVProxy arranque automáticamente sin buscar servidores externos.'),
        ('Fase 3: Potencia del Chasis y Prueba de Actuadores en Banco: ', 'Conectar la batería LiPo principal, encender el variador ESC (verificar Bat1 > 7.4V en Mission Planner), comprobar resistencia magnética en las ruedas y ejecutar en MAVProxy: param set ARMING_REQUIRE 0 y param set FS_THR_ENABLE 0, probando el servo (rc 1 1650) y motor (rc 3 1560) con ruedas en el aire.'),
        ('Fase 4: Prueba de Conducción en Suelo: ', 'Bajar el vehículo al suelo y teleoperarlo de forma completamente inalámbrica vía WiFi con un mando USB o teclado desde Mission Planner.'),
        ('Fase 5: Migración a ROS 2 y Mapeo SLAM: ', 'Flashear una nueva microSD con Ubuntu Server 22.04 LTS (64-bit) y ROS 2 Humble + MAVROS 2, publicando /cmd_vel y procesando el LiDAR LightWare SF40 (/scan) para navegación autónoma y SLAM con Nav2.')
    ]
    for b, t_text in steps:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(b).bold = True
        p.add_run(t_text)

    out_path = r'D:\Voyager\analisis_sistema\BITACORA_SESION_2026-10-18.docx'
    doc.save(out_path)
    print('Bitacora DOCX saved:', out_path)

def generate_guia_cierre():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(20)
    r = p.add_run('Protocolo de Cierre Seguro, Configuraciones y Next Steps')
    r.font.name = 'Calibri'
    r.font.size = Pt(24)
    r.font.color.rgb = COLOR_PRIMARY
    r.bold = True

    sub = doc.add_paragraph()
    r_sub = sub.add_run('UGV Voyager 3 — Fible ALTU (Consorcio Europeo RAWFIE H2020)')
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = COLOR_SECONDARY
    r_sub.italic = True

    doc.add_paragraph().add_run('Fecha: 18 de octubre de 2026 (Actualizado: 19 de octubre de 2026)').italic = True

    add_styled_heading(doc, '1. Procedimiento de Apagado Seguro de la Raspberry Pi', 1)
    steps = [
        ('1. Detener MAVProxy: ', 'Pulsar Ctrl + C en la ventana de terminal para cerrar el enlace MAVLink ordenadamente y regresar al prompt pi@Voyager_3_RPi:~ $.'),
        ('2. Ordenar el apagado del SO: ', 'Ejecutar sudo poweroff (o sudo shutdown -h now) en la terminal SSH.'),
        ('3. Esperar el reposo de disco (LED Verde): ', 'Observar el LED verde (ACT) de la Raspberry Pi. Parpadeará unos segundos mientras descarga la memoria a la SD y luego se apagará por completo, quedando solo el LED rojo de alimentación fijo.'),
        ('4. Desconectar la alimentación: ', 'Desconectar el cable de la batería o alimentación física, retirar el cable de red y cerrar Mission Planner.')
    ]
    for title, desc in steps:
        p_step = doc.add_paragraph(style='List Bullet')
        p_step.add_run(title).bold = True
        p_step.add_run(desc)

    add_styled_heading(doc, '2. Resumen de Parámetros y Configuraciones Archivadas', 1)
    params = [
        ('Dirección Ackermann (SERVO1): ', 'Función 26 (GroundSteering), Min 1100 us, Max 1900 us, Trim 1470 us, Reversed 1.'),
        ('Tracción (SERVO3): ', 'Función 70 (Throttle), Min 900 us, Max 2000 us, Trim 1300 us, Reversed 1.'),
        ('LiDAR 360° LightWare SF40: ', 'Puerto SERIAL4_PROTOCOL = 11 @ 115.200 bps, AVOID_ENABLE = 3 (margen de parada 2.0 m, distancia máxima 5.0 m).'),
        ('Telemetría Serie Pixhawk-RPi: ', 'SERIAL2_PROTOCOL = 1 @ 921.600 bps hacia /dev/serial0 (GPIO 14/15).'),
        ('Redes Registradas: ', 'WiFi DroneLab (192.168.137.145), Ethernet link-local (169.254.174.253), Telemetría UDP 14550, Vídeo UDP 5600.')
    ]
    for title, desc in params:
        p_p = doc.add_paragraph(style='List Bullet')
        p_p.add_run(title).bold = True
        p_p.add_run(desc)

    add_styled_heading(doc, '3. Hoja de Ruta Consolidada (Next Steps)', 1)
    next_steps = [
        ('Fase 1: Configurar MikroTik en Modo AP: ', 'Abrir WinBox en el portátil, conectar a 192.168.1.1, configurar Quick Set en Home AP con SSID Voyager_3 y servidor DHCP activo (192.168.1.10 - 192.168.1.200).'),
        ('Fase 2: Parche de Red en runDrone.sh: ', 'Fijar UseMaintenanceIP=1 en la Raspberry Pi y comentar el ping a Grecia para arranque local instantáneo.'),
        ('Fase 3: Potencia del Chasis y Prueba de Actuadores: ', 'Conectar batería LiPo principal, encender el variador ESC (Bat1 > 7.4V), ejecutar param set ARMING_REQUIRE 0 y param set FS_THR_ENABLE 0, probando giro y avance en banco.'),
        ('Fase 4: Teleoperación en Suelo: ', 'Conducción inalámbrica por WiFi con mando o Mission Planner.'),
        ('Fase 5: Migración a ROS 2: ', 'Flashear nueva microSD con Ubuntu Server 22.04 LTS (64-bit) y ROS 2 Humble + MAVROS 2 para SLAM y navegación autónoma.')
    ]
    for title, desc in next_steps:
        p_n = doc.add_paragraph(style='List Bullet')
        p_n.add_run(title).bold = True
        p_n.add_run(desc)

    out_file = r'D:\Voyager\analisis_sistema\GUIA_CIERRE_Y_CONFIGURACIONES.docx'
    doc.save(out_file)
    print('Saved:', out_file)

def generate_ros2_plan_docx():
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)

    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(20)
    title_run = title_p.add_run('Plan de Migración y Control en ROS 2')
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = COLOR_PRIMARY
    title_run.bold = True

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run('UGV Voyager 3 — Arquitectura de Tópicos, MAVROS 2, Navegación Nav2 y Gemelo Digital')
    sub_run.font.name = 'Calibri'
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = COLOR_SECONDARY
    sub_run.italic = True

    add_styled_heading(doc, '1. Justificación de la Migración a ROS 2', 1)
    doc.add_paragraph().add_run('El sistema operativo actual (Raspbian Stretch de 32 bits, 2018) representa un cuello de botella insalvable para la robótica moderna. No admite ROS 2 ni librerías actuales de Python 3. La migración a Ubuntu Server 22.04 LTS (64-bit arm64) con ROS 2 Humble permite integrar el vehículo en pipelines de navegación autónoma (Nav2), percepción con LiDAR 360° y validación previa en entornos de simulación física.')

    add_styled_heading(doc, '2. Arquitectura de Integración MAVROS 2', 1)
    doc.add_paragraph().add_run('La Raspberry Pi se comunicará con la Pixhawk por el puerto serie UART /dev/ttyAMA0 a 921.600 bps mediante el nodo mavros. Esto expone todos los sensores y actuadores como tópicos estándar de ROS 2:')
    
    headers = ['Tópico de ROS 2', 'Tipo de Mensaje', 'Función / Flujo']
    widths = [Inches(2.5), Inches(2.2), Inches(2.0)]
    data = [
        ['/cmd_vel', 'geometry_msgs/msg/Twist', 'Entrada de teleoperación o navegación autónoma (velocidad lineal y angular).'],
        ['/mavros/imu/data', 'sensor_msgs/msg/Imu', 'Datos inerciales filtrados de la Pixhawk (50 Hz).'],
        ['/mavros/battery', 'sensor_msgs/msg/BatteryState', 'Monitoreo de voltaje, corriente y nivel de carga de la batería.'],
        ['/mavros/global_position/raw/fix', 'sensor_msgs/msg/NavSatFix', 'Coordenadas satelitales GPS en vivo.'],
        ['/scan', 'sensor_msgs/msg/LaserScan', 'Barrido 360° del LiDAR LightWare SF40 para algoritmos de SLAM.']
    ]
    t = doc.add_table(rows=1, cols=3)
    format_table(t, widths, headers, data)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_styled_heading(doc, '3. Simulación y Transferencia Sim-to-Real', 1)
    doc.add_paragraph().add_run('Al disponer del modelo cinemático Ackermann (radio de giro, límites de dirección 1100-1900 us) y las características del LiDAR, el vehículo puede ser simulado fielmente en entornos de simulación de robótica para validar trayectorias antes de la ejecución física.')

    out_path = r'D:\Voyager\analisis_sistema\PLAN_MIGRACION_ROS2.docx'
    doc.save(out_path)
    print('ROS 2 Plan DOCX saved:', out_path)

if __name__ == '__main__':
    generate_bitacora()
    generate_guia_cierre()
    generate_ros2_plan_docx()

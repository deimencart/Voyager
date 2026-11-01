import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('voyager_bringup')
    mavros_config_path = os.path.join(pkg_bringup, 'config', 'mavros_config.yaml')
    default_rviz_config = os.path.join(pkg_bringup, 'config', 'voyager_outdoor_nav.rviz')

    # Argumentos de configuración del sistema
    enable_mavros_arg = DeclareLaunchArgument(
        'enable_mavros',
        default_value='true',
        description='Inicia MAVROS para GPS, IMU, odometría y telemetría Pixhawk'
    )
    enable_lidar_arg = DeclareLaunchArgument(
        'enable_lidar',
        default_value='true',
        description='Inicia sf40_scan_node para LaserScan (/scan) y Arc-Cloud 3D (/cloud)'
    )
    enable_camera_arg = DeclareLaunchArgument(
        'enable_camera',
        default_value='true',
        description='Inicia camera_receiver_node para streaming H.264 (/camera/image_raw)'
    )
    enable_teleop_arg = DeclareLaunchArgument(
        'enable_teleop',
        default_value='true',
        description='Inicia ackermann_steering_teleop_node para control /cmd_vel y E-STOP'
    )
    enable_nav_arg = DeclareLaunchArgument(
        'enable_nav',
        default_value='false',
        description='Inicia control reactivo Nearness Diagram (ND)'
    )
    enable_gps_nav_arg = DeclareLaunchArgument(
        'enable_gps_nav',
        default_value='false',
        description='Inicia guiado autónomo por waypoints GPS Pure Pursuit con soporte RViz'
    )
    enable_slam_arg = DeclareLaunchArgument(
        'enable_slam',
        default_value='false',
        description='Inicia SLAM Toolbox (modo online sync) con parámetros de Voyager 3'
    )
    enable_rviz_arg = DeclareLaunchArgument(
        'enable_rviz',
        default_value='false',
        description='Lanza la interfaz gráfica de supervisión RViz 2 con mapa satelital'
    )
    fcu_url_arg = DeclareLaunchArgument(
        'fcu_url',
        default_value='udp://@127.0.0.1:14550',
        description='URL de conexión MAVLink (udp://@127.0.0.1:14550 o /dev/serial0:921600)'
    )

    # 1. MAVROS: GPS, Odometría, Velocidades del Rover, IMU y Estado
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_mavros')),
        parameters=[
            mavros_config_path,
            {
                'fcu_url': LaunchConfiguration('fcu_url'),
                'gcs_url': 'udp://@192.168.137.255:14550'
            }
        ]
    )

    # 2. LiDAR SF40/C: LaserScan 2D (/scan) y Arc-Cloud 3D (/cloud)
    lidar_node = Node(
        package='voyager_navigation',
        executable='sf40_scan_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_lidar'))
    )

    # 3. Cámara CSI Raspberry Pi (Sony IMX219): Imagen (/camera/image_raw)
    camera_node = Node(
        package='voyager_bringup',
        executable='camera_receiver_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_camera')),
        parameters=[{
            'port': 5600,
            'fps': 30.0,
            'frame_id': 'camera_optical_frame'
        }]
    )

    # 4. Teleoperación y E-STOP Ackermann (/cmd_vel -> MAVLink RC Override)
    teleop_node = Node(
        package='voyager_navigation',
        executable='ackermann_steering_teleop_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_teleop')),
        parameters=[{
            'pwm_trim': 1470,
            'pwm_min': 1050,
            'pwm_max': 1950,
            'throttle_neutral': 1485,
            'pwm_forward_max': 1750,
            'pwm_reverse_min': 1350,
            'watchdog_timeout': 0.3
        }]
    )

    # 5. Navegación Reactiva Nearness Diagram (Opcional)
    nd_node = Node(
        package='voyager_navigation',
        executable='nearness_diagram_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_nav')),
        parameters=[{
            'wheelbase_L': 0.35,
            'max_linear_vel': 0.8,
            'max_steering_angle': 0.436,
            'security_dist_ds': 0.8
        }],
        remappings=[
            ('/scan', '/scan'),
            ('/mavros/setpoint_velocity/cmd_vel', '/mavros/setpoint_velocity/cmd_vel')
        ]
    )

    # 6. Guiado Autónomo por Waypoints GPS Pure Pursuit con Publicadores RViz 2
    gps_node = Node(
        package='voyager_navigation',
        executable='gps_waypoint_follower',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_gps_nav')),
        parameters=[{
            'wheelbase_L': 0.33,
            'max_steering_angle': 0.436,
            'max_linear_vel': 0.8,
            'min_linear_vel': 0.2,
            'look_ahead_distance': 2.0,
            'acceptance_radius': 1.5,
            'demo_circuit': True
        }]
    )

    # 7. Visualización y Supervisión Gráfica en RViz 2 (WSLg)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', default_rviz_config],
        condition=IfCondition(LaunchConfiguration('enable_rviz'))
    )

    # 8. Transformada Estática de Compatibilidad: base_link -> base_footprint (REP 105 / Nav2 / SLAM)
    base_footprint_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_base_footprint',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint']
    )

    # 9. SLAM Toolbox Online Sync (Mapeo 2D adaptado a Voyager 3)
    slam_config_path = os.path.join(pkg_bringup, 'config', 'slam_toolbox_params.yaml')
    slam_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_config_path, {'use_sim_time': False}],
        condition=IfCondition(LaunchConfiguration('enable_slam'))
    )

    return LaunchDescription([
        enable_mavros_arg,
        enable_lidar_arg,
        enable_camera_arg,
        enable_teleop_arg,
        enable_nav_arg,
        enable_gps_nav_arg,
        enable_slam_arg,
        enable_rviz_arg,
        fcu_url_arg,
        base_footprint_tf_node,
        mavros_node,
        lidar_node,
        camera_node,
        teleop_node,
        nd_node,
        gps_node,
        slam_node,
        rviz_node
    ])

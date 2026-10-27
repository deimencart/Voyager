import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('voyager_bringup')
    mavros_config_path = os.path.join(pkg_bringup, 'config', 'mavros_config.yaml')

    # Nodo MAVROS para interfaz con la Pixhawk 1 por UART
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        output='screen',
        parameters=[
            mavros_config_path,
            {
                'fcu_url': '/dev/serial0:921600',
                'gcs_url': 'udp://@192.168.4.255:14550'
            }
        ]
    )

    # Nodo Nearness Diagram para control reactivo Ackermann
    nd_node = Node(
        package='voyager_navigation',
        executable='nearness_diagram_node',
        output='screen',
        parameters=[{
            'wheelbase_L': 0.32,
            'max_linear_vel': 0.8,
            'max_steering_angle': 0.45,
            'security_dist_ds': 0.8
        }],
        remappings=[
            ('/scan', '/scan'),
            ('/mavros/setpoint_velocity/cmd_vel', '/mavros/setpoint_velocity/cmd_vel')
        ]
    )

    return LaunchDescription([
        mavros_node,
        nd_node
    ])

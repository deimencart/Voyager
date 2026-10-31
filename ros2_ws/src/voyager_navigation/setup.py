from setuptools import setup

package_name = 'voyager_navigation'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Voyager Team',
    maintainer_email='diego.mencart@gmail.com',
    description='Nearness Diagram Ackermann Navigation for Voyager 3',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'nearness_diagram_node = voyager_navigation.nearness_diagram_ackermann_node:main',
            'sf40_scan_node = voyager_navigation.sf40_scan_node:main',
            'ackermann_steering_teleop_node = voyager_navigation.ackermann_steering_teleop_node:main',
            'voyager_teleop_key = voyager_navigation.voyager_teleop_key_node:main',
            'gps_waypoint_follower = voyager_navigation.gps_waypoint_follower_node:main',
        ],
    },
)

from setuptools import find_packages, setup

# add by nishi
import os
from glob import glob

package_name = 'mini_pupper_ros_my_ap'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # add by nishi
        (os.path.join('share', package_name,'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name,'launch','config'), glob('launch/config/*.rviz')),
        (os.path.join('share', package_name,'params','foxbot_core3'), glob('params/foxbot_core3/*.yaml')),
        (os.path.join('share', package_name,'params','foxbot_nav2'), glob('params/foxbot_nav2/*.yaml')),
        (os.path.join('share', package_name,'params','turtlebot3_gazebo/depth'), glob('params/turtlebot3_gazebo/depth/*.yaml')),
        (os.path.join('share', package_name,'params','tugbot_gazebo/depth'), glob('params/tugbot_gazebo/depth/*.yaml')),
        (os.path.join('share', package_name,'params','nav2'), glob('params/nav2/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nishi',
    maintainer_email='non@netosa.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'odom_bridge_tf = mini_pupper_ros_my_ap.odom_bridge_tf:main', # 👈 これを追記
            'imu_noise = mini_pupper_ros_my_ap.imu_noise:main', # imu_noise.py
        ],
    },
)

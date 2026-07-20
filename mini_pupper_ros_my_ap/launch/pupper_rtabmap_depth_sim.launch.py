# -*- coding: utf-8 -*-
#
#  mini_pupper_ros_my/mini_pupper_ros_my_ap/launch/pupper_rtabmap_depth_sim.launch.py
#  base:rtabmap_ros_my/launch/tugbot_depth.launch.py
#
#  Rtabmap_ros with depth Mapping or Acitve SLAM
#
# 1. build on SBC and PC
#  $ colcon build --symlink-install --parallel-workers 1 --packages-select mini_pupper_ros_my_ap
#  $ . install/setup.bash
#
# 2. disable firewall on remote PC
#  $ sudo ufw disable
#
# 3 run
# 3.1 Gazebo
#  $ ros2 launch mini_pupper_simulation bringup.launch.py
#    or with GPU
#  $ __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia ros2 launch mini_pupper_simulation bringup.launch.py
#
# 3.2 run rtabmap_ros on remote PC or SBC
#  1) term2
#   $ ros2 launch mini_pupper_ros_my_ap pupper_rtabmap_depth_sim.launch.py SBC:=true
#
#  2) rviz
#   $ ros2 launch mini_pupper_ros_my_ap pupper_rtabmap_depth_sim.launch.py PC:=true
#    注) Map topic は、/rtabmap/map  -> /map に変える
#
# 4. Remote control
# 4.1 Remote PC /cmd_vel controll  -- Mapping
#  1) Teleop keyboard
#   $ ros2 run teleop_twist_keyboard teleop_twist_keyboard
#
# これ以降は、まだです。by nishi 2026.7.19
#
#  2) drive_base
#   $ ros2 run turtlebot3_navi_my drive_base
#
# 5.2 Remote PC or SBC / navigation2  ---  Acitve SLAM
#  1) check
#   $ ros2 topic hz /cloudXYZ
#
#  1'') navigation2 rpp_planner
#   #$ ros2 launch nav2_bringup navigation_launch.py use_sim_time:=False params_file:=/home/nishi/colcon_ws-jazzy/src/rtabmap_ros_my/params/foxbot_core3/oak-d_rpp_params_ekf.yaml
#   $ ros2 launch rtabmap_ros_my navigation.launch.py use_sim_time:=False params_file:=/home/nishi/colcon_ws-jazzy/src/rtabmap_ros_my/params/foxbot_core3/oak-d_rpp_params_ekf.yaml
#
#  5.3 Rviz2 on Remote PC
#  1) Rviz2
#    $ ros2 launch nav2_bringup rviz_launch.py
#     or
#   $ ros2 launch rtabmap_ros_my rtabmap_oak-d_rgb_depth.launch.py PC2:=true
#
#
#  5.4 robot control #2  on SBC or Remote PC
#  1)  Teleop keyboard
#   $ ros2 run turtlebot3_teleop teleop_keyboard
#
#  1') C++ Program controll
#   #$ ros2 run turtlebot3_navi_my multi_goals4_nav2
#   $ ros2 launch turtlebot3_navi_my multi_goals4_nav2.launch.py use_sim_time:=False
#
# append.
# how to map save ,on Remote PC OK
# ros2 run nav2_map_server map_saver_cli -f ~/map/my_map --ros-args -p save_map_timeout:=10000.0

import os
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, Substitution, LaunchContext
from launch.actions import IncludeLaunchDescription
from launch.actions import GroupAction
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, LogInfo, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition

from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir, PythonExpression
from typing import Text

from launch_ros.actions import Node

class ConditionalText(Substitution):
    def __init__(self, text_if, text_else, condition):
        self.text_if = text_if
        self.text_else = text_else
        self.condition = condition

    def perform(self, context: 'LaunchContext') -> Text:
        if self.condition == True or self.condition == 'true' or self.condition == 'True':
            return self.text_if
        else:
            return self.text_else


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    qos = LaunchConfiguration('qos')
    localization = LaunchConfiguration('localization')

    config_rviz = os.path.join(
        get_package_share_directory('rtabmap_launch'), 'launch', 'config', 'rgbd.rviz'
    )

    bringup_dir = get_package_share_directory('nav2_bringup')
    config_rviz2=os.path.join(bringup_dir, 'rviz', 'nav2_default_view.rviz'),

    mini_pupper_ros_my_ap=get_package_share_directory('mini_pupper_ros_my_ap')

    parameters={
          #'frame_id':'base_footprint',
          'frame_id':'base_link',
          'use_sim_time':use_sim_time,
          'subscribe_depth':True,
          'use_action_for_goal':True,
          'qos_image':qos,
          'qos_imu':qos,
          'approx_sync': True,
          'queue_size': 20,
          #"queue_size": 20,
          'sync_queue_size': 20,  # add by nishi 2024.9.10
          'topic_queue_size': 20, # add by nishi 2024.9.10
          'buffer_size': 30, 
          'Reg/Force3DoF':'true',
          'Optimizer/GravitySigma':'0', # Disable imu constraints (we are already in 2D)
          #'Vis/MaxDepth':'3.0',        # add by nishi 2024.3.11 No Need
          #'Vis/MeanInliersDistance':'3.0',  # add by nishi 2024.3.11 No Need
          #'Kp/MaxDepth':'3.0',  # add by nishi 2024.3.11 No Need
          #'Grid/RangeMax': '3.0',    # add by nishi 
          'Grid/RangeMax': '10.0',    # add by nishi 
          #'Grid/MinGroundHeight':'0.01',   # add by nishi 2024.3.12 No Need
          'Grid/MaxGroundHeight':'0.05',    # add by nishi 2024.3.12 Very Good!! 3[M] 先の床が障害物になるのを防ぐ
          'Grid/MaxObstacleHeight':'0.7',   # add by nishi 2024.3.11 Needed
          #'Grid/RangeMax':'2.8', # add by nishi 2024.3.11 Ok !!
          #'RGBD/OptimizeMaxError' : '3.3',  # test by nishi 2024.3.12
          'RGBD/OptimizeMaxError' : '2.8',  # test by nishi 2024.3.12
          #'Mem/SaveDepth16Format':'true', # add by nishi 2025.10.22
          'approx_sync_max_interval': 3.0, 
          'wait_for_transform' : 1.5,
          # add by nishi 2026.7.18
          "Rtabmap/DetectionRate": "2.0", # 地図の更新頻度を上げる (Hz)
          "RGBD/ProximityBySpace": "true", # 近くを通ったときに過去の地図とマッチングさせる
          "RGBD/OptimizeFromGraphEnd": "true", # ロボットの最新位置を基準に地図を最適化する

    }
    rtabmap_remappings=[
        # subscribe
        ("rgb/image","/camera/image"),
        ("rgb/camera_info","/camera/camera_info"),
        ("depth/image","/camera/depth_image"),
        ("odom", "/odom"),      # gazebo mini_pupper_simulation で、 /odom/raw を、publish する。
        #("odom", "/odom/raw"),      # gazebo mini_pupper_simulation で、 /odom/raw を、publish する。
        #("odom", "/odom_fox"),    # foxbot_core3_r2.ino で、 /odom_fox を、publish する。
        # /rtabmap/rgbd_image
        # publish
        ('map','/map'),
        ]

    #[rtabmap-1] rtabmap subscribed to (approx sync):
    #[rtabmap-1]    /odom/raw \   --> こいつの time が、 PC の時刻のまま
    #[rtabmap-1]    /camera/image \
    #[rtabmap-1]    /camera/depth_image \
    #[rtabmap-1]    /camera/camera_info

    rtabmap_rviz_remappings=[
        # subscribe
        #("rgb/image","/rtabmap/rgbd_image"),
        ("rgb/image","/camera/image"),
        #('rgb/camera_info', '/right/camera_info'),
        ('rgb/camera_info', '/camera/camera_info'),
        ("odom", "/odom"),
        #("odom", "/odom_fox"),
        #('depth/image', '/rtabmap/depth/image')
        ("depth/image","/camera/depth_image"),
        # publish
        # 'mapData'
        # 'mapGraph'
        #('map','/map'),
        ]

    #[rtabmap_viz-1] rtabmap_viz subscribed to (approx sync):
    #[rtabmap_viz-1]    /odom \
    #[rtabmap_viz-1]    /rtabmap/rgbd_image \
    #[rtabmap_viz-1]    /rtabmap/depth/image \
    #[rtabmap_viz-1]    /right/camera_info

    return LaunchDescription([
        DeclareLaunchArgument('SBC', default_value='false', description='Launch SBC (optional).'),
        DeclareLaunchArgument('PC', default_value='false', description='Launch PC (optional).'),

        # Launch arguments
        DeclareLaunchArgument('use_sim_time', default_value='true',description='Use simulation (Gazebo) clock if true'),
        #DeclareLaunchArgument('qos', default_value='2',description='QoS used for input sensor topics'),
        DeclareLaunchArgument('qos', default_value='1',description='QoS used for input sensor topics'),
        DeclareLaunchArgument('localization', default_value='false',description='Launch in localization mode.'),

        DeclareLaunchArgument('rtabmapviz',default_value='false', description='Launch rtabmapviz (optional).'),
        DeclareLaunchArgument('rviz',default_value='true', description='Launch RVIZ (optional).'),
        DeclareLaunchArgument('rviz_cfg', default_value=config_rviz, description='Configuration path of rviz2.'),
        DeclareLaunchArgument('rviz_cfg2', default_value=config_rviz2, description='Configuration path of rviz2.'),

        DeclareLaunchArgument('cloud_xyzrgb',default_value='false', description='cloud_xyzrgb.'),

        DeclareLaunchArgument('namespace', default_value='rtabmap', description=''),

        GroupAction(
            [
                # 自作 tool を使う
                # /imu/data から、 noise を載せた /imu/data_fixed を作る
                # /odom/raw から /odom/raw_fixed に変換する。
                Node(
                    package='mini_pupper_ros_my_ap',  # あなたのパッケージ名
                    executable='imu_noise',      # setup.py に書いた名前
                    name='imu_noise_node',
                    output='screen',
                    parameters=[{'use_sim_time': True}], # 👈 シミュレーション時間に対応させる
                    namespace=LaunchConfiguration('namespace'),
                ),

                # ekf を使う
                Node(
                    package='robot_localization', executable='ekf_node', name='ekf_filter_node', output='screen',
                    parameters=[os.path.join(get_package_share_directory("mini_pupper_ros_my_ap"), 'params','nav2', 'ekf.yaml')],
                    remappings=[
                        # subscribe
                        ('wheel', '/odom/raw'), 
                        #('odom_gps', '/odom_gps'),
                        #('imu0', '/imu'),
                        #('imu/data', '/imu_fox'),
                        # publish
                        #('odometry/filtered', '/odom_fusion'),
                        ('odometry/filtered', '/odom'),
                        ],
                ),

                Node(
                    # https://github.com/ros-perception/image_pipeline/tree/foxy/depth_image_proc/src
                    # camera_info (sensor_msgs/CameraInfo) 
                    # image_rect (sensor_msgs/Image) 
                    package='rtabmap_util', executable='point_cloud_xyz', output='screen',
                    parameters=[{
                        "decimation": 4,
                        #"voxel_size": 0.0,
                        # changed by nishi 2024.5.9
                        "voxel_size": 0.05,
                        "approx_sync": True,
                        #"exact_sync": True,
                        #"approx_sync_max_interval": 0.1 ,
                        #"approx_sync_max_interval": 0.2 ,
                        "approx_sync_max_interval": 0.5 ,
                        #"approx_sync_max_interval": 0.7 ,
                        "qos": qos,
                        #"qos": 1,
                        'use_sim_time':True,
                    }],
                    remappings=[
                        #('disparity/image', '/disparity'),   #
                        #('disparity/camera_info', '/right/camera_info'),
                        #('depth/camera_info','/stereo/camera_info'),
                        ('depth/camera_info','/camera/camera_info'),
                        #('depth/image','/stereo/depth'),
                        ('depth/image','/camera/depth_image'),
                        ('cloud', '/cloudXYZ')],
                    # subscribe
                    #  depth/camera_info
                    #  depth/image
                    #  ------
                    #  disparity/camera_info
                    #  disparity/image
                    # publish
                    #  cloud
                    namespace=LaunchConfiguration('namespace'),
                ),

                # SLAM mode:
                Node(
                    condition=UnlessCondition(localization),
                    package='rtabmap_slam', executable='rtabmap', output='screen',
                    parameters=[parameters],
                    remappings=rtabmap_remappings,
                    arguments=['-d'],
                    namespace=LaunchConfiguration('namespace'),
                ), # This will delete the previous database (~/.ros/rtabmap.db)
                    
                # Localization mode:
                Node(
                    condition=IfCondition(localization),
                    package='rtabmap_slam', executable='rtabmap', output='screen',
                    parameters=[parameters,
                    {'Mem/IncrementalMemory':'False',
                    'Mem/InitWMWithAllNodes':'True'}],
                    remappings=rtabmap_remappings,
                    namespace=LaunchConfiguration('namespace'),
                ),
            ],
            condition=IfCondition(LaunchConfiguration('SBC')),
            #condition=IfCondition(PythonExpression(["'",LaunchConfiguration('SBC'), "' == 'true'"])),
        ),

        GroupAction(
            [
            Node(
                condition=IfCondition(LaunchConfiguration('rtabmapviz')),
                package='rtabmap_viz', executable='rtabmap_viz', output='screen',
                parameters=[parameters],
                remappings=rtabmap_rviz_remappings,
                # subscribe
                #/rtabmap/global_path
                #/rtabmap/goal_node
                #/rtabmap/goal_reached
                #/rtabmap/info
                #/rtabmap/mapData
                #/rtabmap/odom
                #/rtabmap/rtabmap/republish_node_data
                #/rtabmap/scan
                namespace=LaunchConfiguration('namespace'),
                ),

            Node(
                package='rviz2', executable='rviz2', output='screen',
                condition=IfCondition(LaunchConfiguration("rviz")),
                arguments=[["-d"], [LaunchConfiguration("rviz_cfg")]],  # 3D の表示はこちら
                #arguments=[["-d"], [LaunchConfiguration("rviz_cfg2")]],    # 2D の表示は、こちら
                ),
            ],
            condition=IfCondition(LaunchConfiguration('PC')),
            #condition=IfCondition(PythonExpression(["'",LaunchConfiguration('PC'), "' == 'true'"])),
        ),
    ])

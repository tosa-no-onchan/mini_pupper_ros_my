#!/usr/bin/env python3
#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2026 MangDang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# build
#  $ colcon build --symlink-install --parallel-workers 1 --packages-select mini_pupper_simulation
#  $ . install/setup.bash
#
# run
# $ ros2 launch mini_pupper_simulation gazebo.launch.py
#
# $ ros2 launch mini_pupper_simulation bringup.launch.py

import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

# add by nishi 2026.7.14
from launch_ros.actions import Node

def generate_launch_description():
    this_package = FindPackageShare('mini_pupper_simulation')

    default_world = PathJoinSubstitution([this_package, 'worlds', 'mini_pupper_home.world'])

    world = LaunchConfiguration('world')
    world_launch_arg = DeclareLaunchArgument(
        name='world',
        default_value=default_world,
        description='Gazebo world path'
    )

    #gazebo_launch_path = PathJoinSubstitution([
    #    FindPackageShare('gazebo_ros'),
    #    'launch',
    #    'gazebo.launch.py'
    #])
    # パッケージ名を 'ros_gz_sim' に、起動ファイル名を 'gz_sim.launch.py' に変更
    gazebo_launch_path = PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py'
    ])

    gui = LaunchConfiguration('gui')
    gui_launch_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Whether to start the Gazebo GUI'
    )

    #gazebo_launch = IncludeLaunchDescription(
    #    PythonLaunchDescriptionSource(gazebo_launch_path),
    #    launch_arguments={
    #        'world': world,
    #        'gui': gui,
    #    }.items()
    #)
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_path),
        launch_arguments={
            # -r オプションは起動と同時にシミュレーションを自動再生する設定
            'gz_args': [world, ' -r'] 
            # '-s' を追加して画面非表示（Server only）にし、'-r' で自動再生します。 by nishi 2026.7.14
            #'gz_args': ['-s ', world, ' -r'] 
        }.items()
    )

    # add by nishi 2026.7.14
    # GazeboのClockトピックをROS 2の /clock トピックに変換するブリッジ
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # YAML設定ファイルのパスを取得
    bridge_config = os.path.join(
        get_package_share_directory('mini_pupper_simulation'),
        'config',
        'mini_pupper_bridge.yaml'
    )

    # Gazebo Harmonic と ROS 2 Jazzy のセンサー通信ブリッジ設定
    # ブリッジノードの定義
    sensor_bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
        }],
        output='screen',
    )

    return LaunchDescription([
        world_launch_arg,
        gui_launch_arg,
        gazebo_launch,
        clock_bridge,
        sensor_bridge_node, # ◀◀ これを追記してリストに追加する
    ])

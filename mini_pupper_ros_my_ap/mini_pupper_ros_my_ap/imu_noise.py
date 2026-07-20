#!/usr/bin/env python3
# imu_nose.py
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from sensor_msgs.msg import Imu  # 👈 IMUメッセージを追加
import math

class ImuNoise(Node):
    def __init__(self):
        super().__init__('imu_noise_node')
        
        # 1. 動作検証用のログを出力
        self.get_logger().info('=== Imu Noise & Odom Fixer Node Started ===')
        
        # 変数の初期化（前回の位置と、IMUの最新Yawを保持）
        self.last_raw_x = None
        self.last_raw_y = None
        self.fixed_x = 0.0
        self.fixed_y = 0.0
        self.current_imu_yaw = 0.0

        # --- 🆕 [新規] IMUの修理設定 ---
        # Gazeboが出す共分散0のトピックを購読
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        # EKFに渡すための、修理済みトピックを配信
        self.imu_pub = self.create_publisher(Imu, '/imu/data_fixed', 10)

        # --- 2. オドメトリの強制幾何学修正設定 ---
        self.odom_sub = self.create_subscription(Odometry, '/odom/raw', self.odom_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom/raw_fixed', 10)

        # --- スリップ率 の設定
        # 自分で、ロボットの移動距離の誤差に応じてセット
        self.slip_rate = 0.67


    # --- 🆕 [新規] IMUの共分散を書き換えるコールバック関数 ---
    def imu_callback(self, msg):
        # ⭕️ クォータニオンからオイラー角（Yaw）を計算して記憶しておく
        q = msg.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_imu_yaw = math.atan2(siny_cosp, cosy_cosp)

        fixed_msg = msg  # データをコピー
        # ⭕️ すべて0.0だった共分散行列に、適当な信頼度（0.01）を代入して修理する
        # [ロール, ピッチ, ヨー] のそれぞれの分散に 0.01（標準偏差0.1ラジアン≒約5.7度）を設定
        fixed_msg.orientation_covariance[0] = 0.01  # Roll
        fixed_msg.orientation_covariance[4] = 0.01  # Pitch
        fixed_msg.orientation_covariance[8] = 0.01  # Yaw (ここが一番大事！)
        # 修理したデータを配信
        self.imu_pub.publish(fixed_msg)

    def odom_callback(self, msg):
        current_raw_x = msg.pose.pose.position.x
        current_raw_y = msg.pose.pose.position.y

        # 初回コールバック時は前回の位置として記憶して終了
        if self.last_raw_x is None:
            self.last_raw_x = current_raw_x
            self.last_raw_y = current_raw_y
            return

        # 1) 前回からの移動距離（純粋なスカラ値のdelta dist）を計算
        dx_raw = current_raw_x - self.last_raw_x
        dy_raw = current_raw_y - self.last_raw_y
        delta_dist = math.sqrt(dx_raw**2 + dy_raw**2) * self.slip_rate

        # 記憶を更新
        self.last_raw_x = current_raw_x
        self.last_raw_y = current_raw_y

        # 2) & 3) IMUの正しいYawを使って、移動距離をX, Y成分に再マッピングして累積加算
        # stanford_controllerがどう勘違いしていようが、足が前に進んだ「距離」だけを盗んでIMUの向きに歩かせます
        self.fixed_x += delta_dist * math.cos(self.current_imu_yaw)
        self.fixed_y += delta_dist * math.sin(self.current_imu_yaw)

        # 新たな /odom/raw_fix メッセージの作成
        fix_msg = msg  # ベースのメッセージ構造をコピー
        fix_msg.header.frame_id = 'odom'
        fix_msg.child_frame_id = 'base_link'
        
        # 修正されたX, Yを代入
        fix_msg.pose.pose.position.x = self.fixed_x
        fix_msg.pose.pose.position.y = self.fixed_y
        
        # 方位情報も、100%信用できる現在のIMUのクォータニオンを完全コピーして上書き
        fix_msg.pose.pose.orientation = fix_msg.pose.pose.orientation # (必要なら上書き)

        # 修正済みオドメトリを配信
        self.odom_pub.publish(fix_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImuNoise()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


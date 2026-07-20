# odom_bridge_tf.py

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster

class OdomBridgeTf(Node):
    def __init__(self):
        super().__init__('odom_bridge_tf_node')
        
        # 1. 動作検証用のログを出力
        self.get_logger().info('=== Odom Bridge TF Node Started ===')
        
        # 2. TF配信用のブロードキャスターを初期化
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # 3. /odom/raw トピックをサブスクライブ
        # (stanford_controller からのデータを待ち受けます)
        self.subscription = self.create_subscription(
            Odometry,
            '/odom/raw',
            self.odom_callback,
            10
        )
        self.counter = 0
        # 👇 時間逆行ガード用の変数を追加
        self.last_stamp_nanos = 0 

    def odom_callback(self, msg):

        # 現在のトピックの時間をナノ秒換算
        current_nanos = msg.header.stamp.sec * 1000000000 + msg.header.stamp.nanosec
        
        # 🚨【ガードレール】もし過去の時間が来たら、処理を無視して終了（TFバッファを守る）
        if current_nanos <= self.last_stamp_nanos:
            return
        self.last_stamp_nanos = current_nanos # 最新の時間を記憶

        self.counter += 1
        
        # 検証用：50回に1回、受け取ったタイムスタンプと位置をターミナルに表示する
        if self.counter % 50 == 0:
            self.get_logger().info(
                f"[検証] トピック受信! 時間: {msg.header.stamp.sec}.{msg.header.stamp.nanosec}秒, "
                f"X: {msg.pose.pose.position.x:.2f}, Y: {msg.pose.pose.position.y:.2f}"
            )
            
        # 4. 受け取ったオドメトリ情報から TF (座標変換) メッセージを作成
        t = TransformStamped()
        
        # トピックのHeader情報をそのままTFに完全コピー（同期用）
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'  # 👈 切れていたフレーム名を指定
        #t.child_frame_id = 'base_footprint' # rtabmapにはここを見せる
        
        # ⭕ 車体中心(base_link)のオドメトリから、Mini Pupperの足の長さ（例: 8cm = 0.08m）を引いて床面を作る
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        #t.transform.translation.z = msg.pose.pose.position.z
        t.transform.translation.z = msg.pose.pose.position.z - 0.08  # 👈 ここで床面（0）に叩き落とす！
        
        # 回転（姿勢）をコピー
        t.transform.rotation = msg.pose.pose.orientation
        
        # 5. TFツリーに配信！
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdomBridgeTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


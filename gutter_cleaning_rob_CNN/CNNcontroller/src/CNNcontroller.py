#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import subprocess  # subprocess 모듈 추가

def cnn_restart_callback(data):
     if data.data == "RESTART CNN" or data.data == "CAR OVER":
        rospy.loginfo("Received restart signal: %s", data.data)
        restart_cnn()  # CNN 재시작 함수를 호출하는 것이 가능

def restart_cnn():
    rospy.loginfo("Restarting CNN processing...")
    # inference.py 스크립트 실행
    try:
        result = subprocess.run(['python', '/path/to/inference.py'], capture_output=True, text=True)
        rospy.loginfo("Inference output: %s", result.stdout)
    except Exception as e:
        rospy.logerr("Failed to run inference script: %s", e)

def main():
    rospy.init_node('CNNcontroller', anonymous=True)
    rospy.Subscriber('cnn_restart', String, cnn_restart_callback)
    rospy.Subscriber('car_overM2J', String, cnn_restart_callback) #car_overM2J == cnn start
    rospy.spin()  # ROS 이벤트 루프를 실행하여 콜백 함수가 계속 호출되게 함

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
      
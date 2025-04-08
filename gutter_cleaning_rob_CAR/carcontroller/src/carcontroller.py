#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import subprocess  # subprocess 모듈 추가

pub = None

def car_restart_callback(data): #restart 안에 start 의 의미도 포함. 즉 둘 다 같은 용도로 사용 
    if data.data == "RESTART CAR":
        rospy.loginfo("Received CAR restart signal: %s", data.data)
        pub.publish("CONTINUE")

def car_over_callback(data):
    if data.data == "CAR OVER":
        rospy.loginfo("Received CAR restart signal: %s", data.data)
        pub.publish("CAR OVER")
        
def car_controller():
    global pub  # 글로벌 변수를 사용하여 퍼블리셔를 초기화
    rospy.init_node('carcontroller', anonymous=True)
    pub = rospy.Publisher('car_command', String, queue_size=10)  
    rospy.Subscriber('car_restart', String, car_restart_callback)
    rospy.Subscriber('car_over', String, car_over_callback)  # car_over 콜백 추가
    rospy.spin()  # ROS 이벤트 루프를 실행하여 콜백 함수가 계속 호출되게 함

if __name__ == '__main__':
    try:
        car_controller()
    except rospy.ROSInterruptException:
        pass
  
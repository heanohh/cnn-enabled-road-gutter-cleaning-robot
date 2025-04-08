#!/usr/bin/env python3
import rospy
from robcontroller3.msg import Coordinate
from std_msgs.msg import String

pub = None  # 전역 변수로 발행자를 설정

def move_robot(data):
    rospy.loginfo(f"Received coordinates_re: x={data.x}, y={data.y}")
    pub.publish(data)

def robot_controller3():
    global pub
    rospy.init_node('robcontroller3', anonymous=True)
    pub = rospy.Publisher('robcoord2', Coordinate, queue_size=10)  # 발행자를 노드 초기화 시 한 번만 생성
    rospy.Subscriber('move_robot2', Coordinate, move_robot)
    rospy.spin()

if __name__ == '__main__':
    try:
        robot_controller3()
    except rospy.ROSInterruptException:
        pass

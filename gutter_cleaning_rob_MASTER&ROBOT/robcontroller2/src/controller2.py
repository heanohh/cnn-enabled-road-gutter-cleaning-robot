#!/usr/bin/env python3
import rospy
from std_msgs.msg import String

def rob1_completed_callback(data):
    if data.data == "rob1DONE":
        rospy.loginfo("Task completed signal received from robot_controller1")
        # 이미 생성된 발행자를 사용하여 메시지를 발행
        pub.publish("CONTINUE")

pub = rospy.Publisher('rob2start', String, queue_size=10)

def robot_controller2():
    rospy.init_node('robcontroller2', anonymous=True)
    rospy.Subscriber('rob1done', String, rob1_completed_callback)  # 올바른 콜백 함수 이름 사용
    rospy.spin()

if __name__ == '__main__':
    try:
        robot_controller2()
    except rospy.ROSInterruptException:
        pass

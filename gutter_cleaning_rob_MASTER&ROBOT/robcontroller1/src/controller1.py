#!/usr/bin/env python3
import rospy
from robcontroller1.msg import Coordinate
from std_msgs.msg import String

def move_robot(data):
    rospy.loginfo(f"Received coordinates1: x={data.x}, y={data.y}")
    pub = rospy.Publisher('robcoord1', Coordinate, queue_size=10)
    pub.publish(data)

def robot_controller1():
    rospy.init_node('robcontroller1', anonymous=True)
    rospy.Subscriber('move_robot1', Coordinate, move_robot)
    rospy.spin()

if __name__ == '__main__':
    try:
        robot_controller1()
    except rospy.ROSInterruptException:
        pass
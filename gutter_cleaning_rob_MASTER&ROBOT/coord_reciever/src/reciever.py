#!/usr/bin/env python3
import rospy
from coord_reciever.msg import Coordinate
from std_msgs.msg import String

def c1_callback(data):
    rospy.loginfo(f"Received coordinates1: x={data.x}, y={data.y}")
    pub = rospy.Publisher('move_robot1', Coordinate, queue_size=10)
    pub.publish(data)

def c2_callback(data):
    rospy.loginfo(f"Received coordinates2: x={data.x}, y={data.y}")
    pub = rospy.Publisher('move_robot2', Coordinate, queue_size=10)
    pub.publish(data)

def coordinate_listener1():
    rospy.init_node('coord_receiver1', anonymous=True)
    rospy.Subscriber('coordinate1', Coordinate, c1_callback)
    rospy.spin()

def coordinate_listener2():
    rospy.init_node('coord_receiver2', anonymous=True)
    rospy.Subscriber('coordinate2', Coordinate, c2_callback)
    rospy.spin()

if __name__ == '__main__':
    try:
        coordinate_listener1()
    except rospy.ROSInterruptException:
        try:
            coordinate_listener2()
        except rospy.ROSInterruptException:
            pass
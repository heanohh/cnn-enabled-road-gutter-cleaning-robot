#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image

image_pub = None
message_pub = None

def image_callback(msg):
    """
    Callback function for image messages.
    """
    rospy.loginfo("Received an image!")
    try:
        image_pub.publish(msg)
        rospy.loginfo("Image has been forwarded")
    except Exception as e:
        rospy.logerr("Could not forward the image: %s", str(e))

def message_callback(data):
    """
    Callback function for string messages.
    """
    rospy.loginfo("Received car_over message: %s", data.data)
    try:
        message_pub.publish(data)
        rospy.loginfo("Message has been forwarded to Jetson")
    except Exception as e:
        rospy.logerr("Could not forward the message: %s", str(e))

def main():
    rospy.init_node('bridge', anonymous=True)

    # Subscribers
    rospy.Subscriber("imageJ2M", Image, image_callback)
    rospy.Subscriber("car_command", String, message_callback)

    # Publishers
    global image_pub, message_pub
    image_pub = rospy.Publisher("imageM2C", Image, queue_size=10)
    message_pub = rospy.Publisher("car_overM2J", String, queue_size=10)

    rospy.spin()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
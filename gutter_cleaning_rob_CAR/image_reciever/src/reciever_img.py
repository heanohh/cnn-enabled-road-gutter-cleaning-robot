#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

def callback(img_msg):
    bridge = CvBridge()
    try:
        cv_image = bridge.imgmsg_to_cv2(img_msg, "bgr8")
        file_name = '/path/to/save/images/image_' + str(rospy.Time.now()) + '.jpg'
        cv2.imwrite(file_name, cv_image)
        rospy.loginfo("Image saved as: %s", file_name)
    except Exception as e:
        rospy.logerr("Failed to convert or save image: %s", str(e))

def main():
    rospy.init_node('image_reciever', anonymous=True)
    rospy.Subscriber("imageM2C", Image, callback)
    rospy.spin()

if __name__ == '__main__':
    main()
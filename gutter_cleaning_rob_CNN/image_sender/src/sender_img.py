#!/usr/bin/env python3
import rospy
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
import os

def load_and_publish_image(image_path, publisher):
    cv_image = cv2.imread(image_path)
    if cv_image is None:
        rospy.logerr("Failed to load image from %s", image_path)
        return

    try:
        bridge = CvBridge()
        ros_image = bridge.cv2_to_imgmsg(cv_image, "bgr8")
        publisher.publish(ros_image)
        rospy.loginfo("Published image to imageJ2M")
    except cv2.error as e:
        rospy.logerr("Failed to convert image: %s", str(e))

def main():
    rospy.init_node('sender_img', anonymous=True)
    pub = rospy.Publisher('imageJ2M', Image, queue_size=10)
    
    image_directory = '/path/to/your/image/folder'
    images = [os.path.join(image_directory, f) for f in os.listdir(image_directory) if f.endswith('.jpg')]
    
    rate = rospy.Rate(1)  # 1 Hz
    while not rospy.is_shutdown():
        for image_path in images:
            load_and_publish_image(image_path, pub)
            rate.sleep()

if __name__ == '__main__':
    main()
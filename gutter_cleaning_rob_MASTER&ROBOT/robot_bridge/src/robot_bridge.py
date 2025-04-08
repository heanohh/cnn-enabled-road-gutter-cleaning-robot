import rospy
from std_msgs.msg import String

def rob2_completed_callback(data):
    if data.data == "rob2DONE":
        rospy.loginfo("Task completed signal received from robot_controller2")
        send_signal_to_jetson("RESTART CNN")

def rob3_completed_callback(data):
    if data.data == "rob3DONE":
        rospy.loginfo("Task completed signal received from robot_controller3")
        send_signal_to_car("RESTART CAR")

def send_signal_to_jetson(signal):
    global pub_jetson
    pub_jetson.publish(signal)
    rospy.loginfo("Sent '%s' signal to Jetson" % signal)
    
def send_signal_to_car(signal):
    global pub_car
    pub_car.publish(signal)
    rospy.loginfo("Sent '%s' signal to Car" % signal)

def robot_over():
    global pub_jetson, pub_car
    rospy.init_node('robot_over', anonymous=True)
    
    # Create two different publishers for each signal destination
    pub_jetson = rospy.Publisher('cnn_restart', String, queue_size=10)
    pub_car = rospy.Publisher('car_restart', String, queue_size=10)
    
    # Subscribe to different topics
    rospy.Subscriber('task_completed_2', String, rob2_completed_callback)
    rospy.Subscriber('task_completed_3', String, rob3_completed_callback)

    rospy.spin()

if __name__ == '__main__':
    try:
        robot_over()
    except rospy.ROSInterruptException:
        pass
#include <ros.h>
#include <Servo.h>
#include <robcontroller3/Coordinate.h>
#include <std_msgs/String.h>

#define M_PI 3.1415926535897932384626433832795

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

ros::NodeHandle nh;

std_msgs::String done_msg;
ros::Publisher task_completed_pub("task_completed_r3", &done_msg);

const float l1 = 250.0;  
const float l2 = 100.0;  
const float l3 = 900.0;  
const float l4 = 0.0;    

Gripper gripper(12, 2000, 2000, 2000);

bool returnToHome = true;

void moveToPosition(float dx, float dy, float dz, float phi) {
  float theta1 = atan2(dy, dx);
  float a = l3 * sin(phi);
  float b = l2 + l3 * cos(phi);
  float c = dz - l1 - l4 * sin(phi);
  float r = sqrt(a * a + b * b);
  float theta3 = acos((a * a + b * b + c * c - l2 * l2 - l3 * l3) / (2 * l2 * l3));
  float theta2 = atan2(c, sqrt(r * r - c * c)) - atan2(l3 * sin(theta3), l2 + l3 * cos(theta3));
  float theta4 = phi - theta2 - theta3;

  servo1.write((int)(theta1 * 180.0 / M_PI));
  servo2.write((int)(theta2 * 180.0 / M_PI));
  servo3.write((int)(theta3 * 180.0 / M_PI));
  servo4.write((int)(theta4 * 180.0 / M_PI));
}

void coordinateCallback(const coordinate_msgs::Coordinate& msg) {
  float dx = msg.x * 196.5356806749;
  float dy = msg.y * 158.7403574682;
  float dz = 0.13;
  float phi = 0.4;  

  moveToPosition(dx, dy, dz, phi);
  done_msg.data = "DONE";
  task_completed_pub.publish(&done_msg);
}

void setup() {
  nh.initNode();
  nh.advertise(task_completed_pub);
  nh.subscribe<coordinate_msgs::Coordinate>("robcoord2", coordinateCallback);

  servo1.attach(9);
  servo2.attach(10);
  servo3.attach(11);
  servo4.attach(12);
}

void loop() {
  nh.spinOnce();
  if (returnToHome) {
    gripper.close();
    delay(5000);
    moveToPosition(0, 0, 0, 0);
    returnToHome = false;
    done_msg.data = "rob3DONE";
    task_completed_pub.publish(&done_msg);
  }
  delay(10);
}

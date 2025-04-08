_arm2.ino_  
#include <ros.h>
#include <Servo.h>
//#include <coordinate_msgs/Coordinate.h>
#include <std_msgs/String.h>

#define M_PI 3.1415926535897932384626433832795

// Servo objects and pins
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

// Node handle
ros::NodeHandle nh;

// Done message and publisher
std_msgs::String done_msg;
ros::Publisher task_completed_pub("task_completed_r2", &done_msg);

// Link lengths in mm
const float l1 = 250.0;  // Link length for joint 1
const float l2 = 100.0;  // Link length for joint 2
const float l3 = 900.0;  // Link length for joint 3
const float l4 = 0.0;    // Link length for joint 4

bool returnToHome = true; // Flag to check if return to home is needed

void moveToPosition(float dx, float dy, float dz, float phi) {
  float theta1 = atan2(dy, dx);
  float a = l3 * sin(phi);
  float b = l2 + l3 * cos(phi);
  float c = dz - l1 - l4 * sin(phi);
  float r = sqrt(a * a + b * b);
  float theta3 = acos((a * a + b * b + c * c - l2 * l2 - l3 * l3) / (2 * l2 * l3));
  float theta2 = atan2(c, sqrt(r * r - c * c)) - atan2(l3 * sin(theta3), l2 + l3 * cos(theta3));
  float theta4 = phi - theta2 - theta3;

  // Convert radians to degrees and move servos
  servo1.write((int)(theta1 * 180.0 / M_PI));
  servo2.write((int)(theta2 * 180.0 / M_PI));
  servo3.write((int)(theta3 * 180.0 / M_PI));
  servo4.write((int)(theta4 * 180.0 / M_PI));
}


void moveCallback(const std_msgs::String& msg) {
  // Using the incoming coordinate message to determine position
  if (msg.data == "CONTINUE") {
    moveToPosition(0.46, 0.06, 0.14, 0.4);
    delay(1000);
    moveToPosition(0.46, 0.36, 0.14, 0.4);
    delay(1000);
    moveToPosition(0.06, 0.36, 0.14, 0.4);
    delay(1000);
    moveToPosition(0.06, 0.06, 0.14, 0.4);
    delay(1000);
  }
}

void setup() {
  nh.initNode();
  nh.advertise(task_completed_pub);
  nh.subscribe<std_msgs::String>("rob2start", moveCallback);

  servo1.attach(9);
  servo2.attach(10);
  servo3.attach(11);
  servo4.attach(12);

  pinMode(5, OUTPUT); //ENA
  pinMode(6, OUTPUT); //IN2
  pinMode(7, OUTPUT); //IN2
}

void loop() {
  digitalWrite(5, HIGH);
  digitalWrite(6, HIGH);
  digitalWrite(7, LOW);
  nh.spinOnce();
  digitalWrite(5, LOW);
  digitalWrite(6, LOW);
  digitalWrite(7, HIGH);
  if (returnToHome) {
    delay(5000); // Wait for 5 seconds before returning
    moveToPosition(0, 0, 0, 0); // Move to home position
    returnToHome = false; // Reset the flag
    done_msg.data = "rob2DONE";
    task_completed_pub.publish(&done_msg); // Publish message upon return to home
  }
  delay(10);
}
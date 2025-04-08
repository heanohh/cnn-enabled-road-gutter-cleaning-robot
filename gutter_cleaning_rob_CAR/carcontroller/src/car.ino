#include <ros.h>
#include <ros/time.h>
#include <std_msgs/String.h>
#include <Servo.h>

Servo motor_A;
Servo motor_B;

ros::NodeHandle nh;

void messageCb(const std_msgs::String& msg){
  if (msg.data == "CONTINUE") {
    motor_A.write(120);  // 전진
    motor_B.write(120);
  } else if (msg.data == "STOP") {
    motor_A.write(90);  // 정지
    motor_B.write(90);
  }
}

ros::Subscriber<std_msgs::String> sub("car_command", &messageCb);

void setup() {
  nh.initNode();
  nh.subscribe(sub);

  motor_A.attach(6);  // 모터 A를 6번 핀에 연결
  motor_B.attach(7);  // 모터 B를 7번 핀에 연결
}

void loop() {
  nh.spinOnce();
  delay(1);
}


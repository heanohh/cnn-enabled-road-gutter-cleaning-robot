#!/usr/bin/env python3
# coding:utf-8
import math
import numpy as np
import time
import rospy
import serial
from common import *
from time import sleep
from sensor_msgs.msg import LaserScan
from dynamic_reconfigure.server import Server
from yahboomcar_laser.cfg import laserAvoidPIDConfig

RAD2DEG = 180 / math.pi


class laserAvoid:
    def __init__(self):
        rospy.on_shutdown(self.cancel)
        self.r = rospy.Rate(20) #초당 20초
        self.Moving = False
        self.switch = False
        self.Right_warning = 0
        self.Left_warning = 0
        self.front_warning = 0
        self.obstacle_detected_time = None  # 장애물 감지 시간을 기록

        # arduino port connect
        port = "/dev/ttyACM0"
        baudrate = 9600
        self.arduino = serial.Serial(port, baudrate)

        # dynamic_reconfigure 서버 설정
        Server(laserAvoidPIDConfig, self.dynamic_reconfigure_callback)

        # 기본 동작 설정
        self.linear = 0.3
        self.angular = 0.6
        self.ResponseDist = 0.80 #detect obstacle(80cm)
        self.LaserAngle = 30  # 10~50
        self.ObstacleValidAngle = 4  # valid # 유효한 장애물 각도
        self.sub_laser = rospy.Subscriber('/scan', LaserScan, self.registerScan, queue_size=1)

    def cancel(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.write(b'P')
            self.arduino.close()
        self.sub_laser.unregister()
        rospy.loginfo("Shutting down this node.")

    def dynamic_reconfigure_callback(self, config, level):
        self.switch = config['switch']
        self.linear = config['linear']
        self.angular = config['angular']
        self.LaserAngle = config['LaserAngle']
        self.ResponseDist = config['ResponseDist']
        return config

    def registerScan(self, scan_data):
        if not isinstance(scan_data, LaserScan): return

        # Record the laser scan and publish the position of the nearest object (or point to a point)
        ranges = np.array(scan_data.ranges)
        self.Right_warning = 0
        self.Left_warning = 0
        self.front_warning = 0

        # if we already have a last scan to compare to
        for i in range(len(ranges)):
            angle = (scan_data.angle_min + scan_data.angle_increment * i) * RAD2DEG * 1  # -90 90
            # print(scan_data.angle_min)
            # print(int(5/(scan_data.angle_increment* RAD2DEG)))
            # print(angle)
            # if angle > 90: print "i: {},angle: {},dist: {}".format(i, angle, scan_data.ranges[i])
            # print("i: "+str(i)+",angle: "+str(angle)+",dist: "+str(scan_data.ranges[i]))

            # 오른쪽 각도 범위 체크
            if -10 > angle > -10 - self.LaserAngle:
                if ranges[i] < self.ResponseDist:
                    self.Right_warning += 1
                    # print(angle)

            # 왼쪽 각도 범위 체크
            if 10 + self.LaserAngle > angle > 10:
                if ranges[i] < self.ResponseDist:
                    self.Left_warning += 1
                    # print(angle)

            # 정면 각도 범위 체크
            if abs(angle) < 10:
                if ranges[i] <= self.ResponseDist:
                    self.front_warning += 1
                    # print(angle)
        # print (self.Left_warning, self.front_warning, self.Right_warning)

        # 장애물 회피 기능이 꺼져 있으면 반환
        if self.switch == True:
            return

        # judge real obstacle number
        # 유효한 장애물 각도를 계산
        valid_num = int(self.ObstacleValidAngle / (scan_data.angle_increment * RAD2DEG))

        # 정면에 장애물이 감지되었을 때 속도 줄이기 및 방향 전환 로직
        if self.front_warning > valid_num:
            if self.obstacle_detected_time is None:
                self.obstacle_detected_time = time.time()
                print('Obstacle detected, reducing speed.')
                self.arduino.write(b'W\n')  # 속도 줄이기(거의 멈출정도로)
            elif time.time() - self.obstacle_detected_time > 5:
                print('Obstacle still present after 5 seconds, changing direction.')
                self.change_direction(valid_num)  # 방향 전환
        else:
            self.obstacle_detected_time = None
            self.execute_movement(valid_num)

        self.r.sleep()


    def change_direction(self, valid_num):
        # 오른쪽, 왼쪽, 정면 경고를 기반으로 방향 전환
        # 정면 막혀있고 양옆에 장애물 둘다 있다면 뒤로 가는것을 기본으로 설정
        if self.Left_warning > valid_num and self.Right_warning > valid_num:
            self.arduino.write(b'B\n')
            print('Both sides blocked. Go back.')
        elif self.Left_warning > valid_num: #정면, 왼쪽 막힘=> 오른쪽으로 돌고 직진했다가 다시 왼쪽으로 돌아서 정면을 바라보도록
            self.arduino.write(b'R\n')
            self.arduino.write(b'F\n')
            self.arduino.write(b'L\n')
            print('Left side blocked. Turn right.')
        elif self.Right_warning > valid_num: #정면, 오른쪽 막힘=> 왼쪽으로 돌고 직진했다가 다시 오른쪽으로 돌아서 정면을 바라보도록
            self.arduino.write(b'L\n')
            self.arduino.write(b'F\n')
            self.arduino.write(b'R\n')
            print('Right side blocked. Turn left.')
        else:
            #정면 막혀있고 양옆에 장애물 둘다 없다면 오른쪽으로 가는것을 기본으로 설정=>오른쪽으로 돌고 직진했다가 다시 왼쪽으로 돌아서 정면을 바라보도록
            self.arduino.write(b'R\n')
            print('Front blocked. Turn right.')
            self.arduino.write(b'F\n')
            self.arduino.write(b'L\n')
        time.sleep(0.2)  # 변경 후 잠시 대기


   def execute_movement(self, valid_num):
       # 방향 전환 로직(정면에 장애물 없을때)=> 직진
        if self.front_warning <= valid_num:
            print('No obstacles, go foward')
            self.arduino.write(b'F\n')
            sleep(0.2)



if __name__ == '__main__':
    print("init laser_Avoidance")
    rospy.init_node('laser_Avoidance', anonymous=False)
    tracker = laserAvoid()
    rospy.spin()



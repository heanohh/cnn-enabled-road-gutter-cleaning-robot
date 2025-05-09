# 24-Spring_CNN-Enabled-Road-Gutter-Cleaning-Robot
At Ewha Womans University's 17th Challenge Semester, we crafted a Rain Gutter Detection Robot with CNN technology. It's designed to detect and clean rain gutters efficiently. With a CNN model, the robot autonomously identifies and cleans road gutters, ensuring optimal drainage and minimizing flooding risks.

# How is it implemented?
- AI algorithm: YOLO4-tiny + NanoSAM
![image](https://github.com/jaeeunHwang/24-Spring_CNN-Enabled-Road-Gutter-Cleaning-Robot/assets/98397375/8539bf86-d8ea-4d9d-80d8-145a02cb3c46)

Image segmentation is performed by passing the coordinates of Object Detection through YOLO4-tiny to NanoSAM.
You can check the learned results in nanosam/yolo/custom data and the implemented code in nanosam/inference.py

- Imbedded algorithm
</br>
![image](https://github.com/user-attachments/assets/a0d9c2aa-ca4a-4f9b-bf8c-8130cb0de674)


![image](https://github.com/user-attachments/assets/85d39e76-ba2d-4915-9780-d686fd1801d5)

We made each node for MASTER(PC Ubuntu1), CNN(Jetson Orin Nano), and CAR(PC Ubuntu2). And using roslaunch, we'll let them telecommunicate to act like a flowchart. 


# How to use
1. Run inference.py
```bash
python3 inference.py
```
-> The files point_coordinates.txt and nanosam/output_image.jpg are created

2. Run each dode in Jetson Orin Nano, Pc Ubuntu1, Pc ubuntu 2.
```bash
roscore
```
```bash
catkin_ws/src/launch/master_ros.launch
```
```bash
catkin_ws/src/launch/CNN_ros.launch
```
```bash
catkin_ws/src/launch/CAR_ros.launch
```


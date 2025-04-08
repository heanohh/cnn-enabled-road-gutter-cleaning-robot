
#!/usr/bin/env python
import rospy
from coord_sender.msg import Coordinate
import os

def read_coordinates(file_path):
    """ 파일에서 좌표를 읽고 반환하는 제너레이터 함수 """
    with open(file_path, 'r') as file:
        for line in file:
            x, y = map(float, line.strip().split(','))
            yield Coordinate(x=x, y=y)

def publish_coordinates(publisher, coordinates_directory):
    """ 좌표를 읽고 발행하는 함수 """
    try:
        coordinate_files = [os.path.join(coordinates_directory, f) for f in os.listdir(coordinates_directory) if f.endswith('.txt')]
        rate = rospy.Rate(1)  # 1 Hz, 발행 주기를 조절
        for coord_file in coordinate_files:
            for coord in read_coordinates(coord_file):
                publisher.publish(coord)
                rospy.loginfo(f"Published coordinate: x={coord.x}, y={coord.y}")
                rate.sleep()  # 발행 후 1초 대기
    except Exception as e:
        rospy.logwarn(f"Error processing files in {coordinates_directory}: {e}")

def main():
    rospy.init_node('coord_sender', anonymous=True)

    # 두 개의 퍼블리셔 설정
    coordpub1 = rospy.Publisher('coordinate1', Coordinate, queue_size=10)
    coordpub2 = rospy.Publisher('coordinate2', Coordinate, queue_size=10)

    # 두 개의 경로 설정
    coordinates_directory1 = '/path/to/your/coord1'
    coordinates_directory2 = '/path/to/your/coord2'

    # 별도의 스레드나 병행 처리 없이 각 경로의 좌표를 순차적으로 발행
    while not rospy.is_shutdown():
        publish_coordinates(coordpub1, coordinates_directory1)
        publish_coordinates(coordpub2, coordinates_directory2)

if __name__ == '__main__':
    main()
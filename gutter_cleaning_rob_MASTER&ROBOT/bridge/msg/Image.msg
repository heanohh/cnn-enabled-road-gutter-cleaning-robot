# This is a message to hold data from an image stream which may be from
# a camera or other sensors that return images as a 2D array. 
# 이미지 스트림에서 오는 데이터를 보관하기 위한 메시지입니다. 이 데이터는 카메라 또는 2D 배열로 이미지를 반환하는 다른 센서에서 올 수 있습니다.

std_msgs/Header header   # 표준 메시지 헤더 포함. 타임스탬프와 프레임 정보가 있습니다.
uint32 height            # 이미지 높이 (픽셀 단위)
uint32 width             # 이미지 너비 (픽셀 단위)
string encoding          # 인코딩 형식 (예: "rgb8", "bgr8", "mono8")
uint8 is_bigendian       # 데이터의 바이트 순서 (big endian = 1, little endian = 0)
uint32 step              # 풀 이미지의 한 행을 저장하는 데 필요한 바이트 수 (이는 픽셀 간격과 너비를 곱한 값이 아닐 수 있음)
uint8[] data             # 실제 이미지 데이터, 길이는 (step * rows)




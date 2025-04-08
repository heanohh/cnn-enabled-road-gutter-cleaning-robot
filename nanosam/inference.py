# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import PIL.Image
import cv2
import numpy as np
import argparse
from nanosam.utils.predictor import Predictor
from nanosam.utils.tracker import Tracker

# JE
import nvtx, time
import ctypes as ct
from yolo.darknet import darknet

parser = argparse.ArgumentParser()
parser.add_argument("--image_encoder", type=str, default="data/resnet18_image_encoder.engine")
parser.add_argument("--mask_decoder", type=str, default="data/mobile_sam_mask_decoder.engine")

# JE : args for darknet (yolov4-tiny)
parser.add_argument("--darknet_cfg", type=str, default="/home/vetsagong/spring/nanosam/yolo/custom_data/yolov4-tiny-custom.cfg")
parser.add_argument("--darknet_data", type=str, default="/home/vetsagong/spring/nanosam/yolo/custom_data/obj.names")
parser.add_argument("--darknet_weights", type=str, default="/home/vetsagong/spring/nanosam/yolo/custom_data/yolov4-tiny-custom_best.weights")

args = parser.parse_args()

use_cuda = True

# Instantiate TensorRT predictor
predictor = Predictor(
    args.image_encoder,
    args.mask_decoder
)

# JE : Instantiate YOLO detector
network, class_names, class_colors = darknet.load_network(args.darknet_cfg, args.darknet_weights, batch_size=1)

# Instantiate Tracker
tracker = Tracker(predictor)

cap = cv2.VideoCapture(0)

mask = None
bbox = None 
point = None

# Convert the NumPy array to a PIL image object
def cv2_to_pil(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return PIL.Image.fromarray(image) 
    
# JE
def save_coordinates(point):
    # Save the point coordinates to a file
    with open('point_coordinates.txt', 'w') as file:
        # point is a tuple (x, y)
        x, y = point
        file.write(f"{x}, {y}\n")

            
# JE
def pil_to_image(pil_image):
    
    # Convert PIL image to NumPy array
    image_array = np.array(pil_image).astype(np.float32)  # Convert to float32
    
    # Ensure that the image is in RGB mode
    if len(image_array.shape) == 2:
        # Grayscale image, add a channel dimension
        image_array = np.expand_dims(image_array, axis=-1)
    elif image_array.shape[2] == 4:
        # RGBA image, convert to RGB
        image_array = image_array[:, :, :3]
    
    # Get image shape
    height, width, channels = image_array.shape
    
    # Allocate memory for image data
    data_size = height * width * channels
    data_ptr = image_array.ctypes.data_as(ct.POINTER(ct.c_float))  # Use c_float
    
    # Create IMAGE structure
    image_yolo = darknet.IMAGE(width, height, channels, data_ptr)
    
    return image_yolo

      
""" ********************** VERSION 0 : Test by using image *********************
    
# JE : Convert the read jpg file to image struct
def jpg_to_image_struct(image_path):
    
    # Read jpg image
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)
    
    image = cv2.imread(image_path)
    
    # Convert to RGB format
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)
    
    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
   
    return darknet_image

image_path = "/home/vetsagong/spring/nanosam/yolo/custom_data/TEST2.jpg"
image_yolo = jpg_to_image_struct(image_path)
      
# JE : making bbox using detector
start = time.time()
detections = darknet.detect_image(network, class_names, image_yolo, thresh=.2, nms=.45)
finish = time.time()
print("Predicted in %f seconds." % (finish - start))
    
# JE : Check detections
print("\n JE : detections ")
print(detections)
print("####################################################################\n")
    
image_with_boxes, bbox = darknet.draw_boxes(detections, image_yolo, class_colors)
    
# Draw mask
if mask is not None:
    bin_mask = (mask[0,0].detach().cpu().numpy() < 0)
        
    #JE
    save_coordinates(bin_mask)
        
    green_image = np.zeros_like(image_with_boxes)
    green_image[:, :] = (0, 185, 118)
    green_image[bin_mask] = 0

    image = cv2.addWeighted(image_with_boxes, 0.4, green_image, 0.6, 0)
         
# Draw center
if point is not None:

    image = cv2.circle(
        image,
        point,
        5,
        (0, 185, 118),
         -1
     )
     
cv2.imwrite("/home/vetsagong/spring/nanosam/output_image.jpg", image)
print("/home/vetsagong/spring/nanosam/output_image.jpg")

cv2.imshow("Segmented Image", image)
cv2.waitKey(0)
cv2.destroyAllWindows() """


      
""" **************** VERSION 1 : Inference using yolo image detect***************** 
    
cv2.namedWindow('image')

# JE : Segment using bounding box
def init_track():
    global mask, bbox, point, point_label
    if bbox is not None and bbox !=  []:
      point = ((bbox[0][0]+bbox[0][1])/2, (bbox[0][2]+bbox[0][3])/2)
      mask = tracker.init(image_pil, point)
    else :
      print("JE : Failed")
      
while True:

    re, image = cap.read()
      
    if not re:
        break
      
    image_pil = cv2_to_pil(image)
    image_yolo = pil_to_image(image_pil)
    
    # JE : making bbox using detector
    start = time.time()
    detections = darknet.detect_image(network, class_names, image_yolo, thresh=.2, nms=.45)
    finish = time.time()
    print("Predicted in %f seconds." % (finish - start))
    
    # JE : Check detections
    print("\n JE : detections ")
    print(detections)
    print("####################################################################\n")
    
    image_yolo, bbox = darknet.draw_boxes(detections, image_yolo, class_colors)
    
    init_track()

    if tracker.token is not None:
        mask, point = tracker.update(image_pil)
    
    # Draw mask
    if mask is not None:
        bin_mask = (mask[0,0].detach().cpu().numpy() < 0)
        
        #JE
        save_coordinates(bin_mask)
        
        green_image = np.zeros_like(image)
        green_image[:, :] = (0, 185, 118)
        green_image[bin_mask] = 0

        image = cv2.addWeighted(image, 0.4, green_image, 0.6, 0)
         
    # Draw center
    if point is not None:

        image = cv2.circle(
            image,
            point,
            5,
            (0, 185, 118),
            -1
        )

    cv2.imshow("image", image)

    ret = cv2.waitKey(1)

    if ret == ord('q'):
        break
    elif ret == ord('r'):
        tracker.reset()
        mask = None
        box = None """


""" ***************** VERSION 2 : Inference using mouse click  ****************** """
    
def init_track(event,x,y,flags,param):
    global mask, point
    if event == cv2.EVENT_LBUTTONDBLCLK:
        mask = tracker.init(image_pil, point=(x, y))
        point = (x, y)


cv2.namedWindow('image')
cv2.setMouseCallback('image',init_track)

while True:

    re, image = cap.read()


    if not re:
        break

    image_pil = cv2_to_pil(image)

    if tracker.token is not None:
        mask, point = tracker.update(image_pil)
    
    # Draw mask
    if mask is not None:
        bin_mask = (mask[0,0].detach().cpu().numpy() < 0) 
        
       
        
        green_image = np.zeros_like(image)
        green_image[:, :] = (0, 185, 118)
        green_image[bin_mask] = 0

        image = cv2.addWeighted(image, 0.4, green_image, 0.6, 0)

    # Draw center
    if point is not None:
        
        #JE
        save_coordinates(point)
        
        image = cv2.circle(
            image,
            point,
            5,
            (0, 185, 118),
            -1
        )

    cv2.imshow("image", image)
    cv2.imwrite("output_image.jpg", image)
    
    ret = cv2.waitKey(1)

    if ret == ord('q'):
        break
    elif ret == ord('r'):
        tracker.reset()
        mask = None
        box = None 


cv2.destroyAllWindows()

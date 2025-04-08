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

from torch2trt import TRTModule
from typing import Tuple
import tensorrt as trt
import PIL.Image
import torch
import numpy as np
import torch.nn.functional as F

# JE : import nn, resnet for je_image_encoder
import torch.nn as nn
from timm.models import resnet
# JE : Add nvtx for profiling
import nvtx

# JE : BasicBlock
class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False) #OK
        self.bn1 = nn.BatchNorm2d(planes, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True) #OK
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False) #OK
        self.bn2 = nn.BatchNorm2d(planes, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True) #OK

        #OK
        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != self.expansion*planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, self.expansion*planes, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(self.expansion*planes, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x))) # OK
        out = F.relu(self.bn2(self.conv2(out))) # OK
        out += self.shortcut(x)
        return out

class ResNet(nn.Module):
    def __init__(self, block, num_blocks):
        super(ResNet, self).__init__()
        self.in_planes = 64

        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
        self.layer1 = self._make_layer(block, 64, num_blocks[0], stride=1)
        self.layer2 = self._make_layer(block, 128, num_blocks[1], stride=2)
        self.layer3 = self._make_layer(block, 256, num_blocks[2], stride=2)
        self.layer4 = self._make_layer(block, 512, num_blocks[3], stride=2)
        
        self.channels = 512
        self.neck_channels = 256
        self.feature_dim = 256
        self.feature_shape = (64,64)
        self.pos_embedding = nn.Parameter(1e-5*torch.randn(1, self.feature_dim, *self.feature_shape))
        
        self.up_1 = nn.Sequential(
            nn.Conv2d(self.channels, self.neck_channels, 3, padding=1),
            nn.GELU(),
            nn.Conv2d(self.neck_channels, self.neck_channels, 3, padding=1),
            nn.GELU(),
            nn.Conv2d(self.neck_channels, self.neck_channels, 3, padding=1),
            nn.GELU(),
            nn.ConvTranspose2d(self.neck_channels, self.neck_channels, 3, 2, 1, 1),
            nn.GELU()
        )
        self.proj = nn.Sequential(
            nn.Conv2d(self.neck_channels, self.neck_channels, 3, padding=1),
            nn.GELU(),
            nn.Conv2d(self.neck_channels, self.feature_dim, 1, padding=0)
        )

    def _make_layer(self, block, planes, num_blocks, stride):
        strides = [stride] + [1]*(num_blocks-1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
            self.in_planes = planes * block.expansion
        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.proj(self.up_1(out[-1]))
        #out += self.pos_embedding
        return out


@nvtx.annotate(message="load_mask_decoder_engine", color="green") # JE
def load_mask_decoder_engine(path: str):
    
    with trt.Logger() as logger, trt.Runtime(logger) as runtime:
        with open(path, 'rb') as f:
            engine_bytes = f.read()
        engine = runtime.deserialize_cuda_engine(engine_bytes)

    mask_decoder_trt = TRTModule(
        engine=engine,
        input_names=[
            "image_embeddings",
            "point_coords",
            "point_labels",
            "mask_input",
            "has_mask_input"
        ],
        output_names=[
            "iou_predictions",
            "low_res_masks"
        ]
    )

    return mask_decoder_trt

@nvtx.annotate(message="load_image_encoder_engine", color="green") # JE
def load_image_encoder_engine(path: str):

    with trt.Logger() as logger, trt.Runtime(logger) as runtime:
        with open(path, 'rb') as f:
            engine_bytes = f.read()
        engine = runtime.deserialize_cuda_engine(engine_bytes)

    image_encoder_trt = TRTModule(
        engine=engine,
        input_names=["image"],
        output_names=["image_embeddings"]
    )

    return image_encoder_trt

@nvtx.annotate(message="preprocess_image", color="green") # JE
def preprocess_image(image, size: int = 512):

    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)

    image_mean = torch.tensor([123.675, 116.28, 103.53])[:, None, None]
    image_std = torch.tensor([58.395, 57.12, 57.375])[:, None, None]

    image_pil = image
    aspect_ratio = image_pil.width / image_pil.height
    if aspect_ratio >= 1:
        resize_width = size
        resize_height = int(size / aspect_ratio)
    else:
        resize_height = size
        resize_width = int(size * aspect_ratio)

    image_pil_resized = image_pil.resize((resize_width, resize_height))
    image_np_resized = np.asarray(image_pil_resized)
    image_torch_resized = torch.from_numpy(image_np_resized).permute(2, 0, 1)
    image_torch_resized_normalized = (image_torch_resized.float() - image_mean) / image_std
    image_tensor = torch.zeros((1, 3, size, size))
    image_tensor[0, :, :resize_height, :resize_width] = image_torch_resized_normalized
    print(image_tensor.shape)
    output_path = '/home/vetsagong/resnet_cuda/input/image_tensor.txt'
    
    """if output_path:
        with open(output_path, 'w') as f:
            f.write("Tensor Shape: {}\n".format(image_tensor.shape))
            f.write("Tensor Values:\n")
            for i in range(image_tensor.shape[0]):
                for j in range(image_tensor.shape[1]):
                    for k in range(image_tensor.shape[2]):
                        for l in range(image_tensor.shape[3]):
                            f.write(str(image_tensor[i, j, k, l].item()) + '\n')"""
            
    return image_tensor.cuda()

@nvtx.annotate(message="preprocess_points", color="green") # JE
def preprocess_points(points, image_size, size: int = 1024):
    scale = size / max(*image_size)
    points = points * scale
    return points


@nvtx.annotate(message="run_mask_decoder", color="green") # JE
def run_mask_decoder(mask_decoder_engine, features, points=None, point_labels=None, mask_input=None):
    if points is not None:
        assert point_labels is not None
        assert len(points) == len(point_labels)

    image_point_coords = torch.tensor([points]).float().cuda()
    image_point_labels = torch.tensor([point_labels]).float().cuda()

    if mask_input is None:
        mask_input = torch.zeros(1, 1, 256, 256).float().cuda()
        has_mask_input = torch.tensor([0]).float().cuda()
    else:
        has_mask_input = torch.tensor([1]).float().cuda()


    iou_predictions, low_res_masks = mask_decoder_engine(
        features,
        image_point_coords,
        image_point_labels,
        mask_input,
        has_mask_input
    )

    return iou_predictions, low_res_masks


@nvtx.annotate(message="upscale_mask", color="green") # JE
def upscale_mask(mask, image_shape, size=256):
    
    if image_shape[1] > image_shape[0]:
        lim_x = size
        lim_y = int(size * image_shape[0] / image_shape[1])
    else:
        lim_x = int(size * image_shape[1] / image_shape[0])
        lim_y = size

    mask[:, :, :lim_y, :lim_x]
    mask = F.interpolate(mask[:, :, :lim_y, :lim_x], image_shape, mode='bilinear')
    
    return mask
    
def je_image_encoder(x) :
    image_encoder = ResNet(BasicBlock, [2, 2, 2, 2])
    device = torch.device("cuda")
    image_encoder.to(device)
    return image_encoder(x)
    
class Predictor_je(nn.Module):
  def __init__(self,
          image_encoder_size: int = 1024,
      ):
      self.image_encoder_size = image_encoder_size
    
  @nvtx.annotate(message="Predictor : JE - Set image", color="red") # JE
  def je_set_image(self, image):
      self.image = image
      self.image_tensor = preprocess_image(image, self.image_encoder_size)
      self.features = je_image_encoder(self.image_tensor)
      print(self.features)  
        

class Predictor(object):

    @nvtx.annotate(message="Predictor : Initialize Predictor class", color="red") # JE
    def __init__(self,
            image_encoder_engine: str,
            mask_decoder_engine: str,
            image_encoder_size: int = 1024,
            orig_image_encoder_size: int = 1024,
        ):
        self.image_encoder_engine = load_image_encoder_engine(image_encoder_engine)
        self.mask_decoder_engine = load_mask_decoder_engine(mask_decoder_engine)
        self.image_encoder_size = image_encoder_size
        self.orig_image_encoder_size = orig_image_encoder_size

    @nvtx.annotate(message="Predictor : Set image", color="red") # JE
    def set_image(self, image):
        self.image = image
        self.image_tensor = preprocess_image(image, self.image_encoder_size)
        self.features = self.image_encoder_engine(self.image_tensor)
        print(self.features)    

    @nvtx.annotate(message="Predictor : Predict", color="red") # JE
    def predict(self, points, point_labels, mask_input=None):
        points = preprocess_points(
            points, 
            (self.image.height, self.image.width),
            self.orig_image_encoder_size
        )
        mask_iou, low_res_mask = run_mask_decoder(
            self.mask_decoder_engine,
            self.features,
            points,
            point_labels,
            mask_input
        )

        hi_res_mask = upscale_mask(
            low_res_mask, 
            (self.image.height, self.image.width)                           
        )

        return hi_res_mask, mask_iou, low_res_mask

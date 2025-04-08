#!/bin/bash

# Set the name of the Docker image
IMAGE_NAME="nanosam_with_ros"

# Run the Docker container
echo "Running Docker container..."

# Define any required runtime arguments here, such as the need to use GPU
docker run \
    -it \
    -d \
    --rm \
    --ipc host \
    --gpus all \
    --shm-size 14G \
    --device /dev/video0:/dev/video0 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    -p 5000:5000 \
    -p 8888:8888 \
    -v /home/vetsagong/dockervolume/nanosam_ros:/workspace/dockervolume \
    --name JE-NanoSAMwithROS \
    $IMAGE_NAME /bin/bash


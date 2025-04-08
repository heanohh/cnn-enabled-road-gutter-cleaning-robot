#!/bin/bash

# Set the name of the Docker image
IMAGE_NAME="nanosam_with_ros"

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Check if the build was successful
if [ $? -ne 0 ]; then
    echo "Docker build failed"
    exit 1
else
    echo "Docker build completed successfully"
fi

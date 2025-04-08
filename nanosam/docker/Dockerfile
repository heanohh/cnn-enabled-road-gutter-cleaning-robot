# Base image setting, using NVIDIA's L4T PyTorch image
ARG BASE_IMAGE=dustynv/l4t-pytorch:r35.4.1
FROM ${BASE_IMAGE}

# Setting environment variables for ONNX Runtime
ARG ONNXRUNTIME_VERSION=1.17.0\
    ONNXRUNTIME_BRANCH=v1.17 \
    ONNXRUNTIME_FLAGS='--allow_running_as_root' \
    FORCE_BUILD=off
COPY install.sh build.sh /tmp/onnxruntime/
RUN /tmp/onnxruntime/install.sh || /tmp/onnxruntime/build.sh

# Set up environment for ROS
ARG ROS_PACKAGE=ros_base
ENV ROS_DISTRO=noetic
ENV ROS_ROOT=/opt/ros/${ROS_DISTRO}
ENV ROS_PYTHON_VERSION=3
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

# Add the ROS deb repo to the apt sources list and install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
          git \
        cmake \
        build-essential \
        curl \
        wget \
        gnupg2 \
        lsb-release \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -

# Install bootstrap dependencies for ROS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
          libpython3-dev \
          python3-rosdep \
          python3-rosinstall-generator \
          python3-vcstool \
          build-essential && \
    rosdep init && \
    rosdep update && \
    rm -rf /var/lib/apt/lists/*

# Download and build the ROS source
RUN mkdir ros_catkin_ws && \
    cd ros_catkin_ws && \
    rosinstall_generator ${ROS_PKG} vision_msgs image_transport --rosdistro ${ROS_DISTRO} --deps --tar > ${ROS_DISTRO}-${ROS_PKG}.rosinstall && \
    mkdir src && \
    vcs import --input ${ROS_DISTRO}-${ROS_PKG}.rosinstall ./src && \
    apt-get update && \
    rosdep install -y \
     --from-paths ./src \
     --ignore-packages-from-source \
     --rosdistro ${ROS_DISTRO} \
     --skip-keys "python3-pykdl libopencv-dev libopencv-contrib-dev libopencv-imgproc-dev python-opencv python3-opencv" && \
    python3 ./src/catkin/bin/catkin_make_isolated --install --install-space ${ROS_ROOT} -DCMAKE_BUILD_TYPE=Release -DSETUPTOOLS_DEB_LAYOUT=OFF && \
    rm -rf /var/lib/apt/lists/*

# Set the entrypoint which sources the ROS environment
COPY ros_entrypoint.sh /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["/bin/bash"]

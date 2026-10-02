FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/SUMMER-SCHOOL-RL

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxcursor1 \
    libxi6 \
    libxinerama1 \
    libegl1 \
    libglfw3 \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# CycloneDDS for Unitree SDK
ENV CYCLONEDDS_HOME=/workspace/SUMMER-SCHOOL-RL/2.Deploy/cyclonedds/install
ENV LD_LIBRARY_PATH="${CYCLONEDDS_HOME}/lib:${LD_LIBRARY_PATH}"

# Python paths for deploy + training packages
ENV PYTHONPATH="/workspace/SUMMER-SCHOOL-RL:/workspace/SUMMER-SCHOOL-RL/2.Deploy/unitree_sdk2_python:/workspace/SUMMER-SCHOOL-RL/1.Training/src:${PYTHONPATH}"

# Install Unitree SDK
RUN cd /workspace/SUMMER-SCHOOL-RL/2.Deploy/unitree_sdk2_python \
    && pip install -e .

# Install Go2 MJLab training package
RUN cd /workspace/SUMMER-SCHOOL-RL/1.Training \
    && pip install -e .

# Install uv + MJLab
RUN pip install --no-cache-dir uv

RUN uv --version

RUN git clone https://github.com/mujocolab/mjlab.git /opt/mjlab
RUN cd /opt/mjlab && uv sync
RUN cd /opt/mjlab && uv pip install -e /workspace/SUMMER-SCHOOL-RL/1.Training
RUN cp -r /workspace/SUMMER-SCHOOL-RL/1.Training/src/unitree_go2_velocity \
    /opt/mjlab/src/mjlab/tasks/velocity/config/go2

CMD ["bash"]

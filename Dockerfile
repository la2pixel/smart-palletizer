###############################################
# Base image: lightweight Debian with Python 3.10
FROM python:3.10-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

###############################################
# Install system dependencies for:
# - Open3D
# - OpenCV (headless)
# - SciPy 
# - Building Python wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    libgl1 \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    liblapack-dev \
    libblas-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

###############################################
# Install Python dependencies 
COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project into container
COPY . /workspace

###############################################
# Install project in editable mode
RUN pip install -e .

#Default command
CMD ["/bin/bash"]

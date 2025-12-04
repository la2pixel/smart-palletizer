# TODO

FROM ros:humble
RUN apt-get update && apt-get install -y python3-pip
WORKDIR /workspace
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["/bin/bash"]

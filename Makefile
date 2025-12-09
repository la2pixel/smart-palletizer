# Task 1 – 2D Detection
task1:
	$(PYTHON) -c "from smart_palletizer.task1_2d_detection import run_task1; run_task1('$(DATA)', verbose=True)"

clean_task1:
	rm -rf outputs/task1/* 2>/dev/null || true


# Task 2 – Planar Patch Detection
task2:
	$(PYTHON) -c "from smart_palletizer.task2_planarpatch import run_task2; run_task2('$(DATA)', verbose=True, save_viz=True)"

clean_task2:
	rm -rf outputs/task2/* 2>/dev/null || true


# Task 3 – Point Cloud Processing
task3:
	$(PYTHON) -c "from smart_palletizer.task3_pointcloud_processing import run_task3; run_task3('$(DATA)')"

clean_task3:
	rm -rf outputs/task3/* 2>/dev/null || true

task3_demo:
	$(PYTHON) -c "from smart_palletizer.task3_pointcloud_processing import run_task3; run_task3('$(DATA)')"


# Task 4 – 6D Pose Estimation
task4:
	$(PYTHON) -c "from smart_palletizer.task4_pose3d import run_task4; run_task4('$(DATA)', verbose=True)"

clean_task4:
	rm -rf outputs/task4/* 2>/dev/null || true


# Documentation (Sphinx)
docs:
	cd docs && make html

clean_docs:
	rm -rf docs/build/* 2>/dev/null || true


# Installations and Utilities
install:
	pip install -e .

freeze:
	pip freeze > requirements.txt


# Docker Commands
docker-build:
	docker build -t smart_palletizer .

docker-run:
	docker run -it --rm -v $(PWD):/workspace smart_palletizer /bin/bash

compose-build:
	docker compose build

compose-up:
	docker compose up -d

compose-shell:
	docker compose exec pallet_dev /bin/bash


# Run all main tasks
all: task1 task2 task3 task4


# Clean all outputs + docs
clean: clean_task1 clean_task2 clean_task3 clean_task4 clean_docs


# Help text
help:
	@echo ""
	@echo "Smart Palletizer - Available Commands"
	@echo "---------------------------------------------------------"
	@echo " Task execution:"
	@echo "  make task1         - Run Task 1 (2D Detection)"
	@echo "  make task2         - Run Task 2 (Planar Patch Detection)"
	@echo "  make task3         - Run Task 3 (Point Cloud Processing)"
	@echo "  make task4         - Run Task 4 (6D Pose Estimation)"
	@echo ""
	@echo " Containers:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run the Docker container"
	@echo "  make compose-build - Build using Docker Compose"
	@echo "  make compose-up    - Start Compose services"
	@echo "  make compose-shell - Enter running container shell"
	@echo ""
	@echo " Utilities:"
	@echo "  make clean         - Clean all task outputs"
	@echo "  make docs          - Build documentation"
	@echo "  make install       - Install package in editable mode"
	@echo "---------------------------------------------------------"
	@echo ""

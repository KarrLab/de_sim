#!/bin/bash

# Build Docker image
docker build \
    --tag karrlab/de_sim:0.0.2 \
    --tag karrlab/de_sim:latest \
    .

# Test image
docker run -it --rm \
    --workdir /root/de_sim \
    --entrypoint bash \
    karrlab/de_sim:latest \
    -c "pip install .[tests] pytest && python -m pytest tests"

# Push image to DockerHub
docker login
docker push karrlab/de_sim

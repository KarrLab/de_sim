#!/bin/bash

# Build Docker image
docker build \
    --tag karrlab/de_sim:0.0.3 \
    --tag karrlab/de_sim:latest \
    .

# Test image
docker run -it --rm \
    --workdir /root \
    --entrypoint bash \
    karrlab/de_sim:latest \
    -c "git clone https://github.com/Karrlab/de_sim.git \
        && cd de_sim \
        && pip install -r tests/requirements.txt \
        && pip install pytest \
        && python -m pytest tests"

# Push image to DockerHub
docker login
docker push karrlab/de_sim

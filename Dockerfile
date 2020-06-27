# Base OS
FROM python:3.7

# Copy DE-Sim code into image
COPY . /root/de_sim

# Install DE-Sim
RUN pip install /root/de_sim

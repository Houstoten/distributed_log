ARG PYTHON_VERSION=3.10 ALPINE_VERSION=3.14

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# required by grpc
RUN apk add --no-cache \
    g++ \
    gcc \
    musl-dev \
    libffi-dev \
    libstdc++ \
    build-base \
    linux-headers

COPY requirements.txt ./

RUN pip install --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt && \
    # cleanup
    rm requirements.txt && \
    apk del --purge \
    g++ \
    gcc \
    musl-dev \
    libffi-dev \
    libstdc++ \
    build-base \
    linux-headers
# Use the official Python image as the base image
# FROM python:3.11.5


# RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
# RUN pip install -r some.txt

# Expose the ports
EXPOSE 3000 50051 

# Command to run the application
ARG MASTER
ARG REPLICAS
ENV MASTER=$MASTER
ENV REPLICAS=$REPLICAS

CMD "python run.py $MASTER $REPLICAS"

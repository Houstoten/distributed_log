# Use the official Python image as the base image
FROM python:3.11.5

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r some.txt

# Expose the ports
EXPOSE 3000 50051 

# Command to run the application
CMD ["python", "run.py"]

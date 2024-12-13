# Use an official Python runtime as a parent image
FROM python:3.11-alpine3.18

# Set the working directory in the container
WORKDIR /app

# Install system dependencies using Alpine's package manager (apk)
RUN apk update && apk add --no-cache \
    wget \
    chromium \
    chromium-chromedriver

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run parfium.py when the container launches
CMD ["python", "-u", "parfium-chromium.py"]
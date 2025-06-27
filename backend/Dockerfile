FROM python:3.10-slim

# Set environment variables to prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies, including ffmpeg for audio processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
# This leverages Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code into the container
COPY . .

# Expose the port the application will run on
EXPOSE 8000

# Command to run the application
# Using run_backend.py which likely contains the uvicorn startup logic
CMD ["python", "run_backend.py"]
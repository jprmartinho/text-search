# Specify the Python version and Debian distribution
ARG PYTHON_VERSION=3.11.6-slim-bullseye

# Base image for the final Python runtime environment
FROM python:${PYTHON_VERSION} as python

# Build stage for dependencies and build tools
FROM python as python-build-stage

# Set the build environment (dev, production, etc.)
ARG BUILD_ENVIRONMENT=dev

# Install necessary dependencies for building Python packages
RUN apt-get update && apt-get install --no-install-recommends -y build-essential

# Copy requirements files to the build stage (copy from host machine to the container)
COPY ./requirements .
# Build stage for creating Python wheels from requirements
# the generated wheels will be stored in the /usr/src/app/wheels directory within the Docker image.
# The generated wheels can later be used to speed up the installation of Python dependencies when the image is run.
RUN pip wheel --wheel-dir /usr/src/app/wheels \
    -r ${BUILD_ENVIRONMENT}.txt

# Final stage for running the Python application
FROM python as python-run-stage

# Set the build environment (dev, production, etc.)
ARG BUILD_ENVIRONMENT=dev

# Set the application's home directory
ARG APP_HOME=/app


# Set environment variables for Python runtime

# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1 ensures that Python's standard output (stdout) and standard error (stderr) are not buffered, allowing for immediate display or writing of output as it is generated.
# This is particularly useful in containerized or automated environments where real-time feedback and troubleshooting are essential.
ENV PYTHONUNBUFFERED 1
# Sets the build environment variable
ENV BUILD_ENV ${BUILD_ENVIRONMENT}
# Set the working directory for the application
WORKDIR ${APP_HOME}

# Update package lists, install required packages, and clean up unnecessary packages
RUN apt-get update \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Copy Python wheel files from build stage to the current image
COPY --from=python-build-stage /usr/src/app/wheels /wheels/

# Install Python packages using pip from the /wheels/ directory, which contains the wheel files copied in a previous step.
# After the installation is complete, the /wheels/ directory is removed to clean up the unnecessary files.
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/

# Copy entrypoint script to the image
COPY ./docker/dev/flask/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
# Set executable permissions for the entrypoint script
RUN chmod +x /entrypoint

COPY . ${APP_HOME}

ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_RUN_PORT=5001

ENTRYPOINT [ "/entrypoint" ]

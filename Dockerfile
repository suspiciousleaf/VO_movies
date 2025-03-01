FROM python:3.12.3

# Set working directory
WORKDIR /app

# Install vim-tiny and clean up apt cache to keep the image size small
RUN apt-get update && apt-get install -y nano && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml and other necessary files to the container
COPY pyproject.toml uv.lock README.md /app/

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies using uv
RUN uv pip install --system --resolution=highest --requirements pyproject.toml

# Copy the project files into the container
COPY . /app

# Expose the port the app runs on - this is for clarity since the docker compose file handles port forwarding
EXPOSE 7990

# Set the entrypoint to an interactive shell for debugging, this will be overridden by the docker-compose file if present
ENTRYPOINT ["tail", "-f", "/dev/null"]
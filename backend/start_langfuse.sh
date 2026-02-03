#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if LANGFUSE_DATABASE_URL is set
if [ -z "$LANGFUSE_DATABASE_URL" ]; then
    echo "Error: LANGFUSE_DATABASE_URL is not set."
    echo "Please set it in your backend/.env file or export it in your shell."
    echo "Example: LANGFUSE_DATABASE_URL=postgresql://user:pass@host:5432/dbname"
    exit 1
fi

echo "Checking Docker installation..."

# Check for Docker
if ! command_exists docker; then
    echo "Docker not found. Attempting to install Docker..."
    # Update package list
    sudo apt-get update
    # Install prerequisites
    sudo apt-get install -y ca-certificates curl
    # Install Docker
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Post-install group check
if ! docker info > /dev/null 2>&1; then
    # Try adding to group if not present
    if ! groups $USER | grep &>/dev/null 'docker'; then
        echo "Adding user to docker group..."
        sudo usermod -aG docker $USER
    fi
fi

# Check permission (for non-root usage)
if ! docker info > /dev/null 2>&1; then
    COMPOSE_CMD="sudo docker compose"
else
    COMPOSE_CMD="docker compose"
fi

echo "Starting Langfuse with database: $LANGFUSE_DATABASE_URL"
# Pass the env var explicitly to docker-compose
LANGFUSE_DATABASE_URL=$LANGFUSE_DATABASE_URL $COMPOSE_CMD -f docker-compose.langfuse.yml up -d

echo "Langfuse is starting at http://localhost:3000"

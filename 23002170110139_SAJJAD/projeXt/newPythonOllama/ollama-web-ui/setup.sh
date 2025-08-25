#!/bin/bash

echo "Setting up Ollama Web UI..."

# Create virtual environment if it doesn't exist
if [ ! -d ".VirtualEnv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .VirtualEnv
fi

# Activate virtual environment
source .VirtualEnv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Build Tailwind CSS
echo "Building Tailwind CSS..."
npm run build-css-prod

# Run Django migrations
echo "Running Django migrations..."
cd ollama_web_ui
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
echo "Would you like to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

echo "Setup complete!"
echo "To start the development server:"
echo "1. Activate virtual environment: source .VirtualEnv/bin/activate"
echo "2. Navigate to project: cd ollama_web_ui"
echo "3. Start server: python manage.py runserver"
echo ""
echo "Make sure Ollama is running on http://localhost:11434"
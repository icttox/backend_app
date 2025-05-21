#!/bin/bash

# Check if .env file exists, if not, copy from env.sample
if [ ! -f .env ]; then
    echo "No .env file found. Creating from env.sample..."
    cp env.sample .env
    echo "Please edit .env file with your actual configuration values."
    echo "Created .env file from template."
else
    echo ".env file already exists."
fi

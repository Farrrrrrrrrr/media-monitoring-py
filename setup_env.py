#!/usr/bin/env python
"""
Set up environment variables for Google App Engine deployment.
Run this script before deploying to set your environment variables.
"""
import os
import argparse
import subprocess
from dotenv import load_dotenv

def setup_env_vars():
    parser = argparse.ArgumentParser(description='Set environment variables for App Engine')
    parser.add_argument('--env-file', default='.env', help='Path to .env file (default: .env)')
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv(args.env_file)
    
    # List of environment variables to set in App Engine
    env_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_SECRET',
        'FACEBOOK_EMAIL',
        'FACEBOOK_PASSWORD',
        'INSTAGRAM_USERNAME',
        'INSTAGRAM_PASSWORD',
        'API_KEY',
        'JWT_SECRET_KEY'
    ]
    
    # Build gcloud command
    command = ['gcloud', 'app', 'deploy', 'app.yaml']
    
    # Add environment variables
    env_values = []
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            env_values.append(f"{var}={value}")
    
    if env_values:
        command.extend(['--set-env-vars', ','.join(env_values)])
    
    # Print command (without the actual values for security)
    print("Running command:")
    print("gcloud app deploy app.yaml --set-env-vars [ENVIRONMENT_VARIABLES]")
    
    # Execute command
    subprocess.run(command)

if __name__ == '__main__':
    setup_env_vars()

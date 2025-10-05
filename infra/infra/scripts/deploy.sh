#!/bin/bash

# Deployment script for AI Knowledge Agent infrastructure
# Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment is provided
if [ $# -lt 1 ]; then
    print_error "Usage: $0 [staging|prod] [plan|apply|destroy]"
    exit 1
fi

ENVIRONMENT=$1
ACTION=${2:-plan}

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    print_error "Environment must be 'staging' or 'prod'"
    exit 1
fi

# Validate action
if [[ "$ACTION" != "plan" && "$ACTION" != "apply" && "$ACTION" != "destroy" ]]; then
    print_error "Action must be 'plan', 'apply', or 'destroy'"
    exit 1
fi

# Set working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/.."
ENV_DIR="$INFRA_DIR/envs/$ENVIRONMENT"

print_status "Deploying to $ENVIRONMENT environment"
print_status "Action: $ACTION"
print_status "Working directory: $ENV_DIR"

# Check if environment directory exists
if [ ! -d "$ENV_DIR" ]; then
    print_error "Environment directory not found: $ENV_DIR"
    exit 1
fi

# Change to environment directory
cd "$ENV_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars not found in $ENV_DIR"
    exit 1
fi

# Initialize Terraform
print_status "Initializing Terraform..."
terraform init

# Validate Terraform configuration
print_status "Validating Terraform configuration..."
terraform validate

# Format check
print_status "Checking Terraform formatting..."
terraform fmt -check -recursive

# Execute action
case $ACTION in
    "plan")
        print_status "Creating Terraform plan..."
        terraform plan -no-color
        ;;
    "apply")
        print_warning "This will apply changes to the $ENVIRONMENT environment"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Applying Terraform configuration..."
            terraform apply -auto-approve
            print_status "Deployment completed successfully!"
        else
            print_status "Deployment cancelled"
            exit 0
        fi
        ;;
    "destroy")
        print_error "This will DESTROY the $ENVIRONMENT environment"
        print_error "This action cannot be undone!"
        read -p "Are you absolutely sure? Type 'yes' to confirm: " -r
        if [[ $REPLY == "yes" ]]; then
            print_status "Destroying infrastructure..."
            terraform destroy -auto-approve
            print_status "Infrastructure destroyed successfully!"
        else
            print_status "Destruction cancelled"
            exit 0
        fi
        ;;
esac

print_status "Script completed successfully!"
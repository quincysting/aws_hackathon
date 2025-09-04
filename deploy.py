#!/usr/bin/env python
"""
Deployment script for Stock Forecast Agent to AWS Bedrock AgentCore.
Handles ECR image push and Bedrock agent runtime deployment.
"""

import boto3
import json
import subprocess
import sys
import os
from datetime import datetime
import argparse
import time
from typing import Dict, Any, Optional

# Configuration
AWS_REGION = "us-west-2"
ECR_REPOSITORY = "stock-forecast-agent"
IMAGE_TAG = "latest"
AGENT_NAME = "stock-forecast-agent"
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

class BedrockAgentDeployer:
    """Deploy agent to Bedrock AgentCore."""
    
    def __init__(self, region: str = AWS_REGION):
        self.region = region
        self.ecr_client = boto3.client('ecr', region_name=region)
        self.bedrock_client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
        self.account_id = self.sts_client.get_caller_identity()['Account']
        
    def create_ecr_repository(self) -> str:
        """Create ECR repository if it doesn't exist."""
        try:
            response = self.ecr_client.describe_repositories(
                repositoryNames=[ECR_REPOSITORY]
            )
            repo_uri = response['repositories'][0]['repositoryUri']
            print(f"ECR repository already exists: {repo_uri}")
            return repo_uri
        except self.ecr_client.exceptions.RepositoryNotFoundException:
            print(f"Creating ECR repository: {ECR_REPOSITORY}")
            response = self.ecr_client.create_repository(
                repositoryName=ECR_REPOSITORY,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'}
            )
            repo_uri = response['repository']['repositoryUri']
            print(f"ECR repository created: {repo_uri}")
            return repo_uri
    
    def get_ecr_login_token(self) -> str:
        """Get ECR login token."""
        response = self.ecr_client.get_authorization_token()
        auth_data = response['authorizationData'][0]
        token = auth_data['authorizationToken']
        registry = auth_data['proxyEndpoint']
        return token, registry
    
    def build_and_push_image(self, repo_uri: str) -> bool:
        """Build and push Docker image to ECR."""
        try:
            # Get ECR login
            token, registry = self.get_ecr_login_token()
            
            # Login to ECR
            print("Logging into ECR...")
            login_cmd = f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {registry}"
            subprocess.run(login_cmd, shell=True, check=True, capture_output=True, text=True)
            
            # Build ARM64 image
            print("Building ARM64 Docker image...")
            image_name = f"{repo_uri}:{IMAGE_TAG}"
            
            # Use buildx for ARM64
            subprocess.run([
                "docker", "buildx", "create", "--use", "--name", "arm-builder"
            ], capture_output=True)
            
            build_cmd = [
                "docker", "buildx", "build",
                "--platform", "linux/arm64",
                "-t", image_name,
                "--push",
                "."
            ]
            
            result = subprocess.run(build_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                # Try regular build as fallback
                print("Trying regular Docker build...")
                subprocess.run([
                    "docker", "build",
                    "--platform", "linux/arm64",
                    "-t", image_name,
                    "."
                ], check=True)
                
                # Push image
                print(f"Pushing image to ECR: {image_name}")
                subprocess.run(["docker", "push", image_name], check=True)
            
            print("Image successfully pushed to ECR!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error building/pushing image: {e}")
            return False
    
    def create_iam_role(self) -> str:
        """Create IAM role for Bedrock Agent runtime."""
        iam_client = boto3.client('iam', region_name=self.region)
        role_name = f"{AGENT_NAME}-bedrock-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role exists
            iam_client.get_role(RoleName=role_name)
            print(f"IAM role already exists: {role_name}")
            return f"arn:aws:iam::{self.account_id}:role/{role_name}"
        except iam_client.exceptions.NoSuchEntityException:
            # Create role
            print(f"Creating IAM role: {role_name}")
            response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Stock Forecast Bedrock Agent"
            )
            
            # Attach policies
            policies = [
                "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
                "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
            ]
            
            for policy_arn in policies:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            
            print(f"IAM role created: {response['Role']['Arn']}")
            return response['Role']['Arn']
    
    def deploy_agent_runtime(self, image_uri: str, role_arn: str) -> Dict[str, Any]:
        """Deploy agent to Bedrock AgentCore runtime."""
        print("Deploying agent to Bedrock AgentCore...")
        
        # Create agent runtime configuration
        agent_config = {
            "agentName": AGENT_NAME,
            "description": "Stock Forecast Agent using yfinance and technical analysis",
            "containerConfiguration": {
                "imageUri": image_uri,
                "port": 8080,
                "environment": {
                    "AWS_DEFAULT_REGION": self.region,
                    "MODEL_ID": MODEL_ID
                }
            },
            "iamRole": role_arn,
            "networkMode": "awsvpc",
            "tags": {
                "Project": "StockForecast",
                "Environment": "Production",
                "CreatedBy": "DeployScript"
            }
        }
        
        # Deploy using boto3
        try:
            # Note: The actual Bedrock AgentCore API might differ
            # This is a conceptual implementation
            response = self.bedrock_client.create_agent_runtime(
                **agent_config
            )
            
            agent_arn = response.get('agentArn')
            print(f"Agent deployed successfully!")
            print(f"Agent ARN: {agent_arn}")
            return response
            
        except Exception as e:
            print(f"Error deploying agent: {e}")
            print("Note: Ensure you have proper AWS permissions and Bedrock access")
            return {}
    
    def test_agent(self, agent_arn: str, ticker: str = "AAPL") -> None:
        """Test the deployed agent."""
        print(f"\nTesting agent with ticker: {ticker}")
        
        try:
            response = self.bedrock_client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                sessionId=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                payload={
                    "input": ticker
                }
            )
            
            result = response.get('output', {})
            print("\nAgent Response:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Error testing agent: {e}")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Stock Forecast Agent to Bedrock")
    parser.add_argument("--region", default=AWS_REGION, help="AWS region")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker build")
    parser.add_argument("--test", action="store_true", help="Test deployed agent")
    parser.add_argument("--ticker", default="AAPL", help="Test ticker symbol")
    
    args = parser.parse_args()
    
    print("="*60)
    print("STOCK FORECAST AGENT - BEDROCK DEPLOYMENT")
    print("="*60)
    print(f"Region: {args.region}")
    print(f"Repository: {ECR_REPOSITORY}")
    print(f"Model: {MODEL_ID}")
    print()
    
    deployer = BedrockAgentDeployer(region=args.region)
    
    # Step 1: Create ECR repository
    repo_uri = deployer.create_ecr_repository()
    image_uri = f"{repo_uri}:{IMAGE_TAG}"
    
    # Step 2: Build and push Docker image
    if not args.skip_build:
        success = deployer.build_and_push_image(repo_uri)
        if not success:
            print("Failed to build/push Docker image")
            return 1
    else:
        print("Skipping Docker build (--skip-build flag)")
    
    # Step 3: Create IAM role
    role_arn = deployer.create_iam_role()
    
    # Step 4: Deploy to Bedrock AgentCore
    deployment = deployer.deploy_agent_runtime(image_uri, role_arn)
    
    if deployment and args.test:
        # Step 5: Test the agent
        agent_arn = deployment.get('agentArn')
        if agent_arn:
            time.sleep(30)  # Wait for deployment to stabilize
            deployer.test_agent(agent_arn, args.ticker)
    
    print("\n" + "="*60)
    print("Deployment Summary:")
    print(f"- ECR Repository: {repo_uri}")
    print(f"- Docker Image: {image_uri}")
    print(f"- IAM Role: {role_arn}")
    if deployment:
        print(f"- Agent ARN: {deployment.get('agentArn', 'N/A')}")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
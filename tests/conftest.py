# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Pytest configuration and shared fixtures.

This file provides fixtures and configuration for both unit and integration tests.
"""

import pytest
import boto3
import os


# ===== Integration Test Fixtures =====


@pytest.fixture(scope="session")
def aws_region() -> str:
    """AWS region for integration tests."""
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture(scope="session")
def stack_name() -> str:
    """CloudFormation stack name."""
    return os.environ.get("STACK_NAME", "healthcare-agents-stack")


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    """AWS SSM client for reading configuration."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def cfn_client(aws_region):
    """AWS CloudFormation client for reading stack outputs."""
    return boto3.client("cloudformation", region_name=aws_region)


@pytest.fixture(scope="session")
def gateway_url(ssm_client, stack_name):
    """Get Gateway URL from SSM Parameter Store."""
    try:
        response = ssm_client.get_parameter(Name=f"/{stack_name}/gateway_url")
        return response["Parameter"]["Value"]
    except Exception as e:
        pytest.skip(f"Could not get gateway URL from SSM: {e}")


@pytest.fixture(scope="session")
def runtime_arn(cfn_client, stack_name):
    """Get Runtime ARN from CloudFormation stack outputs."""
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
        outputs = response["Stacks"][0]["Outputs"]

        for output in outputs:
            if output["OutputKey"] == "RuntimeArn":
                return output["OutputValue"]

        pytest.skip(f"RuntimeArn not found in stack {stack_name} outputs")
    except Exception as e:
        pytest.skip(f"Could not get stack outputs: {e}")


@pytest.fixture(scope="session")
def cognito_config(ssm_client, stack_name):
    """Get Cognito configuration from SSM."""
    try:
        params = {
            "client_id": f"/{stack_name}/cognito/machine_client_id",
            "client_secret": f"/{stack_name}/cognito/machine_client_secret",
            "user_pool_id": f"/{stack_name}/cognito/user_pool_id",
            "domain": f"/{stack_name}/cognito/domain",
        }

        config = {}
        for key, param_name in params.items():
            response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
            config[key] = response["Parameter"]["Value"]

        return config
    except Exception as e:
        pytest.skip(f"Could not get Cognito config from SSM: {e}")


@pytest.fixture
def oauth_token(cognito_config, aws_region):
    """Get OAuth token for Gateway authentication."""
    import requests

    token_url = f"https://{cognito_config['domain']}.auth.{aws_region}.amazoncognito.com/oauth2/token"

    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": cognito_config["client_id"],
            "client_secret": cognito_config["client_secret"],
        },
        timeout=10,
    )

    if response.status_code != 200:
        pytest.skip(f"Could not obtain OAuth token: {response.text}")

    return response.json()["access_token"]


# ===== Test Markers Configuration =====


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no AWS)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires deployed stack)"
    )
    config.addinivalue_line("markers", "slow: Slow tests (> 30 seconds)")


# ===== Test Collection Hooks =====


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Auto-mark tests in integration/ directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

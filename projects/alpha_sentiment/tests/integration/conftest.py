"""Fixtures for integration tests"""
import pytest
import os


@pytest.fixture
def has_deepseek_key():
    """Check if DeepSeek API key is available"""
    return bool(os.getenv("DEEPSEEK_API_KEY"))


@pytest.fixture
def skip_without_deepseek_key(has_deepseek_key):
    """Skip test if DeepSeek API key is not available"""
    if not has_deepseek_key:
        pytest.skip("DEEPSEEK_API_KEY not set")

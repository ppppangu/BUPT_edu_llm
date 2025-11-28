"""Root pytest fixtures for all test types"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_stock_code():
    """Sample stock code for testing"""
    return "000001"  # 平安银行


@pytest.fixture
def sample_stock_name():
    """Sample stock name for testing"""
    return "平安银行"

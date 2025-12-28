"""
Pytest fixtures for network effects analyzer tests.

Provides sample data and common test utilities.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_users():
    """Generate sample user count data with realistic values."""
    np.random.seed(42)
    n = 500
    # Simulate growing user base with some noise
    base = np.linspace(1000, 100000, n)
    noise = np.random.lognormal(0, 0.1, n)
    users = base * noise
    return users.astype(int)


@pytest.fixture
def sample_market_cap(sample_users):
    """Generate sample market cap data following Metcalfe's Law with noise."""
    np.random.seed(42)
    # Generate market cap with beta ~ 1.5 (sustainable network effects)
    alpha = 10.0
    beta = 1.5
    noise = np.random.lognormal(0, 0.2, len(sample_users))
    market_cap = np.exp(alpha) * (sample_users ** beta) * noise
    return market_cap


@pytest.fixture
def sample_market_cap_weak(sample_users):
    """Generate sample market cap data with weak network effects (beta < 1)."""
    np.random.seed(42)
    alpha = 15.0
    beta = 0.4  # Weak network effects
    noise = np.random.lognormal(0, 0.3, len(sample_users))
    market_cap = np.exp(alpha) * (sample_users ** beta) * noise
    return market_cap


@pytest.fixture
def sample_dataframe(sample_users, sample_market_cap):
    """Create a DataFrame with user and market cap data."""
    return pd.DataFrame({
        'users': sample_users,
        'market_cap': sample_market_cap,
        'log_users': np.log(sample_users),
        'log_mcap': np.log(sample_market_cap)
    })


@pytest.fixture
def small_sample():
    """Small sample for quick tests."""
    np.random.seed(42)
    users = np.array([100, 200, 500, 1000, 2000, 5000, 10000])
    alpha = 10.0
    beta = 1.3
    market_cap = np.exp(alpha) * (users ** beta)
    return {'users': users, 'market_cap': market_cap}


@pytest.fixture
def regime_switching_data():
    """Generate data with regime-switching behavior."""
    np.random.seed(42)
    n = 500
    
    # First half: bullish regime (beta ~ 1.8)
    users_1 = np.linspace(1000, 50000, n // 2)
    alpha = 10.0
    beta_bull = 1.8
    noise_1 = np.random.lognormal(0, 0.15, n // 2)
    mcap_1 = np.exp(alpha) * (users_1 ** beta_bull) * noise_1
    
    # Second half: bearish regime (beta ~ 0.8)
    users_2 = np.linspace(50000, 100000, n // 2)
    beta_bear = 0.8
    # Adjust alpha to make transition smooth
    alpha_bear = alpha + (beta_bull - beta_bear) * np.log(50000)
    noise_2 = np.random.lognormal(0, 0.2, n // 2)
    mcap_2 = np.exp(alpha_bear) * (users_2 ** beta_bear) * noise_2
    
    users = np.concatenate([users_1, users_2])
    market_cap = np.concatenate([mcap_1, mcap_2])
    
    return {
        'users': users,
        'market_cap': market_cap,
        'beta_bull': beta_bull,
        'beta_bear': beta_bear
    }


@pytest.fixture
def ethereum_like_data():
    """Generate data mimicking Ethereum's network effects (~beta=1.3)."""
    np.random.seed(42)
    n = 1000
    
    # Ethereum-like growing user base
    users = np.linspace(10000, 500000, n)
    # Add cyclical pattern
    cycle = 1 + 0.3 * np.sin(np.linspace(0, 6 * np.pi, n))
    users = users * cycle
    
    alpha = 12.0
    beta = 1.31  # Match Ethereum's estimated beta
    noise = np.random.lognormal(0, 0.25, n)
    market_cap = np.exp(alpha) * (users ** beta) * noise
    
    return {
        'users': users,
        'market_cap': market_cap,
        'expected_beta': beta
    }


@pytest.fixture
def invalid_data():
    """Data with invalid values for testing error handling."""
    return {
        'users_with_zeros': np.array([0, 100, 200, 300]),
        'users_with_negatives': np.array([-100, 100, 200, 300]),
        'users_with_nan': np.array([100, np.nan, 200, 300]),
        'mcap_with_zeros': np.array([0, 1e9, 2e9, 3e9]),
        'mcap_with_negatives': np.array([-1e9, 1e9, 2e9, 3e9])
    }


# Path fixtures
@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root):
    """Return the data directory."""
    return project_root / 'data'


@pytest.fixture
def cache_dir(data_dir):
    """Return the cache directory."""
    return data_dir / 'cache'

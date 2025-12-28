"""
Integration tests for network effects analyzer.

Tests the full workflow from data loading to model fitting and prediction.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.metcalfe_model import MetcalfeModel
from src.analysis.markov_switching import FTPMSModel


class TestFullWorkflow:
    """Test the complete analysis workflow."""
    
    def test_metcalfe_workflow(self, sample_dataframe):
        """Test full Metcalfe model workflow."""
        # 1. Load data
        df = sample_dataframe
        assert 'users' in df.columns
        assert 'market_cap' in df.columns
        
        # 2. Fit model
        model = MetcalfeModel()
        results = model.fit(df['users'].values, df['market_cap'].values)
        
        # 3. Analyze results
        assert results['beta'] is not None
        assert results['r_squared'] > 0
        
        # 4. Make predictions
        future_users = np.array([150000, 200000, 250000])
        predictions = model.predict(future_users)
        
        # 5. Validate predictions
        assert len(predictions) == 3
        assert np.all(predictions > 0)
        # Higher users should give higher predictions (for positive beta)
        if model.beta > 0:
            assert predictions[2] > predictions[0]
            
    @pytest.mark.xfail(reason="MS models may not converge on synthetic data")
    def test_markov_switching_workflow(self, regime_switching_data):
        """Test full Markov-switching workflow."""
        # 1. Prepare data
        users = regime_switching_data['users']
        mcap = regime_switching_data['market_cap']
        
        # 2. Fit model
        model = FTPMSModel(k_regimes=2)
        results = model.fit(users, mcap)
        
        # 3. Analyze regimes
        assert results['betas'] is not None
        assert len(results['betas']) == 2
        current_regime = model.get_current_regime()
        assert current_regime in [1, 2]
        
        # 4. Make regime-specific predictions
        test_users = np.array([75000])
        pred_bull = model.predict(test_users, regime=1)
        pred_bear = model.predict(test_users, regime=2)
        
        # 5. Predictions should differ by regime
        assert pred_bull[0] != pred_bear[0]
        
    @pytest.mark.xfail(reason="MS models may not converge on synthetic data")
    def test_model_comparison(self, sample_users, sample_market_cap):
        """Test comparing base Metcalfe vs Markov-switching."""
        # Fit base model
        base_model = MetcalfeModel()
        base_model.fit(sample_users, sample_market_cap)
        
        # Fit Markov-switching model
        ms_model = FTPMSModel()
        ms_model.fit(sample_users, sample_market_cap)
        
        # Both should produce valid results
        assert base_model.beta is not None
        assert ms_model.betas is not None
        
        # Base model beta should be roughly the average of MS betas
        avg_ms_beta = (ms_model.betas[1] + ms_model.betas[2]) / 2
        # This is a loose check - just ensure they're in same ballpark
        assert abs(base_model.beta - avg_ms_beta) < 1.0


class TestDataQuality:
    """Test data quality checks."""
    
    def test_data_consistency(self, sample_users, sample_market_cap):
        """Test that data is internally consistent."""
        assert len(sample_users) == len(sample_market_cap)
        assert np.all(sample_users > 0)
        assert np.all(sample_market_cap > 0)
        
    def test_log_transform_validity(self, sample_users, sample_market_cap):
        """Test that log transforms produce valid values."""
        log_users = np.log(sample_users)
        log_mcap = np.log(sample_market_cap)
        
        assert np.all(np.isfinite(log_users))
        assert np.all(np.isfinite(log_mcap))


class TestSustainabilityClassification:
    """Test sustainability classification based on beta values."""
    
    def test_sustainable_classification(self, sample_users, sample_market_cap):
        """Test that high beta is classified as sustainable."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        # Our synthetic data has true beta = 1.5 (sustainable)
        is_sustainable = model.beta > 1.0
        assert is_sustainable
        
    def test_unsustainable_classification(self, sample_users, sample_market_cap_weak):
        """Test that low beta is classified as unsustainable."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap_weak)
        
        # Our weak synthetic data has true beta = 0.4 (unsustainable)
        is_sustainable = model.beta > 1.0
        assert not is_sustainable
        
    def test_ethereum_like_classification(self, ethereum_like_data):
        """Test classification with Ethereum-like data."""
        model = MetcalfeModel()
        model.fit(ethereum_like_data['users'], ethereum_like_data['market_cap'])
        
        # Expected beta is 1.31 (sustainable)
        is_sustainable = model.beta > 1.0
        assert is_sustainable
        
        # Check we're close to expected value
        assert abs(model.beta - ethereum_like_data['expected_beta']) < 0.2


class TestRealDataIntegration:
    """Test integration with real data files if available."""
    
    def test_load_ethereum_data(self, cache_dir):
        """Test loading Ethereum data if available."""
        eth_dir = cache_dir / 'ethereum'
        if not eth_dir.exists():
            pytest.skip("Ethereum cache data not available")
            
        # Look for any CSV files
        csv_files = list(eth_dir.glob('*.csv'))
        if not csv_files:
            pytest.skip("No Ethereum CSV files found")
            
        # Load first available file
        df = pd.read_csv(csv_files[0])
        assert len(df) > 0
        
    def test_load_render_data(self, cache_dir):
        """Test loading Render data if available."""
        render_dir = cache_dir / 'render'
        if not render_dir.exists():
            pytest.skip("Render cache data not available")
            
        csv_files = list(render_dir.glob('*.csv'))
        if not csv_files:
            pytest.skip("No Render CSV files found")
            
        df = pd.read_csv(csv_files[0])
        assert len(df) > 0


class TestResultsReproducibility:
    """Test that results are reproducible."""
    
    def test_metcalfe_reproducibility(self, sample_users, sample_market_cap):
        """Test that Metcalfe model gives same results on refit."""
        model1 = MetcalfeModel()
        model1.fit(sample_users, sample_market_cap)
        
        model2 = MetcalfeModel()
        model2.fit(sample_users, sample_market_cap)
        
        assert model1.beta == model2.beta
        assert model1.alpha == model2.alpha
        assert model1.r_squared == model2.r_squared
        
    def test_prediction_reproducibility(self, sample_users, sample_market_cap):
        """Test that predictions are reproducible."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        test_users = np.array([100000, 200000])
        pred1 = model.predict(test_users)
        pred2 = model.predict(test_users)
        
        np.testing.assert_array_equal(pred1, pred2)

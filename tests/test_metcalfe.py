"""
Unit tests for MetcalfeModel.

Tests the base Metcalfe's Law model implementation.
"""

import pytest
import numpy as np
from src.analysis.metcalfe_model import MetcalfeModel


class TestMetcalfeModelInit:
    """Tests for MetcalfeModel initialization."""
    
    def test_initialization(self):
        """Test that model initializes with None values."""
        model = MetcalfeModel()
        assert model.alpha is None
        assert model.beta is None
        assert model.r_squared is None
        assert model.std_error is None
        
    def test_repr_unfitted(self):
        """Test string representation before fitting."""
        model = MetcalfeModel()
        assert "not fitted" in repr(model)


class TestMetcalfeModelFit:
    """Tests for MetcalfeModel.fit() method."""
    
    def test_basic_fit(self, sample_users, sample_market_cap):
        """Test basic model fitting."""
        model = MetcalfeModel()
        results = model.fit(sample_users, sample_market_cap)
        
        assert model.alpha is not None
        assert model.beta is not None
        assert model.r_squared is not None
        assert 'beta' in results
        assert 'r_squared' in results
        
    def test_beta_estimation_accuracy(self, sample_users, sample_market_cap):
        """Test that beta is estimated close to true value."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        # True beta is 1.5, should be within 0.2
        assert abs(model.beta - 1.5) < 0.2
        
    def test_weak_network_effects(self, sample_users, sample_market_cap_weak):
        """Test detection of weak network effects (beta < 1)."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap_weak)
        
        # True beta is 0.4, should be less than 1
        assert model.beta < 1.0
        
    def test_r_squared_reasonable(self, sample_users, sample_market_cap):
        """Test that R-squared is in valid range."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        assert 0 <= model.r_squared <= 1
        # With our synthetic data, should have decent fit
        assert model.r_squared > 0.5
        
    def test_confidence_interval(self, sample_users, sample_market_cap):
        """Test that confidence interval is computed correctly."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap, confidence_level=0.95)
        
        ci_low, ci_high = model.confidence_interval
        assert ci_low < model.beta < ci_high
        assert ci_high - ci_low > 0
        
    def test_p_value(self, sample_users, sample_market_cap):
        """Test that p-value is computed and significant."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        assert 0 <= model.p_value <= 1
        # With our synthetic data, should be highly significant
        assert model.p_value < 0.05
        
    def test_fitted_values_and_residuals(self, sample_users, sample_market_cap):
        """Test that fitted values and residuals are computed."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        assert model.fitted_values is not None
        assert model.residuals is not None
        assert len(model.fitted_values) == len(sample_users)
        assert len(model.residuals) == len(sample_users)
        
    def test_small_sample(self, small_sample):
        """Test fitting with small sample."""
        model = MetcalfeModel()
        results = model.fit(small_sample['users'], small_sample['market_cap'])
        
        assert model.beta is not None
        # Should be close to 1.3 (true value)
        assert abs(model.beta - 1.3) < 0.1


class TestMetcalfeModelPredict:
    """Tests for MetcalfeModel.predict() method."""
    
    def test_predict_basic(self, sample_users, sample_market_cap):
        """Test basic prediction."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        predictions = model.predict(sample_users)
        assert len(predictions) == len(sample_users)
        assert np.all(predictions > 0)
        
    def test_predict_single_value(self, sample_users, sample_market_cap):
        """Test prediction with single value."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        prediction = model.predict(np.array([50000]))
        assert len(prediction) == 1
        assert prediction[0] > 0
        
    def test_predict_before_fit_raises(self):
        """Test that prediction before fitting raises error."""
        model = MetcalfeModel()
        
        with pytest.raises(ValueError, match="fitted"):
            model.predict(np.array([1000, 2000]))
            
    def test_predict_with_zero_raises(self, sample_users, sample_market_cap):
        """Test that prediction with zero users raises error."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        with pytest.raises(ValueError, match="positive"):
            model.predict(np.array([0, 1000]))


class TestMetcalfeModelEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_mismatched_lengths_raises(self):
        """Test that mismatched array lengths raise error."""
        model = MetcalfeModel()
        users = np.array([100, 200, 300])
        mcap = np.array([1e9, 2e9])
        
        with pytest.raises(ValueError, match="same length"):
            model.fit(users, mcap)
            
    def test_zero_users_raises(self, invalid_data):
        """Test that zero users raise error."""
        model = MetcalfeModel()
        mcap = np.array([1e9, 2e9, 3e9, 4e9])
        
        with pytest.raises(ValueError, match="positive"):
            model.fit(invalid_data['users_with_zeros'], mcap)
            
    def test_negative_users_raises(self, invalid_data):
        """Test that negative users raise error."""
        model = MetcalfeModel()
        mcap = np.array([1e9, 2e9, 3e9, 4e9])
        
        with pytest.raises(ValueError, match="positive"):
            model.fit(invalid_data['users_with_negatives'], mcap)
            
    def test_zero_mcap_raises(self, invalid_data):
        """Test that zero market cap raises error."""
        model = MetcalfeModel()
        users = np.array([100, 200, 300, 400])
        
        with pytest.raises(ValueError, match="positive"):
            model.fit(users, invalid_data['mcap_with_zeros'])
            
    def test_repr_after_fit(self, sample_users, sample_market_cap):
        """Test string representation after fitting."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        repr_str = repr(model)
        assert "α=" in repr_str
        assert "β=" in repr_str
        assert "R²=" in repr_str


class TestMetcalfeModelGetResults:
    """Tests for MetcalfeModel.get_results() method."""
    
    def test_get_results_structure(self, sample_users, sample_market_cap):
        """Test that get_results returns correct structure."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        results = model.get_results()
        
        expected_keys = [
            'alpha', 'beta', 'r_squared', 'std_error',
            'p_value', 'confidence_interval', 'fitted_values', 'residuals'
        ]
        for key in expected_keys:
            assert key in results
            
    def test_get_results_values_match_attributes(self, sample_users, sample_market_cap):
        """Test that get_results values match model attributes."""
        model = MetcalfeModel()
        model.fit(sample_users, sample_market_cap)
        
        results = model.get_results()
        
        assert results['alpha'] == model.alpha
        assert results['beta'] == model.beta
        assert results['r_squared'] == model.r_squared

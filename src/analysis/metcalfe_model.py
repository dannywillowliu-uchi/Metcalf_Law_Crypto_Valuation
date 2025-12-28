"""
Base Metcalfe's Law Model Implementation

Implements the core model: P = e^α × u^β
In log form: ln(P) = α + β ln(u)

Where:
- P = Market capitalization (network value)
- u = Active users (appropriately defined)
- β = Network effect strength parameter
- α = Scaling constant
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from sklearn.linear_model import LinearRegression
from scipy import stats


class MetcalfeModel:
    """
    Base Metcalfe's Law model using OLS regression.
    
    Fits the relationship: ln(P) = α + β ln(u)
    """
    
    def __init__(self):
        self.alpha: Optional[float] = None
        self.beta: Optional[float] = None
        self.r_squared: Optional[float] = None
        self.std_error: Optional[float] = None
        self.p_value: Optional[float] = None
        self.confidence_interval: Optional[Tuple[float, float]] = None
        self.fitted_values: Optional[np.ndarray] = None
        self.residuals: Optional[np.ndarray] = None
        
    def fit(
        self, 
        users: np.ndarray, 
        value: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Fit the Metcalfe's Law model using OLS regression.
        
        Parameters
        ----------
        users : np.ndarray
            Active user counts (should be positive)
        value : np.ndarray
            Market capitalization or network value (should be positive)
        confidence_level : float, default=0.95
            Confidence level for beta confidence interval
            
        Returns
        -------
        dict
            Dictionary containing:
            - alpha: Intercept parameter
            - beta: Network effect strength parameter
            - r_squared: R-squared value
            - std_error: Standard error of beta
            - p_value: P-value for beta coefficient
            - confidence_interval: (lower, upper) for beta
            - fitted_values: Predicted log values
            - residuals: Residuals from regression
        """
        # Validate inputs
        users = np.asarray(users)
        value = np.asarray(value)
        
        if len(users) != len(value):
            raise ValueError("users and value must have the same length")
        
        if np.any(users <= 0) or np.any(value <= 0):
            raise ValueError("users and value must be strictly positive")
        
        # Transform to log space
        log_users = np.log(users)
        log_value = np.log(value)
        
        # Remove any infinite or NaN values
        valid_mask = np.isfinite(log_users) & np.isfinite(log_value)
        if not np.all(valid_mask):
            log_users = log_users[valid_mask]
            log_value = log_value[valid_mask]
        
        # Fit OLS regression: ln(P) = α + β ln(u)
        X = log_users.reshape(-1, 1)
        y = log_value
        
        regressor = LinearRegression()
        regressor.fit(X, y)
        
        # Extract parameters
        self.beta = regressor.coef_[0]
        self.alpha = regressor.intercept_
        
        # Calculate fitted values and residuals
        self.fitted_values = regressor.predict(X)
        self.residuals = y - self.fitted_values
        self.r_squared = regressor.score(X, y)
        
        # Calculate standard error and confidence interval for beta
        n = len(y)
        mse = np.sum(self.residuals ** 2) / (n - 2)
        var_beta = mse / np.sum((log_users - np.mean(log_users)) ** 2)
        self.std_error = np.sqrt(var_beta)
        
        # T-statistic and p-value
        t_stat = self.beta / self.std_error
        self.p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
        # Confidence interval
        t_critical = stats.t.ppf((1 + confidence_level) / 2, n - 2)
        margin = t_critical * self.std_error
        self.confidence_interval = (self.beta - margin, self.beta + margin)
        
        return self.get_results()
    
    def predict(self, users: np.ndarray) -> np.ndarray:
        """
        Predict network value given user counts.
        
        Parameters
        ----------
        users : np.ndarray
            Active user counts
            
        Returns
        -------
        np.ndarray
            Predicted market capitalization values
        """
        if self.alpha is None or self.beta is None:
            raise ValueError("Model must be fitted before prediction")
        
        users = np.asarray(users)
        if np.any(users <= 0):
            raise ValueError("users must be strictly positive")
        
        log_users = np.log(users)
        log_predicted = self.alpha + self.beta * log_users
        return np.exp(log_predicted)
    
    def get_results(self) -> Dict:
        """
        Get model results as a dictionary.
        
        Returns
        -------
        dict
            Dictionary of model parameters and statistics
        """
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'r_squared': self.r_squared,
            'std_error': self.std_error,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'fitted_values': self.fitted_values,
            'residuals': self.residuals
        }
    
    def __repr__(self) -> str:
        if self.beta is None:
            return "MetcalfeModel(not fitted)"
        return f"MetcalfeModel(α={self.alpha:.4f}, β={self.beta:.4f}, R²={self.r_squared:.4f})"


"""
Fixed Transition Probabilities Markov-Switching (FTP-MS) Model

Implements the two-regime Markov-switching model:
ln(pt) = {
  α + β₁,₁ ln(ut) + ε  if st = 1  (bullish regime)
  α + β₁,₂ ln(ut) + ε  if st = 2  (bearish regime)
}

Uses statsmodels.tsa.regime_switching.MarkovRegression
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
import warnings

try:
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
except ImportError:
    raise ImportError(
        "statsmodels>=0.14.0 is required for Markov-switching models. "
        "Install with: pip install statsmodels>=0.14.0"
    )


class FTPMSModel:
    """
    Fixed Transition Probabilities Markov-Switching model.
    
    Implements the two-regime model where network effects (β) vary
    between bullish and bearish market conditions.
    """
    
    def __init__(self, k_regimes: int = 2):
        """
        Initialize FTP-MS model.
        
        Parameters
        ----------
        k_regimes : int, default=2
            Number of regimes (2 for bull/bear, 3 for robustness check)
        """
        if k_regimes not in [2, 3]:
            raise ValueError("k_regimes must be 2 or 3")
        
        self.k_regimes = k_regimes
        self.model: Optional[MarkovRegression] = None
        self.results: Optional[object] = None
        
        # Parameters (will be set after fitting)
        self.alpha: Optional[float] = None
        self.betas: Optional[Dict[int, float]] = None
        self.transition_probs: Optional[np.ndarray] = None
        self.regime_probabilities: Optional[np.ndarray] = None
        self.smoothed_probabilities: Optional[np.ndarray] = None
        
    def fit(
        self,
        users: np.ndarray,
        value: np.ndarray,
        switching_variance: bool = False,
        **kwargs
    ) -> Dict:
        """
        Fit the FTP-MS model.
        
        Parameters
        ----------
        users : np.ndarray
            Active user counts (should be positive)
        value : np.ndarray
            Market capitalization or network value (should be positive)
        switching_ar : bool, default=False
            Whether AR coefficients switch between regimes
        switching_var : bool, default=False
            Whether variance switches between regimes
        **kwargs
            Additional arguments passed to MarkovRegression.fit()
            
        Returns
        -------
        dict
            Dictionary containing model parameters and statistics
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
        
        # Prepare data for statsmodels
        # MarkovRegression expects: y = X @ params + error
        # We want: ln(P) = α + β ln(u) + ε
        # Per paper: α is constant, only β switches between regimes
        # Use only log_users as exog, let switching_trend=False handle constant α
        # This avoids numerical issues with switching_exog=[False, True]
        X = log_users.reshape(-1, 1)  # Only log_users, no constant
        y = log_value
        
        # Create and fit Markov-switching model
        # k_regimes: number of regimes
        # order: AR order (0 for no AR terms, just regression)
        # switching_variance: whether variance switches between regimes
        # switching_trend: whether intercept (α) switches (False = constant α)
        # switching_exog: whether exogenous coefficients (β) switch (True = β switches)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Per paper: α is constant, only β switches between regimes
            # Equation 3: ln(pt) = α + β₁,₁ ln(ut) + ε (same α for both regimes)
            # With X = [log_users] only:
            #   - switching_trend=False means constant intercept α
            #   - switching_exog=True means β switches between regimes
            self.model = MarkovRegression(
                endog=y,
                exog=X,
                k_regimes=self.k_regimes,
                order=0,  # No AR terms, just regression
                switching_trend=False,  # α is constant (per paper Section 6, Equation 3)
                switching_exog=True,   # β switches between regimes
                switching_variance=False  # Constant variance (per paper)
            )
            
            # Initialize using split-sample approach (helps identify regime differences)
            # This is more robust than single OLS initialization
            from sklearn.linear_model import LinearRegression
            import statsmodels.api as sm
            
            # Fit base model for overall starting values
            base_reg = LinearRegression()
            base_reg.fit(log_users.reshape(-1, 1), log_value)
            base_alpha = base_reg.intercept_
            base_beta = base_reg.coef_[0]
            
            # Split-sample approach: fit OLS on first and second half separately
            # This helps identify if there are regime differences
            half_idx = len(log_users) // 2
            first_half_X = sm.add_constant(log_users[:half_idx])
            first_half_y = log_value[:half_idx]
            second_half_X = sm.add_constant(log_users[half_idx:])
            second_half_y = log_value[half_idx:]
            
            ols_first = sm.OLS(first_half_y, first_half_X).fit()
            ols_second = sm.OLS(second_half_y, second_half_X).fit()
            
            beta_first = ols_first.params[1]
            beta_second = ols_second.params[1]
            alpha_avg = (ols_first.params[0] + ols_second.params[0]) / 2
            
            # Get number of parameters
            n_params = self.model.k_params
            
            # Use model's default start params as base
            try:
                start_params = self.model.start_params.copy()
            except:
                start_params = np.zeros(n_params)
            
            # Find parameter indices by name (more reliable)
            param_names = self.model.param_names if hasattr(self.model, 'param_names') else None
            beta0_idx = None
            beta1_idx = None
            
            if param_names:
                for i, name in enumerate(param_names):
                    if 'x1[0]' in name or ('x1' in name and '[0]' in name):
                        beta0_idx = i
                    elif 'x1[1]' in name or ('x1' in name and '[1]' in name):
                        beta1_idx = i
            
            # Set β values using split-sample results
            # Higher β = regime 1 (bullish), lower β = regime 2 (bearish)
            if beta_first > beta_second:
                beta1_start = beta_first
                beta2_start = beta_second
            else:
                beta1_start = beta_second
                beta2_start = beta_first
            
            # Set β starting values directly (in parameter space, not transformed)
            # This is the key: use split-sample betas directly, don't transform
            if beta0_idx is not None and beta1_idx is not None:
                start_params[beta0_idx] = beta1_start  # Higher β = regime 1 (bullish)
                start_params[beta1_idx] = beta2_start  # Lower β = regime 2 (bearish)
            elif n_params >= 5:
                # Fallback: assume structure [p00, p10, const, β0, β1, sigma2]
                start_params[3] = beta1_start
                start_params[4] = beta2_start
            
            # Transition probabilities: use default (model handles transformation)
            # Don't modify - let model use defaults for stability
            
            # Variance: use default (don't modify - causes numerical issues)
            # The model will estimate variance during EM algorithm
            
            # Fit with split-sample initialization
            # Use conservative settings to avoid numerical issues
            fit_kwargs = {
                'maxiter': kwargs.get('maxiter', 500),  # Fewer iterations for stability
                'start_params': start_params,
                'em_iter': kwargs.get('em_iter', 20),  # Fewer EM iterations
            }
            # Remove mle_iter if present (not always supported)
            fit_kwargs.update({k: v for k, v in kwargs.items() if k not in fit_kwargs and k != 'mle_iter'})
            
            try:
                self.results = self.model.fit(**fit_kwargs)
            except (RuntimeError, np.linalg.LinAlgError, ValueError) as e:
                # If fit fails, try with even more conservative initialization
                print(f"Warning: Initial fit failed ({e}), trying more conservative initialization...")
                
                # Use default start params, only set betas (most important)
                try:
                    conservative_start = self.model.start_params.copy()
                except:
                    conservative_start = np.zeros(n_params)
                
                # Use split-sample betas (already calculated above)
                # This is more stable than using base_beta variations
                if beta0_idx is not None and beta1_idx is not None:
                    if beta_first > beta_second:
                        conservative_start[beta0_idx] = beta_first
                        conservative_start[beta1_idx] = beta_second
                    else:
                        conservative_start[beta0_idx] = beta_second
                        conservative_start[beta1_idx] = beta_first
                elif n_params >= 5:
                    if beta_first > beta_second:
                        conservative_start[3] = beta_first
                        conservative_start[4] = beta_second
                    else:
                        conservative_start[3] = beta_second
                        conservative_start[4] = beta_first
                
                # Don't modify transition probs or variance - use defaults
                
                fit_kwargs['start_params'] = conservative_start
                fit_kwargs['maxiter'] = 300  # Fewer iterations
                fit_kwargs['em_iter'] = 15   # Fewer EM iterations
                
                try:
                    self.results = self.model.fit(**fit_kwargs)
                except Exception as e2:
                    # Last resort: use default initialization
                    print(f"Warning: Second attempt failed ({e2}), using default initialization...")
                    fit_kwargs.pop('start_params', None)
                    fit_kwargs['maxiter'] = 200
                    fit_kwargs['em_iter'] = 10
                    self.results = self.model.fit(**fit_kwargs)
        
        # Extract parameters
        # Access parameters through the results object
        # IMPORTANT: Parameters are in transformed space, need to untransform
        params_transformed = self.results.params
        params = self.model.untransform_params(params_transformed)
        param_names = self.results.param_names if hasattr(self.results, 'param_names') else None
        
        # Get transition matrix directly from results (most reliable)
        # This avoids parameter extraction issues
        if hasattr(self.results, 'regime_transition'):
            transition_matrix = self.results.regime_transition
            if transition_matrix.shape == (2, 2):
                p11 = float(transition_matrix[0, 0])
                p22 = float(transition_matrix[1, 1])
            else:
                # Handle different shapes
                p11 = 0.95
                p22 = 0.95
        else:
            p11 = 0.95
            p22 = 0.95
        
        # Extract betas and alpha based on parameter structure
        # Based on actual statsmodels parameter names:
        # ['p[0->0]', 'p[1->0]', 'const[1]', 'x1[0]', 'x1[1]', 'sigma2']
        # With switching_trend=False, switching_exog=True:
        # - p[0->0]: P₁₁ (staying in regime 0)
        # - p[1->0]: P₂₁ (switching from regime 1 to 0), so P₂₂ = 1 - p[1->0]
        # - const[1]: Constant for regime 1 (but we want constant α, so this might be 0 or unused)
        # - x1[0]: β for regime 0 (regime 1 in paper)
        # - x1[1]: β for regime 1 (regime 2 in paper)
        # - sigma2: variance
        if self.k_regimes == 2:
            # Use parameter names if available for accurate extraction
            if param_names is not None:
                # Find indices by name
                alpha_idx = None
                beta0_idx = None
                beta1_idx = None
                p00_idx = None
                p10_idx = None
                
                for i, name in enumerate(param_names):
                    if 'const' in name.lower():
                        alpha_idx = i
                    elif 'x1[0]' in name or ('x1' in name and '[0]' in name):
                        beta0_idx = i
                    elif 'x1[1]' in name or ('x1' in name and '[1]' in name):
                        beta1_idx = i
                    elif 'p[0->0]' in name or 'p00' in name.lower():
                        p00_idx = i
                    elif 'p[1->0]' in name or 'p10' in name.lower():
                        p10_idx = i
                
                # Extract alpha - with switching_trend=False, should be single constant
                # If const[1] exists, it might be regime-specific, but paper says constant
                # Use first param as alpha, or const if found
                if alpha_idx is not None:
                    self.alpha = params[alpha_idx]
                elif len(params) > 0:
                    # Fallback: might be in first position or need to calculate
                    self.alpha = params[0] if 'const' not in str(param_names[0]).lower() else 0.0
                else:
                    self.alpha = 0.0
                
                # Extract betas
                if beta0_idx is not None and beta1_idx is not None:
                    self.betas = {
                        1: params[beta0_idx],  # Regime 0 = Regime 1 in paper
                        2: params[beta1_idx]   # Regime 1 = Regime 2 in paper
                    }
                elif len(params) >= 4:
                    # Fallback: assume structure [p00, p10, const, β0, β1, sigma2]
                    self.betas = {
                        1: params[3] if len(params) > 3 else 1.0,
                        2: params[4] if len(params) > 4 else 1.0
                    }
                else:
                    self.betas = {1: 1.0, 2: 1.0}
                
                # Extract transition probabilities
                if p00_idx is not None:
                    p11 = params[p00_idx]
                elif len(params) > 0:
                    p11 = params[0]  # First param is usually P₁₁
                else:
                    p11 = 0.95
                
                if p10_idx is not None:
                    p21 = params[p10_idx]
                    p22 = 1.0 - p21  # P₂₂ = 1 - P₂₁
                elif len(params) > 1:
                    p21 = params[1]
                    p22 = 1.0 - p21
                else:
                    p22 = 0.95
            else:
                # Fallback: assume structure based on common patterns
                # Try: [P₁₁, P₂₁, α, β₁, β₂, σ²] or [P₁₁, P₂₁, const[1], β₁, β₂, σ²]
                if len(params) >= 6:
                    p11 = params[0]
                    p21 = params[1]
                    p22 = 1.0 - p21
                    # Alpha might be in position 2, or might need calculation
                    self.alpha = params[2] if abs(params[2]) < 100 else 0.0  # Const might be regime-specific
                    self.betas = {
                        1: params[3],
                        2: params[4]
                    }
                elif len(params) >= 4:
                    # Minimal structure
                    self.alpha = params[2] if len(params) > 2 else 0.0
                    self.betas = {
                        1: params[3] if len(params) > 3 else 1.0,
                        2: params[3] if len(params) > 3 else 1.0
                    }
                    p11 = 0.95
                    p22 = 0.95
                else:
                    self.alpha = 0.0
                    self.betas = {1: 1.0, 2: 1.0}
                    p11 = 0.95
                    p22 = 0.95
            
            # Use transition probabilities from matrix (more reliable than extracting from params)
            # Ensure probabilities are valid
            p11 = max(0.01, min(0.99, p11))
            p22 = max(0.01, min(0.99, p22))
            
            self.transition_probs = np.array([
                [p11, 1 - p22],
                [1 - p11, p22]
            ])
            
        elif self.k_regimes == 3:
            # For 3 regimes, structure is more complex
            # This is a simplified extraction - may need adjustment based on actual statsmodels output
            self.alpha = params[0] if len(params) > 0 else 0.0
            self.betas = {
                1: params[3] if len(params) > 3 else 1.0,
                2: params[4] if len(params) > 4 else 1.0,
                3: params[5] if len(params) > 5 else 1.0
            }
            # Transition probabilities for 3x3 matrix
            # This is a placeholder - actual structure needs verification
            self.transition_probs = np.eye(3) * 0.9  # Default to high persistence
        
        # Get smoothed probabilities (probability of being in each regime at each time)
        self.smoothed_probabilities = self.results.smoothed_marginal_probabilities
        
        # Get current regime probabilities (most recent)
        if self.smoothed_probabilities is not None:
            self.regime_probabilities = self.smoothed_probabilities[-1]
        
        return self.get_results()
    
    def get_current_regime(self) -> int:
        """
        Get the most likely current regime.
        
        Returns
        -------
        int
            Regime number (1 for bullish, 2 for bearish)
        """
        if self.regime_probabilities is None:
            raise ValueError("Model must be fitted first")
        
        return int(np.argmax(self.regime_probabilities) + 1)
    
    def predict(
        self, 
        users: np.ndarray, 
        regime: Optional[int] = None
    ) -> np.ndarray:
        """
        Predict network value given user counts.
        
        Parameters
        ----------
        users : np.ndarray
            Active user counts
        regime : int, optional
            Regime to use for prediction (1 or 2). If None, uses current regime.
            
        Returns
        -------
        np.ndarray
            Predicted market capitalization values
        """
        if self.alpha is None or self.betas is None:
            raise ValueError("Model must be fitted before prediction")
        
        users = np.asarray(users)
        if np.any(users <= 0):
            raise ValueError("users must be strictly positive")
        
        if regime is None:
            regime = self.get_current_regime()
        
        if regime not in self.betas:
            raise ValueError(f"regime must be one of {list(self.betas.keys())}")
        
        log_users = np.log(users)
        beta = self.betas[regime]
        log_predicted = self.alpha + beta * log_users
        return np.exp(log_predicted)
    
    def get_results(self) -> Dict:
        """
        Get model results as a dictionary.
        
        Returns
        -------
        dict
            Dictionary of model parameters and statistics
        """
        if self.results is None:
            return {}
        
        # Build transition probs dict for easier access
        transition_dict = None
        if self.transition_probs is not None:
            transition_dict = {
                'P11': float(self.transition_probs[0, 0]),
                'P12': float(self.transition_probs[0, 1]),
                'P21': float(self.transition_probs[1, 0]),
                'P22': float(self.transition_probs[1, 1])
            }
        
        results_dict = {
            'alpha': self.alpha,
            'betas': self.betas,
            'transition_probs': transition_dict,
            'transition_matrix': self.transition_probs.tolist() if self.transition_probs is not None else None,
            'regime_probabilities': self.regime_probabilities.tolist() if self.regime_probabilities is not None else None,
            'smoothed_probabilities': self.smoothed_probabilities.tolist() if self.smoothed_probabilities is not None else None,
            'aic': self.results.aic if hasattr(self.results, 'aic') else None,
            'bic': self.results.bic if hasattr(self.results, 'bic') else None,
            'log_likelihood': self.results.llf if hasattr(self.results, 'llf') else None,
            'current_regime': self.get_current_regime() if self.regime_probabilities is not None else None
        }
        
        return results_dict
    
    def __repr__(self) -> str:
        if self.betas is None:
            return f"FTPMSModel(k_regimes={self.k_regimes}, not fitted)"
        
        beta_str = ", ".join([f"β{reg}={val:.4f}" for reg, val in self.betas.items()])
        return f"FTPMSModel(k_regimes={self.k_regimes}, {beta_str})"


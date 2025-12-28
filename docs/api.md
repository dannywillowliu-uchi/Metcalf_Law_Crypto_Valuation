# API Reference

## MetcalfeModel

Base Metcalfe's Law model: `P = e^alpha * u^beta`

### Usage

```python
from src.analysis import MetcalfeModel

model = MetcalfeModel()
results = model.fit(users, market_cap)
predictions = model.predict(new_users)
```

### Methods

**fit(users, value, confidence_level=0.95)**
- `users`: array of active user counts
- `value`: array of market cap values
- Returns: dict with alpha, beta, r_squared, std_error, p_value, confidence_interval

**predict(users)**
- `users`: array of user counts
- Returns: array of predicted market cap values

**get_results()**
- Returns: dict of all model parameters

### Attributes

- `alpha`: intercept parameter
- `beta`: network effect coefficient
- `r_squared`: model fit
- `std_error`: standard error of beta
- `p_value`: statistical significance
- `confidence_interval`: (lower, upper) bounds

---

## FTPMSModel

Markov-switching model with regime-dependent beta.

### Usage

```python
from src.analysis import FTPMSModel

model = FTPMSModel(k_regimes=2)
results = model.fit(users, market_cap)
regime = model.get_current_regime()
predictions = model.predict(users, regime=1)
```

### Methods

**fit(users, value, switching_variance=False)**
- `users`: array of active user counts
- `value`: array of market cap values
- Returns: dict with betas, transition_probs, regime_probabilities

**predict(users, regime=None)**
- `users`: array of user counts
- `regime`: 1 or 2 (default: current regime)
- Returns: array of predicted values

**get_current_regime()**
- Returns: int (1 or 2)

### Attributes

- `alpha`: constant parameter
- `betas`: dict {1: beta_bull, 2: beta_bear}
- `transition_probs`: 2x2 transition matrix
- `smoothed_probabilities`: regime probabilities over time

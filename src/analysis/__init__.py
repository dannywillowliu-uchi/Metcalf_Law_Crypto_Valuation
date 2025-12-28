"""
Analysis module for network effects models.

Contains implementations of:
- Metcalfe's Law (base model)
- Fixed Transition Probabilities Markov-Switching (FTP-MS) model
"""

from .metcalfe_model import MetcalfeModel
from .markov_switching import FTPMSModel

__all__ = ['MetcalfeModel', 'FTPMSModel']


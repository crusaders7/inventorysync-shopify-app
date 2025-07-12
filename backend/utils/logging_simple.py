"""
Simple logging setup for InventorySync
"""

import logging
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inventorysync.log')
    ]
)

logger = logging.getLogger('inventorysync')

def get_logger(name: str = None):
    """Get logger instance"""
    if name:
        return logging.getLogger(f'inventorysync.{name}')
    return logger
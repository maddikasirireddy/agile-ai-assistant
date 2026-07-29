import logging
import sys

def setup_logging():
    """Configure system-wide logging."""
    logger = logging.getLogger("agile_wellness")
    
    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    # Formatter for log messages
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

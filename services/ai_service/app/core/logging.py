import logging

def get_custom_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """    
    Log levels integer mapping reference:
    - logging.DEBUG = 10
    - logging.INFO = 20
    - logging.WARNING = 30
    - logging.ERROR = 40
    - logging.CRITICAL = 50
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    return logger

logger = get_custom_logger("AI-Service", level=logging.DEBUG)
    
logger.debug("This is a debug message.")

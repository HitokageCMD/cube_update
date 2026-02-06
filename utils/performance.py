import time
import functools
from .logger import logger

def profile_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        # Log if slow (e.g. > 16ms for a frame update)
        if duration > 0.016: 
            logger.warning(f"Performance Warning: {func.__name__} took {duration:.4f}s")
        return result
    return wrapper

"""Polling functionality for async video generation."""
import threading
import time
from typing import Callable
from loguru import logger
from replicate.prediction import Prediction


class PollingThread(threading.Thread):
    """Background thread for status polling without blocking main execution."""
    
    def __init__(self, prediction: Prediction, poll_interval: int, 
                 max_wait_time: int, callback: Callable):
        super().__init__(daemon=True)
        self.prediction = prediction
        self.poll_interval = poll_interval
        self.max_wait_time = max_wait_time
        self.callback = callback
        self.result = None
        
    def run(self) -> None:
        """Run polling in background."""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.max_wait_time:
                logger.error(f"Timeout waiting for prediction {self.prediction.id}")
                break
                
            try:
                self.prediction.reload()
            except Exception as e:
                logger.error(f"Error reloading prediction: {e}")
                break
                
            if self.callback:
                self.callback(self.prediction.status, None)
                
            if self.prediction.status == "succeeded":
                self.result = self.prediction.output
                break
            elif self.prediction.status in ["failed", "canceled"]:
                logger.error(f"Prediction {self.prediction.status}")
                break
                
            time.sleep(self.poll_interval)
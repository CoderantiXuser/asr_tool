import time
import statistics
from collections import deque
from enhanced_logger import log_message

class ConfidenceTracker:
    def __init__(self, window_size=20):
        self.window_size = window_size
        self.confidence_history = deque(maxlen=window_size)
        self.rejection_history = deque(maxlen=window_size)
        self.recognition_times = deque(maxlen=window_size)
        
        # Thresholds
        self.base_threshold = 0.6
        self.current_threshold = self.base_threshold
        self.min_threshold = 0.3
        self.max_threshold = 0.9
        
        # Statistics
        self.total_recognitions = 0
        self.total_rejections = 0
        self.last_adjustment_time = time.time()
        self.adjustment_interval = 30  # seconds
        
        # Performance metrics
        self.recent_accuracy = 0.0
        self.average_confidence = 0.0
        self.trend_direction = 0  # -1: declining, 0: stable, 1: improving
        
    def set_threshold(self, threshold):
        """Set the base confidence threshold."""
        self.base_threshold = max(self.min_threshold, min(self.max_threshold, threshold))
        self.current_threshold = self.base_threshold
        log_message(f"Confidence threshold set to: {self.current_threshold:.2f}")
    
    def add_recognition(self, confidence):
        """Record a successful recognition with its confidence score."""
        self.confidence_history.append(confidence)
        self.recognition_times.append(time.time())
        self.total_recognitions += 1
        
        self._update_statistics()
        
    def add_rejection(self, confidence):
        """Record a rejected recognition with its confidence score."""
        self.rejection_history.append(confidence)
        self.total_rejections += 1
        
        self._update_statistics()
    
    def _update_statistics(self):
        """Update internal statistics based on recent performance."""
        if len(self.confidence_history) >= 3:
            self.average_confidence = statistics.mean(self.confidence_history)
            
            # Calculate recent accuracy (last 10 recognitions)
            recent_recognitions = min(10, len(self.confidence_history))
            recent_rejections = min(10, len(self.rejection_history))
            
            if recent_recognitions + recent_rejections > 0:
                self.recent_accuracy = recent_recognitions / (recent_recognitions + recent_rejections)
            
            # Determine trend direction
            if len(self.confidence_history) >= 5:
                recent_confidences = list(self.confidence_history)[-5:]
                older_confidences = list(self.confidence_history)[-10:-5] if len(self.confidence_history) >= 10 else []
                
                if older_confidences:
                    recent_avg = statistics.mean(recent_confidences)
                    older_avg = statistics.mean(older_confidences)
                    
                    if recent_avg > older_avg + 0.05:
                        self.trend_direction = 1  # Improving
                    elif recent_avg < older_avg - 0.05:
                        self.trend_direction = -1  # Declining
                    else:
                        self.trend_direction = 0  # Stable
    
    def should_adjust_threshold(self):
        """Determine if threshold should be adjusted based on recent performance."""
        current_time = time.time()
        
        # Only adjust periodically
        if current_time - self.last_adjustment_time < self.adjustment_interval:
            return False
        
        # Need sufficient data
        if len(self.confidence_history) < 10:
            return False
        
        self.last_adjustment_time = current_time
        return True
    
    def get_adaptive_threshold(self):
        """Calculate adaptive threshold based on performance metrics."""
        if len(self.confidence_history) < 5:
            return self.current_threshold
        
        # Base adjustment on recent accuracy and confidence trends
        adjustment = 0.0
        
        # If accuracy is very high, we can lower threshold slightly
        if self.recent_accuracy > 0.9 and self.average_confidence > 0.7:
            adjustment -= 0.05
        
        # If accuracy is low, raise threshold
        elif self.recent_accuracy < 0.7:
            adjustment += 0.05
        
        # Consider trend direction
        if self.trend_direction == 1:  # Improving
            adjustment -= 0.02
        elif self.trend_direction == -1:  # Declining
            adjustment += 0.03
        
        # Consider rejection rate
        rejection_rate = self.total_rejections / max(1, self.total_recognitions + self.total_rejections)
        if rejection_rate > 0.3:
            adjustment += 0.03
        elif rejection_rate < 0.1:
            adjustment -= 0.02
        
        # Apply adjustment with bounds
        new_threshold = self.current_threshold + adjustment
        new_threshold = max(self.min_threshold, min(self.max_threshold, new_threshold))
        
        # Only update if change is significant
        if abs(new_threshold - self.current_threshold) > 0.02:
            self.current_threshold = new_threshold
            return new_threshold
        
        return self.current_threshold
    
    def get_performance_stats(self):
        """Get current performance statistics."""
        total_attempts = self.total_recognitions + self.total_rejections
        overall_accuracy = self.total_recognitions / max(1, total_attempts)
        
        return {
            'total_recognitions': self.total_recognitions,
            'total_rejections': self.total_rejections,
            'overall_accuracy': overall_accuracy,
            'recent_accuracy': self.recent_accuracy,
            'average_confidence': self.average_confidence,
            'current_threshold': self.current_threshold,
            'trend_direction': self.trend_direction
        }
    
    def should_suggest_recalibration(self):
        """Suggest if user should recalibrate their speech."""
        if self.total_recognitions < 20:
            return False
        
        # Suggest recalibration if consistently low performance
        return (self.recent_accuracy < 0.6 and 
                self.average_confidence < 0.5 and 
                self.trend_direction <= 0)
    
    def reset_statistics(self):
        """Reset all statistics (useful for new sessions)."""
        self.confidence_history.clear()
        self.rejection_history.clear()
        self.recognition_times.clear()
        self.total_recognitions = 0
        self.total_rejections = 0
        self.recent_accuracy = 0.0
        self.average_confidence = 0.0
        self.trend_direction = 0
        self.current_threshold = self.base_threshold
        log_message("Confidence tracking statistics reset")
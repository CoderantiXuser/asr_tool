import re
import time
from collections import deque, Counter
from datetime import datetime

class ContextManager:
    def __init__(self, history_size=50):
        self.text_history = deque(maxlen=history_size)
        self.word_frequency = Counter()
        self.recent_topics = []
        self.session_start = time.time()
        
        # Context patterns for better recognition
        self.context_patterns = {
            'email': r'\b[\w\.-]+@[\w\.-]+\.\w+\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'time': r'\b\d{1,2}:\d{2}(?:\s?[APap][Mm])?\b',
            'url': r'https?://[^\s]+|www\.[^\s]+',
            'money': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            'percentage': r'\d+(?:\.\d+)?%',
        }
        
        # Domain-specific vocabulary enhancement
        self.domain_keywords = {
            'technical': ['API', 'database', 'server', 'code', 'function', 'variable', 'class', 'method'],
            'business': ['revenue', 'profit', 'meeting', 'client', 'project', 'deadline', 'budget'],
            'medical': ['patient', 'diagnosis', 'treatment', 'symptoms', 'medicine', 'doctor'],
            'legal': ['contract', 'agreement', 'clause', 'liability', 'defendant', 'plaintiff'],
            'academic': ['research', 'study', 'analysis', 'hypothesis', 'conclusion', 'methodology']
        }
        
        self.current_domain = None
        self.domain_confidence = 0.0
    
    def add_text(self, text):
        """Add recognized text to context history."""
        if not text or not text.strip():
            return
        
        timestamp = time.time()
        self.text_history.append({
            'text': text,
            'timestamp': timestamp,
            'words': text.lower().split()
        })
        
        # Update word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        self.word_frequency.update(words)
        
        # Detect domain context
        self._update_domain_context(text)
        
        # Update recent topics
        self._update_topics(text)
    
    def _update_domain_context(self, text):
        """Update current domain context based on text content."""
        domain_scores = {}
        text_lower = text.lower()
        
        # Calculate domain scores based on keyword presence
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if score > 0:
                domain_scores[domain] = score / len(keywords)
        
        # Update current domain if we have a strong signal
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            if best_domain[1] > 0.2:  # Threshold for domain detection
                if self.current_domain != best_domain[0]:
                    self.current_domain = best_domain[0]
                    self.domain_confidence = best_domain[1]
    
    def _update_topics(self, text):
        """Extract and update recent topics from text."""
        # Simple topic extraction based on noun phrases and important words
        words = re.findall(r'\b[A-Z][a-z]+\b|\b\w{4,}\b', text)
        
        # Filter out common words
        common_words = {'that', 'this', 'with', 'have', 'will', 'been', 'said', 'each', 'which', 'their'}
        topics = [word.lower() for word in words if word.lower() not in common_words]
        
        # Add to recent topics (keep last 10)
        self.recent_topics.extend(topics)
        self.recent_topics = self.recent_topics[-10:]
    
    def get_context_suggestions(self, partial_text=""):
        """Get context-aware suggestions for improving recognition."""
        suggestions = {}
        
        # Suggest based on recent word frequency
        if self.word_frequency:
            common_words = [word for word, count in self.word_frequency.most_common(10) 
                           if count > 2 and len(word) > 3]
            suggestions['frequent_words'] = common_words
        
        # Suggest based on current domain
        if self.current_domain and self.domain_confidence > 0.3:
            suggestions['domain'] = self.current_domain
            suggestions['domain_keywords'] = self.domain_keywords[self.current_domain]
        
        # Suggest based on recent topics
        if self.recent_topics:
            suggestions['recent_topics'] = list(set(self.recent_topics[-5:]))
        
        # Suggest likely patterns based on partial text
        if partial_text:
            patterns = self._detect_patterns(partial_text)
            if patterns:
                suggestions['likely_patterns'] = patterns
        
        return suggestions
    
    def _detect_patterns(self, text):
        """Detect likely patterns in partial text."""
        detected = []
        
        for pattern_name, pattern in self.context_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pattern_name)
        
        # Check for incomplete patterns that might be forming
        text_lower = text.lower()
        
        # Email pattern detection
        if '@' in text or 'at' in text.split()[-3:]:
            detected.append('potential_email')
        
        # Phone number pattern
        if re.search(r'\d{3}[-.]?\d{0,3}[-.]?\d{0,4}$', text):
            detected.append('potential_phone')
        
        # Date pattern
        if re.search(r'\d{1,2}[/-]?\d{0,2}[/-]?\d{0,4}$', text):
            detected.append('potential_date')
        
        return detected
    
    def get_word_predictions(self, partial_word, limit=5):
        """Get word predictions based on context and frequency."""
        if len(partial_word) < 2:
            return []
        
        # Find words that start with the partial word
        candidates = []
        partial_lower = partial_word.lower()
        
        # Check frequent words first
        for word, count in self.word_frequency.most_common():
            if word.startswith(partial_lower) and word != partial_lower:
                candidates.append((word, count))
        
        # Add domain-specific words if in a domain context
        if self.current_domain:
            domain_words = [w.lower() for w in self.domain_keywords[self.current_domain]]
            for word in domain_words:
                if word.startswith(partial_lower) and word not in [c[0] for c in candidates]:
                    candidates.append((word, 1))  # Give domain words some weight
        
        # Sort by frequency and return top predictions
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [word for word, _ in candidates[:limit]]
    
    def get_context_window(self, window_size=3):
        """Get recent context window for better recognition."""
        if len(self.text_history) < window_size:
            return [item['text'] for item in self.text_history]
        
        return [item['text'] for item in list(self.text_history)[-window_size:]]
    
    def analyze_session(self):
        """Analyze current session for insights."""
        if not self.text_history:
            return {}
        
        session_duration = time.time() - self.session_start
        total_words = sum(len(item['words']) for item in self.text_history)
        
        # Calculate words per minute
        wpm = (total_words / (session_duration / 60)) if session_duration > 0 else 0
        
        # Most common words
        common_words = self.word_frequency.most_common(10)
        
        # Detected patterns
        all_text = ' '.join(item['text'] for item in self.text_history)
        detected_patterns = []
        for pattern_name, pattern in self.context_patterns.items():
            if re.search(pattern, all_text, re.IGNORECASE):
                detected_patterns.append(pattern_name)
        
        return {
            'session_duration_minutes': session_duration / 60,
            'total_recognitions': len(self.text_history),
            'total_words': total_words,
            'words_per_minute': wpm,
            'most_common_words': common_words,
            'current_domain': self.current_domain,
            'domain_confidence': self.domain_confidence,
            'detected_patterns': detected_patterns,
            'recent_topics': self.recent_topics
        }
    
    def export_context(self):
        """Export context data for analysis or backup."""
        return {
            'text_history': list(self.text_history),
            'word_frequency': dict(self.word_frequency),
            'current_domain': self.current_domain,
            'recent_topics': self.recent_topics,
            'session_start': self.session_start
        }
    
    def import_context(self, context_data):
        """Import previously exported context data."""
        try:
            if 'text_history' in context_data:
                self.text_history.extend(context_data['text_history'])
            
            if 'word_frequency' in context_data:
                self.word_frequency.update(context_data['word_frequency'])
            
            if 'current_domain' in context_data:
                self.current_domain = context_data['current_domain']
            
            if 'recent_topics' in context_data:
                self.recent_topics = context_data['recent_topics']
            
            return True
        except Exception as e:
            return False
    
    def clear_context(self):
        """Clear all context data."""
        self.text_history.clear()
        self.word_frequency.clear()
        self.recent_topics.clear()
        self.current_domain = None
        self.domain_confidence = 0.0
        self.session_start = time.time()
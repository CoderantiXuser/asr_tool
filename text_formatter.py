import re
import json
import os
from datetime import datetime

class TextFormatter:
    def __init__(self):
        # Load custom corrections and abbreviations
        self.corrections = self._load_corrections()
        self.abbreviations = self._load_abbreviations()
        self.sentence_enders = {'.', '!', '?'}
        self.last_sentence_end = False
        
        # Common dictation patterns
        self.dictation_patterns = {
            # Punctuation commands
            r'\b(period|dot|full stop)\b': '.',
            r'\b(comma)\b': ',',
            r'\b(question mark)\b': '?',
            r'\b(exclamation mark|exclamation point)\b': '!',
            r'\b(colon)\b': ':',
            r'\b(semicolon)\b': ';',
            r'\b(quote|quotation mark)\b': '"',
            r'\b(apostrophe)\b': "'",
            r'\b(open parenthesis|left parenthesis)\b': '(',
            r'\b(close parenthesis|right parenthesis)\b': ')',
            r'\b(open bracket|left bracket)\b': '[',
            r'\b(close bracket|right bracket)\b': ']',
            r'\b(dash|hyphen)\b': '-',
            r'\b(underscore)\b': '_',
            
            # Number formatting
            r'\b(zero|oh)\b': '0',
            r'\bone\b': '1',
            r'\btwo\b': '2',
            r'\bthree\b': '3',
            r'\bfour\b': '4',
            r'\bfive\b': '5',
            r'\bsix\b': '6',
            r'\bseven\b': '7',
            r'\beight\b': '8',
            r'\bnine\b': '9',
            r'\bten\b': '10',
            
            # Special formatting
            r'\b(new line|newline)\b': '\n',
            r'\b(new paragraph|paragraph)\b': '\n\n',
            r'\b(tab)\b': '\t',
            
            # Common corrections
            r'\bi\b': 'I',  # Always capitalize standalone 'i'
            r'\bim\b': "I'm",
            r'\bive\b': "I've",
            r'\bill\b': "I'll",
            r'\bid\b': "I'd",
            r'\byoure\b': "you're",
            r'\byouve\b': "you've",
            r'\byoull\b': "you'll",
            r'\byoud\b': "you'd",
            r'\btheyre\b': "they're",
            r'\btheyve\b': "they've",
            r'\btheyll\b': "they'll",
            r'\btheyd\b': "they'd",
            r'\bwere\b': "we're",
            r'\bweve\b': "we've",
            r'\bwell\b': "we'll",
            r'\bwed\b': "we'd",
            r'\bcant\b': "can't",
            r'\bwont\b': "won't",
            r'\bdont\b': "don't",
            r'\bdidnt\b': "didn't",
            r'\bwouldnt\b': "wouldn't",
            r'\bshouldnt\b': "shouldn't",
            r'\bcouldnt\b': "couldn't",
            r'\bhavent\b': "haven't",
            r'\bhasnt\b': "hasn't",
            r'\bhadnt\b': "hadn't",
            r'\bisnt\b': "isn't",
            r'\barent\b': "aren't",
            r'\bwasnt\b': "wasn't",
            r'\bwerent\b': "weren't",
        }
        
        # Email and URL patterns
        self.email_pattern = r'\b([a-zA-Z0-9._%+-]+)\s+at\s+([a-zA-Z0-9.-]+)\s+dot\s+([a-zA-Z]{2,})\b'
        self.url_pattern = r'\b(www|http|https)\s+(dot|\.|[a-zA-Z0-9.-]+)\b'
        
    def _load_corrections(self):
        """Load custom word corrections from file."""
        corrections_file = os.path.join(os.path.dirname(__file__), "corrections.json")
        try:
            with open(corrections_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default corrections file
            default_corrections = {
                "there": "their",
                "your": "you're",
                "its": "it's",
                "to": "too",
                "loose": "lose",
                "accept": "except"
            }
            try:
                with open(corrections_file, 'w') as f:
                    json.dump(default_corrections, f, indent=2)
            except:
                pass
            return default_corrections
        except json.JSONDecodeError:
            return {}
    
    def _load_abbreviations(self):
        """Load abbreviation expansions from file."""
        abbrev_file = os.path.join(os.path.dirname(__file__), "abbreviations.json")
        try:
            with open(abbrev_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default abbreviations file
            default_abbrevs = {
                "btw": "by the way",
                "fyi": "for your information",
                "asap": "as soon as possible",
                "etc": "et cetera",
                "ie": "that is",
                "eg": "for example",
                "vs": "versus",
                "aka": "also known as"
            }
            try:
                with open(abbrev_file, 'w') as f:
                    json.dump(default_abbrevs, f, indent=2)
            except:
                pass
            return default_abbrevs
        except json.JSONDecodeError:
            return {}
    
    def format_text(self, text):
        """Apply comprehensive text formatting."""
        if not text or not text.strip():
            return text
        
        # Store original for comparison
        original_text = text
        
        # Step 1: Handle email addresses
        text = self._format_emails(text)
        
        # Step 2: Handle URLs
        text = self._format_urls(text)
        
        # Step 3: Apply dictation patterns
        text = self._apply_dictation_patterns(text)
        
        # Step 4: Apply custom corrections
        text = self._apply_corrections(text)
        
        # Step 5: Expand abbreviations
        text = self._expand_abbreviations(text)
        
        # Step 6: Handle capitalization
        text = self._handle_capitalization(text)
        
        # Step 7: Clean up spacing
        text = self._clean_spacing(text)
        
        # Step 8: Handle sentence structure
        text = self._handle_sentence_structure(text)
        
        return text
    
    def preview_formatting(self, partial_text):
        """Show a preview of how text will be formatted (for partial results)."""
        if not partial_text:
            return partial_text
        
        # Quick preview without full processing
        preview = partial_text
        
        # Apply basic dictation patterns
        for pattern, replacement in list(self.dictation_patterns.items())[:10]:  # First 10 patterns only
            preview = re.sub(pattern, replacement, preview, flags=re.IGNORECASE)
        
        # Basic capitalization
        if preview and not self.last_sentence_end:
            words = preview.split()
            if words:
                words[0] = words[0].capitalize()
                preview = ' '.join(words)
        
        return preview
    
    def _format_emails(self, text):
        """Convert dictated email addresses to proper format."""
        def replace_email(match):
            username = match.group(1).replace(' ', '')
            domain = match.group(2).replace(' ', '')
            tld = match.group(3).replace(' ', '')
            return f"{username}@{domain}.{tld}"
        
        return re.sub(self.email_pattern, replace_email, text, flags=re.IGNORECASE)
    
    def _format_urls(self, text):
        """Convert dictated URLs to proper format."""
        # Simple URL formatting - can be expanded
        text = re.sub(r'\bwww\s+dot\s+', 'www.', text, flags=re.IGNORECASE)
        text = re.sub(r'\bhttp\s+colon\s+slash\s+slash\s+', 'http://', text, flags=re.IGNORECASE)
        text = re.sub(r'\bhttps\s+colon\s+slash\s+slash\s+', 'https://', text, flags=re.IGNORECASE)
        return text
    
    def _apply_dictation_patterns(self, text):
        """Apply all dictation patterns."""
        for pattern, replacement in self.dictation_patterns.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def _apply_corrections(self, text):
        """Apply custom word corrections."""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Check for corrections (case-insensitive)
            word_lower = word.lower().strip('.,!?;:"()[]')
            if word_lower in self.corrections:
                # Preserve original capitalization pattern
                corrected = self.corrections[word_lower]
                if word[0].isupper():
                    corrected = corrected.capitalize()
                # Preserve punctuation
                punctuation = ''.join(c for c in word if not c.isalnum())
                corrected_words.append(corrected + punctuation)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _expand_abbreviations(self, text):
        """Expand abbreviations to full forms."""
        words = text.split()
        expanded_words = []
        
        for word in words:
            word_clean = word.lower().strip('.,!?;:"()[]')
            if word_clean in self.abbreviations:
                expansion = self.abbreviations[word_clean]
                # Preserve capitalization
                if word[0].isupper():
                    expansion = expansion.capitalize()
                # Preserve punctuation
                punctuation = ''.join(c for c in word if not c.isalnum())
                expanded_words.append(expansion + punctuation)
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def _handle_capitalization(self, text):
        """Handle proper capitalization rules."""
        if not text:
            return text
        
        # Capitalize first word if starting new sentence
        words = text.split()
        if words and (self.last_sentence_end or not hasattr(self, '_in_sentence')):
            words[0] = words[0].capitalize()
            self._in_sentence = True
        
        # Capitalize 'I' when standalone
        for i, word in enumerate(words):
            if word.lower() == 'i':
                words[i] = 'I'
        
        return ' '.join(words)
    
    def _clean_spacing(self, text):
        """Clean up spacing issues."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        # Fix spacing around quotes and parentheses
        text = re.sub(r'\s+"([^"]*)"', r' "\1"', text)
        text = re.sub(r'\s+\(', ' (', text)
        text = re.sub(r'\)\s+', ') ', text)
        
        return text.strip()
    
    def _handle_sentence_structure(self, text):
        """Handle sentence ending detection for future capitalization."""
        if not text:
            return text
        
        # Check if this text ends with sentence-ending punctuation
        self.last_sentence_end = text.rstrip()[-1:] in self.sentence_enders
        
        return text
    
    def add_correction(self, wrong_word, correct_word):
        """Add a new word correction."""
        self.corrections[wrong_word.lower()] = correct_word
        self._save_corrections()
    
    def add_abbreviation(self, abbrev, expansion):
        """Add a new abbreviation expansion."""
        self.abbreviations[abbrev.lower()] = expansion
        self._save_abbreviations()
    
    def _save_corrections(self):
        """Save corrections to file."""
        corrections_file = os.path.join(os.path.dirname(__file__), "corrections.json")
        try:
            with open(corrections_file, 'w') as f:
                json.dump(self.corrections, f, indent=2)
        except:
            pass
    
    def _save_abbreviations(self):
        """Save abbreviations to file."""
        abbrev_file = os.path.join(os.path.dirname(__file__), "abbreviations.json")
        try:
            with open(abbrev_file, 'w') as f:
                json.dump(self.abbreviations, f, indent=2)
        except:
            pass
    
    def reset_sentence_state(self):
        """Reset sentence state (useful after commands)."""
        self.last_sentence_end = True
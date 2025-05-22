import os
import warnings
import re

# Suppress warnings before importing transformers
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from transformers import pipeline

# Global variable to store the model
_flan_model = None

def load_flan_model():
    """Load and cache the FLAN-T5 model with proper error handling."""
    global _flan_model
    
    if _flan_model is None:
        try:
            print("🔄 Loading FLAN-T5 model...")
            _flan_model = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",
                framework="pt",
                device_map="auto" if os.environ.get('CUDA_VISIBLE_DEVICES') else None,
                torch_dtype="auto"
            )
            print("✅ FLAN-T5 model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading FLAN-T5 model: {e}")
            # Fallback to CPU
            try:
                _flan_model = pipeline(
                    "text2text-generation",
                    model="google/flan-t5-small",
                    framework="pt",
                    device=-1  # Force CPU
                )
                print("✅ FLAN-T5 model loaded on CPU")
            except Exception as e2:
                print(f"❌ Failed to load model on CPU: {e2}")
                raise e2
    
    return _flan_model

def parse_query_with_flan(user_input: str) -> str:
    """
    Converts natural language queries into structured key-value pairs.
    Now supports only two intents: top_songs and song_duration.
    
    Args:
        user_input: Natural language query (e.g., "Top 5 songs of 2020")
        
    Returns:
        Structured output (e.g., "intent: top_songs; year: 2020; n: 5")
    """
    # Clean input and validate
    if not isinstance(user_input, str) or not user_input.strip():
        return "intent: invalid_input; error: empty_query"
    
    # Get model instance
    try:
        flan_t5 = load_flan_model()
    except Exception as e:
        return f"intent: error; error: model_load_failed - {str(e)}"
    
    prompt = f"""
    You are a music chart query parser. Extract ONLY these intents:
    
    INTENT TYPES:
    1. top_songs - For queries about top/best songs of a year
    2. song_duration - For queries about how long a song was on charts
    
    OUTPUT FORMAT:
    intent: <type>; [year: YYYY]; [n: NUMBER]; [song: "SONG NAME"]
    
    EXAMPLES:
    Query: "Show me top 10 songs of 2020"
    Output: intent: top_songs; year: 2020; n: 10
    
    Query: "Best 5 hits from 1985" 
    Output: intent: top_songs; year: 1985; n: 5
    
    Query: "How long was Shape of You on the chart?"
    Output: intent: song_duration; song: Shape of You
    
    Query: "Duration of Blinding Lights on Billboard"
    Output: intent: song_duration; song: Blinding Lights
    
    RULES:
    - Return EXACTLY one intent
    - Extract year numbers (1958-2021)
    - Extract song names without quotes in output
    - Default n=10 for top songs if not specified
    - Only use the two intent types above
    
    Query: {user_input}
    Output: """
    
    try:
        # Generate structured output with fixed parameters
        result = flan_t5(
            prompt,
            max_new_tokens=60,
            num_beams=3,
            do_sample=False,  # Deterministic output
            early_stopping=True,
            pad_token_id=flan_t5.tokenizer.eos_token_id
        )[0]["generated_text"].strip()
        
        # Post-processing to enforce format
        return _validate_and_clean_output(result)
        
    except Exception as e:
        print(f"FLAN-T5 parsing error: {e}")
        return f"intent: error; error: {str(e)}"

def _validate_and_clean_output(raw_output: str) -> str:
    """
    Ensures output follows strict formatting rules.
    Only allows top_songs and song_duration intents.
    """
    try:
        # Clean up the output
        cleaned = raw_output.lower().strip()
        
        # Extract intent
        intent_match = re.search(r"intent:\s*(top_songs|song_duration)", cleaned)
        if not intent_match:
            return "intent: unknown; error: no_valid_intent"
        
        intent = intent_match.group(1)
        result_parts = [f"intent: {intent}"]
        
        # Extract year (for top_songs)
        year_match = re.search(r"year:\s*(\d{4})", cleaned)
        if year_match:
            year = int(year_match.group(1))
            # Validate year range
            if 1950 <= year <= 2025:  # Reasonable range
                result_parts.append(f"year: {year}")
        
        # Extract n (number of songs)
        n_match = re.search(r"n:\s*(\d+)", cleaned)
        if n_match:
            n = min(int(n_match.group(1)), 50)  # Cap at 50
            result_parts.append(f"n: {n}")
        
        # Extract song name (for song_duration)
        song_patterns = [
            r'song:\s*"([^"]+)"',  # song: "Song Name"
            r'song:\s*([^;]+)',     # song: Song Name
        ]
        
        for pattern in song_patterns:
            song_match = re.search(pattern, raw_output)  # Use original case
            if song_match:
                song_name = song_match.group(1).strip().strip('"\'')
                if song_name:
                    result_parts.append(f"song: {song_name}")
                break
        
        return "; ".join(result_parts)
        
    except Exception as e:
        print(f"Output validation error: {e}")
        return f"intent: error; error: validation_failed"

def extract_year_from_text(text: str) -> int:
    """Helper function to extract 4-digit years from text."""
    years = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', text)
    return int(years[0]) if years else 0

def extract_number_from_text(text: str) -> int:
    """Helper function to extract numbers from text (for top N songs)."""
    # Look for patterns like "top 5", "best 10", etc.
    patterns = [
        r'\b(?:top|best|first)\s+(\d+)\b',
        r'\b(\d+)\s+(?:top|best|songs|hits)\b',
        r'\b(\d+)\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            num = int(matches[0])
            if 1 <= num <= 50:  # Reasonable range
                return num
    
    return 10  # Default

# Fallback function for when FLAN-T5 fails
def fallback_parser(user_input: str) -> str:
    """Simple rule-based parser as fallback when FLAN-T5 fails."""
    user_input = user_input.lower().strip()
    
    # Check for song duration queries
    duration_keywords = ['how long', 'duration', 'weeks', 'stayed', 'chart time']
    if any(keyword in user_input for keyword in duration_keywords):
        # Try to extract song name
        song_patterns = [
            r'how long (?:was|did) (.+?) (?:on|stay)',
            r'duration (?:of|for) (.+?)(?:\s|$)',
            r'(.+?) (?:duration|weeks|stayed)'
        ]
        
        for pattern in song_patterns:
            match = re.search(pattern, user_input)
            if match:
                song = match.group(1).strip()
                return f"intent: song_duration; song: {song}"
        
        return "intent: song_duration; song: unknown"
    
    # Check for top songs queries
    top_keywords = ['top', 'best', 'greatest', 'popular']
    if any(keyword in user_input for keyword in top_keywords):
        # Extract year
        year = extract_year_from_text(user_input)
        # Extract number
        n = extract_number_from_text(user_input)
        
        result = "intent: top_songs"
        if year:
            result += f"; year: {year}"
        result += f"; n: {n}"
        
        return result
    
    return "intent: unknown; error: no_pattern_match"

# Test function
if __name__ == "__main__":
    test_queries = [
        "Top 5 songs of 2020",
        "Best hits from 1985", 
        "How long was Blinding Lights on chart?",
        "Show me 15 top songs from 1999",
        "Duration of Shape of You"
    ]
    
    for query in test_queries:
        result = parse_query_with_flan(query)
        print(f"Query: {query}")
        print(f"Output: {result}\n")
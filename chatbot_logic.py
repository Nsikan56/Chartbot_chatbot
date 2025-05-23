from flan_t5_parser import parse_query_with_flan
from data_utils import (get_top_songs_by_year, get_song_matches_with_duration, 
                       format_song_duration_results, validate_year_range)
from fuzzywuzzy import fuzz
import re

def parse_flan_output_to_dict(raw_text: str) -> dict:
    """Convert FLAN-T5's output to a dict with error resilience."""
    parsed = {}
    try:
        for item in raw_text.strip().split(";"):
            item = item.strip()
            if ":" in item:
                key, value = item.split(":", 1)  # Split on first colon only
                parsed[key.strip().lower()] = value.strip()
    except Exception as e:
        print(f"⚠️ Failed to parse FLAN output: {raw_text}. Error: {e}")
    return parsed

def enhanced_query_parser(query: str) -> dict:
    """Enhanced regex-based parser that handles all query types including artist-specific searches."""
    query_lower = query.lower().strip()
    result = {}
    
    # Pattern 1: Top N songs of specific year
    top_year_patterns = [
        r'top\s+(\d+)\s+songs?\s+(?:of|from|in)\s+(\d{4})',
        r'best\s+(\d+)\s+(?:songs?|hits?)\s+(?:of|from|in)\s+(\d{4})',
        r'(\d+)\s+(?:top|best)\s+songs?\s+(?:of|from|in)\s+(\d{4})',
        r'show\s+me\s+(?:top\s+)?(\d+)\s+songs?\s+(?:of|from|in)\s+(\d{4})',
    ]
    
    for pattern in top_year_patterns:
        match = re.search(pattern, query_lower)
        if match:
            result["intent"] = "top_songs"
            result["n"] = int(match.group(1))
            result["year"] = int(match.group(2))
            return result
    
    # Pattern 2: Top songs without number (default to 10)
    top_year_default_patterns = [
        r'top\s+songs?\s+(?:of|from|in)\s+(\d{4})',
        r'best\s+(?:songs?|hits?)\s+(?:of|from|in)\s+(\d{4})',
        r'popular\s+songs?\s+(?:of|from|in)\s+(\d{4})',
    ]
    
    for pattern in top_year_default_patterns:
        match = re.search(pattern, query_lower)
        if match:
            result["intent"] = "top_songs"
            result["year"] = int(match.group(1))
            result["n"] = 10
            return result
    
    # Pattern 3: Decade queries (80s, 90s, 2000s, etc.)
    decade_patterns = [
        r'(?:top|best)\s+(?:songs?|hits?)\s+(?:of|from)\s+the\s+(\d{2})s',  # "top songs from the 80s"
        r'(?:top|best)\s+(?:songs?|hits?)\s+(?:of|from)\s+(\d{4})s',        # "top songs from 2000s"
        r'best\s+of\s+(?:the\s+)?(\d{2})s',                                # "best of 80s"
        r'best\s+of\s+(\d{4})s',                                           # "best of 2000s"
    ]
    
    for pattern in decade_patterns:
        match = re.search(pattern, query_lower)
        if match:
            decade_str = match.group(1)
            if len(decade_str) == 2:  # 80s, 90s format
                decade = int(decade_str)
                if decade >= 50:  # 50s-90s
                    year = 1900 + decade
                else:  # 00s, 10s, 20s
                    year = 2000 + decade
            else:  # 2000s format
                year = int(decade_str)
            
            result["intent"] = "top_songs_decade" 
            result["decade_start"] = year
            result["n"] = 20  # Default more songs for decade queries
            return result
    
    # Pattern 4: Song duration queries with artist - ENHANCED to parse artist names
    duration_with_artist_patterns = [
        # "How long did [SONG] by [ARTIST] stay on the chart"
        r'how long (?:was|did) (.+?) by (.+?) (?:stay|on|chart|last)',
        # "How many weeks was [SONG] by [ARTIST] on chart"
        r'how many weeks (?:was|did) (.+?) by (.+?) (?:on|stay|chart)',
        # "[SONG] by [ARTIST] duration"
        r'(.+?) by (.+?) (?:duration|weeks|chart time)(?:\?|$)',
        # "Duration of [SONG] by [ARTIST]"
        r'duration (?:of|for) (.+?) by (.+?)(?:\?|$|on)',
        # "[SONG] by [ARTIST] on chart"
        r'(.+?) by (.+?) on (?:the )?chart(?:\?|$)',
    ]
    
    for pattern in duration_with_artist_patterns:
        match = re.search(pattern, query_lower)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            
            # Clean up common words that aren't part of song/artist names
            cleanup_words = ['the', 'on', 'chart', 'billboard', 'hot', '100', 'was', 'did', 'stay', 'long']
            for word in cleanup_words:
                song_name = re.sub(rf'\b{word}\b', '', song_name, flags=re.IGNORECASE).strip()
                artist_name = re.sub(rf'\b{word}\b', '', artist_name, flags=re.IGNORECASE).strip()
            
            # Remove extra whitespace
            song_name = re.sub(r'\s+', ' ', song_name).strip()
            artist_name = re.sub(r'\s+', ' ', artist_name).strip()
            
            if song_name and artist_name:  # Make sure we have both
                result["intent"] = "song_duration_with_artist"
                result["song"] = song_name
                result["artist"] = artist_name
                return result
    
    # Pattern 5: General song duration queries (without specific artist)
    duration_patterns = [
        r'how long (?:was|did) (.+?) (?:stay|on|chart|last)',
        r'how many weeks (?:was|did) (.+?) (?:on|stay|chart)',
        r'duration (?:of|for) (.+?)(?:\?|$|on)',
        r'weeks (?:for|of) (.+?)(?:\?|$|on)',
        r'(.+?) (?:duration|weeks|chart time)(?:\?|$)',
        r'chart time (?:for|of) (.+?)(?:\?|$)',
        r'how long (.+?)(?:\?|$)',  # Simple "how long [song]"
        r'(.+?) on (?:the )?chart(?:\?|$)',  # "[song] on chart"
        r'(.+?) billboard(?:\?|$)',  # "[song] billboard"
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, query_lower)
        if match:
            song_name = match.group(1).strip()
            # Clean up common words that aren't part of song titles
            cleanup_words = ['the', 'on', 'chart', 'billboard', 'hot', '100', 'was', 'did']
            for word in cleanup_words:
                song_name = re.sub(rf'\b{word}\b', '', song_name, flags=re.IGNORECASE).strip()
            
            # Remove extra whitespace
            song_name = re.sub(r'\s+', ' ', song_name).strip()
            
            if song_name:  # Make sure we still have something left
                result["intent"] = "song_duration"
                result["song"] = song_name
                return result
    
    return result

def get_decade_songs(decade_start: int, n: int = 20) -> list:
    """Get top songs from a decade."""
    try:
        from data_utils import df
        
        # Define decade range
        decade_end = decade_start + 9
        decade_data = df[(df['year'] >= decade_start) & (df['year'] <= decade_end)].copy()
        
        if decade_data.empty:
            return []
        
        # Get best performance for each song across the decade
        best_performance = (
            decade_data
            .groupby(['song', 'artist'])
            .agg({
                'rank': 'min',  # Best rank achieved
                'peak-rank': 'min',
                'weeks-on-board': 'max',
                'year': 'first'  # Keep year for reference
            })
            .reset_index()
            .sort_values('rank')
            .head(n)
        )
        
        return best_performance.to_dict('records')
        
    except Exception as e:
        print(f"Error getting decade songs for {decade_start}s: {e}")
        return []

def respond_to_query(query: str) -> str:
    """Handle user queries with enhanced parsing and song search including artist-specific searches."""
    try:
        if not query or not isinstance(query, str):
            return "❌ Please enter a valid text query."

        print(f"🔍 DEBUG: Processing query: '{query}'")

        # Try enhanced parser first (since FLAN-T5 is failing)
        enhanced_result = enhanced_query_parser(query)
        print(f"🎯 DEBUG: Enhanced parser result: {enhanced_result}")
        
        if enhanced_result:
            # Use enhanced parser result
            intent = enhanced_result.get("intent", "")
            year = enhanced_result.get("year")
            n = enhanced_result.get("n", 10)
            song = enhanced_result.get("song", "")
            artist = enhanced_result.get("artist", "")
            decade_start = enhanced_result.get("decade_start")
            
        else:
            # Fallback to FLAN-T5 (though it's not working well)
            flan_output = parse_query_with_flan(query)
            print(f"🤖 DEBUG: FLAN-T5 raw output: '{flan_output}'")
            
            nlp_result = parse_flan_output_to_dict(flan_output)
            print(f"📊 DEBUG: Parsed result: {nlp_result}")
            
            intent = nlp_result.get("intent", "").lower()
            year_str = nlp_result.get("year", "")
            year = int(year_str) if year_str.isdigit() else None
            song = nlp_result.get("song", "").strip('"\'')
            artist = nlp_result.get("artist", "").strip('"\'')
            n = min(int(nlp_result.get("n", 10)), 50) if nlp_result.get("n", "").isdigit() else 10
            decade_start = None

        print(f"🎯 DEBUG: Final extracted - Intent: '{intent}', Year: {year}, N: {n}, Song: '{song}', Artist: '{artist}', Decade: {decade_start}")

        # Route based on intent
        if intent == "top_songs":
            print(f"✅ DEBUG: Routing to top_songs handler")
            if not year:
                return "🔍 Please specify a valid year between 1958-2021 (e.g., 'Top 5 songs of 2012')."
            
            if not validate_year_range(year):
                return f"📅 Sorry, I only have data from 1958-2021. Year {year} is outside this range."
            
            print(f"📈 DEBUG: Getting top {n} songs for year {year}")
            songs = get_top_songs_by_year(year, n)
            print(f"🎵 DEBUG: Found {len(songs)} songs")
            return format_top_songs(songs, year, n)
            
        elif intent == "top_songs_decade":
            print(f"✅ DEBUG: Routing to decade handler")
            if not decade_start:
                return "🔍 Please specify a valid decade (e.g., 'Best songs from the 80s')."
            
            print(f"📈 DEBUG: Getting top {n} songs for {decade_start}s")
            songs = get_decade_songs(decade_start, n)
            print(f"🎵 DEBUG: Found {len(songs)} songs from {decade_start}s")
            return format_decade_songs(songs, decade_start, n)
            
        elif intent == "song_duration_with_artist":
            print(f"✅ DEBUG: Routing to artist-specific song_duration handler")
            if not song:
                return "🔍 Please specify a song name (e.g., 'How long was Thriller by Michael Jackson on the chart?')."
            
            # Use artist-specific search
            matches = get_song_matches_with_duration(song, artist_name=artist, max_results=3)
            print(f"🎵 DEBUG: Found {len(matches)} matches for '{song}' by '{artist}'")
            
            return format_song_duration_results(matches, f"{song} by {artist}")
            
        elif intent == "song_duration":
            print(f"✅ DEBUG: Routing to general song_duration handler")
            if not song:
                return "🔍 Please specify a song name (e.g., 'How long was Thriller on the chart?')."
            
            # Use general search (no artist filter)
            matches = get_song_matches_with_duration(song, max_results=5)
            print(f"🎵 DEBUG: Found {len(matches)} matches for '{song}'")
            
            return format_song_duration_results(matches, song)
            
        else:
            print(f"❌ DEBUG: Unknown intent '{intent}', showing help message")
            return get_help_message()
            
    except Exception as e:
        print(f"💥 DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"⚠️ Something went wrong. Please try a different query. (Error: {str(e)})"

def format_top_songs(songs: list, year: int, n: int) -> str:
    """Format songs list into a structured, readable Markdown list."""
    if not songs:
        return f"📭 No songs found for {year}. Try a year between 1958–2021."
    
    actual_count = len(songs)
    header = f"🎵 **Top {actual_count} Billboard Hot 100 songs of {year}:**\n\n"
    
    song_list = []
    for i, song in enumerate(songs):
        title = song.get('song', 'Unknown')
        artist = song.get('artist', 'Unknown Artist')
        weeks = song.get('weeks-on-board', 'N/A')
        peak = song.get('peak-rank', 'N/A')
        
        song_info = f"**{i+1}. {title}** by *{artist}*"
        details = []
        if weeks != 'N/A':
            details.append(f"• {weeks} weeks on chart")
        if peak != 'N/A':
            details.append(f"• Peaked at #{peak}")
        
        if details:
            song_info += "\n   " + "\n   ".join(details)
        
        song_list.append(song_info)
    
    return header + "\n\n".join(song_list)


def format_decade_songs(songs: list, decade_start: int, n: int) -> str:
    """Format top songs from a decade in a structured Markdown list."""
    if not songs:
        return f"📭 No songs found for the {decade_start}s."
    
    actual_count = len(songs)
    decade_end = decade_start + 9
    header = f"🎵 **Top {actual_count} Billboard Hot 100 songs of the {decade_start}s ({decade_start}–{decade_end}):**\n\n"
    
    song_list = []
    for i, song in enumerate(songs):
        title = song.get('song', 'Unknown')
        artist = song.get('artist', 'Unknown Artist')
        year = song.get('year', 'N/A')
        weeks = song.get('weeks-on-board', 'N/A')
        
        song_info = f"**{i+1}. {title}** by *{artist}* ({year})"
        details = []
        if weeks != 'N/A':
            details.append(f"• {weeks} weeks on chart")
        
        if details:
            song_info += "\n   " + "\n   ".join(details)
        
        song_list.append(song_info)
    
    return header + "\n\n".join(song_list)

def find_similar_song(query_song: str, threshold: int = 70) -> str:
    """
    DEPRECATED: Use get_song_matches_with_duration() instead.
    This function is kept for backward compatibility.
    """
    try:
        matches = get_song_matches_with_duration(query_song, max_results=1)
        if matches:
            return matches[0]['song']
        return ""
    except:
        return ""

def get_help_message() -> str:
    """Return helpful usage instructions."""
    return """
🤖 **I can help you with Billboard Hot 100 data (1958-2021)!**

**Try these formats:**
• 📊 **Top songs by year**: "Top 10 songs of 1985" or "Best 5 hits from 2020"
• 🎭 **Top songs by decade**: "Best songs from the 80s" or "Top hits of 2000s"
• ⏱ **Song duration**: "How long was Bohemian Rhapsody on the chart?" or just "Judy on chart"
• 🎤 **Artist-specific search**: "How long did Back to Back by Drake stay on the chart?"
• 🎯 **Any year**: Ask about any year from 1958 to 2021!

**Example queries:**
- "Show me top 15 songs of 1999"
- "How many weeks was Blinding Lights on the Billboard chart?"
- "Best songs from the 90s"
- "Shape of You duration"
- "How long did Hotline Bling by Drake stay on chart?"
- "God's Plan by Drake weeks on chart"
"""
import pandas as pd
from pathlib import Path
from fuzzywuzzy import fuzz
import re

def load_billboard_data():
    """Load and cache the Billboard dataset with error handling."""
    try:
        csv_path = Path("billboard_cleaned.csv")
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset not found at {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ['date', 'rank', 'song', 'artist', 'last-week', 'peak-rank', 'weeks-on-board', 'year']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        
        # Clean and validate data
        df = df.dropna(subset=['song', 'artist'])  # Remove rows with missing song/artist
        df['song'] = df['song'].str.strip()  # Remove leading/trailing whitespace
        df['artist'] = df['artist'].str.strip()
        
        print(f"✅ Loaded {len(df):,} records from Billboard dataset ({df['year'].min()}-{df['year'].max()})")
        return df
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        raise

# Load data once when module imports
df = load_billboard_data()

def validate_year_range(year: int) -> bool:
    """Check if year is within available data range."""
    return df['year'].min() <= year <= df['year'].max()

def get_top_songs_by_year(year: int, n: int = 10) -> list[dict]:
    """Get top N songs for a specific year, ranked by best chart performance."""
    try:
        year_data = df[df['year'] == year].copy()
        
        if year_data.empty:
            return []
        
        # Get the best chart performance for each song (lowest rank number = higher position)
        # Group by song-artist combination to handle songs that appeared multiple times
        best_performance = (
            year_data
            .groupby(['song', 'artist'])
            .agg({
                'rank': 'min',  # Best (lowest) rank achieved
                'peak-rank': 'min',  # Best peak rank
                'weeks-on-board': 'max',  # Maximum weeks (in case of re-entries)
                'last-week': 'first'  # Just take first occurrence
            })
            .reset_index()
            .sort_values('rank')  # Sort by best rank achieved
            .head(n)
        )
        
        return best_performance.to_dict('records')
        
    except Exception as e:
        print(f"Error getting top songs for {year}: {e}")
        return []

def get_song_matches_with_duration(query_song: str, artist_name: str = None, max_results: int = 5, fuzzy_threshold: int = 60) -> list[dict]:
    """
    Enhanced song search with fuzzy matching and duration information.
    Now supports artist-specific searches.
    
    Args:
        query_song: Song name to search for
        artist_name: Optional artist name to filter by
        max_results: Maximum number of results to return
        fuzzy_threshold: Minimum fuzzy match score (0-100)
    
    Returns:
        List of dictionaries with song info including duration on charts
    """
    try:
        if not query_song or not isinstance(query_song, str):
            return []
        
        query_song = query_song.strip()
        if not query_song:
            return []
        
        search_info = f"'{query_song}'"
        if artist_name:
            search_info += f" by {artist_name}"
        print(f"🔍 Searching for songs matching: {search_info}")
        
        # Get unique songs for searching
        unique_songs = df.groupby(['song', 'artist']).agg({
            'rank': 'min',  # Best rank achieved
            'peak-rank': 'min',
            'weeks-on-board': 'max',  # Total weeks on chart
            'year': 'first'  # Year of first appearance
        }).reset_index()
        
        # Filter by artist if provided
        if artist_name:
            artist_name = artist_name.strip()
            unique_songs = unique_songs[
                unique_songs['artist'].str.contains(artist_name, case=False, na=False)
            ]
            print(f"🎤 Filtered to {len(unique_songs)} songs by artists matching '{artist_name}'")
        
        matches = []
        
        # 1. Exact song match (case-insensitive)
        exact_matches = unique_songs[
            unique_songs['song'].str.lower() == query_song.lower()
        ]
        
        for _, song in exact_matches.iterrows():
            matches.append({
                'song': song['song'],
                'artist': song['artist'],
                'weeks_on_chart': song['weeks-on-board'],
                'best_rank': song['rank'],
                'peak_rank': song['peak-rank'],
                'year': song['year'],
                'match_score': 100,
                'match_type': 'exact'
            })
        
        # 2. Song contains match (if not enough exact matches)
        if len(matches) < max_results:
            contains_matches = unique_songs[
                unique_songs['song'].str.contains(query_song, case=False, na=False) &
                ~unique_songs['song'].str.lower().eq(query_song.lower())  # Exclude exact matches
            ]
            
            for _, song in contains_matches.iterrows():
                if len(matches) >= max_results:
                    break
                matches.append({
                    'song': song['song'],
                    'artist': song['artist'],
                    'weeks_on_chart': song['weeks-on-board'],
                    'best_rank': song['rank'],
                    'peak_rank': song['peak-rank'],
                    'year': song['year'],
                    'match_score': 85,
                    'match_type': 'contains'
                })
        
        # 3. Fuzzy matching on song titles (if still not enough matches)
        if len(matches) < max_results:
            all_song_titles = unique_songs['song'].tolist()
            already_matched = {match['song'].lower() for match in matches}
            
            # Calculate fuzzy scores for remaining songs
            fuzzy_matches = []
            for song_title in all_song_titles:
                if song_title.lower() not in already_matched:
                    score = fuzz.partial_ratio(query_song.lower(), song_title.lower())
                    if score >= fuzzy_threshold:
                        song_data = unique_songs[unique_songs['song'] == song_title].iloc[0]
                        fuzzy_matches.append({
                            'song': song_data['song'],
                            'artist': song_data['artist'],
                            'weeks_on_chart': song_data['weeks-on-board'],
                            'best_rank': song_data['rank'],
                            'peak_rank': song_data['peak-rank'],
                            'year': song_data['year'],
                            'match_score': score,
                            'match_type': 'fuzzy'
                        })
            
            # Sort fuzzy matches by score and add to results
            fuzzy_matches.sort(key=lambda x: x['match_score'], reverse=True)
            for match in fuzzy_matches:
                if len(matches) >= max_results:
                    break
                matches.append(match)
        
        print(f"🎵 Found {len(matches)} matches for {search_info}")
        return matches[:max_results]
        
    except Exception as e:
        print(f"❌ Error searching for song '{query_song}': {e}")
        return []

def format_song_duration_results(matches: list[dict], original_query: str) -> str:
    """
    Format song duration search results into a user-friendly string.
    
    Args:
        matches: List of song match dictionaries from get_song_matches_with_duration
        original_query: Original search query for context
    
    Returns:
        Formatted string with song duration information
    """
    if not matches:
        return f"🔍 Sorry, I couldn't find any songs matching '{original_query}'. Try:\n" \
               "• Check spelling\n" \
               "• Use partial song names (e.g., 'Shape' instead of 'Shape of You')\n" \
               "• Try just the artist name"
    
    if len(matches) == 1:
        song = matches[0]
        header = f"🎵 **{song['song']}** by *{song['artist']}* ({song['year']})\n\n"
        
        weeks = song['weeks_on_chart']
        best_rank = song['best_rank']
        peak_rank = song['peak_rank']
        
        duration_info = f"📊 **Chart Performance:**\n"
        duration_info += f"• **{weeks} weeks** on Billboard Hot 100\n"
        duration_info += f"• **Best position:** #{best_rank}\n"
        
        if peak_rank != best_rank:
            duration_info += f"• **Peak rank:** #{peak_rank}\n"
        
        # Add some context about the performance
        if weeks >= 50:
            duration_info += f"\n🔥 **Incredible!** This song had amazing staying power on the charts!"
        elif weeks >= 30:
            duration_info += f"\n⭐ **Great performance!** This was a major hit."
        elif weeks >= 15:
            duration_info += f"\n👍 **Solid hit!** Good chart performance."
        else:
            duration_info += f"\n📈 **Chart entry** - Brief but notable appearance."
            
        return header + duration_info
    
    else:
        # Multiple matches - show all with brief info
        header = f"🔍 Found **{len(matches)}** songs matching '{original_query}':\n\n"
        
        results = []
        for i, song in enumerate(matches, 1):
            match_indicator = ""
            if song['match_type'] == 'exact':
                match_indicator = " ✅"
            elif song['match_type'] == 'fuzzy':
                match_indicator = f" ({song['match_score']}% match)"
            
            song_info = (
                f"**{i}.** {song['song']} by *{song['artist']}* ({song['year']}){match_indicator}\n"
                f"   📊 {song['weeks_on_chart']} weeks on chart, peaked at #{song['peak_rank']}"
            )
            results.append(song_info)
        
        footer = f"\n\n💡 **Tip:** Try a more specific query like the full song title for better results."
        
        return header + "\n\n".join(results) + footer

def get_song_weeks_on_chart(song_name: str) -> int:
    """Get total weeks a song spent on the Billboard Hot 100."""
    try:
        # Use the enhanced search function
        matches = get_song_matches_with_duration(song_name, max_results=1)
        if matches:
            return matches[0]['weeks_on_chart']
        return 0
        
    except Exception as e:
        print(f"Error getting weeks for song '{song_name}': {e}")
        return 0

def get_all_songs() -> list:
    """Get list of all unique songs for fuzzy matching."""
    try:
        return df['song'].unique().tolist()
    except Exception as e:
        print(f"Error getting all songs: {e}")
        return []

def get_dataset_stats() -> dict:
    """Get basic statistics about the dataset."""
    try:
        return {
            'total_records': len(df),
            'unique_songs': df['song'].nunique(),
            'unique_artists': df['artist'].nunique(),
            'year_range': (int(df['year'].min()), int(df['year'].max())),
            'total_years': df['year'].nunique()
        }
    except Exception as e:
        print(f"Error getting dataset stats: {e}")
        return {}

def search_songs_by_artist(artist_name: str, limit: int = 20) -> list[dict]:
    """Find songs by a specific artist."""
    try:
        artist_songs = df[df['artist'].str.contains(artist_name, case=False, na=False)]
        
        if artist_songs.empty:
            return []
        
        # Get best performance for each song by this artist
        best_performance = (
            artist_songs
            .groupby(['song', 'artist'])
            .agg({
                'rank': 'min',
                'peak-rank': 'min', 
                'weeks-on-board': 'max',
                'year': 'first'
            })
            .reset_index()
            .sort_values('rank')
            .head(limit)
        )
        
        return best_performance.to_dict('records')
        
    except Exception as e:
        print(f"Error searching songs by artist '{artist_name}': {e}")
        return []

def find_songs_by_pattern(pattern: str, limit: int = 10) -> list[dict]:
    """
    Find songs matching a specific pattern or keyword.
    Useful for queries like "songs with 'love' in the title"
    """
    try:
        # Use regex for flexible pattern matching
        matching_songs = df[df['song'].str.contains(pattern, case=False, na=False, regex=True)]
        
        if matching_songs.empty:
            return []
        
        # Get best performance for each matching song
        best_performance = (
            matching_songs
            .groupby(['song', 'artist'])
            .agg({
                'rank': 'min',
                'peak-rank': 'min',
                'weeks-on-board': 'max',
                'year': 'first'
            })
            .reset_index()
            .sort_values('rank')
            .head(limit)
        )
        
        return best_performance.to_dict('records')
        
    except Exception as e:
        print(f"Error finding songs by pattern '{pattern}': {e}")
        return []
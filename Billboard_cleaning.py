import pandas as pd

# Load dataset
df = pd.read_csv("charts.csv")

# Step 1: Convert 'date' to datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Step 2: Handle missing values in 'last-week'
# Fill missing with 0 if the song is new to the chart
df['last-week'] = df['last-week'].fillna(0).astype(int)

# Step 3: Add a 'year' column for easier querying
df['year'] = df['date'].dt.year

# Step 4: Standardize artist names (remove "feat.", "&", etc. if needed)
df['artist'] = df['artist'].str.replace("feat\\..*", "", regex=True)
df['artist'] = df['artist'].str.strip()

# Step 5: Remove duplicates (if any)
df = df.drop_duplicates()

# Step 6: Save cleaned version
df.to_csv("billboard_cleaned.csv", index=False)

print("✅ Billboard data cleaned and saved to 'billboard_cleaned.csv'")
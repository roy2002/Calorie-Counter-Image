# 🍎 Calorie Tracker

A web-based calorie tracking application that uses AI to analyze food images and calculate calories. Built with Flask and powered by OpenRouter AI.

## Features

- 📸 **Image Upload**: Upload food images via drag-and-drop or file selection
- 🤖 **AI Analysis**: Automatic calorie calculation using AI vision models
- ✏️ **Edit & Correct**: Fix misidentified food items and reanalyze
- 💾 **Database Storage**: Stores daily calorie counts in SQLite database
- 📊 **Daily Tracking**: View today's total calories and meal count
- 📈 **History**: Access historical data and weekly summaries

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python api.py
```

3. Open your browser and navigate to:
```
http://localhost:5001
```

## Usage

### Analyze Food Image

1. **Upload Image**: Click the upload area or drag and drop a food image
2. **Analyze**: Click "Analyze Image" to get calorie information
3. **View Results**: See the identified food items and total calories

### Edit & Correct

If the AI misidentifies a food item:

1. Click **"✏️ Edit & Correct"** button
2. Enter the correct food items in the text box (e.g., "1 slice of pizza, 1 apple")
3. Click **"🔄 Reanalyze"** to get corrected calorie counts
4. The corrected data will be saved to your daily total

### View Data

- **Today's Stats**: Displayed at the top of the page
- **Daily Totals**: Access via `/daily-total` endpoint
- **Weekly Summary**: Access via `/weekly-summary` endpoint
- **All Entries**: Access via `/entries` endpoint

## API Endpoints

### POST `/analyze`
Analyze an uploaded food image.
- **Body**: FormData with `image` file
- **Returns**: Analysis text, calories, daily total, entry count

### POST `/reanalyze`
Reanalyze with corrected food items.
- **Body**: JSON with `corrected_items` string
- **Returns**: Updated analysis text, calories, daily total, entry count

### GET `/daily-total?date=YYYY-MM-DD`
Get total calories for a specific date (defaults to today).
- **Returns**: Date, total_calories, entry_count, last_updated

### GET `/daily-totals?limit=30`
Get daily totals for the last N days.
- **Returns**: Array of daily totals

### GET `/entries?date=YYYY-MM-DD`
Get all entries for a specific date (defaults to today).
- **Returns**: Array of calorie entries

### GET `/weekly-summary`
Get summary of the last 7 days.
- **Returns**: Array of daily summaries

## Database Structure

### Table: `calorie_entries`
- `id`: Primary key
- `date`: Entry date (YYYY-MM-DD)
- `food_items`: Description of food items
- `total_calories`: Calorie count for this entry
- `analysis_text`: Full AI analysis text
- `timestamp`: Entry timestamp

### Table: `daily_totals`
- `date`: Primary key (YYYY-MM-DD)
- `total_calories`: Sum of all entries for the day
- `entry_count`: Number of entries for the day
- `last_updated`: Last update timestamp

## Files

- `api.py`: Flask application with API endpoints
- `database.py`: Database operations and helper functions
- `templates/index.html`: Frontend UI
- `requirements.txt`: Python dependencies
- `calorie_tracker.db`: SQLite database (auto-created)

## Technologies

- **Backend**: Flask, Python
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **AI**: OpenRouter API (Google Gemma model)

## Notes

- The application uses OpenRouter's free tier with Google Gemma model
- Images are converted to base64 for API transmission
- Database is automatically initialized on first run
- All calorie calculations are stored per day for historical tracking

## Future Enhancements

- User authentication
- Export data to CSV
- Meal planning features
- Nutrition breakdown (protein, carbs, fats)
- Mobile app version
- Multiple language support

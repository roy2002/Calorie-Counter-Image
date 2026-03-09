from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import base64
import os
from database import init_db, save_entry, update_entry, extract_calories, get_daily_total, get_all_daily_totals, get_entries_by_date, get_weekly_summary, clear_all_data

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Ensure the environment variable is set

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_image():
    try:
        # Get the uploaded image
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Read and encode the image to base64
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Determine the image format
        file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else 'jpg'
        mime_type = f"image/{file_extension}" if file_extension in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else "image/jpeg"
        
        # Create the data URL
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        # Make request to OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Can you calculate the calories in the following food item? Give answer in the following format -> Item n: No of calories: x. Total calories -> . DON'T give any explanation, just the calorie count. If you can't determine the calories, just say 'Unable to determine calories'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            # Extract calories and save to database
            total_calories = extract_calories(analysis_text)
            entry_id = save_entry(analysis_text, total_calories)
            
            # Get today's total
            daily_total = get_daily_total()
            
            return jsonify({
                'success': True,
                'analysis': analysis_text,
                'calories': total_calories,
                'daily_total': daily_total['total_calories'] if daily_total else total_calories,
                'entry_count': daily_total['entry_count'] if daily_total else 1,
                'entry_id': entry_id  # Return entry ID for future updates
            })
        else:
            return jsonify({
                'error': f'API request failed: {response.text}'
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daily-total', methods=['GET'])
def daily_total():
    """Get total calories for today or a specific date"""
    date = request.args.get('date')  # Optional date parameter
    result = get_daily_total(date)
    
    if result:
        return jsonify({'success': True, 'data': result})
    else:
        return jsonify({'success': True, 'data': {'total_calories': 0, 'entry_count': 0}})

@app.route('/daily-totals', methods=['GET'])
def daily_totals():
    """Get daily totals for the last 30 days"""
    limit = request.args.get('limit', 30, type=int)
    results = get_all_daily_totals(limit)
    return jsonify({'success': True, 'data': results})

@app.route('/entries', methods=['GET'])
def entries():
    """Get all entries for today or a specific date"""
    date = request.args.get('date')  # Optional date parameter
    results = get_entries_by_date(date)
    return jsonify({'success': True, 'data': results})

@app.route('/weekly-summary', methods=['GET'])
def weekly_summary():
    """Get summary of the last 7 days"""
    results = get_weekly_summary()
    return jsonify({'success': True, 'data': results})

@app.route('/reanalyze', methods=['POST'])
def reanalyze():
    """Re-analyze with corrected food items"""
    try:
        data = request.get_json()
        
        if 'corrected_items' not in data:
            return jsonify({'error': 'No corrected items provided'}), 400
        
        if 'entry_id' not in data:
            return jsonify({'error': 'No entry ID provided'}), 400
        
        corrected_items = data['corrected_items']
        entry_id = data['entry_id']
        
        # Make request to OpenRouter API with corrected items
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Calculate the calories for the following food items: {corrected_items}. Give answer in the following format -> Item n: No of calories: x. Total calories -> . DON'T give any explanation, just the calorie count."
                    }
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            # Extract calories and UPDATE the existing entry (not create new one)
            total_calories = extract_calories(analysis_text)
            updated_entry_id = update_entry(entry_id, analysis_text, total_calories)
            
            if updated_entry_id is None:
                return jsonify({'error': 'Entry not found'}), 404
            
            # Get today's total
            daily_total = get_daily_total()
            
            return jsonify({
                'success': True,
                'analysis': analysis_text,
                'calories': total_calories,
                'daily_total': daily_total['total_calories'] if daily_total else total_calories,
                'entry_count': daily_total['entry_count'] if daily_total else 1,
                'entry_id': updated_entry_id
            })
        else:
            return jsonify({
                'error': f'API request failed: {response.text}'
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all data from the database"""
    try:
        clear_all_data()
        return jsonify({'success': True, 'message': 'All data cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on all network interfaces (0.0.0.0) to allow access from other devices
    # You can access from your phone using: http://<your-laptop-ip>:5001
    app.run(host='0.0.0.0', port=5001, debug=True)
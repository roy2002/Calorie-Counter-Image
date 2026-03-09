from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import requests
import json
import base64
import os
from database import (
    init_db, save_entry, update_entry, extract_calories, 
    get_daily_total, get_all_daily_totals, get_entries_by_date, 
    get_weekly_summary, clear_all_data, delete_entry,
    create_user, authenticate_user, create_session, validate_token, delete_session,
    DATABASE
)

app = Flask(__name__)
CORS(app, supports_credentials=True)

OPENROUTER_API_KEY = "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"
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'your-secret-key-change-me')

# Initialize database on startup
init_db()

# Authentication middleware
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id = validate_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user_id to request context
        request.user_id = user_id
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/')
def index():
    return jsonify({'message': 'Calorie Tracker API'})

# ============= Authentication Endpoints =============

@app.route('/auth/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        user_id = create_user(username, email, password)
        
        if user_id is None:
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Create session token
        token = create_session(user_id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = authenticate_user(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create session token
        token = create_session(user['id'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    try:
        token = request.headers.get('Authorization', '')[7:]
        delete_session(token)
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    # This endpoint can be used to validate the token
    return jsonify({'success': True, 'user_id': request.user_id})

@app.route('/analyze', methods=['POST'])
@require_auth
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
            entry_id = save_entry(analysis_text, total_calories, request.user_id)
            
            # Get today's total
            daily_total = get_daily_total(user_id=request.user_id)
            
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
@require_auth
def daily_total():
    """Get total calories for today or a specific date"""
    date = request.args.get('date')  # Optional date parameter
    result = get_daily_total(date, user_id=request.user_id)
    
    if result:
        return jsonify({'success': True, 'data': result})
    else:
        return jsonify({'success': True, 'data': {'total_calories': 0, 'entry_count': 0}})

@app.route('/daily-totals', methods=['GET'])
@require_auth
def daily_totals():
    """Get daily totals for the last 30 days"""
    limit = request.args.get('limit', 30, type=int)
    results = get_all_daily_totals(limit, user_id=request.user_id)
    return jsonify({'success': True, 'data': results})

@app.route('/entries', methods=['GET'])
@require_auth
def entries():
    """Get all entries for today or a specific date"""
    date = request.args.get('date')  # Optional date parameter
    results = get_entries_by_date(date, user_id=request.user_id)
    return jsonify({'success': True, 'data': results})

@app.route('/weekly-summary', methods=['GET'])
@require_auth
def weekly_summary():
    """Get summary of the last 7 days"""
    results = get_weekly_summary(user_id=request.user_id)
    return jsonify({'success': True, 'data': results})

@app.route('/reanalyze', methods=['POST'])
@require_auth
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
            daily_total = get_daily_total(user_id=request.user_id)
            
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

@app.route('/delete-entry/<int:entry_id>', methods=['DELETE'])
@require_auth
def delete_entry_route(entry_id):
    """Delete a specific entry"""
    try:
        success = delete_entry(entry_id, user_id=request.user_id)
        if success:
            return jsonify({'success': True, 'message': 'Entry deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-data', methods=['POST'])
@require_auth
def clear_data():
    """Clear all data from the database for the current user"""
    try:
        clear_all_data(user_id=request.user_id)
        return jsonify({'success': True, 'message': 'All data cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/recreate-database', methods=['POST'])
def recreate_database():
    """ADMIN ONLY: Recreate database with new schema. WARNING: Deletes all data!"""
    try:
        # Check admin secret
        admin_secret = request.headers.get('X-Admin-Secret')
        if not admin_secret or admin_secret != ADMIN_SECRET:
            return jsonify({'error': 'Unauthorized - Invalid admin secret'}), 401
        
        import os
        from database import DATABASE
        
        # Backup existing database
        if os.path.exists(DATABASE):
            backup_name = f"{DATABASE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(DATABASE, backup_name)
                print(f"Backup created: {backup_name}")
            except Exception as e:
                print(f"Backup failed: {e}")
        
        # Recreate database with new schema
        init_db()
        
        return jsonify({
            'success': True, 
            'message': 'Database recreated successfully with authentication schema',
            'note': 'All users must sign up again'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on all network interfaces (0.0.0.0) to allow access from other devices
    # You can access from your phone using: http://<your-laptop-ip>:5001
    app.run(host='0.0.0.0', port=5001, debug=True)
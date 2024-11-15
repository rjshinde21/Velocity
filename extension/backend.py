from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import google.generativeai as genai
import os
import csv
from collections import defaultdict
import logging
import traceback

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure the Gemini API
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY', "AIzaSyAInppRzQoReAnvNyAEIB0xtL1ZCxIjaDk"))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {str(e)}")
    model = None

@app.route('/process', methods=['POST'])
def process_request():
    try:
        # Log the incoming request
        logger.debug(f"Received request: {request.form}")
        
        # Get the form data
        form_data = request.form.get('data')
        if not form_data:
            logger.error("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        # Parse the JSON string from form data
        try:
            data = json.loads(form_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400
        
        if 'prompt' not in data:
            logger.error("No prompt provided in data")
            return jsonify({"error": "No prompt provided"}), 400

        prompt = data['prompt']
        category_data = data.get('category', {})
        
        # Log the processed data
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Categories: {category_data}")
        
        # Format categories
        formatted_categories = []
        for category, value in category_data.items():
            if isinstance(value, str):
                formatted_categories.append(f"{category}: {value}")
            elif isinstance(value, list):
                formatted_categories.append(f"{category}: {','.join(value)}")

        # Join all formatted category strings with spaces
        result = " ".join(formatted_categories)

        prompt_string = (
            "You are a professional prompt designer. Improve the following prompt "
            f"to create an image based on: '{prompt} {result}'. "
            "Show me at least 3 options. Return the response in this exact JSON format: "
            '{"prompts":[{"prompt":"improved prompt 1"},{"prompt":"improved prompt 2"},{"prompt":"improved prompt 3"}]}'
        )

        # Log the final prompt string
        logger.debug(f"Final prompt string: {prompt_string}")

        if not model:
            return jsonify({"error": "Gemini API not properly configured"}), 500

        # Send the prompt to Gemini API
        try:
            response = model.generate_content(prompt_string)
            logger.debug(f"Gemini API response: {response.text}")
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return jsonify({"error": f"AI model error: {str(e)}"}), 500
        
        # Try to parse the response as JSON
        try:
            json_response = json.loads(response.text)
            return jsonify({"response": json.dumps(json_response)})
        except json.JSONDecodeError:
            # If parsing fails, format the response manually
            formatted_response = {
                "prompts": [
                    {"prompt": line.strip()} 
                    for line in response.text.split('\n') 
                    if line.strip()
                ]
            }
            return jsonify({"response": json.dumps(formatted_response)})

    except Exception as e:
        logger.error(f"Error in process_request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        # Get the absolute path to the categories file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, 'assets', 'categories.csv')
        
        logger.debug(f"Looking for categories file at: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            logger.error(f"Categories file not found at {csv_file_path}")
            return jsonify({"error": "Categories file not found"}), 404
            
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            categories = defaultdict(list)
            
            for row in csv_reader:
                category_name = row['category']
                item_name = row['item']
                categories[category_name].append({
                    "name": item_name
                })
            
            formatted_data = [
                {
                    "name": category,
                    "items": items
                }
                for category, items in categories.items()
            ]
            
            return jsonify(formatted_data)
            
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Ensure the assets directory exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Check if categories.csv exists
    csv_file_path = os.path.join(assets_dir, 'categories.csv')
    if not os.path.exists(csv_file_path):
        logger.warning(f"Categories file not found at {csv_file_path}")
        # Create a sample categories file if it doesn't exist
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['category', 'item'])
            writer.writerow(['Style', 'Realistic'])
            writer.writerow(['Style', 'Cartoon'])
            writer.writerow(['Background', 'Nature'])
            writer.writerow(['Background', 'Urban'])
    
    app.run(host='0.0.0.0', port=5000, debug=True)
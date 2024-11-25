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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, 'assets', 'categoriesNew.csv')
        
        if not os.path.exists(csv_file_path):
            logger.error(f"Categories file not found at {csv_file_path}")
            return jsonify({"error": "Categories file not found"}), 404

        # Read CSV and organize data
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            
            # Read category structure (first 4 rows)
            category_structure = []
            for _ in range(4):
                row = next(csv_reader)
                category_structure.append({
                    'name': row[0],
                    'column1': row[1],
                    'column2': row[2]
                })
            
            # Read the remaining data
            remaining_data = list(csv_reader)
            
            # Organize items by category type
            category_items = {}
            for row in remaining_data:
                if row and len(row) >= 3:  # Ensure row has enough columns
                    category_type = row[0]
                    if category_type not in category_items:
                        category_items[category_type] = []
                    # Add non-empty items
                    if row[1]:
                        category_items[category_type].append({"name": row[1]})
                    if row[2]:
                        category_items[category_type].append({"name": row[2]})

            # Format the final data structure
            formatted_data = []
            for structure in category_structure:
                card = {
                    "name": structure['name'],
                    "dropdowns": [
                        {
                            "name": structure['column1'],
                            "items": category_items.get(structure['column1'], [])
                        },
                        {
                            "name": structure['column2'],
                            "items": category_items.get(structure['column2'], [])
                        }
                    ]
                }
                formatted_data.append(card)

            logger.debug(f"Formatted categories data: {formatted_data}")
            return jsonify(formatted_data)
            
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def get_items_for_category(data, category):
    items = []
    for row in data:
        if row[0] == category:
            items.extend([item for item in row[1:] if item])
    return items

if __name__ == '__main__':
    # Ensure the assets directory exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Check if categories.csv exists
    csv_file_path = os.path.join(assets_dir, 'categoriesNew.csv')
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
    
    app.run(host='0.0.0.0', port=2000, debug=True)
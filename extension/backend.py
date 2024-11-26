from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import google.generativeai as genai
import os
import csv
from collections import defaultdict
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from logging import Logger
import re

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
@dataclass
class ProcessedPrompt:
    prompt: str
    categories: str
    tokens: int

class PromptPreprocessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.redundant_phrases = {
            "please make", "please create", "i want", "i need", "generate",
            "create an image", "make an image", "create a picture",
            "please", "if possible", "would like", "could you"
        }
        
        self.style_keywords = {
            "artistic", "realistic", "cartoon", "anime", "photorealistic",
            "digital art", "oil painting", "watercolor", "sketch"
        }
        
    def clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        # Convert to lowercase and remove extra whitespace
        text = ' '.join(text.lower().split())
        
        # Remove redundant phrases
        for phrase in self.redundant_phrases:
            text = re.sub(rf'\b{phrase}\b', '', text, flags=re.IGNORECASE)
        
        # Remove multiple punctuation
        text = re.sub(r'[!.?]+(?=[!.?])', '', text)
        text = re.sub(r'[,;]+(?=[,;])', '', text)
        
        return text.strip()
    
    def extract_style(self, text: str) -> Tuple[str, str]:
        """Extract and separate style information from prompt"""
        style_terms = []
        content_terms = []
        
        words = text.split()
        for word in words:
            if word.lower() in self.style_keywords:
                style_terms.append(word)
            else:
                content_terms.append(word)
        
        return ' '.join(content_terms), ' '.join(style_terms)
    
    def format_categories(self, category_data: Dict[str, Any]) -> str:
        """Format category data into a structured string"""
        formatted_cats = []
        
        for category, value in category_data.items():
            if isinstance(value, str) and value.strip():
                formatted_cats.append(f"{category}: {value}")
            elif isinstance(value, list) and value:
                formatted_cats.append(f"{category}: {', '.join(filter(None, value))}")
                
        return ' | '.join(formatted_cats)
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token count estimation"""
        return len(text.split()) + (len(text) // 4)
    
    def process_prompt(self, raw_prompt: str, category_data: Dict[str, Any]) -> ProcessedPrompt:
        """Main processing pipeline"""
        self.logger.debug(f"Processing raw prompt: {raw_prompt}")
        
        # Clean the basic text
        cleaned_prompt = self.clean_text(raw_prompt)
        self.logger.debug(f"Cleaned prompt: {cleaned_prompt}")
        
        # Extract style information
        content, style = self.extract_style(cleaned_prompt)
        self.logger.debug(f"Content: {content} | Style: {style}")
        
        # Format categories
        formatted_cats = self.format_categories(category_data)
        self.logger.debug(f"Formatted categories: {formatted_cats}")
        
        # Reconstruct optimized prompt
        if style:
            final_prompt = f"{content} in {style} style"
        else:
            final_prompt = content
            
        # Estimate tokens
        tokens = self.estimate_tokens(final_prompt + " " + formatted_cats)
        
        return ProcessedPrompt(
            prompt=final_prompt,
            categories=formatted_cats,
            tokens=tokens
        )
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
        logger.debug(f"Received request: {request.form}")
        
        # Get and validate form data
        form_data = request.form.get('data')
        if not form_data:
            return jsonify({"error": "No data provided"}), 400

        try:
            data = json.loads(form_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400
        
        if 'prompt' not in data:
            return jsonify({"error": "No prompt provided"}), 400

        # Initialize preprocessor
        preprocessor = PromptPreprocessor(logger)
        
        # Process the prompt and categories
        processed = preprocessor.process_prompt(data['prompt'],data.get('category', {}))
        print("processed prompt:" + processed.prompt)
        print("processed categories:" + processed.categories)
        # Construct optimized prompt string for Gemini
        prompt_string = (
            "You are a professional prompt designer. Generate 3 varied and creative "
            f"image prompts based on this concept: '{processed.prompt}'. "
            f"Consider these aspects: {processed.categories}. "
            "Each prompt should be unique and detailed. "
            'Return in JSON format: {"prompts":[{"prompt":"..."}, {"prompt":"..."}, {"prompt":"..."}]}'
        )

        logger.debug(f"Final prompt string: {prompt_string}")
        logger.debug(f"Estimated tokens: {processed.tokens}")

        if not model:
            return jsonify({"error": "Gemini API not properly configured"}), 500

        try:
            response = model.generate_content(prompt_string)
            logger.debug(f"Gemini API response: {response.text}")
            
            try:
                json_response = json.loads(response.text)
                return jsonify({"response": json.dumps(json_response)})
            except json.JSONDecodeError:
                # Fallback formatting if JSON parsing fails
                formatted_response = {
                    "prompts": [
                        {"prompt": line.strip()} 
                        for line in response.text.split('\n') 
                        if line.strip()
                    ]
                }
                return jsonify({"response": json.dumps(formatted_response)})

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return jsonify({"error": f"AI model error: {str(e)}"}), 500

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
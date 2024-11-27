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
from spellchecker import SpellChecker


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
    corrections_made: Dict[str, str]  # Track corrections for logging

class PromptPreprocessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.spell = SpellChecker()
        self.redundant_phrases = {
            "please make", "please create", "i want", "i need", "generate",
            "create an image", "make an image", "create a picture",
            "please", "if possible", "would like", "could you"
        }
        
        self.style_keywords = {
            "artistic", "realistic", "cartoon", "anime", "photorealistic",
            "digital art", "oil painting", "watercolor", "sketch"
        }
        
        # Add common art/style terms to spell checker dictionary
        self.spell.word_frequency.load_words([
            "anime", "manga", "cyberpunk", "steampunk", "vaporwave",
            "minimalist", "maximalist", "surreal", "hyperrealistic",
            "pixelated", "cinematic", "isometric", "dystopian", "utopian"
        ])
    
    def correct_spelling(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Correct spelling in text while tracking corrections.
        Returns corrected text and dictionary of corrections made.
        """
        words = text.split()
        corrected_words = []
        corrections = {}
        
        for word in words:
            # Skip words that are likely intentional or style-related
            if (word.lower() in self.style_keywords or 
                word.isupper() or  # Acronyms
                any(c.isdigit() for c in word)):  # Numbers
                corrected_words.append(word)
                continue
            
            # Check if word is misspelled
            if self.spell.unknown([word]):
                correction = self.spell.correction(word)
                if correction and correction != word:
                    corrections[word] = correction
                    corrected_words.append(correction)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections

    def clean_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Basic text cleaning with spell checking"""
        # Convert to lowercase and remove extra whitespace
        text = ' '.join(text.lower().split())
        
        # Remove redundant phrases
        for phrase in self.redundant_phrases:
            text = re.sub(rf'\b{phrase}\b', '', text, flags=re.IGNORECASE)
        
        # Remove multiple punctuation
        text = re.sub(r'[!.?]+(?=[!.?])', '', text)
        text = re.sub(r'[,;]+(?=[,;])', '', text)
        
        # Correct spelling
        corrected_text, corrections = self.correct_spelling(text.strip())
        
        return corrected_text, corrections
    
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
        
        # Clean the text and get spelling corrections
        cleaned_prompt, corrections = self.clean_text(raw_prompt)
        if corrections:
            self.logger.debug(f"Spelling corrections made: {corrections}")
        
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
            tokens=tokens,
            corrections_made=corrections
        )

def normalize_json_response(response_text: str) -> dict:
    """
    Normalizes JSON response from Gemini to ensure consistent formatting
    regardless of how it was originally formatted.
    """
    try:
        # First try to parse as JSON
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # If parsing fails, try to extract and format the prompts
        lines = response_text.strip().split('\n')
        prompts = []
        current_prompt = ""
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('}') and not line.startswith('"prompts"'):
                if line.startswith('"prompt":'): # New prompt starts
                    if current_prompt:  # Save previous prompt if exists
                        prompts.append({"prompt": current_prompt.strip()})
                    current_prompt = line.split(':', 1)[1].strip().strip('"').strip(',')
                else:
                    # Continue previous prompt
                    current_prompt += " " + line.strip('"').strip(',')
        
        # Add the last prompt if exists
        if current_prompt:
            prompts.append({"prompt": current_prompt.strip()})
            
        data = {"prompts": prompts}
    
    # Ensure each prompt is a single line with no extra whitespace
    for prompt in data.get("prompts", []):
        if "prompt" in prompt:
            # Remove extra whitespace and newlines within the prompt
            prompt["prompt"] = " ".join(prompt["prompt"].split())
    
    return data

# Configure the Gemini API
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY', "AIzaSyBuei3ff-s2bUAFznTXv7FM1v-o9RO9Aig"))
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
        processed = preprocessor.process_prompt(
            data['prompt'],
            data.get('category', {})
        )
        
        # Log any spelling corrections
        if processed.corrections_made:
            logger.info(f"Spelling corrections applied: {processed.corrections_made}")
        
        # Construct optimized prompt string for Gemini
        prompt_string = (
            "You are a professional prompt designer. Generate 3 varied and creative "
            f"image prompts based on this concept: '{processed.prompt}'. "
            f"Consider these aspects: {processed.categories}. "
            "Each prompt should be unique and detailed. "
            'Return ONLY a JSON object in this exact format without any extra whitespace or newlines: '
            '{"prompts":[{"prompt":"prompt1"},{"prompt":"prompt2"},{"prompt":"prompt3"}]}'
        )

        logger.debug(f"Final prompt string: {prompt_string}")
        logger.debug(f"Estimated tokens: {processed.tokens}")

        if not model:
            return jsonify({"error": "Gemini API not properly configured"}), 500

        try:
            response = model.generate_content(prompt_string)
            logger.debug(f"Gemini API response: {response.text}")
            normalized_response = normalize_json_response(response.text)
            print("formatted gemini api response:",normalized_response)
            # Add spelling corrections to response if any were made
            response_data = {
                "response": json.dumps(normalized_response, ensure_ascii=False),
                "corrections": processed.corrections_made if processed.corrections_made else None
            }
            
            try:
                json_response = json.loads(response.text)
                response_data["response"] = json.dumps(json_response)
                return jsonify(response_data)
            except json.JSONDecodeError:
                formatted_response = {
                    "prompts": [
                        {"prompt": line.strip()} 
                        for line in response.text.split('\n') 
                        if line.strip()
                    ]
                }
                response_data["response"] = json.dumps(formatted_response)
                return jsonify(response_data)

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
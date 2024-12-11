from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import csv
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from logging import Logger
import re
from spellchecker import SpellChecker
from llamaapi import LlamaAPI

app = Flask(__name__)
CORS(app, resources={
    r"/process": {
        "origins": [
            "https://chat.openai.com/*",
            "https://chatgpt.com/*",
            "https://claude.ai/*",
            "https://gemini.google.com/*",
            "https://discord.com/*",
            "https://gamma.app/*",
            "https://app.runwayml.com/*",
            "https://thinkvelocity.in/*",
            "http://localhost:*"
        ],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    },
    r"/get_categories": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"]
    }
})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Llama API
# try:
#     llama = LlamaAPI(os.getenv('LLAMA_API_KEY'))
# except Exception as e:
#     logger.error(f"Failed to initialize Llama API: {str(e)}")
#     llama = None
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
try:
    api_key = os.getenv('LLAMA_API_KEY')
    print("API Key loaded:", api_key)  # for debugging
    if not api_key:
        raise ValueError("LLAMA_API_KEY not found in environment variables")
    llama = LlamaAPI(api_key)
except Exception as e:
    logger.error(f"Failed to initialize Llama API: {str(e)}")
    llama = None

@dataclass
class ProcessedPrompt:
    prompt: str
    categories: str
    tokens: int
    corrections_made: Dict[str, str]

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
        words = text.split()
        corrected_words = []
        corrections = {}
        
        for word in words:
            if (word.lower() in self.style_keywords or 
                word.isupper() or  # Acronyms
                any(c.isdigit() for c in word)):  # Numbers
                corrected_words.append(word)
                continue
            
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
        text = ' '.join(text.lower().split())
        
        for phrase in self.redundant_phrases:
            text = re.sub(rf'\b{phrase}\b', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'[!.?]+(?=[!.?])', '', text)
        text = re.sub(r'[,;]+(?=[,;])', '', text)
        
        corrected_text, corrections = self.correct_spelling(text.strip())
        
        return corrected_text, corrections
    
    def extract_style(self, text: str) -> Tuple[str, str]:
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
        formatted_cats = []
        
        for category, value in category_data.items():
            if isinstance(value, str) and value.strip():
                formatted_cats.append(f"{category}: {value}")
            elif isinstance(value, list) and value:
                formatted_cats.append(f"{category}: {', '.join(filter(None, value))}")
                
        return ' | '.join(formatted_cats)
    
    def estimate_tokens(self, text: str) -> int:
        return len(text.split()) + (len(text) // 4)
    
    def process_prompt(self, raw_prompt: str, category_data: Dict[str, Any]) -> ProcessedPrompt:
        self.logger.debug(f"Processing raw prompt: {raw_prompt}")
        
        cleaned_prompt, corrections = self.clean_text(raw_prompt)
        if corrections:
            self.logger.debug(f"Spelling corrections made: {corrections}")
        
        content, style = self.extract_style(cleaned_prompt)
        self.logger.debug(f"Content: {content} | Style: {style}")
        
        formatted_cats = self.format_categories(category_data)
        self.logger.debug(f"Formatted categories: {formatted_cats}")
        
        if style:
            final_prompt = f"{content} in {style} style"
        else:
            final_prompt = content
            
        tokens = self.estimate_tokens(final_prompt + " " + formatted_cats)
        
        return ProcessedPrompt(
            prompt=final_prompt,
            categories=formatted_cats,
            tokens=tokens,
            corrections_made=corrections
        )

def normalize_json_response(response_text: str) -> dict:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
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
                    current_prompt += " " + line.strip('"').strip(',')
        
        if current_prompt:
            prompts.append({"prompt": current_prompt.strip()})
            
        data = {"prompts": prompts}
    
    for prompt in data.get("prompts", []):
        if "prompt" in prompt:
            prompt["prompt"] = " ".join(prompt["prompt"].split())
    
    return data

def call_llama_api(prompt: str) -> str:
    """
    Call the Llama API with the given prompt using the official SDK
    """
    try:
        api_request_json = {
            "model": "llama3.2-11b-vision",  # Using the latest model
            "messages": [
                {"role": "system", "content": "You are a professional prompt designer."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        logger.debug(f"Sending request to Llama API: {api_request_json}")
        response = llama.run(api_request_json)
        response_json = response.json()
        logger.debug(f"Received response from Llama API: {response_json}")
        
        # Extract the content from the response
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            raise Exception("No completion found in response")
            
    except Exception as e:
        logger.error(f"Llama API error: {str(e)}")
        raise


@app.route('/process', methods=['POST'])
def process_request():
    try:
        logger.debug(f"Received request: {request.form}")
        
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
        if not llama:
            return jsonify({"error": "Llama API not properly configured"}), 500

        # Get AI type and style from request
        ai_type = data.get('AIType', 'default')
        writing_style = data.get('style', 'professional')

        # Initialize preprocessor and process the prompt
        preprocessor = PromptPreprocessor(logger)
        processed = preprocessor.process_prompt(
            data['prompt'],
            {}  # Empty dict since we're not using categories anymore
        )
        
        if processed.corrections_made:
            logger.info(f"Spelling corrections applied: {processed.corrections_made}")
        
        # Modify prompt string based on style and AI type
        style_instructions = {
            'descriptive': "Use rich, detailed descriptions with vivid imagery",
            'creative': "Think outside the box with unique and imaginative elements",
            'professional': "Maintain a formal and business-appropriate tone",
            'concise': "Be brief and clear, focusing on essential elements"
        }

        style_instruction = style_instructions.get(writing_style, style_instructions['professional'])
        
        prompt_string = (
            f"Generate 3 varied {writing_style} prompts for {ai_type} based on this concept: "
            f"'{processed.prompt}'. {style_instruction}. "
            "Each prompt should be unique and detailed. "
            'Return ONLY a JSON object in this exact format without any extra text: '
            '{"prompts":[{"prompt":"prompt1"},{"prompt":"prompt2"},{"prompt":"prompt3"}]}'
        )

        logger.debug(f"Final prompt string: {prompt_string}")
        logger.debug(f"Using AI Type: {ai_type}, Style: {writing_style}")
        logger.debug(f"Estimated tokens: {processed.tokens}")

        try:
            response_text = call_llama_api(prompt_string)
            logger.debug(f"Llama API response: {response_text}")
            normalized_response = normalize_json_response(response_text)
            
            response_data = {
                "response": json.dumps(normalized_response, ensure_ascii=False),
                "corrections": processed.corrections_made if processed.corrections_made else None,
                "metadata": {
                    "ai_type": ai_type,
                    "style": writing_style
                }
            }
            response = jsonify(response_data)
            # Add CORS headers explicitly
            response.headers.add('Access-Control-Allow-Origin', request.origin)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')

            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Llama API error: {str(e)}")
            return jsonify({"error": f"AI model error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in process_request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/process', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', request.origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@app.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, 'assets', 'categoriesNew.csv')
        
        if not os.path.exists(csv_file_path):
            logger.error(f"Categories file not found at {csv_file_path}")
            return jsonify({"error": "Categories file not found"}), 404

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            
            category_structure = []
            for _ in range(4):
                row = next(csv_reader)
                category_structure.append({
                    'name': row[0],
                    'column1': row[1],
                    'column2': row[2]
                })
            
            remaining_data = list(csv_reader)
            
            category_items = {}
            for row in remaining_data:
                if row and len(row) >= 3:
                    category_type = row[0]
                    if category_type not in category_items:
                        category_items[category_type] = []
                    if row[1]:
                        category_items[category_type].append({"name": row[1]})
                    if row[2]:
                        category_items[category_type].append({"name": row[2]})

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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    csv_file_path = os.path.join(assets_dir, 'categoriesNew.csv')
    if not os.path.exists(csv_file_path):
        logger.warning(f"Categories file not found at {csv_file_path}")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['category', 'item'])
            writer.writerow(['Style', 'Realistic'])
            writer.writerow(['Style', 'Cartoon'])
            writer.writerow(['Background', 'Nature'])
            writer.writerow(['Background', 'Urban'])
    
    app.run(host='0.0.0.0', port=2000, debug=True)
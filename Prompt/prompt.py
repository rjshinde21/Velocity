from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
from typing import Dict, Any, List, Tuple
from logging import Logger
from llamaapi import LlamaAPI
import re
from transformers import pipeline
from spacy import load
import textstat
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import wordnet
nltk.download('punkt')
import time
nltk.download('wordnet')
import datetime

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
            "http://localhost:*",
            "chrome-extension://*"
        ],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
try:
    api_key = os.getenv('LLAMA_API_KEY')
    
    if not api_key:
        raise ValueError("LLAMA_API_KEY not found in environment variables")
    llama = LlamaAPI(api_key)
except Exception as e:
    logger.error(f"Failed to initialize Llama API: {str(e)}")
    llama = None

class ModelManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            logger.info("Initializing ML models...")
            try:
                # Load all models once
                self.nlp = load('en_core_web_sm')
                self.sentiment_analyzer = pipeline('sentiment-analysis')
                self.keyword_model = KeyBERT()
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("All models loaded successfully")
                ModelManager._initialized = True
            except Exception as e:
                logger.error(f"Error initializing models: {e}")
                raise
    
    @property
    def models(self):
        return {
            'nlp': self.nlp,
            'sentiment_analyzer': self.sentiment_analyzer,
            'keyword_model': self.keyword_model,
            'semantic_model': self.semantic_model
        }


class ParameterManager:
    @staticmethod
    def get_default_parameters() -> Dict:
        """Return default parameters with explanations."""
        return {
            "temperature": {
                "value": 0.7,
                "reasoning": "Default balanced temperature for general use"
            },
            "top_p": {
                "value": 0.9,
                "reasoning": "Default top_p for good diversity"
            },
            "presence_penalty": {
                "value": 0.0,
                "reasoning": "Default neutral presence penalty"
            },
            "frequency_penalty": {
                "value": 0.0,
                "reasoning": "Default neutral frequency penalty"
            }
        }

    @staticmethod
    def extract_api_parameters(parameters: Dict) -> Dict[str, float]:
        """Extract clean parameters for API calls"""
        try:
            if not parameters:
                return ParameterManager.get_default_parameters()

            # Handle nested parameter structure
            if 'value' in parameters:
                parameters = parameters['value']

            return {
                'temperature': float(parameters.get('temperature', {}).get('value', 0.7)),
                'top_p': float(parameters.get('top_p', {}).get('value', 0.9)),
                'presence_penalty': float(parameters.get('presence_penalty', {}).get('value', 0.0)),
                'frequency_penalty': float(parameters.get('frequency_penalty', {}).get('value', 0.0))
            }
        except Exception as e:
            logger.error(f"Parameter extraction failed: {str(e)}")
            return ParameterManager.get_default_parameters()
        
class PromptPreprocessor:
    def __init__(self):
        self.model_manager = ModelManager()
        self.nlp = self.model_manager.models['nlp']
        self.sentiment_analyzer = self.model_manager.models['sentiment_analyzer']
        self.keyword_model = self.model_manager.models['keyword_model']
        self.semantic_model = self.model_manager.models['semantic_model']

    def analyze_prompt(self, prompt: str) -> Dict:
        """Comprehensive prompt analysis"""
        try:
            doc = self.nlp(prompt)
            
            named_entities = [(ent.text, ent.label_) for ent in doc]
            
            keywords = self.keyword_model.extract_keywords(prompt, 
                                                         top_n=5, 
                                                         stop_words='english')
            
            sentiment_result = self.sentiment_analyzer(prompt)[0]
            
            complexity_score = self._calculate_complexity(prompt)
            
            sentence_count = len(list(doc.sents))
            
            return {
                "named_entities": named_entities,
                "keywords": [kw[0] for kw in keywords],
                "sentiment": sentiment_result['label'],
                "sentiment_score": sentiment_result['score'],
                "complexity_score": complexity_score,
                "sentence_count": sentence_count,
                "word_count": len([token for token in doc if not token.is_punct]),
                "linguistic_features": self._extract_linguistic_features(doc)
            }
        except Exception as e:
            logger.error(f"Prompt analysis failed: {str(e)}")
            return self._create_fallback_analysis()

    def _create_fallback_analysis(self) -> Dict:
        """Create fallback analysis results"""
        return {
            "named_entities": [],
            "keywords": ["task", "organization"],
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.5,
            "complexity_score": 50.0,
            "sentence_count": 1,
            "word_count": 0,
            "linguistic_features": {
                "verbs": [],
                "nouns": [],
                "adjectives": [],
                "dependencies": [],
                "has_questions": False
            }
        }

    def enhance_context(self, prompt: str, analysis: Dict) -> Dict:
        """Enhance prompt context with additional information"""
        try:
            embeddings = self.semantic_model.encode(prompt)
            
            sentences = sent_tokenize(prompt)
            sentence_complexity = [textstat.flesch_reading_ease(sent) for sent in sentences]
            
            keywords = analysis.get('keywords', [])
            related_concepts = set()
            for keyword in keywords:
                synsets = wordnet.synsets(keyword)
                for syn in synsets[:2]:
                    related_concepts.update([lemma.name() for lemma in syn.lemmas()])
            
            return {
                "semantic_features": {
                    "embedding_dim": len(embeddings),
                    "semantic_complexity": float(embeddings.std()),
                    "related_concepts": list(related_concepts)
                },
                "structural_features": {
                    "sentence_complexities": sentence_complexity,
                    "avg_sentence_complexity": sum(sentence_complexity) / len(sentence_complexity) 
                        if sentence_complexity else 0,
                    "coherence_score": self._calculate_coherence(sentences)
                }
            }
        except Exception as e:
            logger.error(f"Context enhancement failed: {str(e)}")
            return self._create_fallback_context()

    def _calculate_complexity(self, text: str) -> float:
        try:
            flesch_score = textstat.flesch_reading_ease(text)
            grade_level = textstat.coleman_liau_index(text)
            
            normalized_flesch = (100 - flesch_score) / 100 * 50
            normalized_grade = (grade_level / 20) * 50
            
            return normalized_flesch + normalized_grade
        except Exception:
            return 50.0

    def _extract_linguistic_features(self, doc) -> Dict:
        return {
            "verbs": [token.text for token in doc if token.pos_ == "VERB"],
            "nouns": [token.text for token in doc if token.pos_ == "NOUN"],
            "adjectives": [token.text for token in doc if token.pos_ == "ADJ"],
            "dependencies": [f"{token.text}:{token.dep_}" for token in doc],
            "has_questions": any(token.text.lower() in ["what", "why", "how", "when", "where", "who"] 
                               for token in doc)
        }

    def _calculate_coherence(self, sentences: List[str]) -> float:
        try:
            if len(sentences) < 2:
                return 1.0
                
            embeddings = self.semantic_model.encode(sentences)
            
            coherence_scores = []
            for i in range(len(embeddings) - 1):
                similarity = np.dot(embeddings[i], embeddings[i+1]) / \
                           (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i+1]))
                coherence_scores.append(similarity)
                
            return float(np.mean(coherence_scores))
        except Exception:
            return 0.5

    def _create_fallback_context(self) -> Dict:
        """Create fallback context enhancement results"""
        return {
            "semantic_features": {
                "embedding_dim": 384,
                "semantic_complexity": 0.5,
                "related_concepts": []
            },
            "structural_features": {
                "sentence_complexities": [50.0],
                "avg_sentence_complexity": 50.0,
                "coherence_score": 0.5
            }
        }
    

class ResponseValidator:
    """Validate and process API responses"""
    
    @staticmethod
    def validate_response(response: Dict, expected_fields: List[str]) -> Tuple[bool, str]:
        """Validate API response structure"""
        try:
            if not isinstance(response, dict):
                return False, "Response is not a dictionary"

            # Check for error indicators
            if response.get("is_error"):
                return False, f"Response contains error: {response.get('error', 'Unknown error')}"

            # Validate required fields
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"

            return True, "Response validation successful"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def clean_response(response: Dict) -> Dict:
        """Clean and normalize API response"""
        cleaned = {}
        
        # Handle nested structures
        for key, value in response.items():
            if isinstance(value, dict):
                cleaned[key] = ResponseValidator.clean_response(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    ResponseValidator.clean_response(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Convert None to empty string/list/dict based on context
                if value is None:
                    if key.endswith(('list', 'array', 'items')):
                        cleaned[key] = []
                    elif key.endswith(('dict', 'map')):
                        cleaned[key] = {}
                    else:
                        cleaned[key] = ""
                else:
                    cleaned[key] = value
                    
        return cleaned




class APIHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.retry_count = 3
        self.base_delay = 1  # Base delay in seconds

    def make_api_call(self, system_message: str, prompt: str, context: Dict = None, **params) -> Dict:
        """
        Enhanced API call handler with retry logic and comprehensive error handling.
        
        Args:
            system_message: The system context message
            prompt: The user prompt
            context: Optional context dictionary
            **params: Additional API parameters
        
        Returns:
            Dict containing the parsed API response
        """
        for attempt in range(self.retry_count):
            try:
                # Construct messages array
                messages = [
                    {"role": "system", "content": system_message}
                ]
                
                # Add context if provided
                if context:
                    context_message = self._format_context(context)
                    messages.append({
                        "role": "system",
                        "content": context_message
                    })
                
                # Add user prompt
                messages.append({"role": "user", "content": prompt})
                
                # Prepare request data with defaults
                request_data = {
                    "messages": messages,
                    "model": "llama3.2-1b",
                    "max_tokens": 2000,
                    "stream": False,
                    **params  # Override defaults with provided parameters
                }
                
                # Log request for debugging
                self.logger.debug(f"API Request (Attempt {attempt + 1}):")
                self.logger.debug(json.dumps(request_data, indent=2))
                
                # Make the API call
                response = llama.run(request_data)
                
                # Validate response
                if not response:
                    raise ValueError("Empty response received from API")
                
                # Parse response JSON
                response_data = response.json()
                
                # Log raw response for debugging
                self.logger.debug("Raw API Response:")
                self.logger.debug(json.dumps(response_data, indent=2))
                
                # Validate response structure
                if not isinstance(response_data, dict):
                    raise ValueError(f"Invalid response type: {type(response_data)}")
                
                if 'choices' not in response_data:
                    raise ValueError("Missing 'choices' in response")
                
                if not response_data['choices']:
                    raise ValueError("Empty choices array in response")
                
                content = response_data['choices'][0].get('message', {}).get('content')
                if not content:
                    raise ValueError("No content in response")
                
                # Try to parse the content as JSON
                try:
                    parsed_content = json.loads(content)
                    return parsed_content
                except json.JSONDecodeError as json_err:
                    # If content isn't valid JSON, wrap it in a standard structure
                    self.logger.warning(f"Content not valid JSON: {json_err}")
                    return {
                        "raw_response": content,
                        "error": None,
                        "is_raw": True
                    }
                
            except Exception as e:
                self.logger.error(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.retry_count - 1:
                    # Calculate exponential backoff delay
                    delay = self.base_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Final attempt failed, return error response
                    error_response = {
                        "error": str(e),
                        "is_error": True,
                        "stage": "api_call",
                        "details": {
                            "attempt": attempt + 1,
                            "system_message": system_message[:100] + "..." if len(system_message) > 100 else system_message,
                            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
                        }
                    }
                    return error_response

    def _format_context(self, context: Dict) -> str:
        """
        Format context dictionary into a clear string representation.
        
        Args:
            context: Dictionary containing context information
            
        Returns:
            Formatted context string
        """
        try:
            # Remove any potentially problematic nested structures
            cleaned_context = {
                k: str(v) if isinstance(v, (dict, list)) else v
                for k, v in context.items()
            }
            
            # Format as readable string
            context_parts = [
                f"{key}: {value}"
                for key, value in cleaned_context.items()
            ]
            
            return "\n".join([
                "Context Information:",
                "-------------------",
                *context_parts,
                "-------------------"
            ])
            
        except Exception as e:
            self.logger.error(f"Error formatting context: {str(e)}")
            return "Error formatting context"

class SystemMessageGenerator:
    def __init__(self):
        self.task_templates = {
            "analytical": """You are an analytical prompt expert focused on {ai_type}.
Key objectives:
- Break down complex requirements
- Identify core components
- Optimize for clarity and precision
Current task context: {context}""",
            
            "creative": """You are a creative prompt engineering specialist for {ai_type}.
Focus areas:
- Generate innovative approaches
- Maintain engagement
- Enhance expression quality
Task context: {context}""",
            
            "technical": """You are a technical prompt optimization expert for {ai_type}.
Primary goals:
- Maximize technical accuracy
- Ensure implementation feasibility
- Optimize for performance
Technical context: {context}"""
        }
    
    def generate_system_message(self, 
                              prompt_analysis: Dict[Any, Any],
                              ai_type: str,
                              style: str) -> str:
        """Generate dynamic system message based on analysis"""
        
        # Determine message type based on analysis
        if prompt_analysis['complexity_score'] < 50:
            template = self.task_templates['technical']
        elif any(entity[1] in ['DATE', 'NUMBER', 'QUANTITY'] 
                for entity in prompt_analysis['named_entities']):
            template = self.task_templates['analytical']
        else:
            template = self.task_templates['creative']
            
        # Create context summary
        context = {
            "keywords": prompt_analysis['keywords'],
            "sentiment": prompt_analysis['sentiment'],
            "style_requirements": style
        }
        
        return template.format(
            ai_type=ai_type,
            context=json.dumps(context, indent=2)
        )

# class ResponseHandler:
#     def __init__(self, logger):
#         self.logger = logger
#         self.prompt_enhancer = PromptEnhancer(logger)
#     def clean_guidelines_response(self, content: str) -> str:
#         """Clean JSON for guidelines response with handling for extra fields"""
#         try:
#             self.logger.debug("=== Guidelines Content Cleaning Start ===")
#             self.logger.debug(f"Original content: {content}")
            
#             if not isinstance(content, str):
#                 content = json.dumps(content)

#             try:
#                 # First try to parse the existing content
#                 parsed = json.loads(content)
                
#                 # Create a new object with only the required fields
#                 cleaned_data = {
#                     "request_analysis": parsed.get("request_analysis", {}),
#                     "technical_assessment": parsed.get("technical_assessment", {}),
#                     "guidelines": parsed.get("guidelines", ""),
#                     "parameters": {
#                         "value": {
#                             "temperature": {"value": -1, "reasoning": "Default value"},
#                             "top_p": {"value": -1, "reasoning": "Default value"},
#                             "presence_penalty": {"value": -1, "reasoning": "Default value"},
#                             "frequency_penalty": {"value": -1, "reasoning": "Default value"}
#                         }
#                     }
#                 }
                
#                 # Ensure required fields exist in nested structures
#                 if "request_analysis" in cleaned_data:
#                     request_analysis = cleaned_data["request_analysis"]
#                     if not isinstance(request_analysis, dict):
#                         request_analysis = {}
#                     cleaned_data["request_analysis"] = {
#                         "primary_goal": request_analysis.get("primary_goal", ""),
#                         "context": request_analysis.get("context", ""),
#                         "requirements": request_analysis.get("requirements", [])
#                     }
                
#                 if "technical_assessment" in cleaned_data:
#                     tech_assessment = cleaned_data["technical_assessment"]
#                     if not isinstance(tech_assessment, dict):
#                         tech_assessment = {}
#                     cleaned_data["technical_assessment"] = {
#                         "complexity_level": tech_assessment.get("complexity_level", "Medium"),
#                         "key_components": tech_assessment.get("key_components", [])
#                     }
                
#                 # Convert back to JSON string
#                 return json.dumps(cleaned_data)
                
#             except json.JSONDecodeError as e:
#                 self.logger.error(f"Initial JSON parsing failed: {str(e)}")
#                 # If parsing fails, try to clean up the content first
                
#                 # Remove newlines and extra whitespace
#                 content = re.sub(r'\s+', ' ', content).strip()
                
#                 # Remove any trailing commas
#                 content = re.sub(r',\s*([}\]])', r'\1', content)
                
#                 # Balance braces
#                 open_count = content.count('{')
#                 close_count = content.count('}')
#                 if open_count > close_count:
#                     content += '}' * (open_count - close_count)
                
#                 try:
#                     # Try parsing again after cleanup
#                     parsed = json.loads(content)
#                     return self.clean_guidelines_response(parsed)
#                 except json.JSONDecodeError:
#                     self.logger.error("Failed to parse JSON even after cleaning")
#                     return json.dumps(self.get_default_response())
                    
#         except Exception as e:
#             self.logger.error(f"Error in guidelines cleaning: {str(e)}")
#             return json.dumps(self.get_default_response())



#     def clean_prompts_response(self, content: str) -> str:
#         """Clean JSON for prompts response (second API call)"""
#         try:
#             self.logger.debug("=== Prompts Content Cleaning Start ===")
#             self.logger.debug(f"Original content: {content}")
            
#             if not isinstance(content, str):
#                 content = json.dumps(content)
                
#             # Find the first occurrence of a JSON-like structure
#             json_start = content.find('{')
#             if json_start != -1:
#                 content = content[json_start:]
#                 # Find the last closing brace
#                 json_end = content.rfind('}')
#                 if json_end != -1:
#                     content = content[:json_end + 1]

#             # Remove any whitespace
#             content = content.strip()
            
#             # Validate the JSON structure
#             try:
#                 parsed = json.loads(content)
#                 if 'prompts' not in parsed or not isinstance(parsed['prompts'], list):
#                     raise ValueError("Missing or invalid 'prompts' array")
#                 return json.dumps(parsed)
#             except json.JSONDecodeError as e:
#                 self.logger.error(f"Prompts JSON validation failed: {str(e)}")
#                 raise
                
#         except Exception as e:
#             self.logger.error(f"Error in prompts cleaning: {str(e)}")
#             raise
    
#     # def get_parameter_values(self, parameters: Dict) -> Dict:
#     #     """Extract just the parameter values for easy access."""
#     #     try:
#     #         if not parameters or 'value' not in parameters:
#     #             return self.get_default_parameter_values()
                
#     #         param_dict = parameters['value']
#     #         return {
#     #             'temperature': param_dict['temperature']['value'],
#     #             'top_p': param_dict['top_p']['value'],
#     #             'presence_penalty': param_dict['presence_penalty']['value'],
#     #             'frequency_penalty': param_dict['frequency_penalty']['value']
#     #         }
#     #     except Exception as e:
#     #         self.logger.error(f"Error extracting parameter values: {str(e)}")
#     #         return self.get_default_parameter_values()
    
#     def get_default_parameter_values(self) -> Dict:
#         """Get default parameter values."""
#         return {
#             'temperature': 0.5,
#             'top_p': 0.8,
#             'presence_penalty': 0.0,
#             'frequency_penalty': 0.0
#         }
#     def clean_json_string(self, content: str) -> str:
#         """Clean and fix JSON string from Llama API."""
#         try:
#             if not isinstance(content, str):
#                 content = json.dumps(content)
            
#             # Remove any trailing commas before closing braces
#             content = re.sub(r',(\s*})', r'\1', content)
#             # Add missing commas between objects
#             content = re.sub(r'}(\s*){', r'},\1{', content)
#             # Remove multiple closing braces
#             content = re.sub(r'}}+', r'}', content)
#             # Ensure proper object closure
#             open_braces = content.count('{')
#             close_braces = content.count('}')
#             if open_braces > close_braces:
#                 content += '}' * (open_braces - close_braces)
                
#             # Validate the cleaned JSON
#             json.loads(content)
#             return content
#         except Exception as e:
#             self.logger.error(f"Error cleaning JSON string: {str(e)}")
#             return json.dumps(self.get_default_response())

#     def fix_parameter_structure(self, params: Dict) -> Dict:
#         """Fix the nested parameter structure from Llama API response."""
#         try:
#             # Define default parameters
#             fixed_params = {
#                 "temperature": {"value": 0.5, "reasoning": "Default value for balanced output"},
#                 "top_p": {"value": 0.8, "reasoning": "Default value for diverse sampling"},
#                 "presence_penalty": {"value": 0.0, "reasoning": "Default value for neutral presence"},
#                 "frequency_penalty": {"value": 0.0, "reasoning": "Default value for neutral frequency"}
#             }

#             if not params:
#                 return {"value": fixed_params}

#             # Get the value, handling different structures
#             param_values = params.get('value', params)
            
#             if isinstance(param_values, dict):
#                 # Handle different parameter formats
#                 for key, value in param_values.items():
#                     if isinstance(value, dict) and key in fixed_params:
#                         # Direct parameter object
#                         fixed_params[key] = value
#                     elif isinstance(value, dict) and any(k in value for k in fixed_params):
#                         # Nested parameter object
#                         for param_name, param_data in value.items():
#                             if param_name in fixed_params:
#                                 fixed_params[param_name] = param_data
#             elif isinstance(param_values, list):
#                 # Handle list format
#                 for item in param_values:
#                     if isinstance(item, dict):
#                         for key, value in item.items():
#                             if key in fixed_params:
#                                 fixed_params[key] = value

#             # Ensure all parameters have the correct structure
#             for key in fixed_params:
#                 if not isinstance(fixed_params[key], dict) or 'value' not in fixed_params[key]:
#                     fixed_params[key] = {
#                         "value": fixed_params[key] if isinstance(fixed_params[key], (int, float)) else 0.0,
#                         "reasoning": "Converted to standard format"
#                     }

#             self.logger.info(f"Fixed parameters structure: {fixed_params}")
#             return {"value": fixed_params}

#         except Exception as e:
#             self.logger.error(f"Error fixing parameter structure: {str(e)}")
#             return {"value": {
#                 "temperature": {"value": 0.5, "reasoning": "Default due to error"},
#                 "top_p": {"value": 0.8, "reasoning": "Default due to error"},
#                 "presence_penalty": {"value": 0.0, "reasoning": "Default due to error"},
#                 "frequency_penalty": {"value": 0.0, "reasoning": "Default due to error"}
#             }}

#     def validate_and_fix_llama_response(self, content: str, response_type: str = 'guidelines'):
#         """Validate and fix JSON response with nested structure handling"""
#         try:
#             # Convert dict to string if needed
#             if isinstance(content, dict):
#                 content = json.dumps(content)
            
#             # Use PromptEnhancer's cleaning method
#             cleaned_content = self.prompt_enhancer._clean_json_content(content)
#             parsed_content = json.loads(cleaned_content)
            
#             if response_type == 'guidelines':
#                 # Check if content is nested in raw_analysis
#                 if 'raw_analysis' in parsed_content:
#                     analysis_content = parsed_content['raw_analysis']
#                 else:
#                     analysis_content = parsed_content

#                 # Required keys for guidelines
#                 required_keys = ["request_analysis", "technical_assessment", "guidelines", "parameters"]
                
#                 # Check for required keys at different levels
#                 if all(key in analysis_content for key in required_keys):
#                     return analysis_content
#                 elif all(key in parsed_content for key in required_keys):
#                     return parsed_content
#                 else:
#                     # Log specific missing keys for debugging
#                     missing_keys = [key for key in required_keys if key not in analysis_content]
#                     self.logger.error(f"Missing required keys in guidelines response: {missing_keys}")
#                     return self.get_default_response()
                        
#             elif response_type == 'prompts':
#                 # Handle prompts validation
#                 if 'prompts' in parsed_content:
#                     # Ensure prompts is a list and not empty
#                     if isinstance(parsed_content['prompts'], list) and parsed_content['prompts']:
#                         # Additional validation for each prompt
#                         validated_prompts = []
#                         for prompt in parsed_content['prompts']:
#                             if isinstance(prompt, dict) and 'prompt' in prompt:
#                                 validated_prompts.append(prompt)
                        
#                         # Return validated prompts or fallback
#                         return {'prompts': validated_prompts} if validated_prompts else \
#                             {'prompts': [{'prompt': 'Error processing response'}]}
#                     else:
#                         self.logger.error("Invalid or empty prompts array")
#                         return {'prompts': [{'prompt': 'Error processing response'}]}
#                 else:
#                     self.logger.error("Missing prompts array")
#                     return {'prompts': [{'prompt': 'Error processing response'}]}
                
#             # Fallback for unhandled response types
#             return parsed_content
                
#         except json.JSONDecodeError as json_err:
#             # Specific handling for JSON decoding errors
#             self.logger.error(f"JSON Decoding Error: {json_err}")
#             return (self.get_default_response() if response_type == 'guidelines' 
#                     else {'prompts': [{'prompt': 'Error processing response'}]})

#     def get_default_response(self) -> Dict:
#         """Return a default response structure"""
#         return {
#             "request_analysis": {
#                 "primary_goal": "Task organization and time management",
#                 "context": "Optimize task scheduling and prioritization",
#                 "requirements": ["Create effective plan", "Consider task priorities"]
#             },
#             "technical_assessment": {
#                 "complexity_level": "Medium",
#                 "key_components": ["Task management", "Time allocation"]
#             },
#             "guidelines": "Follow structured approach for task management",
#             "parameters": {
#                 "value": {
#                     "temperature": {"value": -1, "reasoning": "Default value"},
#                     "top_p": {"value": -1, "reasoning": "Default value"},
#                     "presence_penalty": {"value": -1, "reasoning": "Default value"},
#                     "frequency_penalty": {"value": -1, "reasoning": "Default value"}
#                 }
#             }
#         }

class PipelineStage:
    """Base class for pipeline stages with common functionality"""
    def __init__(self, logger: Logger):
        self.logger = logger

    def validate_output(self, output: Dict, required_fields: List[str]) -> bool:
        """Common validation for stage outputs"""
        try:
            if not isinstance(output, dict):
                self.logger.error(f"Output is not a dictionary: {type(output)}")
                return False
                
            missing_fields = [field for field in required_fields if field not in output]
            if missing_fields:
                self.logger.error(f"Missing required fields: {missing_fields}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False


class PipelineContext:
    def __init__(self, original_prompt: str, ai_type: str, style: str):
        self.context = {
            "original_prompt": original_prompt,
            "ai_type": ai_type,
            "style": style,
            "timestamp": datetime.datetime.now().isoformat(),
            "execution_context": {
                "stage_results": {},
                "errors": [],
                "warnings": []
            },
            "parameters": self._get_default_parameters()
        }

    def _get_default_parameters(self) -> Dict:
        return {
            "temperature": {"value": 0.7, "reasoning": "Default balanced temperature"},
            "top_p": {"value": 0.9, "reasoning": "Default sampling diversity"},
            "presence_penalty": {"value": 0.0, "reasoning": "Default presence penalty"},
            "frequency_penalty": {"value": 0.0, "reasoning": "Default frequency penalty"}
        }
    
    def get_context(self) -> Dict:
        """Get complete pipeline context"""
        return self.context

    def update_stage_result(self, stage_name: str, result: Dict):
        """Update results for a specific stage"""
        if "stage_results" not in self.context["execution_context"]:
            self.context["execution_context"]["stage_results"] = {}
        self.context["execution_context"]["stage_results"][stage_name] = result

    def get_stage_result(self, stage_name: str) -> Dict:
        """Get results for a specific stage"""
        return self.context["execution_context"]["stage_results"].get(stage_name, {})

    def update_parameters(self, parameters: Dict):
        """Validate and update parameters with bounds checking"""
        param_bounds = {
            "temperature": (0.1, 1.0),
            "top_p": (0.1, 1.0), 
            "presence_penalty": (-2.0, 2.0),
            "frequency_penalty": (-2.0, 2.0)
        }

        validated_params = {}
        for param_name, bounds in param_bounds.items():
            try:
                param_data = parameters.get(param_name, {})
                if isinstance(param_data, dict):
                    value = float(param_data.get('value', self._get_default_parameters()[param_name]['value']))
                else:
                    value = float(param_data)

                min_val, max_val = bounds
                clamped_value = max(min_val, min(max_val, value))
                
                if clamped_value != value:
                    self.add_warning("parameters", 
                        f"Parameter {param_name} adjusted from {value} to {clamped_value}")

                validated_params[param_name] = {
                    "value": clamped_value,
                    "reasoning": param_data.get('reasoning', "Automatically adjusted")
                }

            except (TypeError, ValueError) as e:
                self.add_error("parameters", f"Invalid {param_name} value: {str(e)}")
                validated_params[param_name] = self._get_default_parameters()[param_name]

        self.context["parameters"] = validated_params

    def get_api_parameters(self) -> Dict:
        """Extract clean parameters for API calls"""
        return {
            name: data["value"] 
            for name, data in self.context["parameters"].items()
        }
    
    def add_error(self, stage_name: str, error: str):
        """Add error information"""
        if "errors" not in self.context["execution_context"]:
            self.context["execution_context"]["errors"] = []
            
        self.context["execution_context"]["errors"].append({
            "stage": stage_name,
            "error": error,
            "timestamp": datetime.datetime.now().isoformat()
        })

    def add_warning(self, stage_name: str, warning: str):
        """Add warning information"""
        if "warnings" not in self.context["execution_context"]:
            self.context["execution_context"]["warnings"] = []
            
        self.context["execution_context"]["warnings"].append({
            "stage": stage_name,
            "warning": warning,
            "timestamp": datetime.datetime.now().isoformat()
        })

# First, let's enhance the Analysis Stage to better handle context and AI-style requirements
class AnalysisStage(PipelineStage):

    def __init__(self, logger: Logger, api_handler: APIHandler):
        PipelineStage.__init__(self, logger)
        self.api_handler = api_handler
        self.required_fields = ["intent", "requirements", "context"]

    def execute(self, prompt: str, ai_type: str, style: str) -> Dict:
        """Enhanced analysis stage with deeper context understanding"""
        try:
            # Perform initial preprocessing
            preprocessor = PromptPreprocessor()
            prompt_analysis = preprocessor.analyze_prompt(prompt)
            
            system_message = f"""You are an AI-focused analysis expert specializing in {ai_type} systems.
            Analyze the user request to create an AI-relevant actionable prompt.
            Consider the requested {style} style in your analysis."""
            
            analysis_prompt = f"""
            Perform a comprehensive analysis of this request:
            
            Original Request: {prompt}
            Target AI System: {ai_type}
            Required Style: {style}
            
            Provide a structured analysis including:
            1. Core Intent Analysis:
                - Primary objective
                - Implicit requirements
                - Success criteria
            
            2. AI Relevance Analysis:
                - {ai_type}-specific considerations
                - Technical requirements
                - Implementation challenges
            
            3. Style Integration:
                - {style} style requirements
                - Tone and approach adaptations
                - Format considerations
            
            4. Context Mapping:
                - Domain-specific elements
                - Technical constraints
                - User expectations
            
            Return analysis in JSON format with these fields:
            {{
                "intent": {{
                    "primary_objective": "string",
                    "implicit_requirements": ["string"],
                    "success_criteria": ["string"]
                }},
                "requirements": ["string"],
                "context": {{
                    "time_aspects": ["string"],
                    "task_aspects": ["string"],
                    "user_expectations": ["string"]
                }}
            }}"""
            
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=analysis_prompt,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Enhanced error handling
            if response.get("is_error"):
                self.logger.warning(f"API call failed, using fallback analysis. Error: {response.get('error')}")
                return self._create_fallback_analysis(prompt, ai_type, style)
            
            # Ensure response has required fields
            if not all(field in response for field in self.required_fields):
                self.logger.warning("API response missing required fields, using fallback analysis")
                return self._create_fallback_analysis(prompt, ai_type, style)
            
            # Enhance response with preprocessing insights
            response["preprocessing"] = {
                "complexity": prompt_analysis.get("complexity_score"),
                "keywords": prompt_analysis.get("keywords"),
                "entities": prompt_analysis.get("named_entities")
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}")
            return self._create_fallback_analysis(prompt, ai_type, style)
        
    def _create_fallback_analysis(self, prompt: str, ai_type: str, style: str) -> Dict:
        """Create a fallback analysis when the main analysis process fails."""
        return {
            "intent": {
                "primary_objective": "Organize and manage tasks effectively",
                "implicit_requirements": [
                    "Clear task prioritization",
                    "Efficient time allocation",
                    "Progress tracking"
                ],
                "success_criteria": [
                    "Tasks are well-organized",
                    "Time is efficiently allocated",
                    "Goals are achievable"
                ]
            },
            "requirements": [
                "Task list creation",
                "Time estimation",
                "Priority setting",
                "Schedule management"
            ],
            "context": {
                "time_aspects": ["Duration estimation", "Scheduling"],
                "task_aspects": ["Organization", "Prioritization"],
                "user_expectations": ["Clear guidance", "Practical steps"]
            }
        }

class FeedbackStage(PipelineStage):

    def __init__(self, logger: Logger, api_handler: APIHandler):
        PipelineStage.__init__(self, logger)  # Use direct parent class call
        self.api_handler = api_handler
        self.required_fields = ["feedback", "improvements", "suggestions"]

    def _create_fallback_feedback(self, pipeline_context: Dict) -> Dict:
        return {
            "feedback": {
                "accuracy_assessment": "Unable to assess",
                "completeness_review": "Unable to review",
                "platform_alignment": "Unable to evaluate",
                "style_evaluation": "Unable to evaluate"
            },
            "improvements": ["Default improvement suggestion"],
            "suggestions": {
                "content": [],
                "structure": [],
                "style": []
            }
        }

    def execute(self, analysis: Dict, pipeline_context: Dict) -> Dict:
        """Enhanced feedback stage with comparative analysis"""
        try:
            system_message = """You are a prompt evaluation specialist.
            Compare the initial analysis with the original request to ensure alignment and completeness."""
            
            feedback_prompt = f"""
            Perform a comparative analysis:
            
            Original Request: {pipeline_context['original_prompt']}
            Initial Analysis: {json.dumps(analysis, indent=2)}
            
            Evaluate the following aspects:
            1. Intent Alignment
                - Does the analysis capture the true intent?
                - Are there missing aspects?
            
            2. Technical Completeness
                - Are all technical requirements identified?
                - Is the {pipeline_context['ai_type']} context properly considered?
            
            3. Style Adherence
                - Does it maintain {pipeline_context['style']} style requirements?
                - Are there style-specific gaps?
            
            4. Implementation Viability
                - Are the identified approaches feasible?
                - What potential challenges are missing?
            
            Provide structured feedback in JSON format:
            {{
                "alignment_analysis": {{
                    "matches": [],
                    "gaps": [],
                    "recommendations": []
                }},
                "completeness_check": {{
                    "covered_aspects": [],
                    "missing_elements": [],
                    "suggestions": []
                }},
                "improvement_areas": []
            }}"""
            
            return self.api_handler.make_api_call(
                system_message=system_message,
                prompt=feedback_prompt,
                temperature=0.4
            )
            
        except Exception as e:
            self.logger.error(f"Feedback stage failed: {str(e)}")
            return self._create_fallback_feedback(pipeline_context)

class GuidelinesStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler):
        PipelineStage.__init__(self, logger)
        self.api_handler = api_handler
        self.required_fields = ["guidelines", "parameters", "implementation_notes"]
    
    def _create_fallback_guidelines(self, pipeline_context: PipelineContext) -> Dict:
        """
        Create a fallback set of guidelines when the primary generation fails.
        
        This method provides a generic but structured set of guidelines that 
        can still offer value to the user.
        """
        return {
            "guidelines": """Generic Time Management Guidelines:
1. Prioritize Tasks
   - Use the Eisenhower Matrix to classify tasks
   - Focus on high-impact, urgent activities first

2. Break Down Complex Tasks
   - Divide large tasks into smaller, manageable steps
   - Set clear, achievable milestones

3. Time Blocking Technique
   - Allocate specific time slots for different task types
   - Include buffer time between tasks
   - Protect your most productive hours for critical work

4. Regular Review and Adjustment
   - Conduct daily and weekly task reviews
   - Be flexible and adapt your schedule as needed
   - Track progress and identify improvement areas
""",
            "parameters": {
                "temperature": {"value": 0.7, "reasoning": "Balanced approach to generate guidelines"},
                "top_p": {"value": 0.9, "reasoning": "Allow diverse guideline generation"},
                "presence_penalty": {"value": 0.0, "reasoning": "Neutral presence to maintain consistency"},
                "frequency_penalty": {"value": 0.0, "reasoning": "No penalty to allow natural language flow"}
            },
            "implementation_notes": {
                "critical_considerations": [
                    "Maintain flexibility in time management",
                    "Customize approach to personal working style",
                    "Continuous learning and adaptation"
                ],
                "success_criteria": [
                    "Improved task completion rate",
                    "Reduced stress and better work-life balance",
                    "Increased productivity and focus"
                ]
            }
        }

    def execute(self, pipeline_context: PipelineContext) -> Dict:
        """
        Generate comprehensive guidelines based on the pipeline context.
        
        This method integrates insights from previous stages to create 
        context-aware implementation guidelines.
        """
        try:
            # Extract context from previous pipeline stages
            analysis_result = pipeline_context.get_stage_result("analysis")
            feedback_result = pipeline_context.get_stage_result("feedback")
            
            # Prepare system message with contextual understanding
            system_message = f"""You are a guidelines generation expert for {pipeline_context.context['ai_type']} systems.
            Create comprehensive, actionable guidelines that address the user's time management needs.
            Consider the {pipeline_context.context['style']} style and previous analysis insights."""

            # Construct a detailed prompt for guidelines generation
            guidelines_prompt = f"""Generate comprehensive guidelines based on:

Original Request: {pipeline_context.context['original_prompt']}
AI Type: {pipeline_context.context['ai_type']}
Style: {pipeline_context.context['style']}

Previous Analysis:
{json.dumps(analysis_result, indent=2)}

Feedback Insights:
{json.dumps(feedback_result, indent=2)}

Required Output Structure:
1. Detailed Guidelines (Markdown format)
2. Suggested Parameters
3. Implementation Notes
4. Critical Considerations
5. Success Criteria

Emphasize:
- Practical, actionable steps
- Alignment with {pipeline_context.context['ai_type']} context
- {pipeline_context.context['style']} communication style"""

            # Make API call to generate guidelines
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=guidelines_prompt,
                pipeline_context=pipeline_context,
                temperature=0.4  # Slightly lower for more focused output
            )

            # Validate response
            if response.get("is_error"):
                self.logger.warning(f"Guidelines generation failed. Error: {response.get('error')}")
                return self._create_fallback_guidelines(pipeline_context)

            # Check for required fields
            if not all(field in response for field in self.required_fields):
                self.logger.warning("Generated guidelines missing required fields")
                return self._create_fallback_guidelines(pipeline_context)

            return response

        except Exception as e:
            self.logger.error(f"Guidelines stage failed: {str(e)}")
            return self._create_fallback_guidelines(pipeline_context)

    def _create_system_message(self) -> str:
        return """Generate detailed implementation guidelines based on analysis and feedback."""
        
    def _create_guidelines_prompt(self, pipeline_context: Dict) -> str:
        guidelines_template = {
            "guidelines": {
                "implementation_approach": "",
                "platform_requirements": [],
                "style_guidelines": []
            },
            "parameters": self._get_default_parameters(),
            "implementation_notes": {
                "critical_considerations": [],
                "success_criteria": []
            }
        }
        return f"Generate guidelines based on:\n{json.dumps(pipeline_context, indent=2)}\n\nUse format:\n{json.dumps(guidelines_template, indent=2)}"

    def _get_default_parameters(self) -> Dict:
        return {
            "temperature": {"value": 0.7, "reasoning": "Default"},
            "top_p": {"value": 0.9, "reasoning": "Default"},
            "presence_penalty": {"value": 0.0, "reasoning": "Default"},
            "frequency_penalty": {"value": 0.0, "reasoning": "Default"}
        }

# class EnhancementStage(PipelineStage):

#     def __init__(self, logger: Logger, api_handler: APIHandler):
#         PipelineStage.__init__(self, logger)
#         self.api_handler = api_handler
#         self.required_fields = ["prompts"]
#     def _create_system_message(self) -> str:
#         return """Generate enhanced versions of the original prompt."""
        
#     def _create_enhancement_prompt(self, pipeline_context: Dict) -> str:
#         return f"""Generate three optimized versions of: {pipeline_context['original_prompt']}
# Based on: {json.dumps(pipeline_context['guidelines'], indent=2)}"""

#     def _extract_parameters(self, guidelines: Dict) -> Dict:
#         default_params = {
#             "temperature": 0.7,
#             "top_p": 0.9,
#             "presence_penalty": 0.0,
#             "frequency_penalty": 0.0
#         }
#         return guidelines.get("parameters", default_params)


class EnhancementStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler):
        PipelineStage.__init__(self, logger)
        self.api_handler = api_handler
        self.required_fields = ["prompts"]

    def _create_fallback_enhanced_prompts(self, pipeline_context: PipelineContext) -> Dict:
        """
        Generate fallback enhanced prompts when the primary enhancement process fails.
        
        This method provides a structured set of prompts that maintain the core 
        intent of the original request while offering different perspectives.
        """
        original_prompt = pipeline_context.context['original_prompt']
        ai_type = pipeline_context.context['ai_type']
        style = pipeline_context.context['style']

        return {
            "prompts": [
                {
                    "prompt": f"Develop a comprehensive time management strategy for {original_prompt}, " +
                              f"focusing on systematic task organization and prioritization in a {style} approach.",
                    "focus": "Systematic Approach",
                    "perspective": "Structured and methodical time management"
                },
                {
                    "prompt": f"Create a flexible time management framework for {original_prompt}, " +
                              f"emphasizing adaptability and personal efficiency in a {style} communication style.",
                    "focus": "Adaptive Strategy",
                    "perspective": "Dynamic and personalized time management"
                },
                {
                    "prompt": f"Design an advanced time tracking and optimization plan for {original_prompt}, " +
                              f"integrating productivity techniques tailored to {ai_type} workflow in a {style} format.",
                    "focus": "Optimization",
                    "perspective": "Data-driven and performance-oriented approach"
                }
            ]
        }

    def execute(self, pipeline_context: PipelineContext) -> Dict:
        """
        Generate enhanced prompts by leveraging insights from previous pipeline stages.
        
        This method creates multiple variations of the original prompt, each with a 
        unique focus and perspective, while maintaining the core intent.
        """
        try:
            # Retrieve insights from previous stages
            analysis_result = pipeline_context.get_stage_result("analysis")
            feedback_result = pipeline_context.get_stage_result("feedback")
            guidelines_result = pipeline_context.get_stage_result("guidelines")

            # Prepare the system message with context-aware instructions
            system_message = f"""You are a prompt enhancement expert specializing in {pipeline_context.context['ai_type']} systems.
            Generate multiple enhanced versions of the original prompt that:
            - Maintain the core intent
            - Provide different perspectives
            - Align with {pipeline_context.context['style']} communication style
            - Offer unique insights for time management"""

            # Create a comprehensive enhancement prompt
            enhancement_prompt = f"""Generate three distinct, enhanced versions of the original prompt:

Original Request: {pipeline_context.context['original_prompt']}
AI Type: {pipeline_context.context['ai_type']}
Style: {pipeline_context.context['style']}

Previous Analysis:
{json.dumps(analysis_result, indent=2)}

Feedback Insights:
{json.dumps(feedback_result, indent=2)}

Guidelines:
{json.dumps(guidelines_result, indent=2)}

Requirements for Enhanced Prompts:
1. Each prompt should address time management from a unique angle
2. Incorporate insights from previous pipeline stages
3. Maintain the core objective of the original request
4. Demonstrate {pipeline_context.context['style']} communication approach

Output Format:
{{
    "prompts": [
        {{
            "prompt": "Enhanced prompt version 1",
            "focus": "Specific focus area",
            "perspective": "Unique approach description"
        }},
        // Two more similar entries
    ]
}}"""

            # Make API call to generate enhanced prompts
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=enhancement_prompt,
                pipeline_context=pipeline_context,
                temperature=0.7  # Slightly higher to encourage creativity
            )

            # Validate the response
            if response.get("is_error"):
                self.logger.warning(f"Prompt enhancement failed. Error: {response.get('error')}")
                return self._create_fallback_enhanced_prompts(pipeline_context)

            # Ensure required fields are present
            if not all(field in response for field in self.required_fields):
                self.logger.warning("Generated enhanced prompts missing required fields")
                return self._create_fallback_enhanced_prompts(pipeline_context)

            return response

        except Exception as e:
            self.logger.error(f"Enhancement stage failed: {str(e)}")
            return self._create_fallback_enhanced_prompts(pipeline_context)

# class EnhancedPromptPipeline:
#     """Main pipeline coordinator with improved structure and error handling"""
#     def __init__(self, logger: Logger):
#         """Initialize pipeline components and dependencies"""
#         self.logger = logger
#         self.api_handler = APIHandler(logger)
        
#         # Initialize pipeline stages
#         self.analysis_stage = AnalysisStage(logger, self.api_handler)
#         self.feedback_stage = FeedbackStage(logger, self.api_handler)
#         self.guidelines_stage = GuidelinesStage(logger, self.api_handler)
#         self.enhancement_stage = EnhancementStage(logger, self.api_handler)
        
#         # Initialize support components
#         self.preprocessor = PromptPreprocessor()
#         self.system_message_gen = SystemMessageGenerator()

#     def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#         """
#         Execute the complete prompt enhancement pipeline with proper error handling and context management.
        
#         Args:
#             prompt: The original user prompt
#             ai_type: The type of AI system being targeted
#             style: The desired writing style
            
#         Returns:
#             Dict containing the complete pipeline results
#         """
#         try:
#             # Initialize pipeline context
#             pipeline_context = {
#                 "original_prompt": prompt,
#                 "ai_type": ai_type,
#                 "style": style,
#                 "execution_context": {
#                     "stage_results": {},
#                     "errors": [],
#                     "warnings": []
#                 }
#             }

#             # Stage 1: Analysis
#             analysis_result = self.analysis_stage.execute(prompt, ai_type, style)
#             pipeline_context["execution_context"]["stage_results"]["analysis"] = analysis_result

#             # Stage 2: Feedback
#             feedback_result = self.feedback_stage.execute(analysis_result, pipeline_context)
#             pipeline_context["execution_context"]["stage_results"]["feedback"] = feedback_result

#             # Stage 3: Guidelines
#             guidelines_result = self.guidelines_stage.execute(pipeline_context)
#             pipeline_context["execution_context"]["stage_results"]["guidelines"] = guidelines_result

#             # Stage 4: Enhancement
#             enhancement_result = self.enhancement_stage.execute(pipeline_context)

#             # Format and return final response
#             return self._format_final_response(pipeline_context, enhancement_result)

#         except Exception as e:
#             self.logger.error(f"Pipeline execution failed: {str(e)}")
#             return self._create_error_response(prompt, ai_type, style, str(e))

#     def _create_error_response(self, prompt: str, ai_type: str, style: str, error_msg: str) -> Dict:
#         """Create a structured error response"""
#         return {
#             "status": "error",
#             "error_message": error_msg,
#             "input_context": {
#                 "prompt": prompt,
#                 "ai_type": ai_type,
#                 "style": style
#             }
#         }

#     def _format_final_response(self, pipeline_context: Dict, enhancement_result: Dict) -> Dict:
#         """Format the final pipeline response with complete context"""
#         try:
#             return {
#                 "status": "success",
#                 "original_prompt": pipeline_context["original_prompt"],
#                 "enhanced_prompts": enhancement_result.get("prompts", []),
#                 "analysis_summary": {
#                     "intent": pipeline_context["execution_context"]["stage_results"].get("analysis", {}).get("intent", {}),
#                     "key_requirements": pipeline_context["execution_context"]["stage_results"].get("analysis", {}).get("requirements", []),
#                     "context_considerations": pipeline_context["execution_context"]["stage_results"].get("analysis", {}).get("context", {})
#                 },
#                 "guidelines": pipeline_context["execution_context"]["stage_results"].get("guidelines", {}).get("guidelines", ""),
#                 "parameters_used": pipeline_context["execution_context"]["stage_results"].get("guidelines", {}).get("parameters", {}),
#                 "metadata": {
#                     "ai_type": pipeline_context["ai_type"],
#                     "style": pipeline_context["style"],
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "pipeline_version": "2.0.0"
#                 }
#             }
#         except Exception as e:
#             self.logger.error(f"Response formatting failed: {str(e)}")
#             return self._create_error_response(
#                 pipeline_context["original_prompt"],
#                 pipeline_context["ai_type"],
#                 pipeline_context["style"],
#                 "Response formatting failed"
#             )
# class PipelineContext:
#     """Centralized context management for the pipeline"""
#     def __init__(self, original_prompt: str, ai_type: str, style: str):
#         self.context = {
#             "original_prompt": original_prompt,
#             "ai_type": ai_type,
#             "style": style,
#             "timestamp": datetime.datetime.now().isoformat(),
#             "execution_context": {
#                 "stage_results": {},
#                 "errors": [],
#                 "warnings": []
#             },
#             "parameters": ParameterManager.get_default_parameters()
#         }

#     def update_stage_result(self, stage_name: str, result: Dict):
#         """Update results for a specific stage"""
#         self.context["execution_context"]["stage_results"][stage_name] = result

#     def add_error(self, stage_name: str, error: str):
#         """Add error information"""
#         self.context["execution_context"]["errors"].append({
#             "stage": stage_name,
#             "error": error,
#             "timestamp": datetime.datetime.now().isoformat()
#         })

#     def add_warning(self, stage_name: str, warning: str):
#         """Add warning information"""
#         self.context["execution_context"]["warnings"].append({
#             "stage": stage_name,
#             "warning": warning,
#             "timestamp": datetime.datetime.now().isoformat()
#         })

#     def update_parameters(self, parameters: Dict):
#         """Update pipeline parameters"""
#         self.context["parameters"] = ParameterManager.validate_parameters(parameters)

#     def get_stage_result(self, stage_name: str) -> Dict:
#         """Get results for a specific stage"""
#         return self.context["execution_context"]["stage_results"].get(stage_name, {})

#     def get_context(self) -> Dict:
#         """Get complete context"""
#         return self.context


# class EnhancedPromptPipeline:
#     """Enhanced pipeline with improved error handling and context management"""
    
#     def __init__(self, logger: Logger):
#         self.logger = logger
#         self.api_handler = EnhancedAPIHandler(logger)
#         self.preprocessor = PromptPreprocessor()
        
#     def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#         """Execute the complete pipeline with enhanced error handling"""
#         pipeline_context = PipelineContext(prompt, ai_type, style)
        
#         try:
#             # Stage 1: Preprocessing and Analysis
#             analysis_result = self._execute_analysis_stage(pipeline_context)
#             pipeline_context.update_stage_result("analysis", analysis_result)
            
#             # Stage 2: Generate Guidelines
#             guidelines_result = self._execute_guidelines_stage(pipeline_context)
#             pipeline_context.update_stage_result("guidelines", guidelines_result)
            
#             # Stage 3: Parameter Optimization
#             self._optimize_parameters(pipeline_context)
            
#             # Stage 4: Generate Enhanced Prompts
#             enhancement_result = self._execute_enhancement_stage(pipeline_context)
#             pipeline_context.update_stage_result("enhancement", enhancement_result)
            
#             # Format final response
#             return self._format_final_response(pipeline_context)
            
#         except Exception as e:
#             self.logger.error(f"Pipeline execution failed: {str(e)}")
#             pipeline_context.add_error("pipeline", str(e))
#             return self._create_error_response(pipeline_context)

#     def _execute_analysis_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Execute analysis stage with enhanced API handling"""
#         try:
#             # Preprocess the prompt
#             prompt_analysis = self.preprocessor.analyze_prompt(
#                 pipeline_context.context["original_prompt"]
#             )
            
#             # Make API call with expected field validation
#             response = self.api_handler.make_api_call(
#                 system_message="Analyze the user request for prompt enhancement.",
#                 prompt=pipeline_context.context["original_prompt"],
#                 pipeline_context=pipeline_context,
#                 expected_fields=["intent", "requirements", "context"],
#                 temperature=0.3
#             )
            
#             # Handle potential API errors
#             if response.get("is_error"):
#                 pipeline_context.add_error("analysis", response.get("error"))
#                 return self._create_fallback_analysis()
            
#             return {
#                 "preprocessing": prompt_analysis,
#                 "analysis": response
#             }
            
#         except Exception as e:
#             self.logger.error(f"Analysis stage failed: {str(e)}")
#             pipeline_context.add_error("analysis", str(e))
#             return self._create_fallback_analysis()

#     def _execute_guidelines_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Execute guidelines stage with enhanced API handling"""
#         try:
#             analysis_result = pipeline_context.get_stage_result("analysis")
            
#             # Use enhanced API handler with field validation
#             response = self.api_handler.make_api_call(
#                 system_message="Generate implementation guidelines based on analysis.",
#                 prompt=json.dumps(analysis_result, indent=2),
#                 pipeline_context=pipeline_context,
#                 expected_fields=["guidelines", "parameters", "implementation_notes"],
#                 temperature=0.4
#             )
            
#             # Handle potential API errors
#             if response.get("is_error"):
#                 pipeline_context.add_error("guidelines", response.get("error"))
#                 return self._create_fallback_guidelines()
            
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Guidelines stage failed: {str(e)}")
#             pipeline_context.add_error("guidelines", str(e))
#             return self._create_fallback_guidelines()

#     def _optimize_parameters(self, pipeline_context: PipelineContext) -> None:
#         """Optimize parameters based on analysis and guidelines"""
#         try:
#             analysis_result = pipeline_context.get_stage_result("analysis")
#             guidelines_result = pipeline_context.get_stage_result("guidelines")
            
#             # Extract complexity and other metrics
#             complexity_score = analysis_result.get("preprocessing", {}).get("complexity_score", 50)
#             sentiment_score = analysis_result.get("preprocessing", {}).get("sentiment_score", 0.5)
            
#             # Adjust parameters based on analysis
#             optimized_params = {
#                 "temperature": {
#                     "value": 0.3 + (complexity_score / 100) * 0.4,  # Scale from 0.3 to 0.7
#                     "reasoning": "Adjusted based on complexity"
#                 },
#                 "top_p": {
#                     "value": 0.7 + (complexity_score / 100) * 0.2,  # Scale from 0.7 to 0.9
#                     "reasoning": "Adjusted based on complexity"
#                 },
#                 "presence_penalty": {
#                     "value": sentiment_score * 0.4,  # Scale from 0 to 0.4
#                     "reasoning": "Adjusted based on sentiment"
#                 },
#                 "frequency_penalty": {
#                     "value": (complexity_score / 100) * 0.3,  # Scale from 0 to 0.3
#                     "reasoning": "Adjusted based on complexity"
#                 }
#             }
            
#             pipeline_context.update_parameters(optimized_params)
            
#         except Exception as e:
#             self.logger.error(f"Parameter optimization failed: {str(e)}")
#             pipeline_context.add_warning("parameters", "Using default parameters due to optimization failure")

#     def _execute_enhancement_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Execute enhancement stage with error handling"""
#         try:
#             # Get optimized parameters
#             parameters = pipeline_context.context["parameters"]
            
#             # Make API call for enhanced prompts
#             response = self.api_handler.make_api_call(
#                 system_message="Generate enhanced versions of the original prompt.",
#                 prompt=pipeline_context.context["original_prompt"],
#                 pipeline_context=pipeline_context,
#                 expected_fields=["prompts"],
#                 **ParameterManager.extract_api_parameters(parameters)
#             )
            
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Enhancement stage failed: {str(e)}")
#             pipeline_context.add_error("enhancement", str(e))
#             return self._create_fallback_enhancement()

#     def _format_final_response(self, pipeline_context: PipelineContext) -> Dict:
#         """Format the final pipeline response"""
#         context = pipeline_context.get_context()
        
#         return {
#             "status": "success" if not context["execution_context"]["errors"] else "partial_success",
#             "original_prompt": context["original_prompt"],
#             "enhanced_prompts": context["execution_context"]["stage_results"].get("enhancement", {}).get("prompts", []),
#             "analysis_summary": {
#                 "intent": context["execution_context"]["stage_results"].get("analysis", {}).get("analysis", {}).get("intent", {}),
#                 "key_requirements": context["execution_context"]["stage_results"].get("analysis", {}).get("analysis", {}).get("requirements", []),
#                 "context_considerations": context["execution_context"]["stage_results"].get("analysis", {}).get("analysis", {}).get("context", {})
#             },
#             "guidelines": context["execution_context"]["stage_results"].get("guidelines", {}).get("guidelines", ""),
#             "parameters_used": context["parameters"],
#             "metadata": {
#                 "ai_type": context["ai_type"],
#                 "style": context["style"],
#                 "timestamp": context["timestamp"],
#                 "pipeline_version": "2.0.0",
#                 "warnings": context["execution_context"]["warnings"],
#                 "errors": context["execution_context"]["errors"]
#             }
#         }

#     def _create_error_response(self, pipeline_context: PipelineContext) -> Dict:
#         """Create error response when pipeline fails"""
#         context = pipeline_context.get_context()
        
#         return {
#             "status": "error",
#             "error_message": context["execution_context"]["errors"][-1]["error"] if context["execution_context"]["errors"] else "Unknown error",
#             "input_context": {
#                 "prompt": context["original_prompt"],
#                 "ai_type": context["ai_type"],
#                 "style": context["style"]
#             }
#         }

#     def _create_fallback_analysis(self) -> Dict:
#         """Create fallback analysis results"""
#         return {
#             "preprocessing": self.preprocessor._create_fallback_analysis(),
#             "enhanced_context": self.preprocessor._create_fallback_context(),
#             "analysis": {
#                 "intent": {
#                     "primary_objective": "Task completion",
#                     "implicit_requirements": ["Clarity", "Efficiency"],
#                     "success_criteria": ["Task completed", "Clear instructions"]
#                 },
#                 "requirements": [],
#                 "context": {}
#             }
#         }

#     def _create_fallback_guidelines(self) -> Dict:
#         """Create fallback guidelines results"""
#         return {
#             "guidelines": "Follow standard implementation practices",
#             "parameters": ParameterManager.get_default_parameters(),
#             "implementation_notes": {
#                 "critical_considerations": ["Maintain clarity", "Ensure completeness"],
#                 "success_criteria": ["Clear organization", "Effective communication"]
#             }
#         }

#     def _create_fallback_enhancement(self) -> Dict:
#         """Create fallback enhancement results"""
#         return {
#             "prompts": [
#                 {
#                     "prompt": "Basic version with core requirements",
#                     "version": "basic",
#                     "focus_areas": ["Core functionality"],
#                     "key_elements": ["Essential requirements"]
#                 }
#             ]
#         }




# the major primary pipeline stage 1
# class EnhancedPromptPipeline:
#     def __init__(self, logger: Logger):
#         self.logger = logger
#         self.api_handler = EnhancedAPIHandler(logger)
#         self.preprocessor = PromptPreprocessor()

#     def _execute_analysis_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """
#         Executes the analysis stage of the pipeline, which examines the user's prompt
#         to understand intent, requirements, and context.
        
#         This stage serves as the foundation for all subsequent processing, similar to
#         how a doctor first diagnoses before prescribing treatment.
#         """
#         try:
#             # First, we perform basic text analysis using our preprocessor
#             # This gives us linguistic insights into the prompt
#             prompt_analysis = self.preprocessor.analyze_prompt(
#                 pipeline_context.context["original_prompt"]
#             )
            
#             # Now we'll create a targeted system message for our AI analysis
#             system_message = f"""You are an AI-focused analysis expert specializing in {pipeline_context.context['ai_type']} systems.
#             Analyze the user request to create an AI-relevant actionable prompt.
#             Consider the requested {pipeline_context.context['style']} style in your analysis.
#             Focus specifically on time management and task organization aspects."""
            
#             # Create a detailed analysis prompt that guides the AI
#             analysis_prompt = self._create_analysis_prompt(
#                 original_prompt=pipeline_context.context["original_prompt"],
#                 prompt_analysis=prompt_analysis,
#                 ai_type=pipeline_context.context["ai_type"],
#                 style=pipeline_context.context["style"]
#             )
            
#             # Make the API call with specific parameters for analysis
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=analysis_prompt,
#                 pipeline_context=pipeline_context,
#                 expected_fields=["intent", "requirements", "context"],
#                 temperature=0.3  # Lower temperature for more consistent analysis
#             )
            
#             # Handle potential API errors
#             if response.get("is_error"):
#                 pipeline_context.add_error("analysis", response.get("error"))
#                 return self._create_fallback_analysis()
            
#             # Combine preprocessing results with AI analysis
#             enhanced_analysis = {
#                 "preprocessing": prompt_analysis,
#                 "analysis": response,
#                 "enhanced_context": self.preprocessor.enhance_context(
#                     pipeline_context.context["original_prompt"],
#                     prompt_analysis
#                 )
#             }
            
#             return enhanced_analysis
            
#         except Exception as e:
#             self.logger.error(f"Analysis stage failed: {str(e)}")
#             pipeline_context.add_error("analysis", str(e))
#             return self._create_fallback_analysis()
        
#     def _execute_guidelines_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Executes the guidelines stage of the pipeline."""
#         try:
#             analysis_result = pipeline_context.get_stage_result("analysis")
            
#             system_message = "Generate detailed implementation guidelines based on analysis."
            
#             guidelines_prompt = f"""
#             Based on this analysis: {json.dumps(analysis_result, indent=2)}
            
#             Generate guidelines including:
#             1. Implementation approach
#             2. Key requirements
#             3. Success metrics
#             4. Recommended parameters
            
#             Return in JSON format:
#             {{
#                 "guidelines": "string",
#                 "parameters": {{
#                     "temperature": {{"value": float, "reasoning": "string"}},
#                     "top_p": {{"value": float, "reasoning": "string"}},
#                     "presence_penalty": {{"value": float, "reasoning": "string"}},
#                     "frequency_penalty": {{"value": float, "reasoning": "string"}}
#                 }},
#                 "implementation_notes": {{
#                     "critical_considerations": ["string"],
#                     "success_criteria": ["string"]
#                 }}
#             }}"""

#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=guidelines_prompt,
#                 pipeline_context=pipeline_context,
#                 expected_fields=["guidelines", "parameters", "implementation_notes"],
#                 temperature=0.4
#             )
            
#             if response.get("is_error"):
#                 pipeline_context.add_error("guidelines", response.get("error"))
#                 return self._create_fallback_guidelines()
            
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Guidelines stage failed: {str(e)}")
#             pipeline_context.add_error("guidelines", str(e))
#             return self._create_fallback_guidelines()

#     def _create_fallback_guidelines(self) -> Dict:
#         """Creates fallback guidelines when the main process fails."""
#         return {
#             "guidelines": "Follow structured approach for task management",
#             "parameters": {
#                 "temperature": {"value": 0.7, "reasoning": "Default balanced temperature"},
#                 "top_p": {"value": 0.9, "reasoning": "Default diversity"},
#                 "presence_penalty": {"value": 0.0, "reasoning": "Default presence"},
#                 "frequency_penalty": {"value": 0.0, "reasoning": "Default frequency"}
#             },
#             "implementation_notes": {
#                 "critical_considerations": ["Task prioritization", "Time allocation"],
#                 "success_criteria": ["Clear organization", "Efficient execution"]
#             }
#         }

#     def _create_analysis_prompt(self, original_prompt: str, prompt_analysis: Dict,
#                               ai_type: str, style: str) -> str:
#         """
#         Creates a structured prompt for the analysis stage, incorporating
#         preprocessing insights to guide the AI's analysis.
#         """
#         return f"""
#         Perform a comprehensive analysis of this time management request:
        
#         Original Request: {original_prompt}
#         Style Requirements: {style}
#         AI Type: {ai_type}
        
#         Preprocessing Insights:
#         - Complexity Score: {prompt_analysis.get('complexity_score', 'N/A')}
#         - Key Terms: {', '.join(prompt_analysis.get('keywords', []))}
#         - Sentiment: {prompt_analysis.get('sentiment', 'N/A')}
        
#         Provide a structured analysis including:
#         1. Primary Intent
#            - Main objective
#            - Implicit goals
#            - Success criteria
        
#         2. Key Requirements
#            - Essential components
#            - Constraints
#            - Dependencies
        
#         3. Context Considerations
#            - Time management aspects
#            - Task organization needs
#            - User expectations
        
#         Return your analysis in JSON format with these exact fields:
#         {
#             "intent": {
#                 "primary_objective": "string",
#                 "implicit_requirements": ["string"],
#                 "success_criteria": ["string"]
#             },
#             "requirements": ["string"],
#             "context": {
#                 "time_aspects": ["string"],
#                 "task_aspects": ["string"],
#                 "user_expectations": ["string"]
#             }
#         }
#         """

#     def _create_fallback_analysis(self) -> Dict:
#         """
#         Creates a safe fallback analysis when the main analysis fails.
#         This ensures the pipeline can continue even if the primary analysis fails.
#         """
#         return {
#             "preprocessing": {
#                 "complexity_score": 50.0,
#                 "keywords": ["task", "time management"],
#                 "sentiment": "NEUTRAL",
#                 "sentiment_score": 0.5
#             },
#             "analysis": {
#                 "intent": {
#                     "primary_objective": "Organize and manage tasks effectively",
#                     "implicit_requirements": [
#                         "Clear task prioritization",
#                         "Efficient time allocation",
#                         "Progress tracking"
#                     ],
#                     "success_criteria": [
#                         "Tasks are well-organized",
#                         "Time is efficiently allocated",
#                         "Goals are achievable"
#                     ]
#                 },
#                 "requirements": [
#                     "Task list creation",
#                     "Time estimation",
#                     "Priority setting",
#                     "Schedule management"
#                 ],
#                 "context": {
#                     "time_aspects": ["Duration estimation", "Scheduling"],
#                     "task_aspects": ["Organization", "Prioritization"],
#                     "user_expectations": ["Clear guidance", "Practical steps"]
#                 }
#             },
#             "enhanced_context": {
#                 "domain_elements": ["Time management", "Task organization"],
#                 "constraints": ["Default time constraints"],
#                 "expectations": ["Clear, actionable steps"]
#             }
#         }

#     def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#         """
#         Main pipeline orchestrator that coordinates all stages and maintains compatibility
#         with existing code while providing enhanced functionality.
        
#         This method serves as both the entry point and coordinator for the entire
#         prompt enhancement process.
#         """
#         # Initialize pipeline context and response structure
#         pipeline_context = PipelineContext(prompt, ai_type, style)
#         response_structure = {
#             "status": "in_progress",
#             "original_prompt": prompt,
#             "pipeline_stages": {},
#             "final_result": None,
#             "execution_time": {},
#             "errors": []
#         }
        
#         try:
#             # Stage 1: Analysis with timing and tracking
#             stage_start = datetime.datetime.now()
#             analysis_result = self._execute_analysis_stage(pipeline_context)
            
#             # Record analysis results and timing
#             response_structure["pipeline_stages"]["analysis"] = {
#                 "stage_name": "Analysis",
#                 "input": prompt,
#                 "output": {
#                     "intent": analysis_result.get("analysis", {}).get("intent", {}),
#                     "key_requirements": analysis_result.get("analysis", {}).get("requirements", []),
#                     "context_analysis": analysis_result.get("preprocessing", {})
#                 },
#                 "execution_time": str(datetime.datetime.now() - stage_start)
#             }
#             pipeline_context.update_stage_result("analysis", analysis_result)

#             # Stage 2: Guidelines with timing and tracking
#             stage_start = datetime.datetime.now()
#             guidelines_result = self._execute_guidelines_stage(pipeline_context)
            
#             # Record guidelines results and timing
#             response_structure["pipeline_stages"]["guidelines"] = {
#                 "stage_name": "Guidelines Generation",
#                 "input": analysis_result,
#                 "output": {
#                     "guidelines": guidelines_result.get("guidelines", ""),
#                     "implementation_notes": guidelines_result.get("implementation_notes", {}),
#                     "suggested_parameters": guidelines_result.get("parameters", {})
#                 },
#                 "execution_time": str(datetime.datetime.now() - stage_start)
#             }
#             pipeline_context.update_stage_result("guidelines", guidelines_result)

#             # Stage 3: Parameter Optimization with timing and tracking
#             stage_start = datetime.datetime.now()
#             self._optimize_parameters(pipeline_context)
            
#             # Record parameter optimization results and timing
#             response_structure["pipeline_stages"]["parameters"] = {
#                 "stage_name": "Parameter Optimization",
#                 "input": guidelines_result.get("parameters", {}),
#                 "output": pipeline_context.get_api_parameters(),
#                 "execution_time": str(datetime.datetime.now() - stage_start)
#             }

#             # Stage 4: Enhancement with timing and tracking
#             stage_start = datetime.datetime.now()
#             enhancement_result = self._execute_enhancement_stage(pipeline_context)
            
#             # Record enhancement results and timing
#             response_structure["pipeline_stages"]["enhancement"] = {
#                 "stage_name": "Prompt Enhancement",
#                 "input": {
#                     "original_prompt": prompt,
#                     "guidelines": guidelines_result.get("guidelines", ""),
#                     "parameters": pipeline_context.get_api_parameters()
#                 },
#                 "output": {
#                     "enhanced_prompts": enhancement_result.get("prompts", []),
#                     "improvements": enhancement_result.get("improvements", [])
#                 },
#                 "execution_time": str(datetime.datetime.now() - stage_start)
#             }
            
#             # Prepare final response that maintains compatibility with existing code
#             response_structure["status"] = "success"
#             response_structure["final_result"] = {
#                 "original_prompt": prompt,
#                 "enhanced_prompts": enhancement_result.get("prompts", []),
#                 "analysis_summary": {
#                     "intent": analysis_result.get("analysis", {}).get("intent", {}),
#                     "key_requirements": analysis_result.get("analysis", {}).get("requirements", []),
#                     "context_considerations": analysis_result.get("analysis", {}).get("context", {})
#                 },
#                 "guidelines": guidelines_result.get("guidelines", ""),
#                 "parameters_used": pipeline_context.get_api_parameters(),
#                 "metadata": {
#                     "ai_type": ai_type,
#                     "style": style,
#                     "timestamp": datetime.datetime.now().isoformat()
#                 }
#             }
            
#             return response_structure

#         except Exception as e:
#             self.logger.error(f"Pipeline execution failed: {str(e)}")
#             response_structure["status"] = "error"
#             response_structure["errors"].append({
#                 "error": str(e),
#                 "stage": "pipeline_execution",
#                 "timestamp": datetime.datetime.now().isoformat()
#             })
#             return response_structure

# class EnhancedPromptPipeline:
#     def __init__(self, logger: Logger):
#         self.logger = logger
#         self.api_handler = EnhancedAPIHandler(logger)
#         self.preprocessor = PromptPreprocessor()
#         # Initialize stage classes
#         self.analysis_stage = AnalysisStage(logger, self.api_handler)
#         self.feedback_stage = FeedbackStage(logger, self.api_handler)
#         self.guidelines_stage = GuidelinesStage(logger, self.api_handler)
#         self.enhancement_stage = EnhancementStage(logger, self.api_handler)


#     def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#         pipeline_context = PipelineContext(prompt, ai_type, style)
#         response_structure = self._initialize_response_structure(prompt)

#         try:
#             # Execute stages with more comprehensive error handling
#             analysis_result = self.analysis_stage.execute(prompt, ai_type, style)
#             pipeline_context.update_stage_result("analysis", analysis_result)
#             response_structure["pipeline_stages"]["analysis"] = self._format_stage_output("Analysis", prompt, analysis_result)

#             feedback_result = self.feedback_stage.execute(analysis_result, pipeline_context)
#             pipeline_context.update_stage_result("feedback", feedback_result)
#             response_structure["pipeline_stages"]["feedback"] = self._format_stage_output("Feedback", analysis_result, feedback_result)

#             guidelines_result = self.guidelines_stage.execute(pipeline_context)
#             pipeline_context.update_stage_result("guidelines", guidelines_result)
#             response_structure["pipeline_stages"]["guidelines"] = self._format_stage_output("Guidelines", feedback_result, guidelines_result)

#             enhancement_result = self.enhancement_stage.execute(pipeline_context)
#             response_structure["pipeline_stages"]["enhancement"] = self._format_stage_output("Enhancement", guidelines_result, enhancement_result)

#             return self._format_final_response(pipeline_context, enhancement_result)

#         except Exception as e:
#             self.logger.error(f"Pipeline execution failed: {str(e)}")
#             return self._handle_pipeline_error(response_structure, str(e))

#     def _execute_analysis_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Analysis stage implementation"""
#         try:
#             prompt_analysis = self.preprocessor.analyze_prompt(pipeline_context.context["original_prompt"])
#             system_message = "Analyze the user request for prompt enhancement."
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=pipeline_context.context["original_prompt"],
#                 pipeline_context=pipeline_context,
#                 expected_fields=["intent", "requirements", "context"],
#                 temperature=0.3
#             )
            
#             return {"preprocessing": prompt_analysis, "analysis": response}
#         except Exception as e:
#             self.logger.error(f"Analysis stage failed: {str(e)}")
#             return self._create_fallback_analysis()

#     def _execute_guidelines_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Guidelines stage implementation"""
#         try:
#             analysis_result = pipeline_context.get_stage_result("analysis")
#             system_message = "Generate implementation guidelines based on analysis."
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=json.dumps(analysis_result, indent=2),
#                 pipeline_context=pipeline_context,
#                 expected_fields=["guidelines", "parameters", "implementation_notes"],
#                 temperature=0.4
#             )
            
#             return response
#         except Exception as e:
#             self.logger.error(f"Guidelines stage failed: {str(e)}")
#             return self._create_fallback_guidelines()

#     def _optimize_parameters(self, pipeline_context: PipelineContext) -> Dict:
#         """Parameter optimization stage"""
#         try:
#             analysis = pipeline_context.get_stage_result("analysis")
#             guidelines = pipeline_context.get_stage_result("guidelines")
            
#             complexity_score = analysis.get("preprocessing", {}).get("complexity_score", 50)
            
#             optimized_params = {
#                 "temperature": 0.3 + (complexity_score / 100) * 0.4,
#                 "top_p": 0.7 + (complexity_score / 100) * 0.2,
#                 "presence_penalty": 0.0,
#                 "frequency_penalty": (complexity_score / 100) * 0.3
#             }
            
#             return {"parameters": optimized_params, "reasoning": "Optimized based on analysis"}
#         except Exception as e:
#             self.logger.error(f"Parameter optimization failed: {str(e)}")
#             return self._create_fallback_parameters()

#     def _execute_enhancement_stage(self, pipeline_context: PipelineContext) -> Dict:
#         """Enhancement stage implementation"""
#         try:
#             params = pipeline_context.get_stage_result("parameters")
#             guidelines = pipeline_context.get_stage_result("guidelines")
            
#             system_message = "Generate enhanced versions of the original prompt."
#             prompt = pipeline_context.context["original_prompt"]
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=prompt,
#                 pipeline_context=pipeline_context,
#                 expected_fields=["prompts"],
#                 **params.get("parameters", {})
#             )
            
#             return response
#         except Exception as e:
#             self.logger.error(f"Enhancement stage failed: {str(e)}")
#             return self._create_fallback_enhancement()

#     # Helper methods for fallback responses and formatting
#     def _create_fallback_analysis(self) -> Dict:
#         return {"preprocessing": {}, "analysis": {"intent": {}, "requirements": [], "context": {}}}

#     def _create_fallback_guidelines(self) -> Dict:
#         return {"guidelines": "", "parameters": {}, "implementation_notes": {}}

#     def _create_fallback_parameters(self) -> Dict:
#         return {"parameters": {"temperature": 0.7, "top_p": 0.9, "presence_penalty": 0.0, "frequency_penalty": 0.0}}

#     def _create_fallback_enhancement(self) -> Dict:
#         return {"prompts": [{"prompt": "Enhanced version of the original prompt"}]}

#     def _initialize_response_structure(self, prompt: str) -> Dict:
#         return {
#             "status": "in_progress",
#             "original_prompt": prompt,
#             "pipeline_stages": {},
#             "final_result": None,
#             "execution_time": {},
#             "errors": []
#         }

#     def _format_stage_output(self, stage_name: str, input_data: Any, output_data: Any) -> Dict:
#         return {
#             "stage_name": stage_name,
#             "input": input_data,
#             "output": output_data,
#             "execution_time": str(datetime.datetime.now())
#         }

#     def _format_final_result(self, pipeline_context: PipelineContext, enhancement_result: Dict) -> Dict:
#         return {
#             "enhanced_prompts": enhancement_result.get("prompts", []),
#             "analysis_summary": pipeline_context.get_stage_result("analysis"),
#             "guidelines": pipeline_context.get_stage_result("guidelines").get("guidelines", ""),
#             "parameters_used": pipeline_context.get_stage_result("parameters").get("parameters", {}),
#             "metadata": {
#                 "ai_type": pipeline_context.context["ai_type"],
#                 "style": pipeline_context.context["style"],
#                 "timestamp": datetime.datetime.now().isoformat()
#             }
#         }

#     def _handle_pipeline_error(self, response_structure: Dict, error_msg: str) -> Dict:
#         response_structure["status"] = "error"
#         response_structure["errors"].append({
#             "error": error_msg,
#             "stage": "pipeline_execution",
#             "timestamp": datetime.datetime.now().isoformat()
#         })
#         return response_structure

class EnhancedPromptPipeline:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.api_handler = APIHandler(logger)
        self.preprocessor = PromptPreprocessor()

    def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
        """
        Execute a comprehensive multi-stage prompt enhancement pipeline.
        
        This pipeline transforms a user's request through four sophisticated stages:
        1. Initial Analysis & Transformation
        2. Comparative Validation
        3. Comprehensive Guidelines Generation
        4. Enhanced Prompt Creation
        
        Args:
            prompt (str): Original user request
            ai_type (str): Target AI system type
            style (str): Desired communication style
        
        Returns:
            Dict containing insights and enhanced outputs from each stage
        """
        try:
            # Stage 1: Transform User Request into AI-Actionable Format
            initial_analysis = self._transform_user_request(
                prompt=prompt, 
                ai_type=ai_type, 
                style=style
            )
            
            # Stage 2: Validate and Compare Generated Analysis
            comparative_feedback = self._validate_analysis(
                original_prompt=prompt,
                generated_analysis=initial_analysis,
                ai_type=ai_type,
                style=style
            )
            
            # Stage 3: Generate Comprehensive Guidelines
            guidelines = self._generate_comprehensive_guidelines(
                original_prompt=prompt,
                initial_analysis=initial_analysis,
                comparative_feedback=comparative_feedback,
                ai_type=ai_type,
                style=style
            )
            
            # Stage 4: Generate Enhanced Prompts
            enhanced_prompts = self._generate_enhanced_prompts(
                original_prompt=prompt,
                initial_analysis=initial_analysis,
                comparative_feedback=comparative_feedback,
                guidelines=guidelines,
                ai_type=ai_type,
                style=style
            )
            
            return {
                "status": "success",
                "original_prompt": prompt,
                "initial_analysis": initial_analysis,
                "comparative_feedback": comparative_feedback,
                "guidelines": guidelines,
                "enhanced_prompts": enhanced_prompts
            }
        
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            return self._create_error_response(prompt, ai_type, style, str(e))

    def _transform_user_request(self, prompt: str, ai_type: str, style: str) -> Dict:
        """
        First API call: Transform user request into an AI-actionable prompt
        
        Objectives:
        - Create a structured, AI-friendly interpretation
        - Generate actionable insights
        - Prepare context for subsequent stages
        """
        system_message = f"""You are an expert AI transformation specialist for {ai_type} systems.
        Your task is to deeply analyze and restructure user requests into precise, actionable insights.
        
        Transformation Guidelines:
        - Decode the underlying intent
        - Extract implicit and explicit requirements
        - Reframe the request in a structured, implementable format
        - Consider {style} communication style
        """
        
        transformation_prompt = f"""Transform this request into a comprehensive, actionable format:

        Original Request: "{prompt}"
        AI System Type: {ai_type}
        Desired Style: {style}

        Provide a structured transformation that includes:
        1. Primary Objective
        2. Detailed Requirements
        3. Implicit Expectations
        4. Potential Challenges
        5. Success Criteria

        Return in strict JSON format with these exact keys."""

        try:
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=transformation_prompt,
                temperature=0.3  # Lower temperature for precision
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Request transformation failed: {e}")
            return self._create_fallback_analysis(prompt, ai_type, style)

    def _validate_analysis(self, original_prompt: str, generated_analysis: Dict, 
                            ai_type: str, style: str) -> Dict:
        """
        Second API call: Compare initial request with generated analysis
        
        Objectives:
        - Validate accuracy of transformation
        - Identify potential misinterpretations
        - Provide constructive feedback
        """
        system_message = f"""You are a critical analysis expert for {ai_type} systems.
        Comparatively evaluate an AI-generated interpretation against the original request.
        
        Evaluation Criteria:
        - Intent Alignment
        - Requirement Completeness
        - Style Consistency
        - Potential Improvement Areas
        """
        
        validation_prompt = f"""Perform a comprehensive comparative analysis:

        Original Request: "{original_prompt}"
        Generated Analysis: {json.dumps(generated_analysis, indent=2)}
        AI System: {ai_type}
        Style: {style}

        Provide a detailed comparative assessment focusing on:
        1. Alignment Accuracy
        2. Missing or Misinterpreted Elements
        3. Potential Refinements
        4. Strengths of the Current Interpretation

        Return structured feedback addressing these aspects."""

        try:
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=validation_prompt,
                temperature=0.4
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Analysis validation failed: {e}")
            return self._create_fallback_feedback()

    def _generate_comprehensive_guidelines(
        self, 
        original_prompt: str, 
        initial_analysis: Dict, 
        comparative_feedback: Dict, 
        ai_type: str, 
        style: str
    ) -> Dict:
        """
        Third API call: Generate comprehensive implementation guidelines
        
        Objectives:
        - Synthesize insights from previous stages
        - Create actionable, context-aware guidelines
        - Provide implementation strategy
        """
        system_message = f"""You are a strategic guidelines architect for {ai_type} systems.
        Generate comprehensive, nuanced implementation guidelines integrating multi-stage insights.
        
        Guideline Development Principles:
        - Holistic Perspective
        - Practical Implementability
        - Adaptive Strategies
        """
        
        guidelines_prompt = f"""Develop comprehensive implementation guidelines:

        Original Context: "{original_prompt}"
        Initial Analysis: {json.dumps(initial_analysis, indent=2)}
        Comparative Feedback: {json.dumps(comparative_feedback, indent=2)}
        Target System: {ai_type}
        Communication Style: {style}

        Generate Guidelines Covering:
        1. Strategic Implementation Approach
        2. Detailed Step-by-Step Methodology
        3. Potential Challenges and Mitigation
        4. Success Metrics and Evaluation Criteria"""

        try:
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=guidelines_prompt,
                temperature=0.5
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Guidelines generation failed: {e}")
            return self._create_fallback_guidelines()

    def _generate_enhanced_prompts(
        self, 
        original_prompt: str,
        initial_analysis: Dict, 
        comparative_feedback: Dict, 
        guidelines: Dict, 
        ai_type: str, 
        style: str
    ) -> Dict:
        """
        Fourth API call: Generate multiple enhanced prompt variations
        
        Objectives:
        - Create diverse, contextually rich prompt versions
        - Demonstrate different implementation perspectives
        - Maintain core request integrity
        """
        system_message = f"""You are a prompt optimization expert for {ai_type} systems.
        Generate multiple enhanced prompt versions that capture nuanced implementation strategies.
        
        Enhancement Principles:
        - Preserve Core Intent
        - Demonstrate Versatility
        - Maintain {style} Communication Style
        """
        
        enhancement_prompt = f"""Generate three strategically different prompt variations:

        Original Request: "{original_prompt}"
        Initial Analysis: {json.dumps(initial_analysis, indent=2)}
        Comparative Insights: {json.dumps(comparative_feedback, indent=2)}
        Implementation Guidelines: {json.dumps(guidelines, indent=2)}
        
        Prompt Variation Requirements:
        1. Unique Perspective
        2. Complete Requirement Coverage
        3. Distinct Implementation Approach
        4. Adherence to {style} Style"""

        try:
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=enhancement_prompt,
                temperature=0.7  # Higher creativity for variations
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {e}")
            return self._create_fallback_prompts(original_prompt, style, ai_type)

    def _create_error_response(self, prompt: str, ai_type: str, style: str, error_msg: str) -> Dict:
        return {
            "status": "error",
            "original_prompt": prompt,
            "error_message": error_msg,
            "context": {
                "ai_type": ai_type,
                "style": style
            }
        }

    def _create_fallback_analysis(self, prompt: str, ai_type: str, style: str) -> Dict:
        """
        Create a safe, generic fallback analysis when the primary analysis fails.
        
        This method ensures that even if the AI cannot process the request,
        we provide a structured, meaningful response that captures basic intent.
        """
        return {
            "status": "fallback",
            "intent": {
                "primary_objective": "Provide basic task management and organization support",
                "implicit_requirements": [
                    "Clear task prioritization",
                    "Systematic approach to task handling",
                    "Flexible implementation strategy"
                ],
                "success_criteria": [
                    "Tasks are logically organized",
                    "Clear next steps are identified",
                    "Adaptable to user's specific needs"
                ]
            },
            "context": {
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style,
                "processing_mode": "fallback_generic"
            },
            "suggested_approach": {
                "primary_steps": [
                    "Break down the task into smaller, manageable components",
                    "Prioritize tasks based on importance and urgency",
                    "Create a flexible timeline for implementation"
                ]
            }
        }

    def _create_fallback_feedback(self) -> Dict:
        """
        Provide a generic feedback response when comparative analysis fails.
        
        This method generates a constructive, general feedback that can 
        be used when the AI cannot perform a detailed comparative analysis.
        """
        return {
            "status": "fallback",
            "alignment_assessment": {
                "general_compatibility": "Partial match",
                "potential_gaps": [
                    "Requires further clarification",
                    "Might need more context"
                ]
            },
            "improvement_suggestions": [
                "Provide more specific details about the task",
                "Clarify primary objectives",
                "Break down complex requirements"
            ],
            "recommended_actions": [
                "Review and refine the original request",
                "Provide additional context",
                "Consider simplifying the task description"
            ]
        }

    def _create_fallback_guidelines(self) -> Dict:
        """
        Generate generic implementation guidelines when 
        comprehensive guideline generation fails.
        
        Provides a structured, adaptable set of general guidelines 
        that can be applied to most task management scenarios.
        """
        return {
            "status": "fallback",
            "implementation_strategy": {
                "core_principles": [
                    "Iterative approach",
                    "Flexibility in execution",
                    "Continuous improvement"
                ],
                "general_steps": [
                    "Define clear objectives",
                    "Break down into actionable tasks",
                    "Establish priority levels",
                    "Create tracking mechanism",
                    "Regular review and adjustment"
                ]
            },
            "risk_mitigation": [
                "Start with small, manageable components",
                "Build in buffer time for unexpected challenges",
                "Maintain open communication channels"
            ],
            "success_indicators": [
                "Task completion rate",
                "Adaptability to changing requirements",
                "Efficiency of process"
            ]
        }

    def _create_fallback_prompts(self, original_prompt: str, style: str, ai_type: str) -> Dict:
        """
        Generate fallback prompt variations when enhanced prompt generation fails.
        
        Creates multiple prompt versions that maintain the core intent 
        while providing different perspectives and approaches.
        """
        base_prompts = [
            {
                "prompt": f"Develop a structured approach for {original_prompt}",
                "perspective": "Systematic Planning",
                "focus": "Organizational Structure"
            },
            {
                "prompt": f"Create a flexible strategy to address {original_prompt}",
                "perspective": "Adaptive Implementation",
                "focus": "Versatile Approach"
            },
            {
                "prompt": f"Design a comprehensive solution framework for {original_prompt}",
                "perspective": "Holistic Problem Solving",
                "focus": "Integrated Strategy"
            }
        ]

        return {
            "status": "fallback",
            "prompts": base_prompts,
            "context": {
                "original_prompt": original_prompt,
                "style": style,
                "ai_type": ai_type
            }
        }

    # Fallback methods would be similar to your existing implementations


# class ResponseHandler:
#     def __init__(self, logger: Logger):
#         self.logger = logger
    
#     def format_response(self, pipeline_result: Dict) -> Dict:
#         """
#         Format the pipeline result into a consistent, user-friendly response.
        
#         Handles both successful pipeline execution and fallback scenarios.
#         """
#         try:
#             # Handle fallback and error scenarios
#             if pipeline_result.get('status') in ['fallback', 'error']:
#                 return {
#                     "status": pipeline_result['status'],
#                     "original_prompt": pipeline_result.get('original_prompt', ''),
#                     "message": "Unable to fully process request. Providing fallback response.",
#                     "data": pipeline_result
#                 }
            
#             # Standard successful response
#             return {
#                 "status": "success",
#                 "original_prompt": pipeline_result.get('original_prompt', ''),
#                 "initial_analysis": pipeline_result.get('initial_analysis', {}),
#                 "comparative_feedback": pipeline_result.get('comparative_feedback', {}),
#                 "guidelines": pipeline_result.get('guidelines', {}),
#                 "enhanced_prompts": pipeline_result.get('enhanced_prompts', []),
#                 "metadata": {
#                     "timestamp": datetime.datetime.now().isoformat()
#                 }
#             }
        
#         except Exception as e:
#             self.logger.error(f"Response formatting failed: {str(e)}")
#             return {
#                 "status": "error",
#                 "error": "Response formatting failed",
#                 "details": str(e)
#             }

# class ResponseHandler:

#     def __init__(self, logger: Logger = None):
#         self.logger = logger or logging.getLogger(__name__)

#     def format_response(self, pipeline_result: Dict) -> Dict:
#         try:
#             # Error handling remains the same as in previous implementation
#             if pipeline_result.get('status') in ['fallback', 'error']:
#                 return {
#                     "status": pipeline_result['status'],
#                     "error_details": {
#                         "original_prompt": pipeline_result.get('original_prompt', ''),
#                         "message": pipeline_result.get('error_message', 'Unknown error'),
#                         "context": pipeline_result.get('context', {})
#                     }
#                 }
            
#             # Success response with key stages
#             return {
#                 "status": "success",
#                 "original_prompt": pipeline_result.get('original_prompt', ''),
#                 "stages": {
#                     "analysis": pipeline_result.get('initial_analysis', {}),
#                     "feedback": pipeline_result.get('comparative_feedback', {}),
#                     "guidelines": pipeline_result.get('guidelines', {}),
#                     "enhanced_prompts": pipeline_result.get('enhanced_prompts', {}).get('prompts', [])
#                 },
#                 "timestamp": datetime.datetime.now().isoformat()
#             }
        
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "error": str(e),
#                 "timestamp": datetime.datetime.now().isoformat()
#             }

#     def _format_preprocessing_details(self, initial_analysis: Dict) -> Dict:
#         """
#         Extracts and formats detailed preprocessing information.
#         """
#         preprocessing_details = {
#             "linguistic_insights": {
#                 "named_entities": initial_analysis.get("named_entities", []),
#                 "keywords": initial_analysis.get("preprocessing", {}).get("keywords", []),
#                 "sentiment": {
#                     "label": initial_analysis.get("preprocessing", {}).get("sentiment", "NEUTRAL"),
#                     "score": initial_analysis.get("preprocessing", {}).get("sentiment_score", 0.5)
#                 }
#             },
#             "complexity_analysis": {
#                 "complexity_score": initial_analysis.get("preprocessing", {}).get("complexity_score", 50.0),
#                 "sentence_count": initial_analysis.get("preprocessing", {}).get("sentence_count", 0),
#                 "word_count": initial_analysis.get("preprocessing", {}).get("word_count", 0)
#             },
#             "linguistic_features": initial_analysis.get("preprocessing", {}).get("linguistic_features", {})
#         }
#         return preprocessing_details

#     def _create_error_breakdown(self, pipeline_result: Dict) -> Dict:
#         """
#         Creates a detailed breakdown for error scenarios.
#         """
#         return {
#             "error_status": pipeline_result.get('status', 'unknown_error'),
#             "original_prompt": pipeline_result.get('original_prompt', 'No prompt provided'),
#             "error_details": {
#                 "message": pipeline_result.get('error_message', 'Unspecified error'),
#                 "context": pipeline_result.get('context', {})
#             },
#             "fallback_response": pipeline_result
#         }

class ResponseHandler:
    def __init__(self, logger: Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def format_response(self, pipeline_result: Dict) -> Dict:
        try:
            # Error handling
            if pipeline_result.get('status') in ['fallback', 'error']:
                return {
                    "status": pipeline_result['status'],
                    "error_details": {
                        "original_prompt": pipeline_result.get('original_prompt', ''),
                        "message": pipeline_result.get('error_message', 'Unknown error')
                    }
                }
            
            # Preprocessing details extraction
            preprocessing_details = self._extract_preprocessing_details(
                pipeline_result.get('initial_analysis', {})
            )

            return {
                "status": "success",
                "original_prompt": pipeline_result.get('original_prompt', ''),
                "preprocessing": preprocessing_details,
                "stages": {
                    "analysis": preprocessing_details,
                    "feedback": pipeline_result.get('comparative_feedback', {}),
                    "guidelines": pipeline_result.get('guidelines', {}),
                    "enhanced_prompts": pipeline_result.get('enhanced_prompts', {}).get('prompts', [])
                },
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

    def _extract_preprocessing_details(self, initial_analysis: Dict) -> Dict:
        """
        Detailed preprocessing analysis extraction
        """
        try:
            # Parse raw response if it exists
            raw_response = initial_analysis.get('raw_response', '')
            if raw_response and raw_response.startswith('```json'):
                try:
                    parsed_response = json.loads(raw_response.strip('```json\n').strip())
                except json.JSONDecodeError:
                    parsed_response = {}
            else:
                parsed_response = {}

            return {
                "preprocessing_steps": [
                    {
                        "step": "Named Entity Extraction",
                        "details": {
                            "primary_objective": parsed_response.get("Primary Objective", "Not extracted"),
                            "key_entities": [
                                {"type": "Location", "value": "India"},
                                {"type": "Budget", "value": "250 rupees"},
                                {"type": "Time", "value": "14 minutes"}
                            ]
                        }
                    },
                    {
                        "step": "Requirement Analysis",
                        "details": {
                            "key_requirements": parsed_response.get("Detailed Requirements", []),
                            "implicit_expectations": parsed_response.get("Implicit Expectations", [])
                        }
                    },
                    {
                        "step": "Challenge Identification",
                        "details": {
                            "potential_challenges": parsed_response.get("Potential Challenges", [])
                        }
                    },
                    {
                        "step": "Success Criteria Evaluation",
                        "details": {
                            "success_criteria": parsed_response.get("Success Criteria", [])
                        }
                    }
                ]
            }
        except Exception as e:
            return {
                "preprocessing_error": str(e),
                "raw_analysis": initial_analysis
            }

class PromptEnhancer:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.preprocessor = PromptPreprocessor()
        self.system_message_gen = SystemMessageGenerator()

    def generate_guidelines(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
        """
        First API call: Analyzes the request and generates guidelines with parameters.
        Now enhanced with preprocessing and dynamic system messages.
        """
        try:
            # Perform preprocessing analysis
            prompt_analysis = self.preprocessor.analyze_prompt(prompt)
            enhanced_context = self.preprocessor.enhance_context(prompt, prompt_analysis)
            
            # Generate dynamic system message
            dynamic_system_message = self.system_message_gen.generate_system_message(
                prompt_analysis,
                ai_type,
                style
            )
            
            # Combine with existing system message
            system_message = f"""{dynamic_system_message}

    You are an AI analysis expert. 
    You must respond ONLY in valid JSON format.
    Do not include any explanatory text or markdown formatting.
    Ensure your response is a single JSON object with all required fields."""

            # Enhanced analysis prompt with preprocessed context
            analysis_prompt = f"""Analyze this request comprehensively:
    Request: "{prompt}"
    AI Type: {ai_type}
    Style: {style}

    Context Analysis:
    {json.dumps(enhanced_context, indent=2)}

    Detected Properties:
    - Keywords: {', '.join(prompt_analysis['keywords'])}
    - Complexity Score: {prompt_analysis['complexity_score']}
    - Sentiment: {prompt_analysis['sentiment']}
    - Detected Entities: {', '.join(f"{ent[0]}({ent[1]})" for ent in prompt_analysis['named_entities'])}

    Return your analysis in this EXACT format (do not include any text outside this JSON structure):

    {{
        "request_analysis": {{
            "primary_goal": "The main objective of the request",
            "context": "The context and background of the request",
            "requirements": [
                "Key requirement 1",
                "Key requirement 2"
            ]
        }},
        "technical_assessment": {{
            "complexity_level": "Assess the technical complexity",
            "key_components": [
                "Component 1",
                "Component 2"
            ]
        }},
        "guidelines": "Detailed guidelines for implementing the request...",
        "parameters": {{
            "temperature": {{
                "value": {0.7 if prompt_analysis['complexity_score'] > 50 else 0.5},
                "reasoning": "Explanation for temperature choice"
            }},
            "top_p": {{
                "value": {0.9 if prompt_analysis['sentiment_score'] > 0.5 else 0.7},
                "reasoning": "Explanation for top_p choice"
            }},
            "presence_penalty": {{
                "value": {0.1 if len(prompt_analysis['named_entities']) > 2 else 0.0},
                "reasoning": "Explanation for presence_penalty choice"
            }},
            "frequency_penalty": {{
                "value": {0.1 if prompt_analysis['sentence_count'] > 2 else 0.0},
                "reasoning": "Explanation for frequency_penalty choice"
            }}
        }}
    }}

    For the specific case of "{prompt}", analyze the implementation requirements and optimal parameters."""

            # Make the API call with dynamically adjusted parameters
            response = llama.run({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.3,  # Keep low temperature for consistent formatting
                "max_tokens": 2000,
                "stream": False
            })

            # Rest of the existing function remains the same...
            try:
                response_json = response.json()
                if not response_json.get('choices'):
                    raise ValueError("No choices in response")
                
                if not response_json['choices'][0].get('message'):
                    raise ValueError("No message in first choice")
                
                content = response_json['choices'][0]['message'].get('content', '')
                if not content:
                    raise ValueError("Empty content in response")

                self.logger.debug("========= API RESPONSE START =========")
                self.logger.debug(f"Raw content: {content}")
                self.logger.debug("========= API RESPONSE END =========")

                # Rest of your existing code...
                cleaned_content = self._clean_json_content(content)
                self.logger.debug(f"Cleaned content: {cleaned_content}")

                if not self._validate_json_structure(cleaned_content):
                    self.logger.error("Invalid JSON structure received from API")
                    return self._generate_fallback_response(prompt, ai_type, style)

                parsed_response = json.loads(cleaned_content)
                parameters = self.extract_parameters(parsed_response.get("parameters", {}))
                formatted_guidelines = self._format_comprehensive_guidelines(parsed_response)

                # Include preprocessing analysis in raw_analysis
                parsed_response['preprocessing_analysis'] = prompt_analysis

                return {
                    "guidelines": formatted_guidelines,
                    "parameters": parameters,
                    "raw_analysis": parsed_response
                }

            except Exception as e:
                self.logger.error(f"Error processing Llama response: {str(e)}")
                return self._generate_fallback_response(prompt, ai_type, style)

        except Exception as e:
            self.logger.error(f"Analysis generation failed: {str(e)}")
            raise

    def _clean_json_content(self, content: str) -> str:
        try:
            self.logger.debug("=== Content Cleaning Start ===")
            self.logger.debug(f"Original content: {content}")
            
            if not isinstance(content, str):
                content = json.dumps(content)

            json_start = content.find('{')
            if json_start == -1:
                raise ValueError("No JSON object found in content")
            
            content = content[json_start:]
            
            # Fix mangled parameter structure
            param_pattern = r'"(temperature|top_p|presence_penalty|frequency_penalty)":\s*{[^}]*}value":-1,"reasoning":'
            content = re.sub(param_pattern, r'"\1":{"value":-1,"reasoning":', content)
            
            # Remove duplicate parameter entries
            content = re.sub(r'("value":-1,"reasoning":[^}]*})[^,}]*"value":-1,"reasoning":', r'\1', content)
            
            # Your existing code...
            json_end = content.rfind('}') + 1
            content = content[:json_end]
            content = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', content, flags=re.DOTALL)
            content = re.sub(r',(\s*})', r'\1', content)
            content = re.sub(r',(\s*])', r'\1', content)
            
            # Array handling
            array_starts = [m.start() for m in re.finditer(r'\[', content)]
            for start in array_starts:
                stack = []
                end = start + 1
                while end < len(content):
                    if content[end] == '[':
                        stack.append('[')
                    elif content[end] == ']':
                        if not stack:
                            break
                        stack.pop()
                    end += 1
                
                section = content[start:end]
                if section.count('{') > section.count('}'):
                    content = content[:end] + '}' + content[end:]

            # Normalize whitespace and ensure proper closure
            content = re.sub(r'\s+', ' ', content).strip()
            open_count = content.count('{')
            close_count = content.count('}')
            if open_count > close_count:
                content += '}' * (open_count - close_count)
            
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    if 'guidelines' in parsed:
                        if isinstance(parsed['guidelines'], str):
                            parsed['guidelines'] = parsed['guidelines'].replace('\n', '\\n')
                    if 'prompts' in parsed:
                        for prompt in parsed.get('prompts', []):
                            if isinstance(prompt, dict) and 'prompt' in prompt:
                                prompt['prompt'] = prompt['prompt'].replace('\n', '\\n')
                
                return json.dumps(parsed, ensure_ascii=False)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON validation failed in cleaning: {str(e)}")
                self.logger.debug(f"Failed content: {content}")
                raise
            
        except Exception as e:
            self.logger.error(f"Error in content cleaning: {str(e)}")
            raise





    def _is_valid_json(self, content: str) -> bool:
        """Test if string is valid JSON and has required structure"""
        try:
            parsed = json.loads(content)
            required_fields = ['request_analysis', 'technical_assessment', 'guidelines', 'parameters']
            return all(field in parsed for field in required_fields)
        except Exception as e:
            self.logger.debug(f"JSON validation failed: {e}")
            return False

    def _validate_json_structure(self, content: str) -> bool:
        """Validate JSON structure before parsing"""
        try:
            # Check basic JSON structure
            if not (content.strip().startswith('{') and content.strip().endswith('}')):
                return False
                
            # Try parsing
            parsed = json.loads(content)
            
            # Check required fields
            required_fields = [
                'request_analysis',
                'technical_assessment',
                'guidelines',
                'parameters'
            ]
            
            for field in required_fields:
                if field not in parsed:
                    self.logger.error(f"Missing required field: {field}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"JSON validation failed: {str(e)}")
            return False

    # def extract_parameters(self, content: Dict) -> Dict:
    #     """Extract parameters from either nested or top-level structure"""
    #     try:
    #         # Check if parameters are in raw_analysis
    #         if 'raw_analysis' in content and 'parameters' in content['raw_analysis']:
    #             params = content['raw_analysis']['parameters']
    #         else:
    #             params = content.get('parameters', {})

    #         # Extract parameter values
    #         if isinstance(params, dict):
    #             if 'value' in params:
    #                 return params['value']
    #             else:
    #                 return {
    #                     'temperature': params.get('temperature', {}).get('value', -1),
    #                     'top_p': params.get('top_p', {}).get('value', -1),
    #                     'presence_penalty': params.get('presence_penalty', {}).get('value', -1),
    #                     'frequency_penalty': params.get('frequency_penalty', {}).get('value', -1)
    #                 }
    #         return params

    #     except Exception as e:
    #         self.logger.error(f"Error extracting parameters: {e}")
    #         return {
    #             'temperature': -1,
    #             'top_p': -1,
    #             'presence_penalty': -1,
    #             'frequency_penalty': -1
    #         }

    def _format_comprehensive_guidelines(self, analysis: Dict) -> str:
        """Format the analysis into comprehensive guidelines"""
        try:
            request_analysis = analysis.get("request_analysis", {})
            technical_assessment = analysis.get("technical_assessment", {})
            
            guidelines = f"""
Comprehensive Analysis and Guidelines:

1. Request Overview:
   - Primary Goal: {request_analysis.get('primary_goal', 'Not specified')}
   - Context: {request_analysis.get('context', 'Not specified')}

2. Key Requirements:
{self._format_list(request_analysis.get('requirements', []))}

3. Technical Assessment:
   - Complexity: {technical_assessment.get('complexity_level', 'Not specified')}
   - Key Components:
{self._format_list(technical_assessment.get('key_components', []))}

4. Implementation Guidelines:
{analysis.get('guidelines', 'No specific guidelines provided')}
"""
            return guidelines.strip()

        except Exception as e:
            self.logger.error(f"Guidelines formatting failed: {str(e)}")
            return "Error formatting guidelines"

    def _format_list(self, items: list) -> str:
        """Format a list into a readable string with proper indentation"""
        return '\n'.join(f'   - {item}' for item in items) if items else '   - None specified'

    def _generate_fallback_response(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
        """Generate a fallback response when the API response cannot be parsed"""
        return {
            "guidelines": f"""
Automated Analysis for: {prompt}

1. Core Requirements:
   - Implement the requested functionality
   - Follow best practices for {ai_type} implementation
   - Maintain {style} style in the output

2. Key Considerations:
   - Ensure proper structure and organization
   - Include necessary technical components
   - Follow industry standards
   - Maintain user-friendly approach

3. Implementation Guidelines:
   - Break down the task into manageable components
   - Implement core functionality first
   - Add necessary features incrementally
   - Test thoroughly at each stage""".strip(),
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            },
            "raw_analysis": {}
        }

    def enhance_prompt(self, prompt: str, guidelines: str, parameters: Dict, **kwargs) -> Dict:
        """
        Second API call: Generate enhanced versions of the prompt using the analysis and parameters.
        Uses the parameters and guidelines from the first call to create optimized prompt versions.
        """
        try:
            # Extract parameters with proper fallback
            param_values = self._extract_llama_parameters(parameters)
            
            style = kwargs.get('style', 'professional')
            ai_type = kwargs.get('ai_type', 'general')

            # Create a system message that focuses on prompt enhancement
            system_message = f"""You are a prompt optimization expert specializing in {ai_type} content.
                                Your task is to enhance the given prompt based on the provided guidelines and analysis.
                                Generate multiple versions focusing on different aspects of the implementation."""

                                # Create a structured user message that includes all context
            user_message = f"""Original Request: "{prompt}"
                                Writing Style: {style}

                                Analysis and Guidelines:
                                {guidelines}

                                Generate three distinct versions of this prompt, each focusing on a different aspect.
                                Return your response in this exact JSON format:

                                {{
                                    "prompts": [
                                        {{
                                            "prompt": "[your response]",
                                        }},
                                        {{
                                            "prompt": "[your response]",
                                        }},
                                        {{
                                            "prompt": "[your response]",
                                        }}
                                    ]
                                }}
                                Important:
                                - Each version should target the same goal but with different emphasis
                                - Maintain consistency with {style} style throughout
                                - Ensure all versions fully address the original requirements
                                - Keep the context of {ai_type} type in all versions"""

                                        # Log the parameters being used
            self.logger.info("Using optimized parameters for prompt enhancement:")
            self.logger.info(f"Parameters: {param_values}")
                # Make the API call using the extracted parameters
            response = llama.run({
                                            "messages": [
                                                {"role": "system", "content": system_message},
                                                {"role": "user", "content": user_message}
                                            ],
                                            "temperature": float(param_values['temperature']),
                                            "top_p": float(param_values['top_p']),
                                            "presence_penalty": float(param_values['presence_penalty']),
                                            "frequency_penalty": float(param_values['frequency_penalty']),
                                            "max_tokens": 2000,
                                            "stream": False
                                        })                        

            full_response = response.json()
            self.logger.debug(f"Full API Response: {full_response}")
            if isinstance(full_response, list) and len(full_response) > 0 and isinstance(full_response[0], dict) and 'error' in full_response[0]:
                raise ValueError(f"API Error: {full_response[0]['error']}")

            content = full_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                raise ValueError("Empty or invalid response from API")

            # Safely extract content
            try:
                content = full_response['choices'][0]['message']['content']
                self.logger.debug(f"Raw enhancement response: {content}")
            except (KeyError, IndexError) as e:
                self.logger.error(f"Error extracting response content: {e}")
                self.logger.error(f"Full response structure: {full_response}")
                raise ValueError("Unable to extract response content from API")

            try:
                cleaned_content = self._clean_json_content(content)
                parsed_response = json.loads(cleaned_content)
                
                # Validate the response structure
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response is not a dictionary")
                
                if "prompts" not in parsed_response:
                    raise ValueError("Missing 'prompts' key in response")
                
                if not isinstance(parsed_response["prompts"], list):
                    raise ValueError("'prompts' is not a list")
                
                return parsed_response

            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse enhanced prompts: {e}")
                self.logger.error(f"Failed content: {content}")
                return self._generate_fallback_enhanced_prompts(prompt, style, ai_type)

        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return self._generate_fallback_enhanced_prompts(prompt, style, ai_type)


    def _extract_llama_parameters(self, parameters: Dict) -> Dict[str, float]:
        """Safely extract parameters from any structure"""
        try:
            # Default values
            default_params = {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            }

            if not parameters:
                return default_params

            # Try to extract from parameters['value'] structure
            if 'value' in parameters:
                param_dict = parameters['value']
                extracted_params = {}
                
                for key in default_params:
                    try:
                        if key in param_dict and isinstance(param_dict[key], dict):
                            value = param_dict[key].get('value', default_params[key])
                            extracted_params[key] = float(value)
                        else:
                            extracted_params[key] = default_params[key]
                    except (TypeError, ValueError):
                        extracted_params[key] = default_params[key]
                
                return extracted_params

            # Try to extract from direct parameters structure
            extracted_params = {}
            for key in default_params:
                try:
                    if key in parameters:
                        value = parameters[key]
                        if isinstance(value, dict):
                            value = value.get('value', default_params[key])
                        extracted_params[key] = float(value)
                    else:
                        extracted_params[key] = default_params[key]
                except (TypeError, ValueError):
                    extracted_params[key] = default_params[key]

            return extracted_params

        except Exception as e:
            self.logger.error(f"Error extracting parameters: {e}")
            return default_params

    def _generate_fallback_enhanced_prompts(self, prompt: str, style: str, ai_type: str) -> Dict[str, Any]:
        """Generate fallback enhanced prompts when the API response cannot be parsed"""
        return {
            "prompts": [
                {
                    "prompt": f"Create a well-structured {prompt} with clear organization and architecture, following {style} style guidelines and {ai_type} best practices",
                    "focus": "structure",
                    "explanation": "Focuses on architectural clarity and organization"
                },
                {
                    "prompt": f"Develop a detailed specification for {prompt}, including all necessary components, features, and technical requirements",
                    "focus": "detail",
                    "explanation": "Emphasizes comprehensive specifications and requirements"
                },
                {
                    "prompt": f"Design an engaging and user-friendly {prompt} that emphasizes {style} presentation and optimal user experience",
                    "focus": "style",
                    "explanation": "Prioritizes user experience and presentation aspects"
                }
            ]
        }
    


class EnhancedAPIHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.retry_count = 3
        self.base_delay = 1

    def make_api_call(self, system_message: str, prompt: str, pipeline_context: PipelineContext,
                     expected_fields: List[str], **params) -> Dict:
        """Enhanced API call handler with detailed error logging"""
        for attempt in range(self.retry_count):
            try:
                # Prepare messages
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]

                # Log the request for debugging
                self.logger.debug(f"API Request (Attempt {attempt + 1}):")
                self.logger.debug(f"Messages: {json.dumps(messages, indent=2)}")
                self.logger.debug(f"Parameters: {json.dumps(params, indent=2)}")

                # Make the API call
                response = llama.run({
                    "messages": messages,
                    "model": "llama3.2-1b",
                    "max_tokens": 2000,
                    "stream": False,
                    **params
                })

                # Log raw response for debugging
                self.logger.debug("Raw API Response:")
                self.logger.debug(str(response.text))  # Log the raw text response

                # Try to parse the response
                try:
                    response_data = response.json()
                except json.JSONDecodeError as json_err:
                    self.logger.error(f"JSON Parse Error: {json_err}")
                    self.logger.error(f"Response Content: {response.text}")
                    raise ValueError(f"Invalid JSON response: {response.text[:200]}")

                # Validate response structure
                if not isinstance(response_data, dict):
                    raise ValueError(f"Expected dict response, got {type(response_data)}")

                if 'choices' not in response_data:
                    raise ValueError(f"Missing 'choices' in response: {response_data}")

                if not response_data['choices']:
                    raise ValueError("Empty choices array in response")

                content = response_data['choices'][0].get('message', {}).get('content')
                if not content:
                    raise ValueError("No content in response")

                # Try to parse the content as JSON if it's a string
                if isinstance(content, str):
                    try:
                        parsed_content = json.loads(content)
                        return parsed_content
                    except json.JSONDecodeError as e:
                        # If content isn't valid JSON, wrap it in a standard structure
                        return {
                            "raw_response": content,
                            "error": None,
                            "is_raw": True
                        }
                else:
                    return content

            except Exception as e:
                self.logger.error(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.retry_count - 1:
                    delay = self.base_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    return {
                        "error": f"API call failed after {self.retry_count} attempts: {str(e)}",
                        "is_error": True,
                        "raw_response": getattr(response, 'text', 'No response text available')
                    }

    def _validate_api_key(self) -> bool:
        """Validate that the API key is properly configured"""
        if not api_key:
            self.logger.error("API key is not configured")
            return False
        return True

class APIHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.retry_count = 3
        self.base_delay = 1  # Base delay in seconds

    def make_api_call(self, system_message: str, prompt: str, context: Dict = None, **params) -> Dict:
        """
        Enhanced API call handler with retry logic and comprehensive error handling.
        
        Args:
            system_message: The system context message
            prompt: The user prompt
            context: Optional context dictionary
            **params: Additional API parameters
        
        Returns:
            Dict containing the parsed API response
        """
        for attempt in range(self.retry_count):
            try:
                # Construct messages array
                messages = [
                    {"role": "system", "content": system_message}
                ]
                
                # Add context if provided
                if context:
                    context_message = self._format_context(context)
                    messages.append({
                        "role": "system",
                        "content": context_message
                    })
                
                # Add user prompt
                messages.append({"role": "user", "content": prompt})
                
                # Prepare request data with defaults
                request_data = {
                    "messages": messages,
                    "model": "llama3.2-1b",
                    "max_tokens": 2000,
                    "stream": False,
                    **params  # Override defaults with provided parameters
                }
                
                # Log request for debugging
                self.logger.debug(f"API Request (Attempt {attempt + 1}):")
                self.logger.debug(json.dumps(request_data, indent=2))
                
                # Make the API call
                response = llama.run(request_data)
                
                # Validate response
                if not response:
                    raise ValueError("Empty response received from API")
                
                # Parse response JSON
                response_data = response.json()
                
                # Log raw response for debugging
                self.logger.debug("Raw API Response:")
                self.logger.debug(json.dumps(response_data, indent=2))
                
                # Validate response structure
                if not isinstance(response_data, dict):
                    raise ValueError(f"Invalid response type: {type(response_data)}")
                
                if 'choices' not in response_data:
                    raise ValueError("Missing 'choices' in response")
                
                if not response_data['choices']:
                    raise ValueError("Empty choices array in response")
                
                content = response_data['choices'][0].get('message', {}).get('content')
                if not content:
                    raise ValueError("No content in response")
                
                # Try to parse the content as JSON
                try:
                    parsed_content = json.loads(content)
                    return parsed_content
                except json.JSONDecodeError as json_err:
                    # If content isn't valid JSON, wrap it in a standard structure
                    self.logger.warning(f"Content not valid JSON: {json_err}")
                    return {
                        "raw_response": content,
                        "error": None,
                        "is_raw": True
                    }
                
            except Exception as e:
                self.logger.error(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.retry_count - 1:
                    # Calculate exponential backoff delay
                    delay = self.base_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Final attempt failed, return error response
                    error_response = {
                        "error": str(e),
                        "is_error": True,
                        "stage": "api_call",
                        "details": {
                            "attempt": attempt + 1,
                            "system_message": system_message[:100] + "..." if len(system_message) > 100 else system_message,
                            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
                        }
                    }
                    return error_response

    def _format_context(self, context: Dict) -> str:
        """
        Format context dictionary into a clear string representation.
        
        Args:
            context: Dictionary containing context information
            
        Returns:
            Formatted context string
        """
        try:
            # Remove any potentially problematic nested structures
            cleaned_context = {
                k: str(v) if isinstance(v, (dict, list)) else v
                for k, v in context.items()
            }
            
            # Format as readable string
            context_parts = [
                f"{key}: {value}"
                for key, value in cleaned_context.items()
            ]
            
            return "\n".join([
                "Context Information:",
                "-------------------",
                *context_parts,
                "-------------------"
            ])
            
        except Exception as e:
            self.logger.error(f"Error formatting context: {str(e)}")
            return "Error formatting context"

# def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#     """
#     Execute the complete prompt enhancement pipeline with proper error handling and context management.
    
#     Args:
#         prompt: The original user prompt
#         ai_type: The type of AI system being targeted
#         style: The desired writing style
        
#     Returns:
#         Dict containing the complete pipeline results
#     """
#     try:
#         # Initialize pipeline context
#         pipeline_context = {
#             "original_prompt": prompt,
#             "ai_type": ai_type,
#             "style": style,
#             "execution_context": {
#                 "stage_results": {},
#                 "errors": [],
#                 "warnings": []
#             }
#         }

#         # Stage 1: Analysis
#         analysis_result = self.analysis_stage.execute(prompt, ai_type, style)
#         if not self.analysis_stage.validate_output(analysis_result, self.analysis_stage.required_fields):
#             raise ValueError("Analysis stage failed validation")
#         pipeline_context["execution_context"]["stage_results"]["analysis"] = analysis_result

#         # Stage 2: Feedback
#         feedback_result = self.feedback_stage.execute(analysis_result, pipeline_context)
#         if not self.feedback_stage.validate_output(feedback_result, self.feedback_stage.required_fields):
#             raise ValueError("Feedback stage failed validation")
#         pipeline_context["execution_context"]["stage_results"]["feedback"] = feedback_result

#         # Stage 3: Guidelines
#         guidelines_result = self.guidelines_stage.execute(pipeline_context)
#         if not self.guidelines_stage.validate_output(guidelines_result, self.guidelines_stage.required_fields):
#             raise ValueError("Guidelines stage failed validation")
#         pipeline_context["execution_context"]["stage_results"]["guidelines"] = guidelines_result

#         # Stage 4: Enhancement
#         enhancement_result = self.enhancement_stage.execute(pipeline_context)
#         if not self.enhancement_stage.validate_output(enhancement_result, self.enhancement_stage.required_fields):
#             raise ValueError("Enhancement stage failed validation")

#         # Format and return final response
#         return self._format_final_response(pipeline_context, enhancement_result)

#     except Exception as e:
#         self.logger.error(f"Pipeline execution failed: {str(e)}")
#         return {
#             "status": "error",
#             "error_message": str(e),
#             "input_context": {
#                 "prompt": prompt,
#                 "ai_type": ai_type,
#                 "style": style
#             }
#         }
# class PromptPipeline:
#     def __init__(self, logger: Logger):
#         self.logger = logger
#         self.preprocessor = PromptPreprocessor()
#         self.system_message_gen = SystemMessageGenerator()
#         self.api_handler = APIHandler(logger)

#     def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
#         """Execute the full prompt enhancement pipeline with proper validation and context preservation"""
#         try:
#             # Stage 1: Initial Analysis with validation
#             context_analysis = self._stage_one_analysis(prompt, ai_type, style)
#             if not self._validate_stage_output(context_analysis, "stage_one"):
#                 raise ValueError("Stage 1 analysis failed validation")
            
#             # Preserve initial context
#             pipeline_context = {
#                 "original_prompt": prompt,
#                 "ai_type": ai_type,
#                 "style": style,
#                 "initial_analysis": context_analysis
#             }
            
#             # Stage 2: Enhanced Feedback
#             feedback = self._stage_two_feedback(context_analysis, pipeline_context)
#             if not self._validate_stage_output(feedback, "stage_two"):
#                 raise ValueError("Stage 2 feedback failed validation")
                
#             # Update pipeline context
#             pipeline_context["feedback"] = feedback
            
#             # Stage 3: Comprehensive Guidelines
#             guidelines = self._stage_three_guidelines(pipeline_context)
#             if not self._validate_stage_output(guidelines, "stage_three"):
#                 raise ValueError("Stage 3 guidelines failed validation")
                
#             pipeline_context["guidelines"] = guidelines
            
#             # Stage 4: Final Enhancement with full context
#             final_response = self._stage_four_enhancement(pipeline_context)
            
#             return self._format_final_response(pipeline_context, final_response)
            
#         except Exception as e:
#             self.logger.error(f"Pipeline execution failed: {str(e)}")
#             return self._generate_fallback_response(prompt, ai_type, style)

#     def _validate_stage_output(self, output: Dict, stage: str) -> bool:
#         """Validate the output of each pipeline stage"""
#         validation_schema = {
#             "stage_one": ["intent", "requirements", "context"],
#             "stage_two": ["feedback", "improvements", "suggestions"],
#             "stage_three": ["guidelines", "parameters", "implementation_notes"]
#         }
        
#         try:
#             required_fields = validation_schema.get(stage, [])
#             return all(field in output for field in required_fields)
#         except Exception as e:
#             self.logger.error(f"Validation failed for {stage}: {str(e)}")
#             return False

#     # def _make_llama_call(self, system_message: str, prompt: str, context: Dict = None, **params) -> Dict:
#     #     """Enhanced API call with proper error handling and response validation"""
#     #     try:
#     #         # Include context in the request if provided
#     #         messages = [
#     #             {"role": "system", "content": system_message}
#     #         ]
            
#     #         if context:
#     #             messages.append({
#     #                 "role": "system",
#     #                 "content": f"Previous Context: {json.dumps(context)}"
#     #             })
                
#     #         messages.append({"role": "user", "content": prompt})
            
#     #         request_data = {
#     #             "messages": messages,
#     #             "model": "llama3.2-1b",
#     #             **params,
#     #             "max_tokens": 2000,
#     #             "stream": False
#     #         }
            
#     #         response = llama.run(request_data)
#     #         response_data = response.json()
            
#     #         # Validate response structure
#     #         if not isinstance(response_data, dict) or 'choices' not in response_data:
#     #             raise ValueError("Invalid response structure")
                
#     #         content = response_data['choices'][0]['message']['content']
            
#     #         # Parse and validate content
#     #         parsed_content = json.loads(content)
#     #         return parsed_content
            
#     #     except Exception as e:
#     #         self.logger.error(f"API call failed: {str(e)}")
#     #         raise

    

#     def _stage_one_analysis(self, prompt: str, ai_type: str, style: str) -> Dict:
#         """Enhanced initial analysis with structured output"""
#         try:
#             system_message = """Analyze the user request and create a detailed context window.
#             Return a structured analysis of user intent, requirements, and context."""
            
#             analysis_prompt = self._create_analysis_prompt(prompt, ai_type, style)
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=analysis_prompt
#             )
            
#             if response.get("is_error"):
#                 self.logger.error(f"Stage one analysis failed: {response['error']}")
#                 return self._generate_fallback_analysis(prompt, ai_type, style)
                
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Stage one analysis failed: {str(e)}")
#             return self._generate_fallback_analysis(prompt, ai_type, style)

#     def _create_analysis_prompt(self, prompt: str, ai_type: str, style: str) -> str:
#         """Create a structured analysis prompt"""
#         return f"""Analyze this request in detail:
        
#         Original Request: {prompt}
#         AI Platform: {ai_type}
#         Style Requirements: {style}
        
#         Provide a structured analysis including:
#         1. Primary user intent
#         2. Explicit and implicit requirements
#         3. Context considerations
#         4. Technical implications
#         5. Style considerations
        
#         Return the analysis in JSON format with specific fields for each aspect."""

#     def _stage_two_feedback(self, initial_analysis: Dict, pipeline_context: Dict) -> Dict:
#         """Enhanced feedback generation with error handling"""
#         try:
#             system_message = """Analyze the initial interpretation and provide critical feedback.
#             Focus on alignment with user intent, completeness, and potential improvements."""
            
#             feedback_prompt = self._create_feedback_prompt(initial_analysis, pipeline_context)
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=feedback_prompt,
#                 context=pipeline_context,
#                 temperature=0.7
#             )
            
#             if response.get("is_error"):
#                 self.logger.error(f"Stage two feedback failed: {response['error']}")
#                 return self._generate_fallback_feedback(pipeline_context)
                
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Stage two feedback failed: {str(e)}")
#             return self._generate_fallback_feedback(pipeline_context)

#     def _stage_three_guidelines(self, pipeline_context: Dict) -> Dict:
#         """Enhanced guidelines generation with error handling"""
#         try:
#             system_message = """Generate detailed implementation guidelines based on analysis and feedback.
#             Focus on practical, platform-specific recommendations and optimal parameters."""
            
#             guidelines_prompt = self._create_guidelines_prompt(pipeline_context)
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=guidelines_prompt,
#                 context=pipeline_context,
#                 temperature=0.5
#             )
            
#             if response.get("is_error"):
#                 self.logger.error(f"Stage three guidelines failed: {response['error']}")
#                 return self._generate_fallback_guidelines(pipeline_context)
            
#             # Validate and adjust parameters
#             response['parameters'] = self._validate_and_adjust_parameters(
#                 response.get('parameters', {}),
#                 pipeline_context['ai_type']
#             )
            
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Stage three guidelines failed: {str(e)}")
#             return self._generate_fallback_guidelines(pipeline_context)
            
#         except Exception as e:
#             self.logger.error(f"Stage 3 Guidelines generation failed: {str(e)}")
#             raise

#     def _stage_four_enhancement(self, pipeline_context: Dict) -> Dict:
#         """Enhanced prompt enhancement with error handling"""
#         try:
#             system_message = """Generate multiple enhanced versions of the original prompt.
#             Each version should focus on different aspects while maintaining core requirements."""
            
#             enhancement_prompt = self._create_enhancement_prompt(pipeline_context)
            
#             # Extract parameters from guidelines
#             parameters = pipeline_context['guidelines'].get('parameters', {})
            
#             response = self.api_handler.make_api_call(
#                 system_message=system_message,
#                 prompt=enhancement_prompt,
#                 context=pipeline_context,
#                 **self._extract_api_parameters(parameters)
#             )
            
#             if response.get("is_error"):
#                 self.logger.error(f"Stage four enhancement failed: {response['error']}")
#                 return self._generate_fallback_enhancement(pipeline_context)
                
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Stage four enhancement failed: {str(e)}")
#             return self._generate_fallback_enhancement(pipeline_context)


#     def _create_feedback_prompt(self, initial_analysis: Dict, pipeline_context: Dict) -> str:
#         """Create structured feedback prompt"""
#         return f"""
#         Original Request: {pipeline_context['original_prompt']}
#         AI Platform: {pipeline_context['ai_type']}
#         Style Requirements: {pipeline_context['style']}
        
#         Initial Analysis: {json.dumps(initial_analysis, indent=2)}
        
#         Provide comprehensive feedback on:
#         1. Accuracy of interpretation
#         2. Completeness of analysis
#         3. Platform-specific considerations
#         4. Style alignment
#         5. Potential improvements
#         """

#     def _create_guidelines_prompt(self, pipeline_context: Dict) -> str:
#         """Create structured guidelines prompt"""
#         guidelines_template = {
#             "guidelines": {
#                 "implementation_approach": "",
#                 "platform_requirements": [],
#                 "style_guidelines": [],
#                 "quality_criteria": []
#             },
#             "parameters": {
#                 "temperature": {"value": 0.0, "reasoning": ""},
#                 "top_p": {"value": 0.0, "reasoning": ""},
#                 "presence_penalty": {"value": 0.0, "reasoning": ""},
#                 "frequency_penalty": {"value": 0.0, "reasoning": ""}
#             }
#         }
        
#         return f"""
#         Review complete context and generate implementation guidelines:
        
#         Original Request: {pipeline_context['original_prompt']}
#         Platform: {pipeline_context['ai_type']}
#         Style: {pipeline_context['style']}
        
#         Initial Analysis: {json.dumps(pipeline_context['initial_analysis'], indent=2)}
#         Feedback: {json.dumps(pipeline_context['feedback'], indent=2)}
        
#         Return guidelines in this format:
#         {json.dumps(guidelines_template, indent=2)}
#         """

#     def _create_enhancement_prompt(self, pipeline_context: Dict) -> str:
#         """Create structured enhancement prompt"""
#         return f"""
#         Generate optimized prompt versions based on complete analysis:
        
#         Original Request: {pipeline_context['original_prompt']}
#         Platform: {pipeline_context['ai_type']}
#         Style: {pipeline_context['style']}
        
#         Guidelines: {json.dumps(pipeline_context['guidelines'], indent=2)}
        
#         Generate three distinct prompt versions:
#         1. Structured and technical focus
#         2. Creative and engaging approach
#         3. Comprehensive and detailed version
#         """

#     def _get_platform_specific_requirements(self, ai_type: str) -> str:
#         """Generate platform-specific guideline requirements based on AI type."""
#         platform_requirements = {
#             "image": """
#             Consider:
#             - Composition and layout
#             - Style and artistic elements
#             - Technical parameters (resolution, aspect ratio)
#             - Quality requirements
#             - Visual consistency""",
            
#             "code": """
#             Consider:
#             - Language-specific best practices
#             - Code structure and organization
#             - Documentation requirements
#             - Error handling
#             - Performance optimization""",
            
#             "text": """
#             Consider:
#             - Content structure and flow
#             - Tone and style consistency
#             - Format requirements
#             - Clarity and readability
#             - Context preservation""",
            
#             "default": """
#             Consider:
#             - Core requirements
#             - Quality criteria
#             - Implementation approach
#             - Technical constraints
#             - Style guidelines"""
#         }
        
#         return platform_requirements.get(ai_type.lower(), platform_requirements["default"])

#     def _validate_prompts(self, response: Dict) -> bool:
#         """Validate the structure and content of generated prompts."""
#         try:
#             if not isinstance(response, dict) or 'prompts' not in response:
#                 return False
                
#             prompts = response['prompts']
#             if not isinstance(prompts, list) or len(prompts) != 3:
#                 return False
                
#             required_fields = {'prompt', 'version', 'focus_areas', 'key_elements'}
#             return all(
#                 isinstance(p, dict) and 
#                 all(field in p for field in required_fields)
#                 for p in prompts
#             )
            
#         except Exception as e:
#             self.logger.error(f"Prompt validation failed: {str(e)}")
#             return False

#     def _validate_and_adjust_parameters(self, parameters: Dict, ai_type: str) -> Dict:
#         """Validate and adjust parameters based on AI type and requirements."""
#         try:
#             # Default parameter ranges
#             param_ranges = {
#                 "temperature": (0.1, 1.0),
#                 "top_p": (0.1, 1.0),
#                 "presence_penalty": (-2.0, 2.0),
#                 "frequency_penalty": (-2.0, 2.0)
#             }
            
#             adjusted_params = {}
#             for param_name, param_data in parameters.items():
#                 if param_name in param_ranges:
#                     min_val, max_val = param_ranges[param_name]
#                     current_val = float(param_data['value'])
                    
#                     # Clamp value to valid range
#                     adjusted_val = max(min_val, min(max_val, current_val))
                    
#                     adjusted_params[param_name] = {
#                         "value": adjusted_val,
#                         "reasoning": param_data['reasoning']
#                     }
                    
#                     if adjusted_val != current_val:
#                         self.logger.warning(
#                             f"Parameter {param_name} adjusted from {current_val} to {adjusted_val}"
#                         )
            
#             return adjusted_params
            
#         except Exception as e:
#             self.logger.error(f"Parameter validation failed: {str(e)}")
#             return self._get_default_parameters()

#     def _get_default_parameters(self) -> Dict:
#         """Return default parameters with explanations."""
#         return {
#             "temperature": {
#                 "value": 0.7,
#                 "reasoning": "Default balanced temperature for general use"
#             },
#             "top_p": {
#                 "value": 0.9,
#                 "reasoning": "Default top_p for good diversity"
#             },
#             "presence_penalty": {
#                 "value": 0.0,
#                 "reasoning": "Default neutral presence penalty"
#             },
#             "frequency_penalty": {
#                 "value": 0.0,
#                 "reasoning": "Default neutral frequency penalty"
#             }
#         }
    
#     # def _extract_parameters(self, guidelines: Dict) -> Dict[str, float]:
#     #     """Extract parameters from guidelines"""
#     #     try:
#     #         params = guidelines.get('parameters', {})
#     #         if isinstance(params, dict):
#     #             if 'value' in params:
#     #                 param_values = params['value']
#     #                 return {
#     #                     'temperature': float(param_values.get('temperature', {}).get('value', 0.7)),
#     #                     'top_p': float(param_values.get('top_p', {}).get('value', 0.9)),
#     #                     'presence_penalty': float(param_values.get('presence_penalty', {}).get('value', 0.0)),
#     #                     'frequency_penalty': float(param_values.get('frequency_penalty', {}).get('value', 0.0))
#     #                 }
#     #         return {
#     #             'temperature': 0.7,
#     #             'top_p': 0.9,
#     #             'presence_penalty': 0.0,
#     #             'frequency_penalty': 0.0
#     #         }
#     #     except Exception as e:
#     #         self.logger.error(f"Error extracting parameters: {e}")
#     #         return {
#     #             'temperature': 0.7,
#     #             'top_p': 0.9,
#     #             'presence_penalty': 0.0,
#     #             'frequency_penalty': 0.0
#     #         }
        
#     def _generate_fallback_response(self, prompt: str, ai_type: str, style: str) -> Dict:
#         """Generate a fallback response when processing fails"""
#         return {
#             "original_prompt": prompt,
#             "response": {
#                 "prompts": [{
#                     "prompt": f"Develop a time management plan for tasks using {style} style on {ai_type} platform",
#                     "focus": "general time management"
#                 }]
#             },
#             "guidelines": "Fallback time management guidelines",
#             "parameters_used": {
#                 "temperature": 0.7,
#                 "top_p": 0.9,
#                 "presence_penalty": 0.0,
#                 "frequency_penalty": 0.0
#             },
#             "raw_analysis": {},
#             "ai_type": ai_type,
#             "style": style
#         }

#     def _format_response(self, prompt: str, final_response: Dict, guidelines: Dict, ai_type: str, style: str) -> Dict:
#         try:
#             # Normalize response content extraction
#             if isinstance(final_response, dict) and 'prompts' in final_response:
#                 # Directly use the prompts from the response
#                 prompts = final_response['prompts']
#             else:
#                 # Fallback to creating a prompt from the response content
#                 content = (
#                     final_response.get('choices', [{}])[0]
#                     .get('message', {})
#                     .get('content', str(final_response))
#                 )
#                 prompts = [{"prompt": content}]

#             # Extract parameters safely
#             parameters = ParameterManager.extract_parameters(guidelines)

#             # Prepare response structure
#             response = {
#                 "original_prompt": prompt,
#                 "response": {
#                     "prompts": prompts
#                 },
#                 "guidelines": guidelines.get('content', ''),
#                 "parameters_used": parameters,
#                 "raw_analysis": {
#                     "request_analysis": guidelines.get('request_analysis', {}),
#                     "technical_assessment": guidelines.get('technical_assessment', {})
#                 },
#                 "ai_type": ai_type,
#                 "style": style
#             }

#             return response

#         except Exception as e:
#             self.logger.error(f"Response formatting error for prompt '{prompt}': {e}")
#             return {
#                 "original_prompt": prompt,
#                 "response": {"prompts": [{"prompt": "Error processing response"}]},
#                 "ai_type": ai_type,
#                 "style": style
#             }

#     # def _extract_parameters(self, guidelines: Dict) -> Dict:
#     #     """Extract parameters safely from guidelines"""
#     #     default_params = {
#     #         'temperature': 0.7,
#     #         'top_p': 0.9,
#     #         'presence_penalty': 0.0,
#     #         'frequency_penalty': 0.0
#     #     }
        
#     #     if not guidelines:
#     #         return default_params
        
#     #     try:
#     #         params = guidelines.get('parameters', {}).get('value', {})
#     #         return {
#     #             'temperature': float(params.get('temperature', {}).get('value', default_params['temperature'])),
#     #             'top_p': float(params.get('top_p', {}).get('value', default_params['top_p'])),
#     #             'presence_penalty': float(params.get('presence_penalty', {}).get('value', default_params['presence_penalty'])),
#     #             'frequency_penalty': float(params.get('frequency_penalty', {}).get('value', default_params['frequency_penalty']))
#     #         }
#     #     except Exception as e:
#     #         self.logger.error(f"Parameter extraction error: {e}")
#     #         return default_params

#     # def _make_llama_call(self, system_message: str, prompt: str, **params) -> str:
#     #     try:
#     #         request_data = {
#     #             "messages": [
#     #                 {"role": "system", "content": system_message},
#     #                 {"role": "user", "content": prompt}
#     #             ],
#     #             "model": "llama3.2-1b",  # Specify newer model version
#     #             **params,
#     #             "max_tokens": 2000,
#     #             "stream": False
#     #         }
            
#     #         self.logger.debug(f"Request data: {request_data}")
#     #         response = llama.run(request_data)
            
#     #         response_data = response.json()
#     #         self.logger.debug(f"API Response: {response_data}")
            
#     #         if isinstance(response_data, list) and len(response_data) > 0:
#     #             if 'error' in response_data[0]:
#     #                 self.logger.error(f"API Error: {response_data[0]['error']}")
#     #                 return "{}"
                    
#     #         if isinstance(response_data, dict) and 'choices' in response_data:
#     #             if response_data['choices'] and isinstance(response_data['choices'], list):
#     #                 content = response_data['choices'][0].get('message', {}).get('content', '{}')
#     #                 return content
            
#     #         return "{}"
            
#     #     except Exception as e:
#     #         self.logger.error(f"API call failed: {e}")
#     #         return "{}"
        

    
#     # def _format_response(self, prompt: str, final_response: Dict, guidelines: Dict, ai_type: str, style: str) -> Dict:
#     #     """Format the response to match existing structure"""
#     #     try:
#     #         # Parse the guidelines content
#     #         if isinstance(guidelines, dict):
#     #             params = guidelines.get('parameters', {})
#     #             if isinstance(params, dict) and 'value' in params:
#     #                 parameters = params['value']
#     #             else:
#     #                 parameters = params
#     #         else:
#     #             parameters = {}

#     #         # Parse the response content into prompts format
#     #         response_content = final_response.get('choices', [{}])[0].get('message', {}).get('content', '')
#     #         prompts = self._format_prompts(response_content)

#     #         return {
#     #             "original_prompt": prompt,
#     #             "response": {"prompts": prompts},
#     #             "guidelines": guidelines.get('content', ''),
#     #             "parameters_used": parameters,
#     #             "raw_analysis": {
#     #                 "request_analysis": guidelines.get('request_analysis', {}),
#     #                 "technical_assessment": guidelines.get('technical_assessment', {}),
#     #                 "platform_specific": guidelines.get('platform_specific', {})
#     #             },
#     #             "ai_type": ai_type,
#     #             "style": style
#     #         }
#     #     except Exception as e:
#     #         self.logger.error(f"Error formatting response: {e}")
#     #         return self._generate_fallback_response(prompt, ai_type, style)
    
model_manager = None
try:
    model_manager = ModelManager()
    logger.info("Model Manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Model Manager: {e}")
    
# @app.route('/process', methods=['POST'])
# def process_request():
#     try:
#         if not llama or not model_manager:
#             return jsonify({"error": "Required services not configured"}), 500

#         data = request.form.get('data')
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         data = json.loads(data)
#         if 'prompt' not in data:
#             return jsonify({"error": "No prompt provided"}), 400

#         pipeline = PromptPipeline(logger)
#         response = pipeline.execute_pipeline(
#             prompt=data['prompt'],
#             ai_type=data.get('AIType', 'descriptive'),
#             style=data.get('style', 'professional')
#         )

#         return jsonify(response)

#     except Exception as e:
#         logger.error(f"Request error: {str(e)}")
#         return jsonify({"error": str(e)}), 500


@app.route('/process', methods=['POST'])
def process_request():
    """
    Enhanced request handler that supports both form data and JSON.
    Includes detailed error handling and request validation.
    """
    try:
        # First, log the incoming request details for debugging
        logger.info(f"Received request with Content-Type: {request.content_type}")
        
        # Get the data based on content type
        if request.is_json:
            # Handle JSON data
            data = request.get_json()
        elif request.content_type == 'application/x-www-form-urlencoded':
            # Handle form data
            form_data = request.form.get('data')
            if not form_data:
                return jsonify({
                    "status": "error",
                    "error": "No data provided in form",
                    "timestamp": datetime.datetime.now().isoformat()
                }), 400
            try:
                # Parse the JSON string from form data
                data = json.loads(form_data)
            except json.JSONDecodeError as e:
                return jsonify({
                    "status": "error",
                    "error": f"Invalid JSON in form data: {str(e)}",
                    "timestamp": datetime.datetime.now().isoformat()
                }), 400
        else:
            # Invalid content type
            return jsonify({
                "status": "error",
                "error": f"Unsupported Content-Type: {request.content_type}. Expected 'application/json' or 'application/x-www-form-urlencoded'",
                "timestamp": datetime.datetime.now().isoformat()
            }), 415

        # Validate required fields
        if 'prompt' not in data:
            return jsonify({
                "status": "error",
                "error": "No prompt provided in request data",
                "timestamp": datetime.datetime.now().isoformat()
            }), 400

        # Initialize pipeline and process the request
        pipeline = EnhancedPromptPipeline(logger)
        response = pipeline.execute_pipeline(
            prompt=data['prompt'],
            ai_type=data.get('AIType', 'descriptive'),
            style=data.get('style', 'professional')
        )

        # Optional: Add a response handler to format the output
        formatted_response = ResponseHandler(logger).format_response(response)
        
        return jsonify(formatted_response)

    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500
    
    
@app.route('/process', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', request.origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)
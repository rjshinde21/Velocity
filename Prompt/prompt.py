import traceback
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
import os
import logging
from typing import Dict, Any, List, Tuple, Union, Optional
from logging import Logger
from llamaapi import LlamaAPI
import re
from transformers import pipeline
import spacy
from spacy import load  # Remove this line if using spacy.load directly
import textstat
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import nltk
from nltk.tokenize import sent_tokenize
import uuid
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
            default_params = {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            }
            
            if not parameters:
                return default_params

            clean_params = {}
            for key, default in default_params.items():
                param = parameters.get(key, {})
                if isinstance(param, dict):
                    value = param.get('value', default)
                else:
                    value = float(param) if param is not None else default
                clean_params[key] = float(value)
                
            return clean_params
            
        except Exception as e:
            logger.error(f"Parameter extraction failed: {str(e)}")
            return default_params
        
class ContextTracker:
    def __init__(self):
        self.context_chain = []  # Main storage for all context
        self.last_context = {}   # Replaces current_context
        self.metadata = {
            "creation_timestamp": datetime.datetime.now(),
            "total_stages_processed": 0
        }

    def _propagate_style_requirements(self, context_entry: Dict) -> Dict:
        """Ensure style requirements are propagated through context chain"""
        base_style = self.get_stage_context("base_configuration")
        if base_style:
            context_entry["inherited_style"] = {
                "style_type": base_style.get("style"),
                "ai_system": base_style.get("ai_type"),
                "style_metadata": base_style.get("style_metadata", {})
            }
        return context_entry

    def _clean_context(self, context: Dict) -> Dict:
        """Remove redundant and unnecessary context data"""
        if not isinstance(context, dict):
            return context
            
        essential_fields = {
            "content", "result", "metadata", "requirements", 
            "style", "ai_type", "parameters"
        }
        
        return {
            k: self._clean_context(v) if isinstance(v, dict) else v 
            for k, v in context.items() 
            if k in essential_fields
        }

    def add_context(self, stage_name: str, context: Dict) -> None:
        try:
            # Get base style requirements
            base_style = self.get_stage_context("base_configuration")
            
            # Create cleaned context entry
            context_entry = {
                "stage": stage_name,
                "data": self._clean_context(context),
                "timestamp": datetime.datetime.now().isoformat(),
                "sequence": len(self.context_chain),
                "style_requirements": base_style if base_style else {},
            }
            
            # Add only essential previous context
            if self.context_chain:
                last_context = self.context_chain[-1]["data"]
                context_entry["inherited_context"] = {
                    "style": last_context.get("style"),
                    "ai_type": last_context.get("ai_type"),
                    "requirements": last_context.get("requirements", [])
                }
            
            self.context_chain.append(context_entry)
            self.last_context = self._clean_context(context)
            self.metadata["total_stages_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to add context for stage {stage_name}: {str(e)}")
            self.last_context = {"error": str(e), "stage": stage_name}

    def _enrich_context(self, current_stage_result: Dict, previous_context: Dict) -> Dict:
        """Intelligently merge current stage result with previous context"""
        enriched_context = previous_context.copy()
        
        # Define stage-specific enrichment rules
        enrichment_mapping = {
            'analysis': ['intent', 'requirements', 'context'],
            'feedback': ['alignment_analysis', 'completeness_check', 'improvement_areas'],
            'guidelines': ['guidelines', 'parameters', 'implementation_notes'],
            'enhancement': ['prompts']
        }
        
        # Determine stage and apply appropriate enrichment
        stage_name = current_stage_result.get('_stage_metadata', {}).get('stage_name')
        if stage_name in enrichment_mapping:
            for key in enrichment_mapping[stage_name]:
                if key in current_stage_result:
                    enriched_context[key] = current_stage_result[key]
        
        # Add stage completion metadata
        enriched_context['_metadata'] = {
            'last_updated_stage': stage_name,
            'updated_at': datetime.datetime.now().isoformat(),
            'stage_sequence': len(enriched_context.get('_metadata', {}).get('completed_stages', [])) + 1
        }
        
        return enriched_context

    def add_stage_result(self, stage_name: str, result: Dict):
        sequence_num = len(self.context_chain)
        stage_entry = {
            "stage": stage_name,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat(),
            "sequence": sequence_num,
            "metadata": {
                "stage_position": sequence_num,
                "total_stages": sequence_num + 1
            }
        }
        self.context_chain.append(stage_entry)
        self.metadata["total_stages_processed"] += 1

    def _extract_dependencies(self, result: Dict) -> List[str]:
        """Extract stage dependencies from result"""
        dependencies = []
        if isinstance(result, dict):
            # Look for references to previous stages
            for key in result.keys():
                if key.endswith('_ref') and isinstance(result[key], str):
                    dependencies.append(result[key].split('_ref')[0])
        return dependencies

    def add_context(self, stage_name: str, context: Dict) -> None:
        """Add new context for a stage with proper error handling"""
        try:
            context_entry = {
                "stage": stage_name,
                "data": context,
                "timestamp": datetime.datetime.now().isoformat(),
                "sequence": len(self.context_chain)
            }
            self.context_chain.append(context_entry)
            self.last_context = context  # Update last context
            self.metadata["total_stages_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to add context for stage {stage_name}: {str(e)}")
            # Create minimal valid context on error
            self.last_context = {"error": str(e), "stage": stage_name}

    def get_latest_context(self) -> Dict:
        """Get the most recent context"""
        return self.last_context if self.last_context else {}

    def get_stage_context(self, stage_name: str) -> Dict:
        """Get context for a specific stage"""
        for entry in reversed(self.context_chain):
            if entry["stage"] == stage_name:
                return entry["data"]
        return {}

    def get_full_context(self) -> Dict:
        """Get the complete context history"""
        return {
            "context_chain": self.context_chain,
            "metadata": self.metadata,
            "current_context": self.current_context
        }

    def _extract_insights(self, stage_result: Dict) -> Dict:
        """
        Extract meaningful insights from stage results.
        Enables intelligent context propagation.
        """
        insights = {}
        
        # Generic insight extraction strategy
        for key, value in stage_result.items():
            if isinstance(value, (str, list, dict)) and value:
                insights[key] = {
                    "type": type(value).__name__,
                    "length": len(value) if hasattr(value, '__len__') else None,
                    "non_empty": bool(value)
                }
        
        return insights

    def get_context(self, 
                    last_n_stages: int = None, 
                    include_insights: bool = True) -> List[Dict]:
        """
        Retrieve context with flexible filtering options.
        
        Args:
            last_n_stages: Number of recent stages to retrieve
            include_insights: Whether to include derived insights
        """
        if last_n_stages is not None:
            context_slice = self.context_chain[-last_n_stages:]
        else:
            context_slice = self.context_chain
        
        if not include_insights:
            return [
                {k: v for k, v in entry.items() if k != 'insights'} 
                for entry in context_slice
            ]
        
        return context_slice

    def get_cumulative_context(self) -> Dict:
        """
        Generate a cumulative context representing the entire pipeline's evolution.
        """
        cumulative_context = {}
        for entry in self.context_chain:
            cumulative_context[entry['stage']] = entry['result']
        
        return {
            "context": cumulative_context,
            "metadata": self.metadata
        }
    
    def add_stage_result(self, stage_name: str, result: Dict, metadata: Dict = None):
        """Enhanced stage result addition with metadata tracking"""
        stage_entry = {
            "stage": stage_name,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat(),
            "sequence": len(self.context_chain),
            "metadata": metadata or {},
            "dependencies": self._extract_dependencies(result)
        }
        self.context_chain.append(stage_entry)
        self.metadata["total_stages_processed"] += 1

    def get_previous_stage_results(self, current_stage: str) -> List[Dict]:
        """Get all previous stage results up to current stage"""
        stage_index = next(
            (i for i, ctx in enumerate(self.context_chain) 
             if ctx["stage"] == current_stage), 
            len(self.context_chain)
        )
        return self.context_chain[:stage_index]


class APIHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.retry_count = 3
        self.base_delay = 1

    def make_api_call(self, system_message: str, prompt: str, **params) -> Dict:
        try:
            response = llama.run({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "model": "llama3.2-1b",
                "stream": False,
                **params
            })

            if hasattr(response, 'json'):
                response_data = response.json()
                
                # Extract content from Llama API response
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    if 'message' in response_data['choices'][0]:
                        content = response_data['choices'][0]['message'].get('content', '')
                    else:
                        content = response_data['choices'][0].get('text', '')
                        
                    return {
                        "content": content,
                        "_metadata": {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "response_type": "message"
                        }
                    }

            raise ValueError("Invalid response structure from API")
            
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            return {"error": str(e)}

    def _extract_clean_parameters(self, params: Dict) -> Dict:
        default = {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,  
            'frequency_penalty': 0.0
        }

        try:
            return {
                k: float(params.get(k, v))
                for k, v in default.items()
            }
        except:
            return default
                
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

    def _create_enhanced_system_message(self, original_message: str) -> str:
        """
        Enhances system messages with strict JSON formatting requirements.
        This ensures consistent response formats across all API calls.
        """
        json_requirements = """
        CRITICAL RESPONSE REQUIREMENTS:
        1. Response MUST be a valid JSON object
        2. DO NOT include any markdown, explanation text, or code blocks
        3. DO NOT use ```json``` tags or other formatting
        4. All strings must use double quotes
        5. Response must be parseable by json.loads()
        
        Example Valid Response Format:
        {
            "key1": "value1",
            "key2": ["item1", "item2"],
            "key3": {
                "nested_key": "nested_value"
            }
        }
        """
        return f"{original_message}\n\n{json_requirements}"

    def _build_messages(self, system_message: str, prompt: str, context: Dict = None) -> List[Dict]:
        """
        Builds the messages array with proper ordering and structure.
        Includes context when provided.
        """
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        if context:
            context_message = self._format_context(context)
            messages.append({
                "role": "system",
                "content": f"Additional Context:\n{context_message}"
            })
        
        messages.append({"role": "user", "content": prompt})
        return messages

    def _execute_api_call(self, messages: List[Dict], params: Dict) -> Dict:
        """
        Executes the actual API call with proper logging and validation.
        """
        request_data = {
            "messages": messages,
            "model": "llama3.2-1b",
            "max_tokens": 2000,
            "stream": False,
            **params
        }
        
        self.logger.debug(f"API Request:\n{json.dumps(request_data, indent=2)}")
        
        response = llama.run(request_data)
        if not response:
            raise ValueError("Empty response received from API")
            
        response_data = response.json()
        self.logger.debug(f"Raw API Response:\n{json.dumps(response_data, indent=2)}")
        
        return response_data

    def _process_response(self, response_data: Dict) -> Dict:
        """Enhanced response processing with proper Llama API response handling"""
        try:
            # Check if it's a raw API response object
            if hasattr(response_data, 'json'):
                response_data = response_data.json()

            if not isinstance(response_data, dict):
                raise ValueError("Response is not a dictionary")
                
            content = None
            # Handle Llama API response structure
            if 'choices' in response_data:
                first_choice = response_data['choices'][0]
                if 'message' in first_choice:
                    content = first_choice['message'].get('content', '')
                elif 'text' in first_choice:
                    content = first_choice['text']
            
            if not content:
                raise ValueError("No content in response")
            
            # Clean and validate JSON structure
            cleaned_content = self._clean_content(content)
            try:
                # First attempt to parse as pure JSON
                parsed_json = json.loads(cleaned_content)
                return self._validate_and_structure_json(parsed_json)
                
            except json.JSONDecodeError:
                # If not valid JSON, convert markdown/text to structured JSON
                structured_content = self._convert_to_json_structure(cleaned_content)
                return self._validate_and_structure_json(structured_content)
                
        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            return self._create_error_response(str(e))
        
    def _enhance_system_message(self, system_message: str, style: str, ai_type: str) -> str:
        """Enhance system message with style and AI type requirements"""
        style_prefix = f"""You are an expert in {ai_type} systems, specializing in {style} communication.
        All responses must maintain:
        - {style} style consistently throughout
        - Appropriate tone for {ai_type} systems
        - Technical accuracy while maintaining style
        """
        return f"{style_prefix}\n\n{system_message}"
    def _validate_and_structure_json(self, content: Dict) -> Dict:
        """Ensure response follows required JSON structure"""
        if not isinstance(content, dict):
            content = {"content": content}
            
        # Add required metadata
        content["_metadata"] = {
            "processed_timestamp": datetime.datetime.now().isoformat(),
            "processing_stage": "api_response",
            "format_version": "2.0"
        }
        
        # Convert any non-JSON-compliant values
        return self._ensure_json_compliance(content)

    def _ensure_json_compliance(self, obj: Any) -> Any:
        """Recursively ensure all values are JSON-compliant"""
        if isinstance(obj, dict):
            return {k: self._ensure_json_compliance(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_json_compliance(v) for v in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)

    def _convert_to_json_structure(self, content: str) -> Dict:
        """Convert markdown/text content to structured JSON"""
        # Extract sections using regex
        section_pattern = r'#{1,6}\s+([^#\n]+)(?:\n((?:(?!#).*\n?)*))?'
        sections = re.findall(section_pattern, content, re.MULTILINE)
        
        if sections:
            structured_content = {}
            for title, content in sections:
                key = title.strip().lower().replace(' ', '_')
                # Convert bullet points to arrays
                if '*' in content:
                    items = re.findall(r'\*\s+([^\n]+)', content)
                    structured_content[key] = items
                else:
                    structured_content[key] = content.strip()
            return {
                "structured_content": structured_content,
                "format_type": "structured",
                "original_format": "markdown"
            }
        else:
            # Handle plain text
            return {
                "content": content.strip(),
                "format_type": "plain_text"
            }

    def _convert_to_structured_format(self, content: str) -> Dict:
        """
        Converts unstructured text content into a structured format.
        This method handles cases where the API response isn't valid JSON
        but still contains valuable information that we want to preserve.
        
        Args:
            content (str): The cleaned content string to convert
            
        Returns:
            Dict: A structured representation of the content
        """
        try:
            # First, try to identify sections using markdown-style headers
            sections = self._extract_sections(content)
            if sections:
                return {
                    "structured_content": sections,
                    "format": "sectioned",
                    "_metadata": {
                        "processed_timestamp": datetime.datetime.now().isoformat(),
                        "processing_stage": "markdown_conversion",
                        "original_content_hash": hash(content)
                    }
                }
            
            # If no sections found, try to parse as bullet points
            bullets = self._extract_bullet_points(content)
            if bullets:
                return {
                    "structured_content": bullets,
                    "format": "bullet_points",
                    "_metadata": {
                        "processed_timestamp": datetime.datetime.now().isoformat(),
                        "processing_stage": "bullet_conversion",
                        "original_content_hash": hash(content)
                    }
                }
            
            # If no structure detected, store as plain text with metadata
            return {
                "content": content,
                "format": "plain_text",
                "_metadata": {
                    "processed_timestamp": datetime.datetime.now().isoformat(),
                    "processing_stage": "plain_text_conversion",
                    "original_content_hash": hash(content)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Structure conversion failed: {str(e)}")
            return {
                "error": str(e),
                "original_content": content,
                "_metadata": {
                    "error_timestamp": datetime.datetime.now().isoformat(),
                    "processing_stage": "conversion_error"
                }
            }

    def _extract_sections(self, content: str) -> Dict[str, Any]:
        """
        Extracts sections from markdown-style headers in the content.
        
        Args:
            content (str): Content to parse
            
        Returns:
            Dict[str, Any]: Dictionary of sections and their content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for markdown headers
            if line.strip().startswith('#'):
                # If we were building a section, save it
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                    current_content = []
                
                # Start new section
                current_section = line.strip('#').strip()
            elif current_section:
                current_content.append(line)
            else:
                # Content before any section headers
                if not sections.get('introduction'):
                    sections['introduction'] = []
                sections['introduction'].append(line)
        
        # Save the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections

    def _extract_bullet_points(self, content: str) -> List[str]:
        """
        Extracts bullet points from the content.
        
        Args:
            content (str): Content to parse
            
        Returns:
            List[str]: List of bullet points
        """
        bullets = []
        current_bullet = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            # Check for common bullet point markers
            if stripped.startswith(('•', '-', '*', '+')):
                # Save previous bullet if exists
                if current_bullet:
                    bullets.append(' '.join(current_bullet).strip())
                    current_bullet = []
                # Start new bullet
                current_bullet.append(stripped[1:].strip())
            elif current_bullet and stripped:
                # Continue previous bullet
                current_bullet.append(stripped)
                
        # Save last bullet
        if current_bullet:
            bullets.append(' '.join(current_bullet).strip())
            
        return bullets

    def _clean_content(self, content: str) -> str:
        """
        Cleans response content by removing formatting artifacts.
        """
        content = content.strip()
        # Remove markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        return content.strip()

    def _convert_markdown_to_json(self, markdown_content: str) -> Dict:
        """
        Converts markdown-formatted content to a structured JSON object.
        This ensures consistent JSON output even when the API returns markdown.
        """
        # Extract sections from markdown using regex
        sections = re.findall(r'\*\*(.*?)\*\*:(.*?)(?=\*\*|$)', markdown_content, re.DOTALL)
        
        structured_response = {}
        for section_title, section_content in sections:
            # Clean section title and content
            title = section_title.strip().lower().replace(' ', '_')
            content = section_content.strip()
            
            # Convert bullet points to arrays
            if '*' in content:
                items = re.findall(r'\*(.*?)(?=\*|$)', content)
                structured_response[title] = [item.strip() for item in items if item.strip()]
            else:
                structured_response[title] = content
                
        return structured_response if structured_response else {
            "raw_content": markdown_content,
            "error": "Could not parse markdown into structured format"
        }

    def _create_error_response(self, error_msg: str) -> Dict:
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def _extract_parameters(self, context: Dict) -> Dict:
        """Extract parameters from context with proper inheritance"""
        try:
            # Get feedback stage parameters if available
            feedback_result = context.get("stage_results", {}).get("feedback", {}).get("result", {})
            parameters = feedback_result.get("parameter_recommendations", {})
            
            # Validate and clean parameters
            clean_params = {}
            param_bounds = {
                "temperature": (0.1, 1.0),
                "top_p": (0.1, 1.0),
                "presence_penalty": (-2.0, 2.0),
                "frequency_penalty": (-2.0, 2.0)
            }
            
            for param_name, (min_val, max_val) in param_bounds.items():
                value = parameters.get(param_name, {}).get("value", 0.7)
                clean_params[param_name] = max(min_val, min(max_val, float(value)))
                
            return clean_params
            
        except Exception as e:
            self.logger.error(f"Parameter extraction failed: {str(e)}")
            return {
                "temperature": 0.7,
                "top_p": 0.9,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }


class PromptPreprocessor:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.model_manager = ModelManager()
        self.nlp = self.model_manager.models['nlp']
        self.sentiment_analyzer = self.model_manager.models['sentiment_analyzer']
        self.keyword_model = self.model_manager.models['keyword_model']
        self.semantic_model = self.model_manager.models['semantic_model']

    def _determine_relationship_type(self, similarity_score: float) -> str:
        """Determine relationship type based on similarity score"""
        if similarity_score > 0.8:
            return 'strong_continuation'
        elif similarity_score > 0.5:
            return 'moderate_continuation'
        else:
            return 'weak_continuation'

    def _analyze_semantic_relationships(self, doc) -> Dict:
        """Analyze semantic relationships between sentences"""
        sentences = [sent.text for sent in doc.sents]
        embeddings = self.semantic_model.encode(sentences)
        
        # Missing numpy import
        
        
        relationships = []
        for i in range(len(embeddings)-1):
            # Improved similarity calculation with error handling
            try:
                similarity = np.dot(embeddings[i], embeddings[i+1]) / \
                        (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i+1]))
                relationship_type = self._determine_relationship_type(similarity)
                relationships.append({
                    'sentence_pair': (i, i+1),
                    'similarity_score': float(similarity),
                    'relationship_type': relationship_type
                })
            except Exception as e:
                self.logger.error(f"Error calculating similarity: {e}")
                relationships.append({
                    'sentence_pair': (i, i+1),
                    'similarity_score': 0.0,
                    'relationship_type': 'unknown'
                })
        
        return {
            'sentence_relationships': relationships,
            'coherence_score': float(np.mean([r['similarity_score'] for r in relationships])) if relationships else 0.0
        }

    def _analyze_discourse_structure(self, doc) -> Dict:
        """Analyze discourse elements and rhetorical structure"""
        discourse_markers = {
            'causal': ['because', 'therefore', 'thus', 'hence'],
            'contrast': ['however', 'but', 'although', 'despite'],
            'sequence': ['first', 'then', 'finally', 'next'],
            'elaboration': ['for example', 'specifically', 'in particular']
        }
        
        structure = {category: [] for category in discourse_markers}
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            for category, markers in discourse_markers.items():
                for marker in markers:
                    if marker in sent_text:
                        structure[category].append({
                            'sentence': sent.text,
                            'marker': marker
                        })
        
        return {
            'discourse_structure': structure,
            'primary_discourse_type': max(structure.items(), key=lambda x: len(x[1]))[0]
        }

    # def analyze_prompt(self, prompt_input: Union[str, Dict]) -> Dict:
    #     """
    #     Enhanced prompt analysis with deeper NLP insights
        
    #     Extends existing preprocessing with advanced intent and context analysis
    #     """
    #     # Log the start of analysis
    #     self.logger.info(f"Starting enhanced prompt analysis")
        
    #     # Extract prompt string if input is dict
    #     prompt = prompt_input['original_prompt'] if isinstance(prompt_input, dict) else prompt_input
        
    #     # Existing preprocessing analysis
    #     self.logger.debug("Performing base linguistic analysis")
    #     base_analysis = super().analyze_prompt(prompt_input)
        
    #     # Intent Classification Enhancement
    #     self.logger.info("Classifying prompt intent")
    #     intent_classification = self._classify_intent(prompt)
    #     base_analysis['intent_classification'] = intent_classification
        
    #     # AI Role/Persona Determination
    #     self.logger.info("Determining AI persona")
    #     ai_persona = self._determine_ai_persona(intent_classification, prompt)
    #     base_analysis['ai_persona'] = ai_persona
        
    #     # Contextual Requirement Extraction
    #     self.logger.info("Extracting contextual requirements")
    #     contextual_requirements = self._extract_contextual_requirements(prompt)
    #     base_analysis['contextual_requirements'] = contextual_requirements
        
    #     # Domain Identification
    #     self.logger.info("Identifying domain and expertise level")
    #     domain_insights = self._identify_domain(prompt)
    #     base_analysis['domain_insights'] = domain_insights
        
    #     # Logging the comprehensive analysis
    #     self.logger.debug(f"Comprehensive Prompt Analysis: {json.dumps(base_analysis, indent=2)}")
        
    #     return base_analysis
    def analyze_prompt(self, prompt_input: Union[str, Dict]) -> Dict:
        """
        Enhanced prompt analysis with deeper NLP insights
        """
        # Log the start of analysis
        self.logger.info(f"Starting enhanced prompt analysis")
        
        # Extract prompt string if input is dict
        prompt = prompt_input['original_prompt'] if isinstance(prompt_input, dict) else prompt_input
        
        # Perform linguistic analysis using spaCy
        doc = self.nlp(prompt)
        linguistic_patterns = {
        'technical_terms': [],
        'action_verbs': [],
        'domain_concepts': [],
        'modifiers': []
        }

        for token in doc:
            if token.pos_ == 'VERB':
                linguistic_patterns['action_verbs'].append(token.text)
            elif token.pos_ == 'NOUN' and not token.is_stop:
                linguistic_patterns['domain_concepts'].append(token.text)
            elif token.pos_ in ['ADJ', 'ADV']:
                linguistic_patterns['modifiers'].append(token.text)
            
        
        # Sentiment analysis
        sentiment_result = self.sentiment_analyzer(prompt)[0]
        
        # Keyword extraction
        keywords = self.keyword_model.extract_keywords(
            prompt, 
            top_n=5, 
            stop_words='english'
        )
        
        # Named entity recognition
        named_entities = [
            {
                "text": ent.text, 
                "label": ent.label_
            } for ent in doc.ents
        ]

        enhanced_entities = [{
            'text': ent.text,
            'label': ent.label_,
            'confidence': self._calculate_entity_confidence(ent)
         } for ent in doc.ents]
        
        
        
        # Linguistic features
        linguistic_features = self._extract_linguistic_features(doc)
        
        # Complexity analysis
        complexity_metrics = {
            "flesch_score": textstat.flesch_reading_ease(prompt),
            "grade_level": textstat.coleman_liau_index(prompt),
            "sentence_count": len(list(doc.sents)),
            "word_count": len([token for token in doc if not token.is_punct])
        }
        
        # Intent Classification Enhancement
        intent_classification = self._classify_intent(prompt)
        
        # AI Role/Persona Determination
        ai_persona = self._determine_ai_persona(intent_classification, prompt)
        
        # Contextual Requirement Extraction
        contextual_requirements = self._extract_contextual_requirements(prompt)
        
        # Domain Identification
        domain_insights = self._identify_domain(prompt)
        
        # Comprehensive analysis dictionary
        comprehensive_analysis = {
            "content_analysis": {
                "named_entities": named_entities,
                "keywords": [kw[0] for kw in keywords],
                "topics": self._extract_topics(prompt),
                "sentiment": {
                    "label": sentiment_result['label'],
                    "score": sentiment_result['score']
                }
            },
            "linguistic_features": {
                "complexity_metrics": complexity_metrics,
                "structural_features": linguistic_features
            },
            "intent_classification": intent_classification,
            "ai_persona": ai_persona,
            "contextual_requirements": contextual_requirements,
            "domain_insights": domain_insights,
            
            # Maintaining compatibility with existing code
            "keywords": [kw[0] for kw in keywords],
            "named_entities": named_entities,
            "sentiment": sentiment_result['label'],
            "complexity_score": complexity_metrics['flesch_score'],
            "sentence_count": complexity_metrics['sentence_count'],
            "word_count": complexity_metrics['word_count']
        }
        
        # Logging the comprehensive analysis
        self.logger.debug(f"Comprehensive Prompt Analysis: {json.dumps(comprehensive_analysis, indent=2)}")
        
        return comprehensive_analysis
    def _classify_intent(self, prompt: str) -> Dict:
        """
        Advanced intent classification using existing NLP capabilities
        """
        self.logger.debug(f"Classifying intent for prompt: {prompt}")
        
        # Intent classification patterns
        intent_patterns = {
            "task_completion": ["create", "develop", "build", "generate", "implement"],
            "information_gathering": ["explain", "describe", "analyze", "breakdown", "understand"],
            "problem_solving": ["solve", "resolve", "fix", "address", "troubleshoot"],
            "creative_generation": ["write", "design", "compose", "imagine", "draft"],
            "strategic_planning": ["plan", "strategy", "roadmap", "outline", "propose"]
        }
        
        # Use spaCy for linguistic analysis
        doc = self.nlp(prompt.lower())
        
        # Detect intent based on verb patterns and semantic analysis
        detected_intents = []
        for intent_type, keywords in intent_patterns.items():
            if any(keyword in prompt.lower() for keyword in keywords):
                detected_intents.append(intent_type)
        
        # Fallback to semantic analysis if no direct pattern match
        if not detected_intents:
            # Use sentence structure and verb types from spaCy
            verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
            if verbs:
                detected_intents = self._infer_intent_from_verbs(verbs)
        
        # Confidence calculation
        confidence = len(detected_intents) / len(intent_patterns)
        
        intent_result = {
            "primary_intent": detected_intents[0] if detected_intents else "general",
            "possible_intents": detected_intents,
            "confidence_score": confidence
        }
        
        self.logger.info(f"Intent Classification Result: {intent_result}")
        return intent_result

    def _determine_ai_persona(self, intent_classification: Dict, prompt: str) -> Dict:
        """
        Determine appropriate AI persona based on intent and prompt characteristics
        """
        self.logger.debug("Determining AI persona")
        
        persona_mapping = {
            "task_completion": {
                "role": "Technical Consultant",
                "communication_style": "professional",
                "traits": ["analytical", "precise", "solution-oriented"]
            },
            "information_gathering": {
                "role": "Research Analyst",
                "communication_style": "informative",
                "traits": ["thorough", "detailed", "objective"]
            },
            "problem_solving": {
                "role": "Strategic Advisor",
                "communication_style": "pragmatic",
                "traits": ["critical-thinking", "methodical", "solution-focused"]
            },
            "creative_generation": {
                "role": "Creative Collaborator",
                "communication_style": "imaginative",
                "traits": ["innovative", "flexible", "inspirational"]
            },
            "strategic_planning": {
                "role": "Strategic Planner",
                "communication_style": "structured",
                "traits": ["visionary", "systematic", "forward-thinking"]
            }
        }
        
        # Default to general persona
        primary_intent = intent_classification.get('primary_intent', 'general')
        persona = persona_mapping.get(primary_intent, {
            "role": "General Assistant",
            "communication_style": "balanced",
            "traits": ["adaptable", "helpful"]
        })
        
        # Additional persona refinement based on prompt complexity
        doc = self.nlp(prompt)
        complexity_factors = {
            "sentence_length": len(doc),
            "named_entities": len(list(doc.ents)),
            "verb_diversity": len(set(token.lemma_ for token in doc if token.pos_ == "VERB"))
        }
        
        persona["complexity_assessment"] = complexity_factors
        
        self.logger.info(f"Recommended AI Persona: {persona}")
        return persona

    def _extract_contextual_requirements(self, prompt: str) -> Dict:
        """
        Extract explicit and implicit requirements from the prompt
        """
        self.logger.debug("Extracting contextual requirements")
        
        doc = self.nlp(prompt)
        
        # Extract named entities as potential requirements
        named_entities = [
            {
                "text": ent.text, 
                "label": ent.label_
            } for ent in doc.ents
        ]
        
        # Use dependency parsing to identify potential requirements
        potential_requirements = [
            token.text for token in doc 
            if token.dep_ in ['dobj', 'attr', 'xcomp']
        ]
        
        requirements = {
            "named_entities": named_entities,
            "potential_requirements": potential_requirements,
            "raw_requirements": [chunk.text for chunk in doc.noun_chunks]
        }
        
        self.logger.info(f"Extracted Requirements: {requirements}")
        return requirements

    def _identify_domain(self, prompt: str) -> Dict:
        """
        Identify the specific domain of the request
        """
        self.logger.debug("Identifying domain and expertise level")
        
        domain_keywords = {
            "Technical": ["code", "develop", "algorithm", "system", "software", "programming"],
            "Creative": ["write", "design", "imagine", "story", "creative", "art"],
            "Business": ["strategy", "plan", "market", "business", "sales", "management"],
            "Academic": ["research", "study", "analysis", "academic", "scientific"],
            "Personal": ["help", "advice", "personal", "guidance"]
        }
        
        # Detect domain based on keyword presence
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in prompt.lower() for keyword in keywords):
                detected_domains.append(domain)
        
        # Complexity and expertise assessment
        doc = self.nlp(prompt)
        complexity_indicators = {
            "vocabulary_complexity": textstat.flesch_reading_ease(prompt),
            "sentence_complexity": len(doc),
            "technical_term_count": len([token for token in doc if token.pos_ == "NOUN" and token.is_stop == False])
        }
        
        domain_result = {
            "primary_domain": detected_domains[0] if detected_domains else "general",
            "possible_domains": detected_domains,
            "expertise_level": self._assess_expertise_level(complexity_indicators)
        }
        
        self.logger.info(f"Domain Identification Result: {domain_result}")
        return domain_result

    def _assess_expertise_level(self, complexity_indicators: Dict) -> str:
        """
        Assess expertise level based on complexity indicators
        """
        vocabulary_complexity = complexity_indicators['vocabulary_complexity']
        technical_term_count = complexity_indicators['technical_term_count']
        
        if vocabulary_complexity < 30 and technical_term_count < 3:
            return "beginner"
        elif 30 <= vocabulary_complexity < 50 and 3 <= technical_term_count < 7:
            return "intermediate"
        else:
            return "advanced"
        
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        try:
            # Use KeyBERT for topic extraction
            topics = self.keyword_model.extract_keywords(text, 
                                                    top_n=3,
                                                    stop_words='english',
                                                    use_maxsum=True,
                                                    diversity=0.7)
            return [topic[0] for topic in topics]
        except Exception:
            return []
        

    def _calculate_sentence_complexity(self, doc) -> Dict:
        """Calculate various sentence complexity metrics"""
        sentences = list(doc.sents)
        return {
            "max_depth": max((len(list(sent.rights)) + len(list(sent.lefts))) for sent in sentences) if sentences else 0,
            "avg_depth": sum((len(list(sent.rights)) + len(list(sent.lefts))) for sent in sentences) / len(sentences) if sentences else 0,
            "compound_sentences": sum(1 for sent in sentences if "and" in sent.text.lower() or "but" in sent.text.lower() or "or" in sent.text.lower())
        }
    

    def _calculate_avg_sentence_length(self, doc) -> float:
        """Calculate average sentence length"""
        sentences = list(doc.sents)
        return sum(len([token for token in sent if not token.is_punct]) for sent in sentences) / len(sentences) if sentences else 0

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
    

class ErrorHandler:
    @staticmethod
    def handle_stage_error(stage_name: str, error: Exception, context: Dict) -> Dict:
        """Handle stage-specific errors with recovery options"""
        error_response = {
            "status": "error",
            "stage": stage_name,
            "error": str(error),
            "timestamp": datetime.datetime.now().isoformat(),
            "context": {
                "stage_name": stage_name,
                "original_prompt": context.get("original_prompt"),
                "ai_type": context.get("ai_type"),
                "style": context.get("style")
            }
        }
        
        # Add recovery attempt if possible
        try:
            recovery_result = ErrorHandler._attempt_recovery(stage_name, context)
            if recovery_result:
                error_response["recovery_result"] = recovery_result
        except Exception as recovery_error:
            error_response["recovery_error"] = str(recovery_error)
            
        return error_response

class ResponseValidator:
    """Validate and process API responses"""
    
    @staticmethod
    def validate_response(response: Dict, expected_structure: Dict) -> Tuple[bool, Dict]:
        """
        Comprehensive response validation with structured error reporting.
        
        Args:
            response (Dict): Raw API response
            expected_structure (Dict): Expected response schema
        
        Returns:
            Tuple of (validation_status, processed_response/error_details)
        """
        try:
            # Deep structural validation
            def validate_structure(response, structure):
                errors = []
                for key, expected_type in structure.items():
                    if key not in response:
                        errors.append(f"Missing required key: {key}")
                        continue
                    
                    if isinstance(expected_type, type):
                        if not isinstance(response[key], expected_type):
                            errors.append(f"Invalid type for {key}: Expected {expected_type}, Got {type(response[key])}")
                    
                    elif isinstance(expected_type, dict):
                        sub_errors = validate_structure(response[key], expected_type)
                        errors.extend([f"{key}.{err}" for err in sub_errors])
                
                return errors

            validation_errors = validate_structure(response, expected_structure)
            
            if validation_errors:
                return False, {
                    "status": "validation_error",
                    "errors": validation_errors,
                    "original_response": response
                }
            
            # Additional sanitization and processing
            sanitized_response = ResponseValidator.sanitize_response(response)
            
            return True, sanitized_response
        
        except Exception as e:
            return False, {
                "status": "processing_error",
                "error": str(e),
                "original_response": response
            }
    
    @staticmethod
    def sanitize_response(response: Dict) -> Dict:
        """
        Clean and normalize response, handling potential inconsistencies.
        """
        sanitized = {}
        for key, value in response.items():
            # Remove None values
            if value is not None:
                # Handle nested dictionaries recursively
                if isinstance(value, dict):
                    sanitized[key] = ResponseValidator.sanitize_response(value)
                # Convert lists, ensuring no None elements
                elif isinstance(value, list):
                    sanitized[key] = [item for item in value if item is not None]
                else:
                    sanitized[key] = value
        
        return sanitized





    

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



class PipelineStage:
    """Base class for pipeline stages with common functionality"""
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        self.logger = logger
        self.api_handler = api_handler
        self.context_tracker = context_tracker

    def _preserve_stage_context(self, current_stage: str, result: Dict, previous_context: Dict) -> Dict:
        """Enhanced context preservation between stages"""
        try:
            # Extract core style and AI type information
            style_info = previous_context.get("metadata", {}).get("style_requirements", {})
            
            # Create stage-specific context
            stage_context = {
                "stage_name": current_stage,
                "execution_timestamp": datetime.datetime.now().isoformat(),
                "style_requirements": style_info,
                "context_chain_position": len(previous_context.get("context_chain", [])),
                "inherited_context": self._extract_relevant_previous_context(previous_context)
            }

            # Merge with result
            result["_stage_metadata"] = stage_context
            result["_context_preservation"] = {
                "inherited_style": style_info.get("type"),
                "inherited_ai_system": style_info.get("ai_system"),
                "context_depth": stage_context["context_chain_position"]
            }

            return result
        except Exception as e:
            self.logger.error(f"Context preservation failed: {str(e)}")
            return result

    def _summarize_stage_result(self, stage_result: Dict) -> Dict:
        """
        Creates a concise summary of stage results by extracting key information.
        This reduces context bloat while preserving essential data.
        
        Args:
            stage_result: Complete stage result dictionary
            
        Returns:
            Dict containing summarized stage information
        """
        try:
            # Extract stage type and core information
            stage_type = stage_result.get('_stage_metadata', {}).get('stage_name', 'unknown')
            
            # Define summarization strategies for different stage types
            summarization_mapping = {
                'analysis': self._summarize_analysis_stage,
                'feedback': self._summarize_feedback_stage,
                'guidelines': self._summarize_guidelines_stage,
                'enhancement': self._summarize_enhancement_stage
            }
            
            # Get appropriate summarization function or use default
            summarize_func = summarization_mapping.get(stage_type, self._default_summarization)
            summary = summarize_func(stage_result)
            
            # Add common metadata
            summary['_summary_metadata'] = {
                'original_stage': stage_type,
                'summarized_at': datetime.datetime.now().isoformat(),
                'summary_version': '1.0'
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Stage summarization failed: {str(e)}")
            return {
                'error': str(e),
                'stage_type': stage_type,
                'timestamp': datetime.datetime.now().isoformat()
            }

    def _extract_relevant_context(self, previous_context: Dict) -> Dict:
        """
        Extracts only the relevant information from previous context needed for 
        current stage execution. This prevents context bloat across stages.
        
        Args:
            previous_context: Complete previous context dictionary
            
        Returns:
            Dict containing only relevant context information
        """
        try:
            # Define essential fields to preserve
            essential_fields = {
                'intent': self._extract_intent_info,
                'requirements': self._extract_requirements_info,
                'context_parameters': self._extract_parameters_info,
                'key_insights': self._extract_insights
            }
            
            relevant_context = {}
            
            # Extract only necessary information using specific extractors
            for field, extractor in essential_fields.items():
                if field_data := extractor(previous_context):
                    relevant_context[field] = field_data
                    
            return relevant_context
            
        except Exception as e:
            self.logger.error(f"Context extraction failed: {str(e)}")
            return {'error': str(e)}

    # Helper functions for stage-specific summarization
    def _summarize_analysis_stage(self, stage_result: Dict) -> Dict:
        """Creates concise summary of analysis stage results"""
        return {
            'primary_intent': stage_result.get('intent', {}).get('primary_objective'),
            'key_requirements': stage_result.get('requirements', [])[:3],  # Top 3 requirements
            'context_summary': {
                'constraints': stage_result.get('context', {}).get('constraints', []),
                'considerations': stage_result.get('context', {}).get('considerations', [])[:2]
            }
        }

    def _summarize_feedback_stage(self, stage_result: Dict) -> Dict:
        """Creates concise summary of feedback stage results"""
        return {
            'key_gaps': stage_result.get('alignment_analysis', {}).get('gaps', [])[:2],
            'primary_recommendations': stage_result.get('alignment_analysis', {}).get('recommendations', [])[:2],
            'improvement_areas': stage_result.get('improvement_areas', [])[:3]
        }

    def _summarize_guidelines_stage(self, stage_result: Dict) -> Dict:
        """Creates concise summary of guidelines stage results"""
        content = stage_result.get('structured_content', {})
        return {
            'critical_considerations': content.get('critical_considerations', [])[:3],
            'key_guidelines': content.get('guidelines_for_chatgpt', [])[:3],
            'implementation_notes': content.get('implementation_notes', [])[:2]
        }

    def _summarize_enhancement_stage(self, stage_result: Dict) -> Dict:
        """Creates concise summary of enhancement stage results"""
        return {
            'enhanced_prompts': [
                {'prompt': p.get('prompt'), 'focus': p.get('focus')}
                for p in stage_result.get('prompts', [])[:2]  # Only top 2 prompts
            ]
        }

    # Helper functions for context extraction
    def _extract_intent_info(self, context: Dict) -> Dict:
        """Extracts essential intent information"""
        intent_data = context.get('intent', {})
        return {
            'primary_objective': intent_data.get('primary_objective'),
            'key_requirements': intent_data.get('implicit_requirements', [])[:3]
        }

    def _extract_requirements_info(self, context: Dict) -> List:
        """Extracts key requirements information"""
        return context.get('requirements', [])[:5]  # Top 5 requirements

    def _extract_parameters(self, params: Dict) -> Dict:
        default_params = {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        }
        
        if not params or not isinstance(params, dict):
            return default_params
            
        clean_params = {}
        for key, default in default_params.items():
            try:
                param = params.get(key, {})
                if isinstance(param, dict) and 'value' in param:
                    clean_params[key] = float(param['value'])
                else:
                    clean_params[key] = float(param) if param is not None else default
            except (TypeError, ValueError):
                clean_params[key] = default
                
        return clean_params

    def _extract_insights(self, context: Dict) -> List:
        """Extracts key insights from context"""
        insights = []
        if 'feedback' in context:
            insights.extend(context['feedback'].get('improvement_areas', [])[:2])
        if 'guidelines' in context:
            insights.extend(context.get('guidelines', {}).get('critical_considerations', [])[:2])
        return insights

    def _enrich_context(self, current_stage_result: Dict, previous_context: Dict) -> Dict:
        # Extract unique content sections
        content_sections = set()
        if isinstance(current_stage_result.get('content'), str):
            sections = current_stage_result['content'].split('\n\n')
            for section in sections:
                if section.strip():
                    content_sections.add(section.strip())
        
        # Rebuild content with unique sections
        current_stage_result['content'] = '\n\n'.join(content_sections)
        return current_stage_result

    def _convert_raw_response(self, response: Dict, stage_name: str) -> Dict:
        """Convert raw API response to normalized format"""
        try:
            if "raw_response" in response:
                converted = {
                    "content": response["raw_response"],
                    "metadata": {
                        "stage": stage_name,
                        "conversion_timestamp": datetime.datetime.now().isoformat()
                    }
                }
                return converted
            return response
        except Exception as e:
            self.logger.error(f"Error converting raw response: {str(e)}")
            return {
                "error": str(e),
                "stage": stage_name,
                "timestamp": datetime.datetime.now().isoformat()
            }

    def _create_fallback_result(self, stage_name: str) -> Dict:
        """Create fallback result when stage processing fails"""
        return {
            "status": "fallback",
            "stage": stage_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "content": f"Fallback response for {stage_name}"
        }

    def _preserve_context(self, stage_name: str, result: Dict) -> Dict:
        try:
            previous_context = self.context_tracker.get_latest_context()
            
            # Maintain existing metadata structure
            stage_metadata = {
                "execution_timestamp": datetime.datetime.now().isoformat(),
                "previous_context": {
                    "ai_type": previous_context.get("ai_type"),
                    "style": previous_context.get("style"),
                    "style_metadata": previous_context.get("style_metadata", {})
                },
                "stage_name": stage_name
            }
            
            # Preserve consistent structure across stages
            result.update({
                "_stage_metadata": stage_metadata,
                "_metadata": {
                    "response_type": "message",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            })
            
            return result
        except Exception as e:
            self.logger.error(f"Error preserving response: {str(e)}")
            return {
                "error": str(e),
                "stage": stage_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
    def execute(self, stage_input: Dict) -> Dict:
        try:
            # Extract core components
            prompt = stage_input["original_prompt"]
            ai_type = stage_input["ai_type"]
            style = stage_input["style"]
            previous_context = stage_input.get("previous_context", {})
            
            # Create stage-specific system message
            system_message = self._create_system_message(ai_type, style)
            
            # Generate stage-specific prompt with context
            user_message = self._create_user_message({
                **stage_input,
                "previous_context": previous_context
            })
            
            # Make API call with context
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                context=stage_input,
                **self._get_stage_parameters(stage_input)
            )
            
            processed_response = self._process_stage_response(response)
            
            # Add stage metadata
            return self._add_stage_metadata(processed_response)
            
        except Exception as e:
            return self._create_fallback_response(stage_input)

    def _check_dependencies(self, pipeline_context: Dict) -> bool:
        """Check if all required previous stages completed successfully"""
        required_stages = self._get_required_stages()
        context_chain = pipeline_context.get("context_chain", [])
        
        completed_stages = {
            stage["stage"]: stage["result"].get("status") == "success"
            for stage in context_chain
        }
        
        return all(completed_stages.get(stage, False) for stage in required_stages)

    def _validate_inputs(self, prompt: str, ai_type: str, style: str) -> bool:
        """Validate required inputs are present"""
        return all([prompt, ai_type, style])

    def _get_stage_config(self) -> Dict:
        """Get stage-specific configuration"""
        raise NotImplementedError

    def _create_system_message(self, ai_type: str, style: str) -> str:
        """Create stage-specific system message"""
        raise NotImplementedError

    def _create_user_message(self, pipeline_context: Dict) -> str:
        """Create stage-specific user message"""
        raise NotImplementedError

    def _process_response(self, response: Dict) -> Dict:
        """Process stage-specific response"""
        raise NotImplementedError

    def _create_fallback_response(self, pipeline_context: Dict) -> Dict:
        """Create stage-specific fallback response"""
        return {
            "status": "fallback",
            "stage": self._get_stage_config()["stage_name"],
            "timestamp": datetime.datetime.now().isoformat(),
            "result": f"Fallback response for {self._get_stage_config()['stage_name']}"
        }
    
    def _get_required_stages(self) -> List[str]:
        """
        Returns list of stages that must complete before this stage can execute.
        Each stage subclass should override this with its specific dependencies.
        
        Returns:
            List[str]: Names of required previous stages
        """
        return []  # Base class has no dependencies

    def _create_enriched_prompt(self, prompt: str, previous_stages: List[Dict], 
                              ai_type: str, style: str) -> str:
        """
        Creates an enhanced prompt by incorporating context from previous stages.
        
        Args:
            prompt: Original user prompt
            previous_stages: List of completed stage results
            ai_type: Type of AI being used
            style: Desired response style
            
        Returns:
            str: Enriched prompt with context
        """
        # Extract relevant information from previous stages
        context_info = []
        for stage in previous_stages:
            if stage["result"].get("content_analysis"):
                context_info.append(
                    f"Previous {stage['stage']} insights: "
                    f"{json.dumps(stage['result']['content_analysis'], indent=2)}"
                )

        # Build enriched prompt
        enriched_prompt = f"""
        Original Request: {prompt}
        AI Type: {ai_type}
        Style: {style}
        
        Previous Context:
        {chr(10).join(context_info)}
        """
        return enriched_prompt

    def _format_stage_context(self, previous_stages: List[Dict]) -> Dict:
        """
        Formats previous stage results into a structured context object.
        
        Args:
            previous_stages: List of completed stage results
            
        Returns:
            Dict: Formatted context information
        """
        formatted_context = {
            "stages": {},
            "metadata": {
                "total_stages": len(previous_stages),
                "timestamp": datetime.datetime.now().isoformat()
            }
        }
        
        for stage in previous_stages:
            formatted_context["stages"][stage["stage"]] = {
                "result": stage["result"],
                "timestamp": stage["timestamp"],
                "sequence": stage["sequence"]
            }
            
        return formatted_context

    def _get_stage_parameters(self, pipeline_context: Dict) -> Dict:
        """
        Gets stage-specific API parameters, with defaults if not specified.
        
        Args:
            pipeline_context: Current pipeline context
            
        Returns:
            Dict: API parameters for this stage
        """
        # Get base parameters
        base_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        
        # Override with stage-specific parameters if present
        stage_name = self.__class__.__name__.lower()
        stage_params = pipeline_context.get("parameters", {}).get(stage_name, {})
        
        return {**base_params, **stage_params}

    def _process_stage_response(self, response: Dict) -> Dict:
        """
        Processes and validates the API response for this stage.
        
        Args:
            response: Raw API response
            
        Returns:
            Dict: Processed and validated response
        """
        if not isinstance(response, dict):
            raise ValueError("Invalid response format")
            
        # Validate required fields for this stage
        required_fields = self._get_required_fields()
        missing_fields = [
            field for field in required_fields 
            if field not in response
        ]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        # Add processing metadata
        response["_processing_metadata"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "stage": self.__class__.__name__
        }
        
        return response

    def _add_stage_metadata(self, response: Dict) -> Dict:
        """
        Adds stage-specific metadata to the response.
        
        Args:
            response: Processed stage response
            
        Returns:
            Dict: Response with added metadata
        """
        metadata = {
            "stage": self.__class__.__name__,
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0"
        }
        
        return {
            **response,
            "_stage_metadata": metadata
        }

    def _get_required_fields(self) -> List[str]:
        """
        Returns list of required fields in the API response for this stage.
        Should be overridden by stage subclasses.
        
        Returns:
            List[str]: Names of required response fields
        """
        return []




class AnalysisStage(PipelineStage):
    def execute(self, pipeline_context: Dict) -> Dict:
        try:
            self.logger.info("Starting analysis stage")
            prompt = pipeline_context.get("original_prompt")
            ai_type = pipeline_context.get("ai_type")
            style = pipeline_context.get("style")
            preprocessor = PromptPreprocessor(self.logger)
            nlp_analysis = preprocessor.analyze_prompt(prompt)

            self.logger.debug("NLP Analysis Insights:")
            self.logger.debug(f"Intent Classification: {nlp_analysis.get('intent_classification', {})}")
            self.logger.debug(f"AI Persona: {nlp_analysis.get('ai_persona', {})}")
            self.logger.debug(f"Contextual Requirements: {nlp_analysis.get('contextual_requirements', {})}")
            self.logger.debug(f"Domain Insights: {nlp_analysis.get('domain_insights', {})}")
            
            system_message = f"""You are a prompt analysis expert specializing in {ai_type} systems.
            Your  task is to perform a COMPLETE analysis of the user's request to communicate it to the {ai_type} LLM in the best possible way.
              Your analysis is supposed to provide the llm a high grade understanding of the user's request so that it understands the user's request to 
              generate precise and optimized response catering to the user's exact contextual requirement.
              Your analysis directly informs prompt construction.

            1.If the user's request is domain-specific, ensure your analysis accounts for domain-relevant terminology, tools, or best practices.
            2.  Key requirements
            3. Essential context
            4. Key constraints specific to {ai_type}'s capabilities
NO speculation or assumptions. NO general guidance.

            CRITICAL - 
            ONLY BUILD UPON WHAT THE USER HAS PROVIDED AND DO NOT ASSUME ANYTHING.
            
            THE RESPONSE SHOULD NOT BE MORE THAN 500 WORDS.
           """

            user_message = f"""Analyze: "{prompt}"
            System: {ai_type}
            Style: {style}
            Your task is to create a concise analysis of the user's requirement in his written prompt,
              understand what the user needs, create pointers that can explain ths user's intent even more clearly.
            Include key requirements and context needed for prompt enhancement.
            Consider whether there are any constraints, uncommon scenarios, or edge cases that might impact prompt effectiveness, and highlight them in your analysis.
            Return ONLY:
1. Core intent
You should breakdown and understand the domain which the user is targeting , and have a deep understanding of 
all the tools relevant to the domain that are present.
2. Essential requirements
3. Critical context needed for {ai_type}
CRITICAL - 
Identify any potential ambiguities or missing details in the user’s request. If clarity is lacking, explicitly state the ambiguity and propose at least two follow-up questions to resolve it before proceeding.
DO NOT ADD ANY EXAMPLES THAT WILL MISLEAD THE PROMPT CREATION PROCESS, DO NOT ADD ANY USER RELATED INFORMATION THAT THE USER HAS NOT MENTIONED. IF NEEDED ONLY USE PLACEHOLDERS.
Keep analysis focused and factual."""

            # Adjust API call parameters
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                temperature=0.3,
                max_tokens=1000,  # Ensure enough tokens for complete response 
                presence_penalty=0.0,
                frequency_penalty=0.0,
                stop=None  # Don't use stop tokens that might truncate
            )

            self.logger.debug(f"Raw API response: {response}")
            processed_response = self._process_analysis_response(response.get("content", ""), pipeline_context)
            return self._preserve_context("analysis", processed_response)

        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            return self._create_fallback_analysis(pipeline_context)

    def _process_analysis_response(self, content: str, pipeline_context: Dict) -> Dict:
        """Process free-form analysis response into structured format"""
        try:
            if not content:
                return self._create_fallback_analysis(pipeline_context)

            # Remove markdown formatting but preserve content
            cleaned_content = re.sub(r'\*\*|\#\#\#|\n\n+', '\n', content)
            
            return {
                "analysis_results": {
                    "content": cleaned_content,
                    "original_prompt": pipeline_context.get("original_prompt"),
                    "ai_type": pipeline_context.get("ai_type"),
                    "style": pipeline_context.get("style"),
                },
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "analysis"
                }
            }

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            return self._create_fallback_analysis(pipeline_context)

    def _create_fallback_analysis(self, pipeline_context: Dict) -> Dict:
        """Create fallback analysis with basic prompt context"""
        prompt = pipeline_context.get("original_prompt", "")
        ai_type = pipeline_context.get("ai_type", "general")
        style = pipeline_context.get("style", "standard")

        fallback_content = f"""
        Basic Analysis:
        - Request: {prompt}
        - System: {ai_type} 
        - Style: {style}
        - Core Intent: Understanding the request
        - Key Requirements: Clear explanation needed
        """

        return {
            "analysis_results": {
                "content": fallback_content,
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style
            },
            "_metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "stage": "analysis",
                "status": "fallback"
            }
        }





class GuidelinesStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.required_fields = ["guidelines", "parameters", "implementation_notes"]
    


    def execute(self, pipeline_context: Dict) -> Dict:
        try:
            # Enhanced context extraction
            analysis = pipeline_context.get("stage_results", {}).get("analysis", {}).get("analysis_results", {})
            nlp_insights = analysis.get("linguistic_features", {})
            domain_concepts = nlp_insights.get("domain_concepts", [])
            action_patterns = nlp_insights.get("action_verbs", [])
            analysis_content = analysis.get("content", "")
            original_prompt = analysis.get("original_prompt", "")
            ai_type = analysis.get("ai_type", "")
            style = analysis.get("style", "professional")
            complexity_score = nlp_insights.get("complexity_metrics", {}).get("flesch_score", 50)
            temperature = 0.7 if complexity_score > 50 else 0.5

            # Ultra-Precise System Message
            system_message = f"""You are a WORLD-CLASS prompt engineering expert specializing in {ai_type} systems.
Your task is to provide SPECIFIC, FOCUSED GUIDANCE for constructing prompts based on:
1. The user's specific request and context
2. {ai_type}'s specific capabilities and interaction patterns,the user is writing the prompts on this specific ai platform.
3. {style} style requirements
RETURN ONLY:
1. Core Prompt Requirements - What MUST be included
2. Style-Specific Guidelines - How to maintain {style} style,In the "Style-Specific Guidelines" section, include common mistakes or pitfalls to avoid when maintaining the specified style.
3. AI-Specific Optimizations - Best practices for {ai_type}
4. Key Considerations - Critical factors for this specific request
5. Ensure all guidelines are directly tied to the user's intent, as identified in the analysis stage.
6.Suggest at least one way the user can validate the prompt's effectiveness in meeting their specific needs.

Keep responses CONCISE and ACTIONABLE. 

CRITICAL GUIDELINE COMPOSITION INSTRUCTIONS:
CRITICAL - 

DO NOT GENERATE ANYTHIN WITHOUT CONFIRMING THE UNDERSTANDING OF MY REQUEST, IF THERE IS ANY CLARITY MISSING , ASK ME FOLLOW UP QUESTIONS BEFORE GENERATING AND ONLY THEN GENERATE.
1. MAXIMUM response length: 500 words
2. Provide concise, bullet-pointed strategies for each section.
3. DO NOT GENERATE ANY EXAMPLES AS IT WILL LEAD TO HALLUCNIATIONS FOR PROMPT CREATION
FAILURE TO MEET THESE REQUIREMENTS RESULTS IN IMMEDIATE REGENERATION OF THE RESPONSE."""

 
            user_message = f"""Generate focused guidelines for constructing prompts for:

CONTEXT:
Original Request: "{original_prompt}"
Analysis: {analysis_content} (If the analysis consists of any follow up questions, analyze them and answer them based on the user's requirements. If it adds up to the prompt, answer it. If it doesn't, don't answer it.)

REQUIREMENTS:
- AI Platform: {ai_type}
- Response Style: {style}

Return guidelines in this structure:
1. CORE REQUIREMENTS:
   - Essential elements for this specific request
   - Critical context to include

2. STYLE GUIDELINES:
   - How to maintain {style} style
   - Style-specific dos and don'ts

3. {ai_type} OPTIMIZATION:
   - Platform-specific best practices
   - Interaction patterns to use/avoid

4. PROMPT CONSTRUCTION:
   - Structure recommendations
Emphasise more on STYLE GUIDELINES and {ai_type} OPTIMIZATION
Keep focused on THIS SPECIFIC REQUEST  No general theory or explanations.

"""

            # Enhanced API Call with More Generous Creativity Parameters
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                temperature=0.7,  # Higher creativity
                top_p=0.9,        # More diverse sampling
                max_tokens=4000,  # Increased token limit
                presence_penalty=0.2  # Slightly more diverse vocabulary
            )
            
            # Advanced Response Processing
            formatted_response = {
                "content": response.get("content", ""),
                "context": {
                    "prompt": original_prompt,
                    "ai_type": ai_type,
                    "style": style,
                    "analysis_depth": len(analysis_content),
                    "generation_timestamp": datetime.datetime.now().isoformat()
                }
            }
            
            return self._preserve_context("guidelines", formatted_response)

        except Exception as e:
            self.logger.error(f"Guidelines generation failed: {str(e)}", exc_info=True)
            return self._create_fallback_guidelines(pipeline_context)

    def _create_fallback_guidelines(self, pipeline_context: Dict) -> Dict:
        """Create a robust fallback with structured, adaptable guidelines"""
        original_prompt = pipeline_context.get("original_prompt", "Generic Prompt")
        ai_type = pipeline_context.get("ai_type", "Generic AI")
        style = pipeline_context.get("style", "Professional")

        return {
            "content": f"""UNIVERSAL PROMPT ENGINEERING FRAMEWORK

1. CONTEXTUAL MASTERY
   - Dissect {original_prompt} with surgical precision
   - Understand underlying conceptual frameworks
   - Anticipate analytical requirements

2. {ai_type} OPTIMIZATION STRATEGIES
   - Leverage system-specific analytical capabilities
   - Construct prompts that maximize {ai_type}'s potential
   - Align with core computational methodologies

3. {style} COMMUNICATION PROTOCOL
   - Maintain impeccable structural integrity
   - Demonstrate clarity without sacrificing depth
   - Balance technical accuracy with elegant expression

4. PROMPT ARCHITECTURE
   - Introduction: Contextual framing
   - Body: Detailed, structured inquiry
   - Conclusion: Clear objective statement

5. ERROR MITIGATION TECHNIQUES
   - Anticipate potential misinterpretations
   - Provide explicit constraints
   - Create self-correcting prompt mechanisms""",
            "context": {
                "prompt": original_prompt,
                "ai_type": ai_type,
                "style": style
            }
        }

    def _extract_parameters(self, params: Dict) -> Dict:
        default_params = {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        }
        
        if not params or not isinstance(params, dict):
            return default_params
            
        clean_params = {}
        for key, default in default_params.items():
            try:
                param = params.get(key, {})
                if isinstance(param, dict) and 'value' in param:
                    clean_params[key] = float(param['value'])
                else:
                    clean_params[key] = float(param) if param is not None else default
            except (TypeError, ValueError):
                clean_params[key] = default
                
        return clean_params

    def _create_system_message(self, ai_type: str, style: str) -> str:
        return f"""You are a guidelines expert for {ai_type} systems.
        Generate comprehensive guidelines and return JSON in this exact structure:
        {{
            "guidelines": {{
                "implementation_approach": "string",
                "key_considerations": ["string"],
                "best_practices": ["string"]
            }},
            "parameters": {{
                "temperature": {{"value": 0.7, "reasoning": "string"}},
                "top_p": {{"value": 0.9, "reasoning": "string"}},
                "presence_penalty": {{"value": 0.0, "reasoning": "string"}},
                "frequency_penalty": {{"value": 0.0, "reasoning": "string"}}
            }},
            "implementation_notes": {{
                "critical_considerations": ["string"],
                "success_criteria": ["string"]
            }}
        }}"""
        
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
class EnhancementStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.required_fields = ["prompts"]

    def _create_fallback_enhanced_prompts(self, original_prompt: str, style: str, ai_type: str) -> Dict:
        """Generate fallback prompts maintaining exact required structure"""
        self.logger.info("Creating fallback enhanced prompts")
        self.logger.debug(f"Fallback inputs - Prompt: {original_prompt}, Style: {style}, AI Type: {ai_type}")
        
        fallback_response = {
            "result": {
                "prompts": [
                    {
                        "prompt": f"Help me with {original_prompt} using {style} communication style"
                    },
                    {
                        "prompt": f"Provide guidance for {original_prompt} optimized for {ai_type}"
                    },
                    {
                        "prompt": f"Create a {style} solution for {original_prompt}"
                    }
                ]
            }
        }
        
        self.logger.debug(f"Generated fallback response: {fallback_response}")
        return fallback_response




    def _create_enhanced_prompts(self, original_prompt: str, context: Dict) -> List[Dict]:
        variations = []
        seen_prompts = set()  # Track unique prompts
        
        # Create variations while checking for uniqueness
        analysis = context.get('analysis', {})
        requirements = analysis.get('requirements', [])
        style = context.get('style', 'professional')
        
        if requirements:
            prompt = f"Generate a {style}  for {original_prompt} focusing on: {', '.join(requirements[:2])}"
            if prompt not in seen_prompts:
                variations.append({"prompt": prompt})
                seen_prompts.add(prompt)
        
        if 'intent' in analysis:
            intent = analysis['intent'].get('primary_objective', '')
            prompt = f"Create an email that {intent} with emphasis on {style} communication"
            if prompt not in seen_prompts:
                variations.append({"prompt": prompt})
                seen_prompts.add(prompt)
        
        prompt = f"Compose a {style} email for {original_prompt} optimized for clarity and professionalism"
        if prompt not in seen_prompts:
            variations.append({"prompt": prompt})
            seen_prompts.add(prompt)
        
        return variations
    
    def _select_enhancement_parameters(self, ai_type: str, style: str) -> Dict[str, float]:
        """Parameter matrix for enhancement stage only"""
        param_matrix = {
            'ChatGPT': {
                'professional': {'temperature': 0.5, 'top_p': 0.8},
                'creative': {'temperature': 0.8, 'top_p': 0.9},
                'descriptive': {'temperature': 0.6, 'top_p': 0.85},
                'concise': {'temperature': 0.4, 'top_p': 0.7}
            },
            'Claude': {
                'professional': {'temperature': 0.4, 'top_p': 0.75},
                'creative': {'temperature': 0.7, 'top_p': 0.85},
                'descriptive': {'temperature': 0.5, 'top_p': 0.8},
                'concise': {'temperature': 0.3, 'top_p': 0.7}
            },
            'Gamma': {
                'professional': {'temperature': 0.5, 'top_p': 0.8},
                'creative': {'temperature': 0.7, 'top_p': 0.9},
                'descriptive': {'temperature': 0.6, 'top_p': 0.85},
                'concise': {'temperature': 0.4, 'top_p': 0.7}
            },
            'Midjourney': {
                'professional': {'temperature': 0.4, 'top_p': 0.75},
                'creative': {'temperature': 0.8, 'top_p': 0.9},
                'descriptive': {'temperature': 0.6, 'top_p': 0.85},
                'concise': {'temperature': 0.3, 'top_p': 0.7}
            },
            'Gemini': {
                'professional': {'temperature': 0.5, 'top_p': 0.8},
                'creative': {'temperature': 0.7, 'top_p': 0.9},
                'descriptive': {'temperature': 0.6, 'top_p': 0.85},
                'concise': {'temperature': 0.4, 'top_p': 0.7}
            }
        }
        
        default_params = {'temperature': 0.7, 'top_p': 0.9}
        return param_matrix.get(ai_type, {}).get(style, default_params)
    
    def _get_basic_parameters(self, style: str) -> Dict:
        params = {
        "creative": {"temperature": 0.8},
        "concise": {"temperature": 0.4},
        "professional": {"temperature": 0.6},
        "descriptive": {"temperature": 0.7}
    }
        return params.get(style, {"temperature": 0.7})

    def execute(self, pipeline_context: Dict) -> Dict:
        try:
            self.logger.info("Starting enhancement stage execution")
            self.logger.debug("Pipeline Context: %s", json.dumps(pipeline_context, indent=2))
            
            # Extract and log context
            analysis = pipeline_context.get("stage_results", {}).get("analysis", {}).get("analysis_results", {})
            # nlp_features = analysis.get("linguistic_features", {})
            guidelines = pipeline_context.get("stage_results", {}).get("guidelines", {}).get("content", "")
            # semantic_relationships = nlp_features.get("semantic", {}).get("relationships", [])
            # prompt_patterns = self._extract_prompt_patterns(nlp_features)
            original_prompt = analysis.get("original_prompt", "")
            nlp_features = analysis.get("linguistic_features", {})
            semantic_relationships = nlp_features.get("semantic", {}).get("relationships", [])
            prompt_patterns = self._extract_prompt_patterns(nlp_features)
            
            enhanced_prompts = self._generate_semantic_variations(
                original_prompt,
                semantic_relationships,
                prompt_patterns
            )
            
            ai_type = analysis.get("ai_type", "")
            style = analysis.get("style", "")
            
            # Log context details - keeping for debugging
            self.logger.debug(f"Original Prompt: {original_prompt}")
            self.logger.debug(f"AI Type: {ai_type}")
            self.logger.debug(f"Style: {style}")
            self.logger.debug(f"Analysis Content Length: {len(analysis.get('content', ''))}")
            self.logger.debug(f"guidelines generated: {guidelines}")

            selected_params = self._select_enhancement_parameters(ai_type, style)
            self.logger.debug("Selected Parameters: %s", json.dumps(selected_params, indent=2))

            # Enhanced system message with strict JSON requirements
            system_message = f"""You are an expert prompt engineer specializing in crafting highly effective prompts for {ai_type} systems. 
Your core expertise is understanding user intent and translating it into optimized prompts that generate superior results.

KEY REQUIREMENTS:
- ONLY generate three variations of the user's request
- Each variation must be self-contained and complete
- NO additional context or metadata
- NO hypothetical scenarios or assumptions
- STRICT adherence to {style} style

CAPABILITIES AND FOCUS:
- Deep understanding of {ai_type}'s strengths and interaction patterns
- Expertise in {style} communication style
- Ability to create contextually aware prompts

YOUR TASK IS TO:
1. Analyze the provided context and requirements
2. Generate three distinct but complementary prompts that:
   - Maintain {style} style consistently
   - Leverage {ai_type}'s specific capabilities
   - Each brings unique value while serving the main goal
   Stay within {ai_type}'s capabilities
   NO additional fields beyond "prompt"

CRITICAL - YOUR RESPONSE MUST BE THIS EXACT JSON STRUCTURE AND NOTHING ELSE:
{{
    "prompts": [
        {{ "prompt": "string - first variation" }},
        {{ "prompt": "string - second variation" }},
        {{ "prompt": "string - third variation" }}
    ]
}}

RULES:

DO NOT USE ANY NAMES, INSTEAD USE PLACEHOLDERS IF AND ONLY IF NEEDED, YOU SHOULD NOT MISLEAD.
- ONLY the exact JSON structure above is allowed
- NO additional fields
- NO nested objects
- NO arrays except the main prompts array
- NO metadata or context fields
- Each prompt must be a plain string

ANY DEVIATION FROM THIS STRUCTURE WILL CAUSE ERRORS.

NO explanations, markdown, or additional text outside this structure."""

            # Create focused user message
            user_message = f"""
            TRANSFORM THIS REQUEST:
            CONTEXT:
Original Request: "{original_prompt}"
Style Required: {style}
Platform: {ai_type}

ANALYSIS INSIGHTS:
{analysis}

GUIDELINES:
{guidelines}

CREATE THREE ENHANCED PROMPTS THAT:
    -If the request relates to a specialized domain, include tailored language and context that reflects industry-standard practices.

   - Focus on primary user intent
   - Maintain clear, direct instruction
   - Emphasize essential requirements

EACH PROMPT MUST:
- Follow {style} style guidelines
- Optimize for {ai_type}'s capabilities
- Consolidate context, action, and expected outcomes into a single cohesive prompt.
- Be complete and self-contained
- Ensure that each prompt is adaptable to slight variations in user input without losing focus on the main objective.

CONSTRAINTS:
- Maintain {style} style consistently,Maintain the overall style but introduce subtle stylistic variations across the three prompts to allow the user to choose the most fitting tone or phrasing.
- No assumptions about tools or capabilities
- Stay focused on user's original request
- No additional content beyond prompt text

GENERATE THREE VARIATIONS IN THE EXACT JSON FORMAT SPECIFIED.
DO NOT ADD ANY FIELDS OR CONTEXT.
"""
            self.logger.debug(f"system message: {system_message}")
            self.logger.debug(f"user message: {user_message}")

            # Make API call with increased token limit
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                temperature=0.7,
                top_p=0.9,
                presence_penalty=0.2,
                frequency_penalty=0.0,
                max_tokens=4000  # Increased to prevent truncation
            )

            # Enhanced response processing
            try:
                # Extract content and clean any non-JSON text
                content = response.get("content", "")
                self.logger.debug(f"Raw response content: {content}")
                
                # Find JSON boundaries
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    
                    # Parse and validate JSON structure
                    parsed = json.loads(json_str)
                    
                    # Validate prompts array
                    if "prompts" not in parsed or not isinstance(parsed["prompts"], list):
                        raise ValueError("Invalid response structure - missing prompts array")
                    
                    # Ensure exactly three prompts
                    prompts = parsed["prompts"][:3]
                    while len(prompts) < 3:
                        prompts.append({"prompt": f"Additional enhanced version of: {original_prompt}"})
                        
                    # Create final response
                    formatted_response = {
                        "result": {
                            "prompts": prompts
                        }
                    }
                    
                    self.logger.debug(f"Formatted response: {formatted_response}")
                    return formatted_response

                else:
                    raise ValueError("No valid JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Response processing failed: {str(e)}")
                self.logger.debug(f"Failed content: {content}")
                return self._create_fallback_enhanced_prompts(original_prompt, style, ai_type)

        except Exception as e:
            self.logger.error(f"Enhancement stage failed: {str(e)}", exc_info=True)
            return self._create_fallback_enhanced_prompts(
                pipeline_context.get("original_prompt", ""),
                pipeline_context.get("style", ""),
                pipeline_context.get("ai_type", "")
            )
        
    # These functions are referenced but not defined in EnhancementStage:
    def _extract_prompt_patterns(self, nlp_features: Dict) -> Dict:
        """Extracts prompt patterns from NLP features for enhanced variation generation"""
        patterns = {
            'structural': nlp_features.get('structural_features', {}),
            'linguistic': nlp_features.get('verbs', []) + nlp_features.get('nouns', []),
            'contextual': nlp_features.get('dependencies', [])
        }
        return patterns

    def _determine_perspective(self, version: str) -> str:
        """Determines the perspective/approach used in a prompt version"""
        perspectives = {
            'systematic': ['structure', 'organize', 'plan'],
            'analytical': ['analyze', 'evaluate', 'assess'],
            'creative': ['design', 'create', 'develop']
        }
        
        for perspective, keywords in perspectives.items():
            if any(keyword in version.lower() for keyword in keywords):
                return perspective
        return 'general'
    
    def _create_fallback_variation(self, prompt: str, patterns: Dict) -> str:
        """Creates a fallback variation when semantic relationships aren't available"""
        try:
            # Extract basic patterns
            structural = patterns.get('structural', {})
            linguistic = patterns.get('linguistic', [])
            contextual = patterns.get('contextual', [])
            
            # Use available patterns to create variation
            if linguistic:
                # Use linguistic patterns first
                key_terms = linguistic[:3]  # Take up to 3 key terms
                return f"Create a response that {' and '.join(key_terms)} for: {prompt}"
            elif contextual:
                # Fall back to contextual patterns
                context = contextual[0] if contextual else ''
                return f"Develop a {context} approach for: {prompt}"
            else:
                # Basic fallback
                return f"Provide a comprehensive solution for: {prompt}"
                
        except Exception as e:
            self.logger.error(f"Fallback variation creation failed: {str(e)}")
            return prompt

    def _generate_semantic_variations(self, prompt: str, 
                                    semantic_relationships: List[Dict],
                                    patterns: Dict) -> List[Dict]:
        """Generates variations based on semantic relationships and patterns"""
        variations = []
        if semantic_relationships:
            # Use semantic relationships for coherent variations
            for relationship in semantic_relationships[:3]:  # Top 3 relationships
                variation = self._create_variation_from_relationship(
                    prompt, relationship, patterns
                )
                variations.append({"prompt": variation})
        
        # Ensure we have at least 3 variations
        while len(variations) < 3:
            variation = self._create_fallback_variation(prompt, patterns)
            variations.append({"prompt": variation})
        
        return variations
    
    def _apply_structural_patterns(self, prompt: str, structural_patterns: Dict) -> str:
        """Apply structural patterns to create a variation"""
        try:
            # Extract structural components
            components = structural_patterns.get('features', {})
            sentence_structure = components.get('sentence_count', 1)
            complexity = components.get('complexity_score', 50)
            
            # Adjust prompt based on structural patterns
            if complexity > 75:
                return f"Create a detailed and structured response that thoroughly addresses: {prompt}"
            elif complexity > 50:
                return f"Provide a well-organized solution for: {prompt}"
            else:
                return f"Give a clear and direct response to: {prompt}"
                
        except Exception as e:
            self.logger.error(f"Structural pattern application failed: {str(e)}")
            return prompt

    def _apply_linguistic_patterns(self, prompt: str, linguistic_patterns: List[str]) -> str:
        """Apply linguistic patterns to create a variation"""
        try:
            if not linguistic_patterns:
                return prompt
                
            # Use key linguistic elements
            key_terms = linguistic_patterns[:2]  # Use top 2 patterns
            terms_str = ' and '.join(key_terms)
            
            return f"Develop a solution that {terms_str} for: {prompt}"
            
        except Exception as e:
            self.logger.error(f"Linguistic pattern application failed: {str(e)}")
            return prompt

    def _apply_contextual_patterns(self, prompt: str, contextual_patterns: List[str]) -> str:
        """Apply contextual patterns to create a variation"""
        try:
            if not contextual_patterns:
                return prompt
                
            # Use contextual dependencies
            context = contextual_patterns[0] if contextual_patterns else ''
            
            return f"Create a {context}-focused solution for: {prompt}"
            
        except Exception as e:
            self.logger.error(f"Contextual pattern application failed: {str(e)}")
            return prompt

    def _create_variation_from_relationship(self, 
                                        prompt: str,
                                        relationship: Dict,
                                        patterns: Dict) -> str:
        """Creates a prompt variation based on semantic relationship"""
        relationship_type = relationship.get('relationship_type', 'weak_continuation')
        score = relationship.get('similarity_score', 0.5)
        
        if relationship_type == 'strong_continuation':
            # Use more structural elements for strong relationships
            structural_patterns = patterns.get('structural', {})
            return self._apply_structural_patterns(prompt, structural_patterns)
        elif relationship_type == 'moderate_continuation':
            # Mix linguistic and structural elements
            linguistic_patterns = patterns.get('linguistic', [])
            return self._apply_linguistic_patterns(prompt, linguistic_patterns)
        else:
            # Focus on contextual elements for weak relationships
            contextual_patterns = patterns.get('contextual', [])
            return self._apply_contextual_patterns(prompt, contextual_patterns)
        
    # Add to EnhancementStage class:
    def _extract_prompt_components(self, prompt: str) -> Dict:
        """Extract key components from prompt for structured enhancement"""
        doc = self.nlp(prompt)
        return {
            'verb': next((token.text for token in doc if token.pos_ == 'VERB'), 'implement'),
            'objective': ' '.join(chunk.text for chunk in doc.noun_chunks),
            'constraints': [token.text for token in doc if token.dep_ == 'prep']
        }

    def _calculate_entity_confidence(self, entity) -> float:
        """Calculate confidence score for named entity recognition"""
        # Example implementation - replace with actual logic
        base_score = 0.8
        modifiers = {
            'PERSON': 0.9,
            'ORG': 0.85,
            'GPE': 0.95
        }
        return modifiers.get(entity.label_, base_score)

    def _extract_domain_vocabulary(self, text: str, domain: str) -> List[str]:
        """Extract domain-specific vocabulary from text"""
        doc = self.nlp(text)
        domain_patterns = {
            'technical': ['implement', 'develop', 'system'],
            'creative': ['design', 'create', 'innovative'],
            'business': ['strategy', 'market', 'revenue']
        }
        
        patterns = domain_patterns.get(domain.lower(), [])
        return [token.text for token in doc if token.text.lower() in patterns]

    def _process_enhancement_response(self, response: Dict, style: str, ai_type: str) -> Dict:
        """Process and validate enhancement response"""
        try:
            # First check if response is valid
            if not isinstance(response, dict):
                raise ValueError("Invalid response format")

            # Get content directly from the response if it exists
            content = response.get('content', '')
            if not content and response.get('choices'):
                # Try getting content from choices if available
                content = response['choices'][0].get('message', {}).get('content', '')
                if not content:
                    content = response['choices'][0].get('text', '')

            if not content:
                raise ValueError("No content found in response")

            # Try to parse the content as JSON
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # If content isn't valid JSON, try to extract prompts from text
                prompts = self._extract_prompts_from_text(content)
                parsed_content = {"prompts": prompts}

            # Ensure we have a "prompts" array
            if not isinstance(parsed_content.get("prompts"), list):
                # Try to convert single prompt to list
                if isinstance(parsed_content.get("prompt"), str):
                    parsed_content["prompts"] = [{"prompt": parsed_content["prompt"]}]
                else:
                    raise ValueError("Invalid prompts structure")

            # Clean and validate prompts
            cleaned_prompts = []
            for prompt_data in parsed_content.get("prompts", []):
                if isinstance(prompt_data, dict):
                    prompt_text = prompt_data.get("prompt", "").strip()
                elif isinstance(prompt_data, str):
                    prompt_text = prompt_data.strip()
                else:
                    continue

                if prompt_text:
                    # Apply style rules and validation
                    prompt_text = self._apply_style_rules(prompt_text, style, ai_type)
                    cleaned_prompts.append({
                        "prompt": prompt_text
                    })

            if not cleaned_prompts:
                raise ValueError("No valid prompts found in response")

            return {
                "prompts": cleaned_prompts,
                "_metadata": {
                    "ai_type": ai_type,
                    "style": style,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }



        except Exception as e:
            self.logger.error(f"Enhancement processing failed: {str(e)}")
            return self._create_fallback_enhanced_prompts(ai_type, style)

    # def _process_enhancement_response(self, response: Dict, style: str, ai_type: str) -> Dict:
    #     try:
    #         # Add NLP validation of generated prompts
    #         for prompt in response.get("prompts", []):
    #             # Validate semantic coherence
    #             coherence_score = self._validate_semantic_coherence(
    #                 prompt["prompt"], 
    #                 original_prompt
    #             )
                
    #             # Check style consistency
    #             style_adherence = self._check_style_patterns(
    #                 prompt["prompt"], 
    #                 style
    #             )
                
    #             # Validate domain terminology
    #             domain_accuracy = self._validate_domain_terms(
    #                 prompt["prompt"], 
    #                 ai_type
    #             )
                
    #             prompt["quality_metrics"] = {
    #                 "coherence": coherence_score,
    #                 "style_adherence": style_adherence,
    #                 "domain_accuracy": domain_accuracy
    #             }
    #     except Exception as e:
    #         self.logger.error(f"Enhancement processing failed: {str(e)}")
    #         return self._create_fallback_enhanced_prompts(ai_type, style)
    def _process_api_response(self, response: Dict) -> Dict:
        try:
            if not isinstance(response, dict) or "content" not in response:
                raise ValueError("Invalid response format")

            content = response["content"]
            # Clean content
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            # Find the first valid JSON object
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                content = content[start_idx:end_idx]

            parsed_content = json.loads(content)
            
            if "prompts" not in parsed_content:
                raise ValueError("Missing prompts in response")

            return {"prompts": [
                {"prompt": p.get("prompt", "")} 
                for p in parsed_content.get("prompts", [])
                if isinstance(p, dict) and "prompt" in p
            ]}

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            return {"prompts": []}

    def _extract_prompts_from_text(self, content: str) -> List[Dict]:
        """Extract prompts from text content if JSON parsing fails"""
        prompts = []
        
        # Try to find prompts using various patterns
        patterns = [
            r'\"prompt\":\s*\"([^\"]+)\"',  # JSON-like format
            r'\d+\.\s*(.+?)(?=\d+\.|$)',    # Numbered list
            r'\*\s*(.+?)(?=\*|$)',          # Bullet points
            r'[-•]\s*(.+?)(?=[-•]|$)',      # Dashed or bullet list
            r'version\s*\d+:\s*(.+?)(?=version|$)',  # Version format
            r'prompt\s*\d*:\s*(.+?)(?=prompt|$)'     # Prompt format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    cleaned_prompt = match.strip().strip('"\'').strip()
                    if cleaned_prompt:
                        prompts.append({"prompt": cleaned_prompt})
        
        # If no prompts found, try splitting by newlines and check each line
        if not prompts:
            lines = content.split('\n')
            for line in lines:
                cleaned_line = line.strip()
                if len(cleaned_line) > 10:  # Minimum length to be considered a prompt
                    prompts.append({"prompt": cleaned_line})
        
        # Ensure we have at least one prompt
        if not prompts:
            prompts = [{"prompt": content.strip()}]
        
        # Limit to 3 prompts and ensure they're unique
        seen_prompts = set()
        unique_prompts = []
        for p in prompts:
            if p["prompt"] not in seen_prompts:
                seen_prompts.add(p["prompt"])
                unique_prompts.append(p)
                if len(unique_prompts) >= 3:
                    break
        
        return unique_prompts

    def _apply_style_rules(self, prompt: str, style: str, ai_type: str) -> str:
        """Apply style-specific rules to prompt"""
        style_rules = {
            "concise": lambda p: self._make_concise(p),
            "professional": lambda p: self._make_professional(p),
            "technical": lambda p: self._make_technical(p, ai_type),
            "conversational": lambda p: self._make_conversational(p)
        }
        
        style_func = style_rules.get(style.lower(), lambda p: p)
        return style_func(prompt)

    def _make_concise(self, prompt: str) -> str:
        """Make prompt concise"""
        # Remove unnecessary words
        filters = [
            (r'\b(please|kindly|would you|could you)\b\s*', ''),
            (r'\b(I think|I believe|In my opinion)\b\s*', ''),
            (r'\b(very|really|quite|basically)\b\s*', '')
        ]
        
        result = prompt
        for pattern, replacement in filters:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
        # Ensure it ends with clear instruction
        if not result.strip().endswith(('.', '?')):
            result = result.strip() + '.'
            
        return result.strip()

    def _make_professional(self, prompt: str) -> str:
        """Make prompt professional"""
        # Add professional markers
        if not any(word in prompt.lower() for word in ['please', 'kindly', 'would']):
            prompt = f"Please {prompt}"
            
        return prompt.strip()

    def _make_technical(self, prompt: str, ai_type: str) -> str:
        """Make prompt technical"""
        technical_terms = {
            "ChatGPT": ["generate", "process", "analyze"],
            "descriptive": ["describe", "detail", "elaborate"],
            "analytical": ["analyze", "evaluate", "assess"]
        }
        
        terms = technical_terms.get(ai_type, ["process"])
        if not any(term in prompt.lower() for term in terms):
            prompt = f"{terms[0]} the following: {prompt}"
            
        return prompt.strip()

    def _make_conversational(self, prompt: str) -> str:
        """Make prompt conversational"""
        if not prompt.endswith('?'):
            prompt = f"Could you {prompt}?"
        return prompt.strip()

    def _validate_style_adherence(self, prompt: str, style: str) -> str:
        """Validate and describe style adherence"""
        style_checks = {
            "concise": lambda p: len(p.split()) < 15,
            "professional": lambda p: any(w in p.lower() for w in ['please', 'kindly', 'would']),
            "technical": lambda p: any(w in p.lower() for w in ['analyze', 'evaluate', 'process']),
            "conversational": lambda p: p.endswith('?')
        }
        
        check_func = style_checks.get(style.lower(), lambda _: True)
        adherence = "Fully compliant" if check_func(prompt) else "Partially compliant"
        return f"{style} style: {adherence}"

    def _validate_style_adherence(self, response: Dict, style: str) -> Dict:
        """Ensures all prompts adhere to the specified style"""
        try:
            if "prompts" not in response:
                return response
                
            for prompt in response["prompts"]:
                if not self._check_style_compliance(prompt.get("prompt", ""), style):
                    prompt["prompt"] = self._enforce_style(prompt["prompt"], style)
                    
            return response
        except Exception as e:
            self.logger.error(f"Style validation failed: {str(e)}")
            return response

    def _check_style_compliance(self, prompt: str, style: str) -> bool:
        """Checks if a prompt complies with the given style"""
        style_markers = {
            "concise": lambda p: len(p.split()) < 30 and ";" not in p,
            "professional": lambda p: any(term in p.lower() for term in ["please", "kindly", "would"]),
            "technical": lambda p: any(term in p.lower() for term in ["implement", "develop", "structure"]),
            "conversational": lambda p: "?" in p or "!" in p or "..." in p
        }
        
        checker = style_markers.get(style.lower(), lambda _: True)
        return checker(prompt)

    def _enforce_style(self, prompt: str, style: str) -> str:
        """Enforces the specified style on a prompt"""
        style_templates = {
            "concise": "{verb} {objective} {constraints}",
            "professional": "Please {verb} {objective} following {constraints}",
            "technical": "Implement {objective} with {constraints}",
            "conversational": "Could you help me {verb} {objective}? {constraints}"
        }
        
        # Extract components from prompt
        components = self._extract_prompt_components(prompt)
        
        # Apply style template
        template = style_templates.get(style.lower(), "{prompt}")
        return template.format(**components)
        
    def _process_stage_response(self, response: Dict) -> Dict:
        """Process and structure the enhancement stage output"""
        try:
            content = response.get('content', '')
            # Extract versions from content
            versions = re.findall(r'\*\*Version \d:\*\*\s*"([^"]+)"', content)
            
            structured_prompts = []
            for i, version in enumerate(versions[:3]):
                structured_prompts.append({
                    "prompt": version.strip(),
                    "focus": f"Version {i+1}",
                    "perspective": self._determine_perspective(version)
                })
                
            return {
                "prompts": structured_prompts,
                "_metadata": {
                    "format_version": "2.0",
                    "processing_stage": "enhancement"
                }
            }
        except Exception as e:
            self.logger.error(f"Enhancement processing failed: {str(e)}")
            return self._create_fallback_enhanced_prompts()
        
    def _create_system_message(self, ai_type: str, style: str) -> str:
        return f"""You are a prompt enhancement expert for {ai_type} systems.
        Generate three optimized versions of the original prompt that are:
        1. Adapted specifically for {ai_type} capabilities
        2. Following {style} style strictly
        3. Direct and implementation-ready
        
        Return ONLY in this exact JSON structure:
        {{
            "prompts": [
                {{ "prompt": "first_enhanced_version" }},
                {{ "prompt": "second_enhanced_version" }},
                {{ "prompt": "third_enhanced_version" }}
            ]
        }}"""

    def _create_user_message(self, pipeline_context: Dict) -> str:
        original_prompt = pipeline_context.get("original_prompt", "")
        style = pipeline_context.get("style", "professional")
        ai_type = pipeline_context.get("ai_type", "general")
        guidelines = pipeline_context.get("stage_results", {}).get("guidelines", {}).get("content", "")

        return f"""Original: "{original_prompt}"
        Style: {style}
        Type: {ai_type}
        Guidelines: {guidelines}
        
        Return ONLY:
        {{
            "prompts": [
                {{"prompt": "version1"}},
                {{"prompt": "version2"}},
                {{"prompt": "version3"}}
            ]
        }}"""



class EnhancedPromptPipeline:
    def __init__(self, logger: Logger):
        self.logger = logger 
        self.api_handler = APIHandler(logger)
        self.response_manager = ResponseManager(logger)
        self.preprocessor = PromptPreprocessor(logger) 
        self.context_tracker = ContextTracker()
        
        self.analysis_stage = AnalysisStage(logger, self.api_handler, self.context_tracker)
        # self.feedback_stage = FeedbackStage(logger, self.api_handler, self.context_tracker)
        self.guidelines_stage = GuidelinesStage(logger, self.api_handler, self.context_tracker)
        self.enhancement_stage = EnhancementStage(logger, self.api_handler, self.context_tracker)

    def _enrich_context(self, base_context: Dict, new_data: Dict) -> Dict:
        """Enrich context with new stage data"""
        try:
            enriched = base_context.copy()
            
            # Update stage results
            for stage, result in new_data.items():
                enriched["stage_results"][stage] = result
                
            # Add metadata about context evolution
            enriched["_metadata"] = {
                "last_updated": datetime.datetime.now().isoformat(),
                "stages_completed": list(enriched["stage_results"].keys())
            }
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Context enrichment failed: {str(e)}")
            return base_context
    
    def _format_final_response(self, pipeline_context: Dict) -> Dict:
        """
        Creates the final formatted response from pipeline context.
        
        Args:
            pipeline_context: Complete pipeline execution context
            
        Returns:
            Dict: Formatted final response
        """
        try:
            # Extract key components
            context_chain = pipeline_context.get("context_chain", [])
            stage_results = pipeline_context.get("stage_results", {})
            
            # Build response structure
            response = {
                "status": "success",
                "request_id": pipeline_context.get("request_id"),
                "metadata": {
                    "timestamp": pipeline_context.get("timestamp"),
                    "ai_type": pipeline_context.get("ai_type"),
                    "style": pipeline_context.get("style"),
                    "execution_metrics": {
                        "total_stages": len(context_chain),
                        "completion_time": datetime.datetime.now().isoformat()
                    }
                },
                "stages": {}
            }
            
            # Add each stage's results with proper error handling
            for stage_name, result in stage_results.items():
                try:
                    response["stages"][stage_name] = {
                        "result": result,
                        "metadata": self._extract_stage_metadata(stage_name, context_chain)
                    }
                except Exception as stage_error:
                    response["stages"][stage_name] = {
                        "status": "error",
                        "error": str(stage_error)
                    }
            
            return response
            
        except Exception as e:
            # Return error response if formatting fails
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

    def _extract_stage_metadata(self, stage_name: str, context_chain: List[Dict]) -> Dict:
        """
        Extracts metadata for a specific stage from the context chain.
        
        Args:
            stage_name: Name of the stage
            context_chain: Complete context chain
            
        Returns:
            Dict: Stage metadata
        """
        for entry in context_chain:
            if entry["stage"] == stage_name:
                return {
                    "timestamp": entry.get("timestamp"),
                    "sequence": entry.get("sequence"),
                    "dependencies": entry.get("dependencies", [])
                }
        return {}

    def _execute_analysis_stage(self, prompt: str, ai_type: str, style: str) -> Dict:
        """Execute the analysis stage of the pipeline"""
        try:
            return self.analysis_stage.execute(prompt, ai_type, style)
        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}")
            return self.analysis_stage._create_fallback_analysis(prompt, ai_type, style)


    def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict:
        try:
            # Log pipeline initialization
            self.logger.info("=== Starting Pipeline Execution ===")
            self.logger.info(f"Input Parameters:")
            self.logger.info(f"Prompt: {prompt}")
            self.logger.info(f"AI Type: {ai_type}")
            self.logger.info(f"Style: {style}")

            # Log base context creation
            self.logger.info("Creating base context")
            base_context = {
                "request_id": str(uuid.uuid4()),
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style,
                "timestamp": datetime.datetime.now().isoformat(),
                "stage_results": {}
            }
            self.logger.debug(f"Base Context Created: {json.dumps(base_context, indent=2)}")

            # Analysis Stage
            self.logger.info("\n=== Starting Analysis Stage ===")
            self.logger.info("Executing analysis_stage.execute()")
            analysis_result = self.analysis_stage.execute(base_context)


            self.logger.debug(f"Analysis Stage Result: {json.dumps(analysis_result, indent=2)}")
            
            # Log context update after analysis
            self.logger.info("Updating context with analysis results")
            base_context["stage_results"]["analysis"] = analysis_result
            self.logger.debug(f"Context after analysis: {json.dumps(base_context['stage_results'], indent=2)}")

            # Guidelines Stage
            self.logger.info("\n=== Starting Guidelines Stage ===")
            self.logger.info("Executing guidelines_stage.execute()")
            guidelines_result = self.guidelines_stage.execute(base_context)
            self.logger.debug(f"Guidelines Stage Result: {json.dumps(guidelines_result, indent=2)}")
            
            # Log context update after guidelines
            self.logger.info("Updating context with guidelines results")
            base_context["stage_results"]["guidelines"] = guidelines_result
            self.logger.debug(f"Context after guidelines: {json.dumps(base_context['stage_results'], indent=2)}")

            # Enhancement Stage
            self.logger.info("\n=== Starting Enhancement Stage ===")
            self.logger.info("Executing enhancement_stage.execute()")
            enhancement_result = self.enhancement_stage.execute(base_context)
            self.logger.debug(f"Enhancement Stage Result: {json.dumps(enhancement_result, indent=2)}")
            
            # Log context update after enhancement
            self.logger.info("Updating context with enhancement results")
            base_context["stage_results"]["enhancement"] = enhancement_result
            self.logger.debug(f"Final context state: {json.dumps(base_context['stage_results'], indent=2)}")

            # Log response creation
            self.logger.info("\n=== Preparing Final Response ===")
            response = {
                "status": "success",
                "request_id": base_context["request_id"],
                "metadata": {
                    "timestamp": base_context["timestamp"],
                    "ai_type": ai_type,
                    "style": style,
                    "execution_metrics": {
                        "completion_time": datetime.datetime.now().isoformat()
                    }
                },
                "stages": {
                    "analysis": {"result": analysis_result},
                    "guidelines": {"result": guidelines_result},
                    "enhancement": {"result": enhancement_result}
                }
            }
            self.logger.debug(f"Final Response: {json.dumps(response, indent=2)}")
            self.logger.info("=== Pipeline Execution Completed ===")

            return response

        except Exception as e:
            # Detailed error logging
            self.logger.error("\n=== Pipeline Execution Failed ===")
            self.logger.error(f"Error message: {str(e)}")
            self.logger.error("Full traceback:", exc_info=True)
            self.logger.error(f"Failed with context state: {json.dumps(base_context, indent=2)}")
            
            error_response = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
                "error_context": {
                    "last_successful_stage": next(
                        (stage for stage in ["enhancement", "guidelines", "analysis"] 
                        if stage in base_context.get("stage_results", {})),
                        None
                    )
                }
            }
            self.logger.debug(f"Error Response: {json.dumps(error_response, indent=2)}")
            return error_response

    def _generate_style_metadata(self, style: str, ai_type: str) -> Dict:
        """
        Generates comprehensive metadata about style and AI type requirements.
        This helps maintain consistent tone and approach across pipeline stages.
        
        Args:
            style (str): The requested style (e.g., 'professional', 'concise', etc.)
            ai_type (str): The type of AI system being used
            
        Returns:
            Dict: Structured metadata about style requirements and characteristics
        """
        try:
            # Define base style characteristics
            style_mapping = {
                "professional": {
                    "tone": "formal",
                    "structure": "well-organized",
                    "vocabulary_level": "business-appropriate",
                    "formatting": "structured",
                    "key_characteristics": [
                        "clear and direct communication",
                        "industry-standard terminology",
                        "formal discourse markers"
                    ]
                },
                "concise": {
                    "tone": "direct",
                    "structure": "compact",
                    "vocabulary_level": "precise",
                    "formatting": "minimal",
                    "key_characteristics": [
                        "brief and focused content",
                        "essential information only",
                        "clear topic sentences"
                    ]
                },
                "conversational": {
                    "tone": "informal",
                    "structure": "natural flow",
                    "vocabulary_level": "everyday",
                    "formatting": "flexible",
                    "key_characteristics": [
                        "natural dialogue patterns",
                        "relatable examples",
                        "engaging tone"
                    ]
                },
                "technical": {
                    "tone": "precise",
                    "structure": "systematic",
                    "vocabulary_level": "technical",
                    "formatting": "detailed",
                    "key_characteristics": [
                        "technical accuracy",
                        "detailed explanations",
                        "domain-specific terminology"
                    ]
                }
            }

            # Define AI type characteristics
            ai_type_requirements = {
                "ChatGPT": {
                    "response_format": "conversational",
                    "interaction_style": "dialogue-based",
                    "special_features": ["context awareness", "natural language understanding"],
                    "formatting_preferences": ["clear paragraph breaks", "natural transitions"]
                },
                "descriptive": {
                    "response_format": "detailed",
                    "interaction_style": "explanatory",
                    "special_features": ["rich descriptions", "structured explanations"],
                    "formatting_preferences": ["organized sections", "clear hierarchies"]
                },
                "analytical": {
                    "response_format": "structured",
                    "interaction_style": "analytical",
                    "special_features": ["data interpretation", "logical flow"],
                    "formatting_preferences": ["clear sections", "evidence-based arguments"]
                }
            }

            # Get base style characteristics or create generic ones if style not found
            style_characteristics = style_mapping.get(style.lower(), {
                "tone": "balanced",
                "structure": "standard",
                "vocabulary_level": "general",
                "formatting": "default",
                "key_characteristics": ["clear communication", "appropriate tone"]
            })

            # Get AI type requirements or use generic ones if type not found
            ai_characteristics = ai_type_requirements.get(ai_type, {
                "response_format": "standard",
                "interaction_style": "general",
                "special_features": ["basic interaction"],
                "formatting_preferences": ["clear structure"]
            })

            # Combine into comprehensive metadata
            return {
                "style_configuration": {
                    "type": style,
                    "characteristics": style_characteristics,
                    "application_rules": {
                        "tone_consistency": True,
                        "vocabulary_constraints": style_characteristics["vocabulary_level"],
                        "formatting_requirements": style_characteristics["formatting"]
                    }
                },
                "ai_configuration": {
                    "type": ai_type,
                    "characteristics": ai_characteristics,
                    "requirements": {
                        "response_format": ai_characteristics["response_format"],
                        "interaction_patterns": ai_characteristics["interaction_style"]
                    }
                },
                "combined_requirements": {
                    "primary_tone": style_characteristics["tone"],
                    "structural_approach": style_characteristics["structure"],
                    "key_features": list(set(
                        style_characteristics["key_characteristics"] +
                        ai_characteristics["special_features"]
                    ))
                },
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "version": "1.0",
                    "validation_status": "active"
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating style metadata: {str(e)}")
            # Return minimal valid metadata on error
            return {
                "style_configuration": {"type": style, "characteristics": {}},
                "ai_configuration": {"type": ai_type, "characteristics": {}},
                "combined_requirements": {"primary_tone": "standard", "structural_approach": "default"},
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "error": str(e)
                }
            }
        
    def _extract_parameters(self, params: Dict) -> Dict:
        try:
            return {
                k: float(v) for k, v in params.items()
            } if params else {
                "temperature": 0.7,
                "top_p": 0.9,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }
        except Exception:
            return {
                "temperature": 0.7,
                "top_p": 0.9,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }

    def _add_to_context_chain(self, pipeline_context: Dict, stage_name: str, result: Dict):
        """Adds stage result to context chain with metadata"""
        pipeline_context["stage_results"][stage_name] = result
        pipeline_context["context_chain"].append({
            "stage": stage_name,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat()
        })
        

    def _check_dependencies(self, context: Dict, dependencies: List[str]) -> bool:
        """Check if all required dependencies are available and valid"""
        stage_results = context.get("stage_results", {})
        for dep in dependencies:
            if dep not in stage_results or stage_results[dep].get("status") == "error":
                return False
        return True

    def _validate_stage_result(self, result: Dict, stage_name: str) -> bool:
        """Validate stage result structure and content"""
        try:
            if not isinstance(result, dict):
                self.logger.error(f"{stage_name} stage returned invalid result type: {type(result)}")
                return False
                
            if result.get("status") == "error":
                self.logger.error(f"{stage_name} stage reported error: {result.get('error')}")
                return False
                
            if "result" not in result and "content" not in result:
                self.logger.error(f"{stage_name} stage missing required content")
                return False
            
            self.logger.debug(f"{stage_name} stage result validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Stage validation failed: {str(e)}")
            return False
        
        

    def _get_stage_structure(self, stage_name: str) -> Dict:
        """Define expected structure for each stage"""
        stage_structures = {
            'analysis_stage.execute': {
                "intent": {},
                "requirements": [],
                "context": {}
            },
            'feedback_stage.execute': {
                "feedback": {},
                "improvements": [],
                "suggestions": {}
            },
            'guidelines_stage.execute': {
                "guidelines": "",
                "parameters": {},
                "implementation_notes": {}
            },
            'enhancement_stage.execute': {
                "prompts": []
            }
        }
        return stage_structures.get(stage_name, {})
    
    def _create_stage_fallback(self, stage_name: str) -> Dict:
        return {
        "status": "fallback",
        "stage": stage_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "result": f"Fallback response for {stage_name}"
    }

    def _generate_fallback_result(self, stage_name: str) -> Dict:
        """Generate a fallback result for a specific stage"""
        fallback_results = {
            'analysis_stage.execute': {
                "intent": {"primary_objective": "Default analysis"},
                "requirements": ["Generic requirement"],
                "context": {"default": "Fallback context"}
            },
            'feedback_stage.execute': {
                "feedback": {"status": "Unable to provide detailed feedback"},
                "improvements": ["Generic improvement"],
                "suggestions": {"content": []}
            },
            'guidelines_stage.execute': {
                "guidelines": "Generic guidelines for implementation",
                "parameters": {"temperature": 0.7},
                "implementation_notes": {"default": "Fallback implementation"}
            },
            'enhancement_stage.execute': {
                "prompts": [{"prompt": "Fallback enhanced prompt"}]
            }
        }
        return fallback_results.get(stage_name, {})

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

        YOU MUST RESPOND WITH A VALID JSON OBJECT USING EXACTLY THIS STRUCTURE:
    {{
        "primary_objective": "string describing main goal",
        "detailed_requirements": [
            "requirement1",
            "requirement2"
        ],
        "implicit_expectations": [
            "expectation1",
            "expectation2"
        ],
        "potential_challenges": [
            "challenge1",
            "challenge2"
        ],
        "success_criteria": [
            "criteria1",
            "criteria2"
        ]
    }}

    ANY DEVIATION FROM THIS FORMAT WILL CAUSE ERRORS.
    DO NOT INCLUDE ANY TEXT OR CONTENT OUTSIDE THE JSON STRUCTURE."""

        try:
            preprocessed = self.preprocessor.analyze_prompt(prompt)
            self.logger.info(f"Preprocessing results: {json.dumps(preprocessed, indent=2)}")
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

    def _create_error_response(self, error: Union[str, Exception]) -> Dict:
        """Create standardized error response"""
        return {
            "status": "error",
            "error": str(error),
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": {
                "error_type": type(error).__name__,
                "pipeline_id": str(uuid.uuid4())
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

 

class ResponseHandler:
    def __init__(self, logger: Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def _format_error_response(self, response: Dict) -> Dict:
        """Format error responses consistently"""
        return {
            "status": "error",
            "error": response.get("error", "Unknown error"),
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": {
                "original_response": response
            }
        }
    
    def standardize_response(self, pipeline_result: Dict) -> Dict:
        """
        Create a consistent, flexible response structure
        that can handle partial or complete pipeline processing.
        """
        standard_response = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_status": pipeline_result.get('status', 'unknown'),
                "ai_configuration": {
                    "type": pipeline_result.get('ai_type', 'generic'),
                    "style": pipeline_result.get('style', 'default')
                }
            },
            "results": {
                stage: result for stage, result in pipeline_result.get('stages', {}).items()
            },
            "errors": pipeline_result.get('errors', [])
        }
        
        return standard_response

    def _create_fallback_preprocessing(self) -> Dict:
        """Create fallback preprocessing response"""
        return {
            "linguistic_features": {
                "semantic": {
                    "coherence": 0.0,
                    "relationships": [],
                    "semantic_clusters": []
                },
                "discourse": {
                    "structure": {},
                    "primary_type": "general",
                    "markers": []
                },
                "complexity": {
                    "overall_score": 0.0,
                    "readability_metrics": {},
                    "structural_analysis": {}
                }
            },
            "content_analysis": {
                "named_entities": [],
                "keywords": [],
                "topics": [],
                "sentiment": {"label": "neutral", "score": 0.5}
            }
        }

    def format_response(self, pipeline_context: Dict) -> Dict:
        try:
            # Ensure all required fields are present
            if not all(k in pipeline_context for k in ["request_id", "timestamp", "ai_type", "style"]):
                raise ValueError("Missing required context fields")

            # Build base response
            response = {
                "status": "success",
                "request_id": pipeline_context["request_id"],
                "metadata": {
                    "timestamp": pipeline_context["timestamp"],
                    "ai_type": pipeline_context["ai_type"],
                    "style": pipeline_context["style"]
                },
                "stages": {}
            }

            # Add stage results with validation
            for stage_name, result in pipeline_context.get("stage_results", {}).items():
                if result:  # Only add non-empty results
                    response["stages"][stage_name] = {
                        "result": result,
                        "metadata": {
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    }

            return response
            
        except Exception as e:
            return self._format_error_response(e)

    def _enrich_stage_result(self, stage_context: Dict) -> Dict:
        """Enrich stage results with additional metadata"""
        result = stage_context["result"]
        return {
            "data": result,
            "metadata": {
                "timestamp": stage_context["timestamp"],
                "sequence": stage_context["sequence"],
                "dependencies": stage_context.get("dependencies", [])
            }
        }
    def _extract_preprocessing_details(self, initial_analysis: Dict) -> Dict:
        """Enhanced preprocessing details extraction with defaults"""
        try:
            # Get analysis components with defaults
            semantic_analysis = initial_analysis.get('linguistic_features', {}).get('semantic', {})
            discourse_analysis = initial_analysis.get('linguistic_features', {}).get('discourse', {})
            complexity_metrics = initial_analysis.get('linguistic_features', {}).get('complexity_metrics', {})
            
            return {
                "linguistic_features": {
                    "semantic": {
                        "coherence": semantic_analysis.get('coherence_score', 0.0),
                        "relationships": semantic_analysis.get('sentence_relationships', []),
                        "semantic_clusters": semantic_analysis.get('semantic_clusters', [])
                    },
                    "discourse": {
                        "structure": discourse_analysis.get('discourse_structure', {}),
                        "primary_type": discourse_analysis.get('primary_discourse_type', 'general'),
                        "markers": discourse_analysis.get('discourse_markers', [])
                    },
                    "complexity": {
                        "overall_score": complexity_metrics.get('overall_score', 0.0),
                        "readability_metrics": complexity_metrics,
                        "structural_analysis": initial_analysis.get('linguistic_features', {}).get('structural_features', {})
                    }
                },
                "content_analysis": initial_analysis.get('content_analysis', {
                    "named_entities": [],
                    "keywords": [],
                    "topics": [],
                    "sentiment": {"label": "neutral", "score": 0.5}
                })
            }
        except Exception as e:
            self.logger.error(f"Error extracting preprocessing details: {e}")
            return self._create_fallback_preprocessing()

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
            if not isinstance(content, str):
                return "{}"
            # Find and extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                # Validate it's parseable
                json.loads(json_str)
                return json_str
            return "{}"
        except:
            return "{}"




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
    
    def _select_api_parameters(self, ai_type: str, style: str) -> Dict[str, float]:
        """
        Select API parameters based on AI type and style combination
        """
        param_matrix = {
            # Default fallback configuration
            'default': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            
            # Parameters for ChatGPT
            'ChatGPT': {
                'professional': {
                    'temperature': 0.5,
                    'top_p': 0.8,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'creative': {
                    'temperature': 0.8,
                    'top_p': 0.9,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.0
                },
                'descriptive': {
                    'temperature': 0.6,
                    'top_p': 0.85,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'concise': {
                    'temperature': 0.4,
                    'top_p': 0.7,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.2
                }
            },
            
            # Parameters for Claude
            'Claude': {
                'professional': {
                    'temperature': 0.4,
                    'top_p': 0.75,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'creative': {
                    'temperature': 0.7,
                    'top_p': 0.85,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.0
                },
                'descriptive': {
                    'temperature': 0.5,
                    'top_p': 0.8,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'concise': {
                    'temperature': 0.3,
                    'top_p': 0.7,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.2
                }
            },
            
            # Parameters for Gamma
            'Gamma': {
                'professional': {
                    'temperature': 0.5,
                    'top_p': 0.8,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'creative': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.0
                },
                'descriptive': {
                    'temperature': 0.6,
                    'top_p': 0.85,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'concise': {
                    'temperature': 0.4,
                    'top_p': 0.7,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.2
                }
            },
            
            # Parameters for Midjourney
            'Midjourney': {
                'professional': {
                    'temperature': 0.4,
                    'top_p': 0.75,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'creative': {
                    'temperature': 0.8,
                    'top_p': 0.9,
                    'presence_penalty': 0.3,
                    'frequency_penalty': 0.0
                },
                'descriptive': {
                    'temperature': 0.6,
                    'top_p': 0.85,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.1
                },
                'concise': {
                    'temperature': 0.3,
                    'top_p': 0.7,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.2
                }
            },
            
            # Parameters for Gemini
            'Gemini': {
                'professional': {
                    'temperature': 0.5,
                    'top_p': 0.8,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'creative': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.0
                },
                'descriptive': {
                    'temperature': 0.6,
                    'top_p': 0.85,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'concise': {
                    'temperature': 0.4,
                    'top_p': 0.7,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.2
                }
            }
        }

        # Retrieve parameters based on AI type and style
        if ai_type in param_matrix and style in param_matrix[ai_type]:
            return param_matrix[ai_type][style]
        else:
            return param_matrix['default']

    def enhance_prompt(self, prompt: str, guidelines: str, parameters: Dict, **kwargs) -> Dict:
        """
        Second API call: Generate enhanced versions of the prompt using the analysis and parameters.
        Uses the parameters and guidelines from the first call to create optimized prompt versions.
        """
        try:

            if not guidelines or len(guidelines) < 10:
                self.logger.warning("Insufficient guidelines for enhancement")
                guidelines = "Generic guidelines for prompt optimization"
            
            style = kwargs.get('style', 'professional')
            ai_type = kwargs.get('ai_type', 'general')
            param_values = self._select_api_parameters(ai_type, style)
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
                                            **param_values,
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
                    
                },
                {
                    "prompt": f"Develop a detailed specification for {prompt}, including all necessary components, features, and technical requirements",
                    },
                {
                    "prompt": f"Design an engaging and user-friendly {prompt} that emphasizes {style} presentation and optimal user experience",
                    }
            ]
        }
    




class ResponseManager:
    """
    Manages response data throughout the pipeline, ensuring consistency and proper formatting.
    Acts as a central point for data transformation and validation.
    """
    def __init__(self, logger: Logger):
        self.logger = logger
        self.preprocessing_data = {}
        self.stage_results = {}

    def _format_error_response(self, error: Union[str, Exception]) -> Dict:
        """Format error responses with proper timestamp handling"""
        return {
            "status": "error",
            "error": str(error),
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": {
                "error_type": type(error).__name__
            }
        }

    def format_response(self, pipeline_context: Dict) -> Dict:
        try:
            prompts = (pipeline_context.get("stage_results", {})
                    .get("enhancement", {})
                    .get("result", {})
                    .get("prompts", []))
            
            return {
                "prompts": prompts,
                "metadata": {
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
        except Exception as e:
            return self._format_error_response(e)
        
    def _format_stage_results(self, stage_results: Dict) -> Dict:
        """Safely format stage results with error handling"""
        formatted_results = {}
        for stage_name, result in stage_results.items():
            try:
                if isinstance(result, dict):
                    # Ensure each stage result has a timestamp
                    if "_metadata" not in result:
                        result["_metadata"] = {
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    formatted_results[stage_name] = result
                else:
                    formatted_results[stage_name] = {
                        "content": str(result),
                        "_metadata": {
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    }
            except Exception as e:
                self.logger.error(f"Error formatting stage {stage_name}: {str(e)}")
                formatted_results[stage_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }
        
        return formatted_results
        
    def _calculate_execution_time(self, pipeline_context: Dict) -> float:
        """Calculate total execution time of pipeline"""
        start_time = datetime.datetime.fromisoformat(
            pipeline_context.get("metadata", {}).get("start_time", "")
        )
        if not start_time:
            return 0.0
        
        end_time = datetime.datetime.now()
        return (end_time - start_time).total_seconds()

    def _collect_stage_errors(self, stage_results: Dict) -> List[Dict]:
        """Collect errors from all pipeline stages"""
        errors = []
        for stage_name, result in stage_results.items():
            if isinstance(result, dict):
                if result.get("status") == "error":
                    errors.append({
                        "stage": stage_name,
                        "error": result.get("error", "Unknown error"),
                        "timestamp": result.get("timestamp", datetime.datetime.now().isoformat())
                    })
                elif result.get("status") == "fallback":
                    errors.append({
                        "stage": stage_name,
                        "error": "Stage failed, using fallback response",
                        "timestamp": result.get("timestamp", datetime.datetime.now().isoformat())
                    })
        return errors
        

        
    def update_stage_result(self, stage_name: str, result: Dict):
        """
        Updates results for a specific pipeline stage while maintaining data integrity.
        """
        try:
            # Validate and normalize the result
            normalized_result = self._normalize_result(result, stage_name)
            
            # Store preprocessing data separately
            if stage_name == "preprocessing":
                self.preprocessing_data = normalized_result
            
            # Store stage result
            self.stage_results[stage_name] = normalized_result
            
        except Exception as e:
            self.logger.error(f"Error updating {stage_name} result: {str(e)}")
            self.stage_results[stage_name] = self._create_fallback_result(stage_name)
    
    def get_final_response(self) -> Dict:
        """
        Creates the final response with all accumulated data.
        Ensures all required fields are present with proper formatting.
        """
        try:
            return {
                "status": "success",
                "metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "version": "2.0.0"
                },
                "preprocessing": self.preprocessing_data,
                "stages": {
                    stage: self._ensure_required_fields(stage, result)
                    for stage, result in self.stage_results.items()
                },
                "summary": self._generate_summary()
            }
        except Exception as e:
            self.logger.error(f"Error creating final response: {str(e)}")
            return self._create_error_response(str(e))

    def _normalize_result(self, result: Dict, stage_name: str) -> Dict:
        """
        Normalizes results to ensure consistent structure.
        """
        if not isinstance(result, dict):
            return {"content": str(result)}
            
        if "raw_response" in result:
            return self._convert_raw_response(result, stage_name)
            
        return result

    def _ensure_required_fields(self, stage_name: str, result: Dict) -> Dict:
        """
        Ensures all required fields are present for each stage.
        """
        required_fields = {
            "preprocessing": {
                "linguistic": {"complexity_metrics": {}, "discourse_analysis": {}, "semantic_analysis": {}},
                "content_analysis": {"named_entities": [], "keywords": [], "topics": [], "sentiment": {}}
            },
            "analysis": {
                "intent": {}, 
                "requirements": [], 
                "context": {}
            },
            # Add required fields for other stages...
        }
        
        stage_fields = required_fields.get(stage_name, {})
        return {**stage_fields, **result}

    def _generate_summary(self) -> Dict:
        """
        Generates a summary of the pipeline results.
        """
        return {
            "stages_completed": list(self.stage_results.keys()),
            "preprocessing_success": bool(self.preprocessing_data),
            "total_stages": len(self.stage_results)
        }
    
model_manager = None
try:
    model_manager = ModelManager()
    logger.info("Model Manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Model Manager: {e}")
    



@app.route('/process', methods=['POST'])
def process_request():
    try:
        if request.is_json:
            data = request.get_json()
        elif request.content_type == 'application/x-www-form-urlencoded':
            try:
                form_data = request.form.get('data')
                if not form_data:
                    return jsonify({
                        "status": "error",
                        "error": "No data provided in form",
                        "timestamp": datetime.datetime.now().isoformat()
                    }), 400
                data = json.loads(form_data)
            except json.JSONDecodeError:
                return jsonify({
                    "status": "error",
                    "error": "Invalid JSON in form data",
                    "timestamp": datetime.datetime.now().isoformat()
                }), 400
        else:
            return jsonify({
                "status": "error",
                "error": f"Unsupported Content-Type: {request.content_type}",
                "timestamp": datetime.datetime.now().isoformat()
            }), 415

        if not data or 'prompt' not in data:
            return jsonify({
                "status": "error",
                "error": "Missing prompt in request data",
                "timestamp": datetime.datetime.now().isoformat()
            }), 400

        pipeline = EnhancedPromptPipeline(logger)
        response = pipeline.execute_pipeline(
            prompt=data['prompt'],
            ai_type=data.get('AIType', 'descriptive'),
            style=data.get('style', 'professional')
        )

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
            "request_info": {
                "content_type": request.content_type,
                "method": request.method
            }
        }), 500
    
    
@app.route('/process', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)
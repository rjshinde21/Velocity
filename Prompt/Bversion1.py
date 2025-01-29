#this was left because multiple API calls are made here, use prompt.py, only 1 API call is made there


from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
import os
import logging
from typing import Dict, Any, List, Tuple, Union
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
        
class ContextTracker:
    def __init__(self):
        self.context_chain = []  # Main storage for all context
        self.last_context = {}   # Replaces current_context
        self.metadata = {
            "creation_timestamp": datetime.datetime.now(),
            "total_stages_processed": 0
        }

    def add_stage_result(self, stage_name: str, result: Dict, metadata: Dict = None) -> None:
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
    
    def add_stage_result(self, stage_name: str, result: Dict) -> None:
        stage_context = {
            "stage": stage_name,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat(),
            "sequence": len(self.context_chain)
        }
        self.context_chain.append(stage_context)
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
        self.response_processors = {
            "enhancement": self._process_enhancement_response
        }

    def make_api_call(self, system_message: str, prompt: str, context: Dict = None, stage: str = None,**params) -> Dict:
        self.logger.info("Starting API call")
        self.logger.debug(f"System message: {system_message}")
        self.logger.debug(f"Prompt: {prompt}")
        self.logger.debug(f"Context: {json.dumps(context, indent=2) if context else 'None'}")
        self.logger.debug(f"Additional params: {json.dumps(params, indent=2)}")

        try:
            messages = [
                {"role": "system", "content": system_message}
            ]
            
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Context: {json.dumps(context, indent=2)}"
                })
            
            messages.append({"role": "user", "content": prompt})
            
            self.logger.debug(f"Final messages array: {json.dumps(messages, indent=2)}")
            
            request_data = {
                "messages": messages,
                "model": "llama3.2-1b",
                "max_tokens": 12000,
                "stream": False,
                **params
            }
            
            self.logger.info("Executing Llama API call")
            response = llama.run(request_data)
            self.logger.info("API call completed")
            self.logger.debug(f"Raw response: {response}")
            
            if stage and stage in self.response_processors:
                self.logger.info(f"Using {stage}-specific response processor")
                return self.response_processors[stage](response)
            return self._process_response(response)


        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}", exc_info=True)
            raise
  
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

    def _process_response(self, response_data: Any) -> Dict:
        """Process API response with support for both list and dict responses"""
        self.logger.info("Starting response processing")
        try:
            # Check if it's a raw API response object
            if hasattr(response_data, 'json'):
                self.logger.debug("Converting response to JSON")
                response_data = response_data.json()

            self.logger.debug(f"Response data type: {type(response_data)}")
            self.logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")

            # Handle list response
            if isinstance(response_data, list):
                self.logger.info("Converting list response to dictionary")
                # Take first message if it's a list of messages
                if response_data and isinstance(response_data[0], dict):
                    content = response_data[0].get('content') or response_data[0].get('text', '')
                    response_data = {"content": content}
                else:
                    # Convert simple list to dictionary
                    response_data = {"content": str(response_data)}

            if not isinstance(response_data, dict):
                error_msg = f"Invalid response type: {type(response_data)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            return response_data

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
    def _extract_content(self, response_data: Dict) -> str:
        self.logger.debug("Extracting content from response")
        content = None
        
        if 'choices' in response_data:
            first_choice = response_data['choices'][0]
            if 'message' in first_choice:
                content = first_choice['message'].get('content', '')
            elif 'text' in first_choice:
                content = first_choice['text']

        if not content:
            error_msg = "No content found in response"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.debug(f"Extracted content: {content}")
        return content


        
    def _validate_and_structure_json(self, content: Dict) -> Dict:
        self.logger.debug("Validating and structuring JSON")
        try:
            if not isinstance(content, dict):
                content = {"content": content}
                
            content["_metadata"] = {
                "processed_timestamp": datetime.datetime.now().isoformat(),
                "processing_stage": "api_response",
                "format_version": "2.0"
            }
            
            result = self._ensure_json_compliance(content)
            self.logger.debug(f"Structured result: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            self.logger.error(f"JSON validation failed: {str(e)}", exc_info=True)
            raise


    def _ensure_json_compliance(self, obj: Any) -> Any:
        self.logger.debug(f"Ensuring JSON compliance for: {type(obj)}")
        try:
            if isinstance(obj, dict):
                return {k: self._ensure_json_compliance(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._ensure_json_compliance(v) for v in obj]
            elif isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            else:
                self.logger.debug(f"Converting {type(obj)} to string")
                return str(obj)
        except Exception as e:
            self.logger.error(f"JSON compliance check failed: {str(e)}", exc_info=True)
            raise


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
        self.logger.debug("Cleaning content")
        content = content.strip()
        
        if '```json' in content:
            self.logger.debug("Removing JSON code blocks")
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            self.logger.debug("Removing generic code blocks")
            content = content.split('```')[1].split('```')[0]
            
        cleaned = content.strip()
        self.logger.debug(f"Cleaned content: {cleaned}")
        return cleaned

    def _process_enhancement_response(self, response_data: Any) -> Dict:
        """Specialized response processor for enhancement stage responses"""
        self.logger.info("Processing enhancement stage response")
        try:
            # Log the initial response data type and structure
            self.logger.debug(f"Initial response_data type: {type(response_data)}")
            self.logger.debug(f"Initial response_data: {json.dumps(response_data, indent=2)}")

            # Handle list response format
            if isinstance(response_data, list) and response_data:
                self.logger.debug("Response is a list, taking first element")
                response_data = response_data[0]

            # Extract content from message structure with detailed logging
            content = None
            if isinstance(response_data, dict):
                self.logger.debug("Response is a dictionary, attempting to extract content")
                # Try different possible content locations
                if 'message' in response_data:
                    content = response_data['message'].get('content', '')
                    self.logger.debug("Found content in message.content")
                elif 'content' in response_data:
                    content = response_data['content']
                    self.logger.debug("Found content directly in content field")
                elif 'choices' in response_data and response_data['choices']:
                    content = response_data['choices'][0].get('message', {}).get('content', '')
                    self.logger.debug("Found content in choices array")
            else:
                content = str(response_data)
                self.logger.debug("Converted response to string")

            if not content:
                self.logger.error("No content found in response")
                return self._create_enhancement_fallback()

            self.logger.debug(f"Extracted raw content: {content}")

            # Try to find JSON within the content
            json_start = content.find('{\n  "prompts"')
            if json_start != -1:
                self.logger.debug(f"Found JSON start at position {json_start}")
                try:
                    json_content = content[json_start:]
                    json_data = json.loads(json_content)
                    self.logger.debug(f"Successfully parsed JSON content: {json.dumps(json_data, indent=2)}")
                    return json_data
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON from content: {str(e)}")

            # If no JSON found, parse the markdown format
            self.logger.debug("Attempting to parse markdown format")
            enhanced_versions = []
            lines = content.split('\n')
            current_version = None
            current_text = []

            # Log each line for debugging
            for i, line in enumerate(lines):
                self.logger.debug(f"Processing line {i}: {line}")
                
                # Check for version markers with more flexible matching
                if "Enhanced Version" in line or "Version" in line:
                    self.logger.debug(f"Found version marker: {line}")
                    if current_version and current_text:
                        prompt_text = ' '.join(current_text).strip('"').strip()
                        self.logger.debug(f"Adding version {current_version}: {prompt_text}")
                        enhanced_versions.append({
                            "prompt": prompt_text,
                            "focus": f"Version {current_version}",
                            "perspective": "Enhanced Description"
                        })
                    try:
                        current_version = line.split('Version')[1].split(':')[0].strip()
                    except IndexError:
                        current_version = str(len(enhanced_versions) + 1)
                    current_text = []
                elif current_version and line.strip():
                    current_text.append(line.strip())

            # Add the last version
            if current_version and current_text:
                prompt_text = ' '.join(current_text).strip('"').strip()
                self.logger.debug(f"Adding final version {current_version}: {prompt_text}")
                enhanced_versions.append({
                    "prompt": prompt_text,
                    "focus": f"Version {current_version}",
                    "perspective": "Enhanced Description"
                })

            if enhanced_versions:
                self.logger.info(f"Successfully extracted {len(enhanced_versions)} enhanced versions")
                return {"prompts": enhanced_versions}

            # If we still haven't found any prompts, try one last parsing attempt
            self.logger.debug("Attempting final parsing of content")
            # Split content by double newlines to separate distinct sections
            sections = content.split('\n\n')
            if len(sections) > 1:
                enhanced_versions = [
                    {
                        "prompt": section.strip('"').strip(),
                        "focus": f"Version {i+1}",
                        "perspective": "Enhanced Description"
                    }
                    for i, section in enumerate(sections)
                    if section.strip()
                ]
                if enhanced_versions:
                    self.logger.info(f"Extracted {len(enhanced_versions)} versions from sections")
                    return {"prompts": enhanced_versions}

            self.logger.warning("Could not extract prompts from content")
            self.logger.debug("Final content that couldn't be parsed:", content)
            return self._create_enhancement_fallback()

        except Exception as e:
            self.logger.error(f"Enhancement response processing failed: {str(e)}", exc_info=True)
            return self._create_enhancement_fallback()


    def _create_enhancement_fallback(self) -> Dict:
        """Create a fallback response for enhancement stage"""
        self.logger.info("Creating enhancement fallback response")
        fallback = {
            "prompts": [{
                "prompt": "Could not process the enhancement request. Please try again with more specific instructions.",
               
            }]
        }
        self.logger.debug(f"Created fallback response: {json.dumps(fallback, indent=2)}")
        return fallback

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
        self.logger.error(f"Creating error response: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.datetime.now().isoformat()
        }


class PromptPreprocessor:
    def __init__(self):
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

    def analyze_prompt(self, prompt: str) -> Dict:
        """Comprehensive prompt analysis with improved field population"""
        try:
            doc = self.nlp(prompt)
            
            # Enhanced entity extraction
            named_entities = []
            for ent in doc.ents:
                named_entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })

            # Enhanced keyword extraction
            keywords = self.keyword_model.extract_keywords(prompt, 
                                                        top_n=5, 
                                                        stop_words='english')

            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer(prompt)[0]
            
            # Enhanced complexity analysis
            complexity_metrics = {
                "flesch_score": textstat.flesch_reading_ease(prompt),
                "grade_level": textstat.coleman_liau_index(prompt),
                "sentence_complexity": self._calculate_sentence_complexity(doc)
            }

            # Semantic analysis
            semantic_analysis = self._analyze_semantic_relationships(doc)
            
            # Discourse analysis
            discourse_analysis = self._analyze_discourse_structure(doc)

            return {
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
                    "semantic": semantic_analysis,
                    "discourse": discourse_analysis,
                    "complexity_metrics": complexity_metrics,
                    "structural_features": {
                        "sentence_count": len(list(doc.sents)),
                        "word_count": len([token for token in doc if not token.is_punct]),
                        "avg_sentence_length": self._calculate_avg_sentence_length(doc)
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"Prompt analysis failed: {str(e)}")
            return self._create_fallback_analysis()
        
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

    # @staticmethod
    # def clean_response(response: Dict) -> Dict:
    #     """Clean and normalize API response"""
    #     cleaned = {}
        
    #     # Handle nested structures
    #     for key, value in response.items():
    #         if isinstance(value, dict):
    #             cleaned[key] = ResponseValidator.clean_response(value)
    #         elif isinstance(value, list):
    #             cleaned[key] = [
    #                 ResponseValidator.clean_response(item) if isinstance(item, dict) else item
    #                 for item in value
    #             ]
    #         else:
    #             # Convert None to empty string/list/dict based on context
    #             if value is None:
    #                 if key.endswith(('list', 'array', 'items')):
    #                     cleaned[key] = []
    #                 elif key.endswith(('dict', 'map')):
    #                     cleaned[key] = {}
    #                 else:
    #                     cleaned[key] = ""
    #             else:
    #                 cleaned[key] = value
                    
    #     return cleaned





    

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

    def _enrich_context(self, current_stage_result: Dict, previous_context: Dict) -> Dict:
        """
        Intelligently merge current stage result with previous context.
        
        Key Improvements:
        - Preserves important information from previous stages
        - Allows controlled context evolution
        """
        enriched_context = previous_context.copy()
        
        # Merge strategy: prioritize current stage's information
        for key, value in current_stage_result.items():
            if value:  # Only add non-empty values
                enriched_context[key] = value
        
        return enriched_context

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
        """Preserve context from stage execution with proper error handling"""
        try:
            # Get latest context first
            previous_context = self.context_tracker.get_latest_context()
            
            # Add metadata
            result["_stage_metadata"] = {
                "stage_name": stage_name,
                "execution_timestamp": datetime.datetime.now().isoformat(),
                "previous_context": previous_context
            }
            
            # Add to context tracker
            self.context_tracker.add_context(stage_name, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Context preservation failed in {stage_name}: {str(e)}")
            # Return original result if context preservation fails
            return result
        
    def execute(self, stage_input: Dict) -> Dict:
        try:
            # Extract core components
            prompt = stage_input["prompt"]
            ai_type = stage_input["ai_type"]
            style = stage_input["style"]
            
            # Create stage-specific system message
            system_message = self._create_system_message(ai_type, style)
            
            # Generate stage-specific prompt
            user_message = self._create_user_message(stage_input)
            
            # Make API call with context
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                context=stage_input,
                **self._get_stage_parameters(stage_input)
            )
            
            return self._process_stage_response(response)
            
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


# class PipelineContext:
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
#             "parameters": self._get_default_parameters()
#         }

#     def _get_default_parameters(self) -> Dict:
#         return {
#             "temperature": {"value": 0.7, "reasoning": "Default balanced temperature"},
#             "top_p": {"value": 0.9, "reasoning": "Default sampling diversity"},
#             "presence_penalty": {"value": 0.0, "reasoning": "Default presence penalty"},
#             "frequency_penalty": {"value": 0.0, "reasoning": "Default frequency penalty"}
#         }
    
#     def get_context(self) -> Dict:
#         """Get complete pipeline context"""
#         return self.context

#     def update_stage_result(self, stage_name: str, result: Dict):
#         """Update results for a specific stage"""
#         if "stage_results" not in self.context["execution_context"]:
#             self.context["execution_context"]["stage_results"] = {}
#         self.context["execution_context"]["stage_results"][stage_name] = result

#     def get_stage_result(self, stage_name: str) -> Dict:
#         """Get results for a specific stage"""
#         return self.context["execution_context"]["stage_results"].get(stage_name, {})

#     def update_parameters(self, parameters: Dict):
#         """Validate and update parameters with bounds checking"""
#         param_bounds = {
#             "temperature": (0.1, 1.0),
#             "top_p": (0.1, 1.0), 
#             "presence_penalty": (-2.0, 2.0),
#             "frequency_penalty": (-2.0, 2.0)
#         }

#         validated_params = {}
#         for param_name, bounds in param_bounds.items():
#             try:
#                 param_data = parameters.get(param_name, {})
#                 if isinstance(param_data, dict):
#                     value = float(param_data.get('value', self._get_default_parameters()[param_name]['value']))
#                 else:
#                     value = float(param_data)

#                 min_val, max_val = bounds
#                 clamped_value = max(min_val, min(max_val, value))
                
#                 if clamped_value != value:
#                     self.add_warning("parameters", 
#                         f"Parameter {param_name} adjusted from {value} to {clamped_value}")

#                 validated_params[param_name] = {
#                     "value": clamped_value,
#                     "reasoning": param_data.get('reasoning', "Automatically adjusted")
#                 }

#             except (TypeError, ValueError) as e:
#                 self.add_error("parameters", f"Invalid {param_name} value: {str(e)}")
#                 validated_params[param_name] = self._get_default_parameters()[param_name]

#         self.context["parameters"] = validated_params

#     def get_api_parameters(self) -> Dict:
#         """Extract clean parameters for API calls"""
#         return {
#             name: data["value"] 
#             for name, data in self.context["parameters"].items()
#         }
    
#     def add_error(self, stage_name: str, error: str):
#         """Add error information"""
#         if "errors" not in self.context["execution_context"]:
#             self.context["execution_context"]["errors"] = []
            
#         self.context["execution_context"]["errors"].append({
#             "stage": stage_name,
#             "error": error,
#             "timestamp": datetime.datetime.now().isoformat()
#         })

#     def add_warning(self, stage_name: str, warning: str):
#         """Add warning information"""
#         if "warnings" not in self.context["execution_context"]:
#             self.context["execution_context"]["warnings"] = []
            
#         self.context["execution_context"]["warnings"].append({
#             "stage": stage_name,
#             "warning": warning,
#             "timestamp": datetime.datetime.now().isoformat()
#         })

#     {
#     "context": {
#         "ai_type": "ChatGPT",
#         "original_prompt": "make plan for 31st new year, i am lonely. my friends have plans and they are not inviting me. Also my budget is 250 rupees. i am in india. and it is 11:45pm i only have 14 minutes",
#         "style": "Concise"
#     },
#     "error": "'dict' object has no attribute 'context'",
#     "status": "error",
#     "timestamp": "2024-12-31T20:03:36.748451"
# }

# First, let's enhance the Analysis Stage to better handle context and AI-style requirements
class AnalysisStage(PipelineStage):

    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.required_fields = ["intent", "requirements", "context"] 

    def execute(self, pipeline_context: Dict) -> Dict:
        try:
            prompt = pipeline_context.get("original_prompt")
            ai_type = pipeline_context.get("ai_type") 
            style = pipeline_context.get("style")
            preprocessing = pipeline_context.get("stage_results", {}).get("preprocessing", {})

            system_message = self._create_system_message(ai_type, style)
            user_message = self._create_user_message(pipeline_context)

            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=user_message,
                context=preprocessing,
                temperature=0.3
            )

            return self._preserve_context("analysis", response)

        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}")
            return {
                "status": "fallback",
                "stage": "analysis",
                "timestamp": datetime.datetime.now().isoformat(),
                "result": "Fallback response for analysis"
            }

    def _create_system_message(self, ai_type: str, style: str) -> str:
        return f"""You are an AI-focused analysis expert specializing in {ai_type} systems. 
        Analyze the request with {style} style formatting."""

    def _create_user_message(self, pipeline_context: Dict) -> str:
        return f"""Analyze this request:
        Original Request: {pipeline_context.get('original_prompt')}
        Return in JSON format with intent, requirements, and context fields."""
        
    def _create_analysis_prompt(self, prompt: str, ai_type: str, style: str, preprocessing: Dict) -> str:
        """Create detailed analysis prompt with preprocessing insights"""
        return f"""
        Perform a comprehensive analysis of this request:
        
        Original Request: {prompt}
        Target AI System: {ai_type}
        Required Style: {style}
        
        Preprocessing Insights:
        - Sentiment: {preprocessing.get('content_analysis', {}).get('sentiment', {})}
        - Keywords: {preprocessing.get('content_analysis', {}).get('keywords', [])}
        - Complexity: {preprocessing.get('linguistic_features', {}).get('complexity_metrics', {})}
        
        Provide structured analysis including:
        1. Core Intent Analysis:
            - Primary objective
            - Implicit requirements
            - Success criteria
        
        2. AI Relevance Analysis:
            - {ai_type}-specific considerations
            - Technical requirements
            - Implementation challenges
        
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
    
    def _create_fallback_analysis(self, pipeline_context: Dict) -> Dict:
        """Create fallback analysis with context awareness"""
        return {
            "status": "fallback",
            "stage": "analysis",
            "timestamp": datetime.datetime.now().isoformat(),
            "intent": {
                "primary_objective": "Process and analyze the given content",
                "implicit_requirements": [
                    "Clear organization",
                    "Proper structure",
                    "Relevant content"
                ],
                "success_criteria": [
                    "Well-structured output",
                    "Complete coverage",
                    "Clear presentation"
                ]
            },
            "context": {
                "original_prompt": pipeline_context.get("original_prompt", ""),
                "ai_type": pipeline_context.get("ai_type", "general"),
                "style": pipeline_context.get("style", "standard")
            }
        }
        
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

    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
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

    def execute(self, pipeline_context: Dict) -> Dict:
        """Enhanced feedback stage with comparative analysis"""
        try:
            analysis_result = pipeline_context.get("stage_results", {}).get("analysis", {})

            context = pipeline_context.copy()
            system_message = """You are a prompt evaluation specialist.
            Compare the initial analysis with the original request to ensure alignment and completeness."""
            
            feedback_prompt = f"""
            Perform a comparative analysis:
            
            Original Request: {context.get('original_prompt', '')}
            Analyze:
            Original Request: {pipeline_context.get('original_prompt', '')}
            Initial Analysis: {json.dumps(analysis_result, indent=2)}
            AI Type: {pipeline_context.get('ai_type')}
            Style: {pipeline_context.get('style')}
            
            Evaluate the following aspects:
            1. Intent Alignment
                - Does the analysis capture the true intent?
                - Are there missing aspects?
            
            2. Technical Completeness
                - Are all technical requirements identified?
                - Is the {context.get('ai_type')} context properly considered?
            
            3. Style Adherence
                - Does it maintain {context.get('style')} style requirements?
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
            
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=feedback_prompt,
                temperature=0.4
            )
            
            return self._preserve_context("feedback", response)
            
        except Exception as e:
            self.logger.error(f"Feedback stage failed: {str(e)}")
            return self._create_fallback_feedback(pipeline_context)

class GuidelinesStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.required_fields = ["guidelines", "parameters", "implementation_notes"]
    
    def _create_fallback_guidelines(self, pipeline_context: ContextTracker) -> Dict:
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

    def execute(self, pipeline_context: Dict) -> Dict:
        """Generate comprehensive guidelines"""
        try:
            # Extract relevant information from the context dictionary
            original_prompt = pipeline_context.get("original_prompt", "")
            ai_type = pipeline_context.get("ai_type", "general")
            style = pipeline_context.get("style", "professional")
            
            # Get stage results
            stage_results = pipeline_context.get("execution_context", {}).get("stage_results", {})
            analysis_result = stage_results.get("analysis", {})
            feedback_result = stage_results.get("feedback", {})
            
            # Create system message
            system_message = f"""You are a guidelines generation expert for {ai_type} systems.
            Create comprehensive, actionable guidelines that address the user's needs.
            Consider the {style} style and previous analysis insights."""

            # Create guidelines prompt
            guidelines_prompt = f"""Generate comprehensive guidelines based on:

Original Request: {original_prompt}
AI Type: {ai_type}
Style: {style}

Previous Analysis:
{json.dumps(analysis_result, indent=2)}

Feedback Insights:
{json.dumps(feedback_result, indent=2)}

Required Output Structure:
1. Detailed Guidelines (Markdown format)
2. Suggested Parameters
3. Implementation Notes
4. Critical Considerations
5. Success Criteria"""

            # Make API call with clean context
            api_context = {
                "original_prompt": original_prompt,
                "ai_type": ai_type,
                "style": style,
                "analysis": analysis_result,
                "feedback": feedback_result
            }

            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=guidelines_prompt,
                context=api_context,
                temperature=0.4
            )

            # Process and return response
            processed_response = self._preserve_context("guidelines", response)
            return processed_response

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
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.required_fields = ["prompts"]
        self.logger.info(f"Initializing EnhancementStage with required fields: {self.required_fields}")

    def _create_fallback_enhanced_prompts(self, pipeline_context: ContextTracker) -> Dict:
        """
        Generate fallback enhanced prompts when the primary enhancement process fails.
        
        This method provides a structured set of prompts that maintain the core 
        intent of the original request while offering different perspectives.
        """
        self.logger.info("Generating fallback enhanced prompts")
        
        try:
            original_prompt = pipeline_context.context['original_prompt']
            ai_type = pipeline_context.context['ai_type']
            style = pipeline_context.context['style']
            
            self.logger.debug(f"Fallback context - Original Prompt: {original_prompt}")
            self.logger.debug(f"Fallback context - AI Type: {ai_type}")
            self.logger.debug(f"Fallback context - Style: {style}")

            fallback_response = {
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
            
            self.logger.info("Successfully generated fallback prompts")
            self.logger.debug(f"Fallback response: {json.dumps(fallback_response, indent=2)}")
            
            return fallback_response

        except Exception as e:
            self.logger.error(f"Error generating fallback prompts: {str(e)}", exc_info=True)
            # Return a minimal fallback response in case of error
            return {
                "prompts": [{
                    "prompt": "Please provide more details about your request.",
                    "focus": "Clarification",
                    "perspective": "Basic inquiry"
                }]
            }

    def execute(self, pipeline_context: Dict) -> Dict:
        self.logger.info("Starting EnhancementStage execution")
        self.logger.debug(f"Initial pipeline context: {json.dumps(pipeline_context, indent=2)}")

        try:
            # Extract and log context information
            original_prompt = pipeline_context.get("original_prompt", "")
            ai_type = pipeline_context.get("ai_type", "general")
            style = pipeline_context.get("style", "professional")
            
            self.logger.info(f"Processing enhancement request - AI Type: {ai_type}, Style: {style}")
            self.logger.debug(f"Original prompt: {original_prompt}")

            # Get and log stage results
            stage_results = pipeline_context.get("execution_context", {}).get("stage_results", {})
            analysis_result = stage_results.get("analysis", {})
            feedback_result = stage_results.get("feedback", {})
            guidelines_result = stage_results.get("guidelines", {})

            self.logger.debug("Stage results retrieved:")
            self.logger.debug(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
            self.logger.debug(f"Feedback result: {json.dumps(feedback_result, indent=2)}")
            self.logger.debug(f"Guidelines result: {json.dumps(guidelines_result, indent=2)}")

            # Create and log system message
            system_message = f"""You are a prompt enhancement expert specializing in {ai_type} systems.
                Generate multiple enhanced versions of the original prompt that:
                - Maintain the core intent
                - Provide different perspectives
                - Align with {style} communication style
                - Offer unique insights

                IMPORTANT: Your response must include a 'prompts' array with enhanced prompts.
                Example response format:
                {{
                    "prompts": [
                        {{
                            "prompt": "enhanced version 1",
                            "focus": "area of focus",
                            "perspective": "perspective taken"
                        }},
                        {{
                            "prompt": "enhanced version 2",
                            "focus": "different focus",
                            "perspective": "different perspective"
                        }}
                    ]
                }}"""


            
            self.logger.debug(f"Generated system message: {system_message}")

            # Create and log enhancement prompt
            enhancement_prompt = f"""Generate three distinct, enhanced versions of the original prompt:

Original Request: {original_prompt}
AI Type: {ai_type}
Style: {style}

Previous Analysis:
{json.dumps(analysis_result, indent=2)}

Feedback Insights:
{json.dumps(feedback_result, indent=2)}

Guidelines:
{json.dumps(guidelines_result, indent=2)}"""

            self.logger.debug(f"Generated enhancement prompt: {enhancement_prompt}")

            # Prepare and log API context
            api_context = {
                "original_prompt": original_prompt,
                "ai_type": ai_type,
                "style": style,
                "stage_results": {
                    "analysis": analysis_result,
                    "feedback": feedback_result,
                    "guidelines": guidelines_result
                }
            }
            
            self.logger.debug(f"Prepared API context: {json.dumps(api_context, indent=2)}")

            # Make API call
            self.logger.info("Attempting API call for enhancement")
            response = self.api_handler.make_api_call(
                system_message=system_message,
                prompt=enhancement_prompt,
                context=api_context,
                stage="enhancement",
                temperature=0.7
            )
            self.logger.info("API call completed successfully")
            self.logger.debug(f"API response: {json.dumps(response, indent=2)}")

            # Validate response
            self._validate_response(response)

            # Preserve context and return
            preserved_context = self._preserve_context("enhancement", response)
            self.logger.info("Enhancement stage completed successfully")
            self.logger.debug(f"Final preserved context: {json.dumps(preserved_context, indent=2)}")

            return preserved_context

        except Exception as e:
            self.logger.error(f"Enhancement stage failed with error: {str(e)}", exc_info=True)
            self.logger.error(f"Pipeline context at failure: {json.dumps(pipeline_context, indent=2)}")
            
            # Generate fallback response
            self.logger.info("Attempting to generate fallback response")
            fallback = self._create_fallback_enhanced_prompts(pipeline_context)
            self.logger.info("Fallback response generated successfully")
            
            return fallback

    def _validate_response(self, response: Dict) -> None:
        """Validate the response contains all required fields"""
        self.logger.debug("Validating API response")
        
        if not isinstance(response, dict):
            error_msg = f"Invalid response type: expected dict, got {type(response)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        missing_fields = [field for field in self.required_fields if field not in response]
        
        if missing_fields:
            error_msg = f"Missing required fields in response: {missing_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not isinstance(response.get("prompts"), list):
            error_msg = "Invalid 'prompts' field: expected list"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.debug("Response validation successful")




class EnhancedPromptPipeline:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.api_handler = APIHandler(logger)
        self.response_manager = ResponseManager(logger)
        self.preprocessor = PromptPreprocessor()
        
        # Create context tracker first
        self.context_tracker = ContextTracker()
        
        # Initialize stages with all required arguments
        self.analysis_stage = AnalysisStage(
            logger=logger,
            api_handler=self.api_handler,
            context_tracker=self.context_tracker
        )
        
        self.feedback_stage = FeedbackStage(
            logger=logger,
            api_handler=self.api_handler,
            context_tracker=self.context_tracker
        )
        
        self.guidelines_stage = GuidelinesStage(
            logger=logger,
            api_handler=self.api_handler,
            context_tracker=self.context_tracker
        )
        
        self.enhancement_stage = EnhancementStage(
            logger=logger,
            api_handler=self.api_handler,
            context_tracker=self.context_tracker
        )

    def _enrich_context(self, current_stage_result: Dict, previous_context: Dict) -> Dict:
        """
        Intelligently merge current stage result with previous context.
        
        Args:
            current_stage_result (Dict): Result from the current pipeline stage
            previous_context (Dict): Accumulated context from previous stages
        
        Returns:
            Dict: Enriched context with merged information
        """
        enriched_context = previous_context.copy()
        
        # Define keys to prioritize for context enrichment
        priority_keys = [
            'intent', 'requirements', 'context', 
            'feedback', 'guidelines', 'prompts'
        ]
        
        for key in priority_keys:
            if key in current_stage_result and current_stage_result[key]:
                enriched_context[key] = current_stage_result[key]
        
        # Add metadata about context evolution
        enriched_context['_metadata'] = {
            'last_updated_stage': current_stage_result.get('_stage_metadata', {}).get('stage_name'),
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        return enriched_context
    
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
            # Create unified context object
            context = {
                "request_id": str(uuid.uuid4()),
                "original_prompt": prompt,
                "ai_type": ai_type, 
                "style": style,
                "timestamp": datetime.datetime.now().isoformat(),
                "stage_results": {},
                "context_chain": []
            }

            # Add logging to track pipeline progression
            self.logger.info(f"Starting pipeline execution for request {context['request_id']}")

            # Execute stages with error recovery
            for stage_name, stage in [
                ("preprocessing", lambda: self.preprocessor.analyze_prompt(prompt)),
                ("analysis", lambda: self.analysis_stage.execute(context)),
                ("feedback", lambda: self.feedback_stage.execute(context)),
                ("guidelines", lambda: self.guidelines_stage.execute(context)),
                ("enhancement", lambda: self.enhancement_stage.execute(context))
            ]:
                try:
                    self.logger.info(f"Executing {stage_name} stage")
                    result = stage()
                    context["stage_results"][stage_name] = result
                    self._add_to_context_chain(context, stage_name, result)
                    self.logger.info(f"Completed {stage_name} stage successfully")
                except Exception as e:
                    self.logger.error(f"Error in {stage_name} stage: {str(e)}")
                    fallback = self._create_stage_fallback(stage_name)
                    context["stage_results"][stage_name] = fallback
                    self._add_to_context_chain(context, stage_name, fallback)

            # Format final response
            return self._format_final_response(context)

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            return self._create_error_response(str(e))
        
    def _extract_parameters(self, guidelines: Dict) -> Dict:
        params = guidelines.get("parameters", {})
        return {
            "temperature": float(params.get("temperature", {}).get("value", 0.7)),
            "top_p": float(params.get("top_p", {}).get("value", 0.9)),
            "presence_penalty": float(params.get("presence_penalty", {}).get("value", 0.0)),
            "frequency_penalty": float(params.get("frequency_penalty", {}).get("value", 0.0))
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
        if not isinstance(result, dict):
            return False
            
        required_fields = {
            "analysis": ["intent", "requirements"],
            "feedback": ["feedback", "suggestions"],
            "guidelines": ["guidelines", "parameters"],
            "enhancement": ["prompts"]
        }
        
        if stage_name in required_fields:
            return all(field in result for field in required_fields[stage_name])
            
        return True
        
        

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

    # def format_response(self, pipeline_result: Dict) -> Dict:
    #     """Enhanced response formatting with comprehensive structure"""
    #     try:
    #         # Error handling
    #         if pipeline_result.get('status') in ['fallback', 'error']:
    #             return self._format_error_response(pipeline_result)
            
    #         # Extract preprocessing details with new structure
    #         preprocessing_details = self._extract_preprocessing_details(
    #             pipeline_result.get('initial_analysis', {})
    #         )
            
    #         # Get enhanced prompts with better structure
    #         enhanced_prompts = pipeline_result.get('enhanced_prompts', {})
    #         if isinstance(enhanced_prompts, str):
    #             try:
    #                 enhanced_prompts = json.loads(enhanced_prompts)
    #             except json.JSONDecodeError:
    #                 enhanced_prompts = {"prompts": []}
                    
    #         prompts_list = enhanced_prompts.get('prompts', [])
            
    #         # Format prompts with more detail
    #         formatted_prompts = []
    #         for p in prompts_list:
    #             if isinstance(p, dict):
    #                 formatted_prompts.append({
    #                     "prompt": p.get("prompt", ""),
    #                     "focus": p.get("focus", "general"),
    #                     "perspective": p.get("perspective", "standard"),
    #                     "metadata": {
    #                         "format_version": "2.0",
    #                         "generated_timestamp": datetime.datetime.now().isoformat()
    #                     }
    #                 })
            
    #         return {
    #             "status": "success",
    #             "metadata": {
    #                 "timestamp": datetime.datetime.now().isoformat(),
    #                 "version": "2.0.0",
    #                 "processing_type": "enhanced"
    #             },
    #             "input": {
    #                 "original_prompt": pipeline_result.get('original_prompt', ''),
    #                 "preprocessing": preprocessing_details
    #             },
    #             "analysis": {
    #                 "linguistic": {
    #                     "semantic_analysis": preprocessing_details.get('semantic_analysis', {}),
    #                     "discourse_analysis": preprocessing_details.get('discourse_analysis', {}),
    #                     "complexity_metrics": preprocessing_details.get('complexity_metrics', {})
    #                 },
    #                 "contextual": pipeline_result.get('comparative_feedback', {})
    #             },
    #             "output": {
    #                 "guidelines": pipeline_result.get('guidelines', {}),
    #                 "enhanced_prompts": formatted_prompts
    #             },
    #             "processing_insights": {
    #                 "key_decisions": preprocessing_details.get('key_decisions', []),
    #                 "adaptation_points": preprocessing_details.get('adaptation_points', [])
    #             }
    #         }
    #     except Exception as e:
    #         return self._format_error_response({
    #             "status": "error",
    #             "error": str(e)
    #         })
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
            return {
                "status": "success",
                "request_id": pipeline_context["request_id"],
                "metadata": {
                    "timestamp": pipeline_context["timestamp"],
                    "ai_type": pipeline_context["ai_type"],
                    "style": pipeline_context["style"]
                },
                "stages": pipeline_context["stage_results"],
                "accumulated_context": pipeline_context["accumulated_context"]
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
    response.headers.add('Access-Control-Allow-Origin', request.origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)
import random
import traceback
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
import os
import logging
from typing import Dict, Any, List, Tuple, Union, Optional, Set
from logging import Logger
from llamaapi import LlamaAPI
import re
import uuid
import time
import requests  # Add at the top with other imports
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor


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
        self.max_retries = 3
        self.base_delay = 1
        self._request_id = uuid.uuid4()

    async def make_api_call(self, system_message: str, prompt: str, **params) -> Dict:
        self.logger.info(f"Request {self._request_id}: Starting API call")
        attempt = 0
            
        while attempt < self.max_retries:
            try:
                self.logger.debug(f"Request {self._request_id}: Attempt {attempt + 1}")
                response = llama.run({
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "model": "llama3.2-1b",
                    "max_tokens": 10000,
                    "stream": False,
                     **params
                })
                    
                self.logger.debug(f"Request {self._request_id}: Raw response type: {type(response)}")
                self.logger.debug(f"Request {self._request_id}: Raw response content: {response}")
                    
                # First check if response is valid
                if not response or not isinstance(response, requests.models.Response):
                    raise ValueError(f"Invalid response format: {response}")
                
                
                        
                # Get response content
                try:
                    json_response = response.json()
                    self.logger.debug(f"Request {self._request_id}: Parsed JSON response: {json_response}")
                        
                    if not isinstance(json_response, dict):
                        raise ValueError("Response is not a dictionary")
                            
                    # Extract content from choices if available
                    if 'choices' in json_response and json_response['choices']:
                        content = json_response['choices'][0].get('message', {}).get('content', '')
                        if content:
                            try:
                                parsed_content = json.loads(content)
                                self.logger.info(f"Request {self._request_id}: Successfully parsed response content")
                                return parsed_content
                            except json.JSONDecodeError as e:
                                self.logger.error(f"Request {self._request_id}: JSON parsing failed: {str(e)}")
                                return self._create_fallback_response("Invalid JSON in response content")
                    else:
                        # Handle direct response format
                        return json_response
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Request {self._request_id}: Response JSON parsing failed: {str(e)}")
                    return self._create_fallback_response("Invalid JSON response")
                    
            except Exception as e:
                self.logger.error(f"Request {self._request_id}: Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return self._create_fallback_response(str(e))
                attempt += 1
                await asyncio.sleep(self.base_delay * (2 ** attempt))

    async def _process_raw_response(self, raw_response: str) -> Dict:
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Use await here
            return await self._format_unstructured_response(raw_response)

    async def _format_unstructured_response(self, raw_text: str) -> Dict:
        system_message = """You are a response formatter. Convert the given text into a valid JSON structure.
        Return ONLY valid JSON with this structure:
        {
            "analysis": {
                "selected_technique": "string",
                "reasoning": "string",
                "metrics": {
                    "clarity": "string",
                    "context": "string",
                    "specificity": "string"
                }
            },
            "enhanced_prompts": [
                {"prompt": "string"},
                {"prompt": "string"},
                {"prompt": "string"}
            ],
            "implementation_notes": {
                "platform_specific": ["string"],
                "style_adherence": ["string"],
                "prompt_analysis": ["string"]
            }
        }"""

        format_prompt = f"Format this response into valid JSON:\n{raw_text}"

        try:
            # Use await here
            formatting_response = await self.make_api_call(
                system_message=system_message,
                prompt=format_prompt,
                temperature=0.3
            )
            return json.loads(formatting_response['content'])
        except Exception as e:
            self.logger.error(f"Formatting failed: {str(e)}")
            return self._create_fallback_response(str(e))

    def _verify_response_structure(self, response: Dict) -> bool:
        """Verify the response has the correct structure"""
        try:
            if not isinstance(response, dict):
                return False
                
            if 'content' not in response:
                return False
                
            content = response['content']
            required_fields = ["analysis", "enhanced_prompts", "implementation_notes"]
            
            return all(field in content for field in required_fields)
            
        except Exception:
            return False

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

    async def _process_response(self, response) -> Dict:
        """Process and validate API response"""
        try:
            # Verify response object
            if not hasattr(response, 'json'):
                raise ValueError("Invalid response object")
                
            # Parse response JSON
            response_data = response.json()
            self.logger.debug(f"Raw API Response:\n{json.dumps(response_data, indent=2)}")
            
            # Extract content from response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                
                # Handle different response formats
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                elif 'text' in choice:
                    content = choice['text']
                else:
                    raise ValueError("No content found in response")
                    
                # Parse and validate content structure
                return self._parse_content(content)
                
            raise ValueError("No choices in response")
            
        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            return self._create_fallback_response(str(e))
        
    def _create_fallback_response(self, error: str) -> Dict:
        """Create a structured fallback response"""
        return {
            "content": {
                "analysis": {
                    "status": "fallback",
                    "error": error
                },
                "enhanced_prompts": [
                    {"prompt": "Fallback prompt 1"},
                    {"prompt": "Fallback prompt 2"},
                    {"prompt": "Fallback prompt 3"}
                ],
                "implementation_notes": {
                    "note": "Fallback response due to API error"
                }
            },
            "_metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "response_type": "fallback"
            }
        }
        
    def _parse_content(self, content: str) -> Dict:
        """Parse and validate content structure"""
        try:
            # Clean content
            cleaned_content = self._clean_json_content(content)
            
            # Parse JSON
            parsed_content = json.loads(cleaned_content)
            
            # Validate required fields
            required_fields = ["analysis", "enhanced_prompts", "implementation_notes"]
            if not all(field in parsed_content for field in required_fields):
                raise ValueError(f"Missing required fields in response: {required_fields}")
                
            return {
                "content": parsed_content,
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "response_type": "structured"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Content parsing failed: {str(e)}")
            raise

    def _clean_json_content(self, content: str) -> str:
        """Clean and extract JSON from content"""
        try:
            # Remove any markdown formatting
            content = re.sub(r'```json\s*|\s*```', '', content.strip())
            
            # Find JSON boundaries
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                potential_json = content[start:end]
                # Verify it's valid JSON
                json.loads(potential_json)  # This will raise JSONDecodeError if invalid
                return potential_json
                
            raise ValueError("No valid JSON found in content")
            
        except Exception as e:
            self.logger.error(f"JSON cleaning failed: {str(e)}")
            raise
        
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
        
    def _format_request(self, system_message: str, prompt: str, params: Dict) -> Dict:
        """Format API request with consistent structure"""
        # Define default parameters
        default_params = {
            "temperature": 0.3,
            "max_tokens": 2000,
            "stream": False,
            "model": "llama3.2-1b"
        }
        
        # Merge with provided parameters
        request_params = {**default_params, **params}
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            **request_params
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
    def validate_response(response: Dict) -> Tuple[bool, Dict]:
        logger = logging.getLogger(__name__)
        request_id = uuid.uuid4()
        
        try:
            logger.debug(f"Validation {request_id}: Starting response validation")
            logger.debug(f"Validation {request_id}: Raw response: {json.dumps(response)}")
            
            if not isinstance(response, dict):
                raise ValueError("Response is not a dictionary")
                
            if 'choices' not in response:
                raise ValueError("Missing 'choices' in response")
                
            if not response['choices']:
                raise ValueError("Empty choices array")
                
            message = response['choices'][0].get('message', {})
            content = message.get('content', '')
            
            if not content:
                raise ValueError("No content in response")
                
            logger.info(f"Validation {request_id}: Response passed validation")
            return True, json.loads(content)
            
        except Exception as e:
            logger.error(f"Validation {request_id}: Failed - {str(e)}")
            return False, {
                "error": str(e),
                "request_id": request_id,
                "timestamp": datetime.datetime.now().isoformat()
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





    




class PipelineStage:
    """Base class for pipeline stages with common functionality"""
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        self.logger = logger
        self.api_handler = api_handler
        self.context_tracker = context_tracker

    async def _resolve_pipeline_context(self, context: Dict) -> Dict:
        """Recursively resolve any coroutines in the pipeline context"""
        resolved_context = {}
        for key, value in context.items():
            if asyncio.iscoroutine(value):
                resolved_context[key] = await value
            elif isinstance(value, dict):
                resolved_context[key] = await self._resolve_pipeline_context(value)
            elif isinstance(value, list):
                resolved_context[key] = [
                    await self._resolve_pipeline_context(item) if isinstance(item, dict)
                    else await value if asyncio.iscoroutine(value)
                    else item
                    for item in value
                ]
            else:
                resolved_context[key] = value
        return resolved_context

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

class FallbackGenerator:
    def __init__(self, logger: Logger):
        self.logger = logger
        # Style-specific templates for different prompt aspects
        self.style_templates = {
            "professional": {
                "prefix": ["Develop a comprehensive", "Create a detailed", "Design a structured"],
                "connector": ["approach for", "solution for", "implementation of"],
                "suffix": ["ensuring professional standards", "maintaining industry best practices", "following established guidelines"]
            },
            "creative": {
                "prefix": ["Imagine an innovative", "Design a unique", "Create an engaging"],
                "connector": ["version of", "interpretation of", "approach to"],
                "suffix": ["with creative elements", "incorporating novel ideas", "with imaginative aspects"]
            },
            "technical": {
                "prefix": ["Implement a robust", "Develop a technical", "Engineer a systematic"],
                "connector": ["solution for", "architecture for", "framework for"],
                "suffix": ["following technical specifications", "using best practices", "with optimal performance"]
            },
            "descriptive": {
                "prefix": ["Provide a detailed", "Create a comprehensive", "Develop an in-depth"],
                "connector": ["description of", "explanation of", "breakdown of"],
                "suffix": ["with thorough details", "covering all aspects", "with complete information"]
            }
        }

        # AI-specific enhancement patterns
        self.ai_patterns = {
            "ChatGPT": {
                "focus_areas": ["conversational flow", "natural language", "interactive elements"],
                "special_features": ["context awareness", "dialogue structure", "user engagement"]
            },
            "Claude": {
                "focus_areas": ["detailed analysis", "logical structure", "comprehensive coverage"],
                "special_features": ["step-by-step breakdown", "thorough explanations", "academic style"]
            },
            "Gemini": {
                "focus_areas": ["multimodal integration", "creative synthesis", "innovative approaches"],
                "special_features": ["visual considerations", "cross-domain connections", "integrated solutions"]
            },
            "Midjourney": {
                "focus_areas": ["visual elements", "creative direction", "artistic composition"],
                "special_features": ["aesthetic considerations", "style guidelines", "visual hierarchy"]
            }
        }

    def generate_enhanced_prompts(self, original_prompt: str, ai_type: str, style: str) -> List[Dict]:
        """Generate enhanced prompt variations using fallback patterns"""
        try:
            self.logger.info(f"Generating fallback prompts for {ai_type} with {style} style")
            
            # Get style templates, defaulting to professional if style not found
            style_temps = self.style_templates.get(style.lower(), self.style_templates["professional"])
            ai_patterns = self.ai_patterns.get(ai_type, self.ai_patterns["ChatGPT"])
            
            # Extract key terms from original prompt
            key_terms = self._extract_key_terms(original_prompt)
            
            # Generate variations using different patterns
            variations = []
            
            # First variation: Focus on structure and organization
            variations.append({
                "prompt": self._create_structured_prompt(
                    original_prompt, style_temps, ai_patterns, 
                    focus="structure and organization"
                )
            })
            
            # Second variation: Focus on implementation details
            variations.append({
                "prompt": self._create_implementation_prompt(
                    original_prompt, style_temps, ai_patterns,
                    key_terms=key_terms
                )
            })
            
            # Third variation: Focus on optimization and special features
            variations.append({
                "prompt": self._create_optimized_prompt(
                    original_prompt, style_temps, ai_patterns,
                    special_features=ai_patterns["special_features"]
                )
            })
            
            return variations
            
        except Exception as e:
            self.logger.error(f"Fallback generation failed: {str(e)}")
            return self._create_emergency_fallback(original_prompt, style)

    def _extract_key_terms(self, prompt: str) -> List[str]:
        """Extract important terms from the prompt"""
        # Remove common stop words and punctuation
        stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with'])
        words = prompt.lower().split()
        key_terms = [word.strip('.,!?()[]{}') for word in words if word not in stop_words]
        return list(set(key_terms))  # Remove duplicates

    def _create_structured_prompt(self, original_prompt: str, style_temps: Dict, 
                                ai_patterns: Dict, focus: str) -> str:
        """Create a structure-focused prompt variation"""
        prefix = random.choice(style_temps["prefix"])
        connector = random.choice(style_temps["connector"])
        focus_area = random.choice(ai_patterns["focus_areas"])
        
        return f"{prefix} {connector} {original_prompt}, focusing on {focus_area} and {focus}"

    def _create_implementation_prompt(self, original_prompt: str, style_temps: Dict,
                                    ai_patterns: Dict, key_terms: List[str]) -> str:
        """Create an implementation-focused prompt variation"""
        prefix = random.choice(style_temps["prefix"])
        key_focus = random.choice(ai_patterns["focus_areas"])
        relevant_terms = ', '.join(key_terms[:3])  # Use up to 3 key terms
        
        return f"{prefix} implementation of {original_prompt}, emphasizing {key_focus} and incorporating {relevant_terms}"

    def _create_optimized_prompt(self, original_prompt: str, style_temps: Dict,
                                ai_patterns: Dict, special_features: List[str]) -> str:
        """Create an optimization-focused prompt variation"""
        prefix = random.choice(style_temps["prefix"])
        feature = random.choice(special_features)
        suffix = random.choice(style_temps["suffix"])
        
        return f"{prefix} solution for {original_prompt}, optimized for {feature}, {suffix}"

    def _create_emergency_fallback(self, prompt: str, style: str) -> List[Dict]:
        """Create very basic fallback prompts when main generation fails"""
        return [
            {
                "prompt": f"Create a {style} version of: {prompt}",
            },
            {
                "prompt": f"Develop a detailed {style} approach to: {prompt}"
            },
            {
                "prompt": f"Design a structured {style} solution for: {prompt}"
            }
        ]



class AnalysisStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        # self.preprocessor = EnhancedPromptPreprocessor(logger)
        self.fallback_generator = FallbackGenerator(logger)

    def _get_ai_format_requirements(self, ai_type: str) -> str:
        requirements = {
        "Midjourney": """
- Image parameters: --ar (aspect ratio), --q (quality), --s (style), --c (chaos)
- Must include clear style descriptions
- Should specify composition details""",
        
        "Claude": """
- Code must be in ```language blocks
- Use proper markdown formatting where needed
- Can utilize XML tags for structure""",
        
        "Gamma": """
- Should include clear structural indicators
- Can specify layout requirements
- Supports presentation formatting""",
        
        "Gemini": """
- Supports combined text and visual descriptions
- Can handle structured data formats
- Accepts mathematical notation""",
        
        "ChatGPT": """
- Can define clear system roles
- Supports function calling formats
- Handles conversation context"""
    }
        return requirements.get(ai_type, "")

    def _validate_pipeline_context(self, pipeline_context: Dict) -> Tuple[str, str, str]:
        """
        Validate and extract required parameters from pipeline context.
        Returns tuple of (prompt, ai_type, style) or raises ValueError if missing required fields.
        """
        if not isinstance(pipeline_context, dict):
            raise ValueError(f"Expected dict for pipeline_context, got {type(pipeline_context)}")

        prompt = pipeline_context.get("original_prompt")
        ai_type = pipeline_context.get("ai_type")
        style = pipeline_context.get("style")

        if not prompt:
            raise ValueError("Missing required field: original_prompt")
        
        # Provide defaults for optional parameters
        ai_type = ai_type or "general"
        style = style or "standard"

        return prompt, ai_type, style

    async def execute(self, pipeline_context: Dict) -> Dict:
        try:
            self.logger.info("Starting analysis stage")
            prompt = pipeline_context.get("original_prompt")
            ai_type = pipeline_context.get("ai_type")
            style = pipeline_context.get("style")
            self.logger.debug(pipeline_context)

            self.context_tracker.add_context("analysis", {
            "original_prompt": prompt,
            "ai_type": ai_type,
            "style": style
        })
            self.logger.info('here')
            # Create analysis-focused system message with enhancement capabilities
            system_message = f"""You are an expert in prompt engineering and analysis.
Your task is to first analyse the user's request done towards getting the most efficient response from {ai_type}'s LLM.
You have to understand what does the user's prompt lack in terms of getting the most efficient response from {ai_type}. You have to then use this understanding to enhance the user's input
into a well formatted {style} prompt that will lead the user to getting the best possible response.

You have THREE key responsibilities:
1. Analyze the core request and determine the most effective prompt engineering technique
2. Generate detailed analysis of requirements and context
3. Create THREE enhanced versions of the original prompt

CRITICAL: Return ONLY a JSON response with both your analysis and enhanced prompts.
DO NOT include any explanations or additional text outside the JSON structure.
Return in this EXACT format:

{{
    "analysis": {{
        "selected_technique": "technique_name",
        "reasoning": "brief explanation of selection",
        "request_characteristics": ["characteristic1", "characteristic2"],
        "requirements": {{
            "primary_factors": ["factor1", "factor2"],
            "constraints": ["constraint1", "constraint2"]
        }}
    }},
    "enhanced_prompts": [
        {{
            "prompt": "first enhanced version"
        }},
        {{
            "prompt": "second enhanced version"
        }},
        {{
            "prompt": "third enhanced version",
        }}
    ],
    "implementation_notes": {{
        "ai_specific_considerations": ["consideration1", "consideration2"],
        "style_guidelines": ["guideline1", "guideline2"],
        "user's prompt analysis" : ["analysis of what the user's prompt lacked and how it was made better"]
    }}
}}
Key Requirements:
1. DO NOT answer the user's request
2. Only transform the request into better prompts
3. Ensure each prompt follows {ai_type} best practices
4. Maintain {style} communication style
5. Apply selected prompt engineering technique consistently
"""

            analysis_prompt = f"""Analyze this request and generate enhanced prompts:

Request: "{prompt}"
AI Type: {ai_type}
Style: {style}

Follow these steps:
1. Analyze the request using prompt engineering best practices
2. Select the most appropriate technique (Chain-of-Thought, Tree of Thoughts, Auto-CoT, etc.)
3. Generate three distinct enhanced {style} versions of the prompt that will lead {ai_type}'s LLM to generate the most efficient response in manner.

Return in this EXACT format:
{{
    "analysis": {{
        "selected_technique": "technique_name",
        "reasoning": "brief explanation of selection",
        "request_characteristics": ["characteristic1", "characteristic2"],
        "requirements": {{
            "primary_factors": ["factor1", "factor2"],
            "constraints": ["constraint1", "constraint2"]
        }}
    }},
    "enhanced_prompts": [
        {{
            "prompt": "first enhanced version"
        }},
        {{
            "prompt": "second enhanced version"
        }},
        {{
            "prompt": "third enhanced version",
        }}
    ],
    "implementation_notes": {{
        "ai_specific_considerations": ["consideration1", "consideration2"],
        "style_guidelines": ["guideline1", "guideline2"],
        "user's prompt analysis" : ["analysis of what the user's prompt lacked and how it was made better"]
    }}
}}"""
            self.logger.info('now here')
            response = await self.api_handler.make_api_call(
            system_message=system_message,
            prompt=analysis_prompt
        )
            self.logger.debug(response)

            if not response:
                raise ValueError("Empty response received")

            if isinstance(response, str):
                parsed_content = json.loads(response)

            elif isinstance(response, dict):
                # If response is already a dictionary, use it directly
                parsed_content = response

            elif hasattr(response, 'json'):
                response_data = response.json()
                if not response_data.get('choices'):
                    raise ValueError("No choices in response")
                
                message = response_data['choices'][0].get('message', {})
                content = message.get('content', '')
                
                if not content:
                    raise ValueError("Empty content in response")
                
                parsed_content = json.loads(content)
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")

            # Validate required fields
            required_fields = ["analysis", "enhanced_prompts", "implementation_notes"]
            if not all(field in parsed_content for field in required_fields):
                raise ValueError("Missing required fields in response")

            return self._format_analysis_response(parsed_content)

        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}")
            return self._create_fallback_analysis(pipeline_context)

        

            # Process and validate response
        #     try:
        #         content = response.get("content", "")
        #         self.logger.debug(f"Raw API Response: {content}")
                
        #         cleaned_content = self._clean_json_content(content)
        #         parsed_response = json.loads(cleaned_content)
                
        #         # Validate required sections
        #         if not all(k in parsed_response for k in ["analysis", "enhanced_prompts", "implementation_notes"]):
        #             raise ValueError("Missing required sections in response")

        #         return {
        #             "analysis_results": {
        #                 "technique": parsed_response["analysis"],
        #                 "original_prompt": prompt,
        #                 "ai_type": ai_type,
        #                 "style": style
        #             },
        #             "enhanced_prompts": parsed_response["enhanced_prompts"],
        #             "implementation_notes": parsed_response["implementation_notes"],
        #             "_metadata": {
        #                 "timestamp": datetime.datetime.now().isoformat(),
        #                 "stage": "analysis"
        #             }
        #         }

        #     except Exception as e:
        #         self.logger.error(f"Response processing failed: {str(e)}")
        #         return self._create_fallback_analysis(pipeline_context)

        # except Exception as e:
        #     self.logger.error(f"Analysis stage failed: {str(e)}", exc_info=True)
        #     return self._create_fallback_analysis(pipeline_context)

    def _format_analysis_response(self, content: Dict) -> Dict:
        """Format the analysis response into the expected structure"""
        try:
            # Validate content structure
            if not isinstance(content, dict):
                raise ValueError("Invalid content structure")

            # Extract required components
            analysis = content.get("analysis", {})
            enhanced_prompts = content.get("enhanced_prompts", [])
            implementation_notes = content.get("implementation_notes", {})

            # Format the response with consistent structure
            return {
                "analysis_results": {
                    "technique": analysis,
                    "original_prompt": self.context_tracker.get_latest_context().get("original_prompt", ""),
                    "ai_type": self.context_tracker.get_latest_context().get("ai_type", ""),
                    "style": self.context_tracker.get_latest_context().get("style", "")
                },
                "enhanced_prompts": enhanced_prompts,
                "implementation_notes": implementation_notes,
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "analysis"
                }
            }

        except Exception as e:
            self.logger.error(f"Response formatting failed: {str(e)}")
            return self._create_fallback_analysis({
                "original_prompt": self.context_tracker.get_latest_context().get("original_prompt", ""),
                "ai_type": self.context_tracker.get_latest_context().get("ai_type", ""),
                "style": self.context_tracker.get_latest_context().get("style", "")
            })

    def _process_technique_selection(self, content: str) -> Dict:
        """Process and validate technique selection from API response"""
        try:
            cleaned_content = self._clean_json_content(content)
            parsed = json.loads(cleaned_content)
            
            # Validate required fields
            if "selected_technique" not in parsed:
                raise ValueError("Missing technique selection")
                
            valid_techniques = {"Chain-of-Thought", "Tree of Thoughts", "Auto-CoT", "Few-shot", "Zero-shot"}
            
            if parsed["selected_technique"] not in valid_techniques:
                raise ValueError("Invalid technique selected")
            
            # Extract requirements from technique_requirements structure
            requirements = []
            if "technique_requirements" in parsed:
                tech_reqs = parsed["technique_requirements"]
                
                # Add primary factors to requirements
                if "primary_factors" in tech_reqs:
                    requirements.extend(tech_reqs["primary_factors"])
                    
                # Add constraints to requirements
                if "constraints" in tech_reqs:
                    requirements.extend(tech_reqs["constraints"])
                
            # Extract request characteristics
            characteristics = parsed.get("request_characteristics", [])
                    
            return {
                "name": parsed["selected_technique"],
                "reasoning": parsed.get("reasoning", ""),
                "request_type": parsed.get("request_type", "general"),
                "requirements": requirements,  # Now populated from technique_requirements
                "characteristics": characteristics  # Added for additional context
            }
        except Exception as e:
            self.logger.error(f"Technique selection processing failed: {str(e)}")
            return {
                "name": "Zero-shot",
                "reasoning": "Fallback selection due to processing error",
                "request_type": "general",
                "requirements": ["clear instructions", "direct execution"],
                "characteristics": ["basic task"]
            }

    def _extract_technique_info(self, analysis_response: Dict) -> Dict:
        """Extract and validate selected prompt engineering technique"""
        try:
            if not isinstance(analysis_response, dict):
                raise ValueError("Invalid analysis response format")

            technique = analysis_response.get("selected_technique")
            if not technique:
                raise ValueError("No technique selected in analysis")

            # Validate selected technique
            valid_techniques = {
                "Chain-of-Thought", "Tree of Thoughts", 
                "Auto-CoT", "Few-shot", "Zero-shot"
            }
            
            if technique not in valid_techniques:
                self.logger.warning(f"Invalid technique selected: {technique}")
                technique = self._get_fallback_technique()

            return {
                "name": technique,
                "reasoning": analysis_response.get("reasoning", ""),
                "requirements": analysis_response.get("technique_requirements", {}),
                "characteristics": analysis_response.get("request_characteristics", [])
            }
        except Exception as e:
            self.logger.error(f"Error extracting technique info: {str(e)}")
            return self._get_fallback_technique()

    def _get_fallback_technique(self) -> Dict:
        """Provide fallback technique when selection fails"""
        return {
            "name": "Chain-of-Thought",
            "reasoning": "Fallback to CoT for structured approach",
            "requirements": {
                "primary_factors": ["step-by-step breakdown"],
                "constraints": ["clear reasoning chain"]
            },
            "characteristics": ["requires structured thinking"]
        }

    def _process_analysis_response(self, content: str, pipeline_context: Dict) -> Dict:
        """Process and validate analysis response"""
        try:
            if not content:
                raise ValueError("Empty response content")

            # Clean JSON content
            cleaned_content = self._clean_json_content(content)
            parsed_content = json.loads(cleaned_content)

            # Determine appropriate prompt engineering technique based on analysis
            request_type = self._analyze_request_type(
                parsed_content, 
                pipeline_context.get("original_prompt", "")
            )
            
            technique = self._determine_technique(request_type)

            # Create structured response
            return {
                "selected_technique": technique["name"],
                "reasoning": technique["reasoning"],
                "request_characteristics": request_type["characteristics"],
                "technique_requirements": technique["requirements"]
            }

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            return self._create_fallback_technique_selection(pipeline_context)

    def _analyze_request_type(self, content: Dict, original_prompt: str) -> Dict:
        """Analyze request type from content and original prompt"""
        characteristics = []
        
        # Check for task indicators in the prompt
        prompt_lower = original_prompt.lower()
        
        # Task type analysis
        if any(word in prompt_lower for word in ['help', 'how to', 'guide', 'explain']):
            characteristics.append("instructional")
        if any(word in prompt_lower for word in ['create', 'make', 'write', 'design']):
            characteristics.append("creative")
        if any(word in prompt_lower for word in ['analyze', 'compare', 'evaluate']):
            characteristics.append("analytical")
        if any(word in prompt_lower for word in ['solve', 'calculate', 'compute']):
            characteristics.append("problem-solving")
        
        # Complexity analysis
        if len(original_prompt.split()) > 20:
            characteristics.append("complex")
        else:
            characteristics.append("straightforward")
            
        return {
            "characteristics": characteristics,
            "complexity": "complex" if "complex" in characteristics else "straightforward"
        }

    def _determine_technique(self, request_type: Dict) -> Dict:
        """Select appropriate prompt engineering technique based on request type"""
        characteristics = request_type["characteristics"]
        
        # Technique selection logic
        if "problem-solving" in characteristics or "analytical" in characteristics:
            return {
                "name": "Chain-of-Thought",
                "reasoning": "Task requires structured analytical thinking and step-by-step problem solving",
                "requirements": {
                    "primary_factors": ["sequential reasoning", "explicit steps"],
                    "constraints": ["logical progression", "clear explanations"]
                }
            }
        elif "creative" in characteristics:
            return {
                "name": "Tree of Thoughts",
                "reasoning": "Task involves creative elements with multiple possible approaches",
                "requirements": {
                    "primary_factors": ["divergent thinking", "multiple perspectives"],
                    "constraints": ["coherent flow", "creative freedom"]
                }
            }
        elif "instructional" in characteristics:
            return {
                "name": "Auto-CoT",
                "reasoning": "Task requires clear guidance and structured explanation",
                "requirements": {
                    "primary_factors": ["clear instructions", "step-by-step guidance"],
                    "constraints": ["user-friendly", "comprehensive"]
                }
            }
        else:
            return {
                "name": "Zero-shot",
                "reasoning": "Straightforward task with clear objectives",
                "requirements": {
                    "primary_factors": ["direct approach", "clear instructions"],
                    "constraints": ["concise", "specific"]
                }
            }

    def _create_fallback_technique_selection(self, pipeline_context: Dict) -> Dict:
        """Create fallback technique selection"""
        return {
            "selected_technique": "Zero-shot",
            "reasoning": "Fallback to basic approach for reliable execution",
            "request_characteristics": ["straightforward", "basic"],
            "technique_requirements": {
                "primary_factors": ["clear instructions", "direct approach"],
                "constraints": ["simple execution", "reliable output"]
            }
        }

    def _clean_json_content(self, content: str) -> str:
        """Clean and extract JSON from response content"""
        try:
            # Remove any markdown formatting
            content = re.sub(r'```json\s*|\s*```', '', content)
            
            # Find JSON boundaries
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                return content[start:end]
                
            raise ValueError("No valid JSON found in content")
            
        except Exception as e:
            self.logger.error(f"JSON cleaning failed: {str(e)}")
            raise

    # async def _execute_preprocessing(self, prompt: str) -> Dict:
    #     """Execute preprocessing with proper error handling"""
    #     try:
    #         return await asyncio.get_event_loop().run_in_executor(
    #             None,
    #             self.preprocessor.analyze_prompt,
    #             prompt
    #         )
    #     except Exception as e:
    #         self.logger.error(f"Preprocessing failed: {str(e)}")
    #         return self.preprocessor._create_fallback_preprocessing(prompt)

    def _create_analysis_system_message(self, preprocessing: Dict, ai_type: str, style: str) -> str:
        """Create dynamic system message based on preprocessing results"""
        complexity = preprocessing.get("complexity_score", 50)
        entities = preprocessing.get("named_entities", [])
        domain_context = preprocessing.get("domain_analysis", {})

        return f"""You are an expert prompt analysis specialist for {ai_type} systems.
Your task is to perform comprehensive analysis of the user's request using Chain-of-Thought reasoning.

Context Information:
- Complexity Level: {'High' if complexity > 70 else 'Medium' if complexity > 40 else 'Low'}
- Domain Context: {domain_context.get('primary_domain', 'General')}
- Style Requirements: {style}

You must:
1. Break down the request into clear logical steps
2. Identify core requirements and constraints
3. Consider {ai_type}-specific capabilities and limitations
4. Maintain {style} communication style
5. Extract domain-specific terminology and context

Return ONLY valid JSON with the following structure:
{{
    "chain_of_thought": {{
        "steps": ["step1", "step2", ...],
        "reasoning": "explanation of analysis process"
    }},
    "analysis_results": {{
        "core_intent": "main objective",
        "requirements": ["req1", "req2", ...],
        "constraints": ["constraint1", "constraint2", ...],
        "domain_context": {{
            "terminology": ["term1", "term2", ...],
            "expertise_level": "level"
        }}
    }},
    "implementation_considerations": {{
        "critical_factors": ["factor1", "factor2", ...],
        "potential_challenges": ["challenge1", "challenge2", ...]
    }}
}}"""

    def _create_chain_of_thought_prompt(self, prompt: str, preprocessing: Dict, ai_type: str, style: str) -> str:
        """Generate analysis prompt using Chain-of-Thought approach"""
        return f"""Analyze this request using step-by-step reasoning:

Original Request: "{prompt}"
AI System: {ai_type}
Style: {style}

Consider these preprocessing insights:
- Complexity Score: {preprocessing.get('complexity_score', 'N/A')}
- Key Entities: {', '.join(str(e) for e in preprocessing.get('named_entities', [])[:3])}
- Domain: {preprocessing.get('domain_analysis', {}).get('primary_domain', 'General')}

Let's think through this systematically:
1. First, understand the core request
2. Then, identify key requirements
3. Next, consider {ai_type} capabilities
4. Finally, align with {style} style

Provide your analysis following the exact JSON structure specified.
Focus on actionable insights that will inform prompt enhancement."""


    def _create_fallback_analysis(self, pipeline_context: Dict) -> Dict:
        """Enhanced fallback with reliable prompt generation"""
        prompt = pipeline_context.get("original_prompt", "")
        ai_type = pipeline_context.get("ai_type", "general")
        style = pipeline_context.get("style", "professional")

        # Generate enhanced prompts using fallback generator
        enhanced_prompts = self.fallback_generator.generate_enhanced_prompts(
            prompt, ai_type, style
        )

        return {
            "analysis_results": {
                "technique": {
                    "selected_technique": "Chain-of-Thought",
                    "reasoning": "Fallback to structured approach due to analysis failure",
                    "request_characteristics": ["requires structured approach", "needs clear steps"],
                    "requirements": {
                        "primary_factors": ["clear communication", "systematic approach"],
                        "constraints": [f"maintain {style} tone", "ensure clarity"]
                    }
                },
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style
            },
            "enhanced_prompts": enhanced_prompts,
            "implementation_notes": {
                "ai_specific_considerations": [
                    f"Optimized for {ai_type}",
                    "Maintains consistent structure"
                ],
                "style_guidelines": [
                    f"Adheres to {style} communication style",
                    "Ensures appropriate tone and format"
                ]
            },
            "_metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "stage": "analysis",
                "status": "fallback"
            }
        }





   



class EnhancedPromptPipeline:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.logger.info("Initializing Enhanced Prompt Pipeline...")
        self.api_handler = APIHandler(logger)
        # self.preprocessor = EnhancedPromptPreprocessor(logger)  # Use new preprocessor
        self.context_tracker = ContextTracker()
        self.analysis_stage = AnalysisStage(logger, self.api_handler, self.context_tracker)


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


    def _extract_command_patterns(self, doc) -> Dict:
        """Extract actionable command patterns"""
        # Find main verb and its modifiers
        main_verb = None
        modifiers = []
        constraints = []
        
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                main_verb = {
                    "verb": token.text,
                    "lemma": token.lemma_,
                    "objects": [child.text for child in token.children 
                              if child.dep_ in ("dobj", "pobj")]
                }
            elif token.dep_ in ("advmod", "amod"):
                modifiers.append({
                    "modifier": token.text,
                    "target": token.head.text,
                    "type": token.dep_
                })
            elif token.dep_ == "prep" and token.text.lower() in ("with", "without", "using"):
                constraints.append({
                    "type": "tool_constraint",
                    "constraint": " ".join([token.text] + 
                                        [child.text for child in token.children])
                })
                
        return {
            "primary": main_verb,
            "modifiers": modifiers,
            "constraints": constraints
        }
    def _create_fallback_preprocessing(self, prompt: str) -> Dict:
        """
        Create a fallback preprocessing result when the primary preprocessing fails.
        
        Args:
            prompt (str): The original user prompt
        
        Returns:
            Dict: A standardized preprocessing fallback result
        """
        return {
            "status": "fallback",
            "linguistic_features": {
                "raw_text": prompt,
                "length": len(prompt),
                "word_count": len(prompt.split()),
                "character_count": len(prompt)
            },
            "basic_analysis": {
                "detected_language": "Unknown",
                "complexity_score": 50.0,
                "processing_mode": "fallback"
            }
        }
   

    async def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict:
        try:
            base_context = {
                "request_id": str(uuid.uuid4()),
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style,
                "timestamp": datetime.datetime.now().isoformat(),
                "stage_results": {},
                "context_chain": []
            }

            # Execute only preprocessing and analysis stages
            # preprocessing_result = await self._execute_preprocessing(prompt)
            # base_context["stage_results"]["preprocessing"] = preprocessing_result

            analysis_result = await self._execute_analysis(prompt, ai_type, style)
            base_context["stage_results"]["analysis"] = analysis_result

            return self._format_final_response(base_context)

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            self.logger.exception("Full traceback:")
            return self._create_error_response(str(e))

    async def _resolve_result(self, result: Any) -> Any:
        """Helper method to resolve coroutines in results"""
        if asyncio.iscoroutine(result):
            return await result
        elif isinstance(result, dict):
            return {k: await self._resolve_result(v) for k, v in result.items()}
        elif isinstance(result, list):
            return [await self._resolve_result(item) for item in result]
        return result


    def _log_stage_result(self, stage_name: str, result: Any):
        """Enhanced stage result logging"""
        if isinstance(result, Exception):
            self.logger.error(f"{stage_name} stage failed: {str(result)}")
            self.logger.debug(f"{stage_name} full error: {traceback.format_exc()}")
        else:
            self.logger.info(f"{stage_name} stage completed successfully")
            self.logger.debug(f"{stage_name} result: {json.dumps(result, indent=2)}")


    def _format_final_response(self, context: Dict) -> Dict:
        """Format the final pipeline response focusing on analysis results"""
        try:
            analysis_results = context["stage_results"]["analysis"]
            
            return {
                "status": "success",
                "request_id": context["request_id"],
                "metadata": {
                    "timestamp": context["timestamp"],
                    "ai_type": context["ai_type"],
                    "style": context["style"]
                },
                "analysis": analysis_results.get("analysis_results", {}),
                "enhanced_prompts": analysis_results.get("enhanced_prompts", []),
                "implementation_notes": analysis_results.get("implementation_notes", {})
            }
        except Exception as e:
            self.logger.error(f"Error formatting final response: {str(e)}")
            return self._create_error_response(str(e))

    async def _execute_analysis(self, prompt: str, ai_type: str, style: str) -> Dict:
        try:
            self.logger.info(f"Starting analysis for prompt: '{prompt[:50]}...'")
            
            # Get preprocessing results from context
            # preprocessing_result = await self._execute_preprocessing(prompt)
            
            analysis_context = {
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style
            }
            
            result = await self.analysis_stage.execute(analysis_context)
            
            self.logger.info("Analysis stage completed")
            self.logger.debug(f"Analysis result: {json.dumps(result, indent=2)}")
            
            return result
        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}")
            self.logger.debug(f"Analysis error details: {traceback.format_exc()}")
            return self._create_fallback_analysis(prompt, ai_type, style)


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

 

  

    



@app.route('/process', methods=['POST'])
async def process_request():
    try:
        logger.info("Received new process request")
        
        # Parse request data
        if request.is_json:
            data = request.get_json()
        elif request.content_type == 'application/x-www-form-urlencoded':
            try:
                form_data = request.form.get('data')
                if not form_data:
                    logger.error("No data provided in form")
                    return jsonify({
                        "status": "error",
                        "error": "No data provided in form",
                        "timestamp": datetime.datetime.now().isoformat()
                    }), 400
                data = json.loads(form_data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in form data: {str(e)}")
                return jsonify({
                    "status": "error",
                    "error": "Invalid JSON in form data",
                    "timestamp": datetime.datetime.now().isoformat()
                }), 400
        else:
            logger.error(f"Unsupported Content-Type: {request.content_type}")
            return jsonify({
                "status": "error",
                "error": f"Unsupported Content-Type: {request.content_type}",
                "timestamp": datetime.datetime.now().isoformat()
            }), 415

        if not data or 'prompt' not in data:
            logger.error("Missing prompt in request data")
            return jsonify({
                "status": "error",
                "error": "Missing prompt in request data",
                "timestamp": datetime.datetime.now().isoformat()
            }), 400

        # Execute pipeline
        pipeline = EnhancedPromptPipeline(logger)
        response = await pipeline.execute_pipeline(
            prompt=data['prompt'],
            ai_type=data.get('AIType', 'descriptive'),
            style=data.get('style', 'professional')
        )

        logger.info("Request processed successfully")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}")
        logger.exception("Full traceback:")
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
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
from typing import Dict, Any
from logging import Logger
from llamaapi import LlamaAPI
import re
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
class ResponseHandler:
    def __init__(self, logger):
        self.logger = logger
    def get_parameter_values(self, parameters: Dict) -> Dict:
        """Extract just the parameter values for easy access."""
        try:
            if not parameters or 'value' not in parameters:
                return self.get_default_parameter_values()
                
            param_dict = parameters['value']
            return {
                'temperature': param_dict['temperature']['value'],
                'top_p': param_dict['top_p']['value'],
                'presence_penalty': param_dict['presence_penalty']['value'],
                'frequency_penalty': param_dict['frequency_penalty']['value']
            }
        except Exception as e:
            self.logger.error(f"Error extracting parameter values: {str(e)}")
            return self.get_default_parameter_values()
    
    def get_default_parameter_values(self) -> Dict:
        """Get default parameter values."""
        return {
            'temperature': 0.5,
            'top_p': 0.8,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        }
    def clean_json_string(self, content: str) -> str:
        """Clean and fix JSON string from Llama API."""
        try:
            if not isinstance(content, str):
                content = json.dumps(content)
            
            # Remove any trailing commas before closing braces
            content = re.sub(r',(\s*})', r'\1', content)
            # Add missing commas between objects
            content = re.sub(r'}(\s*){', r'},\1{', content)
            # Remove multiple closing braces
            content = re.sub(r'}}+', r'}', content)
            # Ensure proper object closure
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces > close_braces:
                content += '}' * (open_braces - close_braces)
                
            # Validate the cleaned JSON
            json.loads(content)
            return content
        except Exception as e:
            self.logger.error(f"Error cleaning JSON string: {str(e)}")
            return json.dumps(self.get_default_response())

    def fix_parameter_structure(self, params: Dict) -> Dict:
        """Fix the nested parameter structure from Llama API response."""
        try:
            # Define default parameters
            fixed_params = {
                "temperature": {"value": 0.5, "reasoning": "Default value for balanced output"},
                "top_p": {"value": 0.8, "reasoning": "Default value for diverse sampling"},
                "presence_penalty": {"value": 0.0, "reasoning": "Default value for neutral presence"},
                "frequency_penalty": {"value": 0.0, "reasoning": "Default value for neutral frequency"}
            }

            if not params:
                return {"value": fixed_params}

            # Get the value, handling different structures
            param_values = params.get('value', params)
            
            if isinstance(param_values, dict):
                # Handle different parameter formats
                for key, value in param_values.items():
                    if isinstance(value, dict) and key in fixed_params:
                        # Direct parameter object
                        fixed_params[key] = value
                    elif isinstance(value, dict) and any(k in value for k in fixed_params):
                        # Nested parameter object
                        for param_name, param_data in value.items():
                            if param_name in fixed_params:
                                fixed_params[param_name] = param_data
            elif isinstance(param_values, list):
                # Handle list format
                for item in param_values:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if key in fixed_params:
                                fixed_params[key] = value

            # Ensure all parameters have the correct structure
            for key in fixed_params:
                if not isinstance(fixed_params[key], dict) or 'value' not in fixed_params[key]:
                    fixed_params[key] = {
                        "value": fixed_params[key] if isinstance(fixed_params[key], (int, float)) else 0.0,
                        "reasoning": "Converted to standard format"
                    }

            self.logger.info(f"Fixed parameters structure: {fixed_params}")
            return {"value": fixed_params}

        except Exception as e:
            self.logger.error(f"Error fixing parameter structure: {str(e)}")
            return {"value": {
                "temperature": {"value": 0.5, "reasoning": "Default due to error"},
                "top_p": {"value": 0.8, "reasoning": "Default due to error"},
                "presence_penalty": {"value": 0.0, "reasoning": "Default due to error"},
                "frequency_penalty": {"value": 0.0, "reasoning": "Default due to error"}
            }}

    def validate_and_fix_llama_response(self, content: str):
        """Validate and fix JSON response from Llama API."""
        try:
            # Clean and fix JSON structure
            cleaned_content = self.clean_json_string(content)
            parsed_content = json.loads(cleaned_content)

            # Handle if content is a list
            if isinstance(parsed_content, list):
                if len(parsed_content) > 0:
                    parsed_content = parsed_content[0]
                else:
                    raise ValueError("Empty response list from Llama API")

            # Ensure required top-level keys exist
            required_keys = ["request_analysis", "technical_assessment", "guidelines", "parameters"]
            for key in required_keys:
                if key not in parsed_content:
                    parsed_content[key] = {}

            # Fix parameters structure
            parsed_content["parameters"] = self.fix_parameter_structure(parsed_content.get("parameters", {}))
            
            # Add easy access parameters
            parsed_content["parameter_values"] = self.get_parameter_values(parsed_content["parameters"])


            # Log the fixed parameters
            self.logger.info("Using optimized parameters for prompt enhancement:")
            self.logger.info(f"value: {parsed_content['parameters']['value']}")

            return parsed_content

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON validation failed in Llama response: {str(e)}")
            return self.get_default_response()
        except Exception as e:
            self.logger.error(f"Error processing Llama response: {str(e)}")
            return self.get_default_response()

    def get_default_response(self) -> Dict:
        """Return a default response structure when processing fails."""
        return {
            "request_analysis": {},
            "technical_assessment": {},
            "guidelines": "",
            "parameters": {
                "value": {
                    "temperature": {"value": 0.5, "reasoning": "Default value"},
                    "top_p": {"value": 0.8, "reasoning": "Default value"},
                    "presence_penalty": {"value": 0.0, "reasoning": "Default value"},
                    "frequency_penalty": {"value": 0.0, "reasoning": "Default value"}
                }
            }
        }

class PromptEnhancer:
    def __init__(self, logger: Logger):
        self.logger = logger

    def generate_guidelines(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
        """
        First API call: Analyzes the request and generates guidelines with parameters.
        Includes comprehensive error handling and response validation.
        """
        try:
            # First, let's create a very explicit system message that enforces response format
            system_message = """You are an AI analysis expert. 
You must respond ONLY in valid JSON format.
Do not include any explanatory text or markdown formatting.
Ensure your response is a single JSON object with all required fields."""

            # Create a more structured analysis prompt with clear instructions
            analysis_prompt = f"""Analyze this request comprehensively:
Request: "{prompt}"
AI Type: {ai_type}
Style: {style}

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
            "value": 0.7,
            "reasoning": "Explanation for temperature choice"
        }},
        "top_p": {{
            "value": 0.9,
            "reasoning": "Explanation for top_p choice"
        }},
        "presence_penalty": {{
            "value": 0.0,
            "reasoning": "Explanation for presence_penalty choice"
        }},
        "frequency_penalty": {{
            "value": 0.0,
            "reasoning": "Explanation for frequency_penalty choice"
        }}
    }}
}}

For the specific case of "{prompt}", analyze the implementation requirements and optimal parameters."""

            # Make the API call with strict parameters for consistent formatting
            response = llama.run({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.3,  # Low temperature for consistent formatting
                "max_tokens": 2000,
                "stream": False
            })

            # Extract and clean the content
            content = response.json()['choices'][0]['message']['content']
            content = response.json()['choices'][0]['message']['content']
            self.logger.debug("========= API RESPONSE START =========")
            self.logger.debug(f"Raw content: {content}")
            self.logger.debug("========= API RESPONSE END =========")

            # Clean and parse the response
            cleaned_content = self._clean_json_content(content)
            self.logger.debug(f"Cleaned content: {cleaned_content}")

            if not self._validate_json_structure(cleaned_content):
                self.logger.error("Invalid JSON structure received from API")
                return self._generate_fallback_response(prompt, ai_type, style)

            try:
                parsed_response = json.loads(cleaned_content)
                
                # Extract and validate parameters
                parameters = self._extract_parameters(parsed_response.get("parameters", {}))
                
                # Format guidelines with the analysis
                formatted_guidelines = self._format_comprehensive_guidelines(parsed_response)

                return {
                    "guidelines": formatted_guidelines,
                    "parameters": parameters,
                    "raw_analysis": parsed_response
                }

            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {str(e)}")
                # If JSON parsing fails, create a structured fallback response
                return self._generate_fallback_response(prompt, ai_type, style)

        except Exception as e:
            self.logger.error(f"Analysis generation failed: {str(e)}")
            raise

    def _clean_json_content(self, content: str) -> str:
        """Enhanced JSON content cleaning with better error handling"""
        try:
            self.logger.debug("=== Content Cleaning Start ===")
            self.logger.debug(f"Original content: {content}")
            
            # Remove any leading/trailing whitespace
            content = content.strip()
            
            # If content is wrapped in markdown code blocks, extract the JSON
            if '```json' in content.lower():
                # Find the JSON block
                start = content.lower().find('```json') + 7
                end = content.rfind('```')
                if start > 6 and end != -1:
                    content = content[start:end].strip()
            elif '```' in content:
                # Handle generic code blocks
                start = content.find('```') + 3
                end = content.rfind('```')
                if start > 2 and end != -1:
                    content = content[start:end].strip()
                    
            # Clean up any remaining whitespace
            content = content.strip()
            
            # Try to find valid JSON within the content
            brace_start = content.find('{')
            brace_end = content.rfind('}')
            
            if brace_start != -1 and brace_end != -1:
                content = content[brace_start:brace_end + 1]
            
            self.logger.debug(f"Cleaned content: {content}")
            self.logger.debug("=== Content Cleaning End ===")
            
            # Validate JSON structure
            try:
                # Test if it's valid JSON
                json.loads(content)
                return content
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON validation failed: {e}")
                raise ValueError(f"Invalid JSON structure: {e}")
                
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

    def _extract_parameters(self, params: Dict) -> Dict[str, float]:
        """Extract and validate parameters with detailed error checking"""
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        
        try:
            processed_params = {}
            for param_name, default_value in default_params.items():
                param_data = params.get(param_name, {})
                if isinstance(param_data, dict) and "value" in param_data:
                    try:
                        value = float(param_data["value"])
                        # Apply appropriate bounds
                        if param_name in ["temperature", "top_p"]:
                            value = min(max(value, 0.0), 1.0)
                        else:
                            value = min(max(value, -2.0), 2.0)
                        processed_params[param_name] = value
                    except (ValueError, TypeError):
                        processed_params[param_name] = default_value
                else:
                    processed_params[param_name] = default_value
                    
            return processed_params

        except Exception as e:
            self.logger.error(f"Parameter extraction failed: {str(e)}")
            return default_params

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

            # Extract and process the response
            content = response.json()['choices'][0]['message']['content']
            self.logger.debug(f"Raw enhancement response: {content}")

            # Clean and parse the response
            cleaned_content = self._clean_json_content(content)
            try:
                parsed_response = json.loads(cleaned_content)
                
                # Validate the response structure
                if "prompts" not in parsed_response or not isinstance(parsed_response["prompts"], list):
                    raise ValueError("Invalid response structure: missing or invalid 'prompts' array")
                
                return parsed_response

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse enhanced prompts: {e}")
                return self._generate_fallback_enhanced_prompts(prompt, style, ai_type)

        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {str(e)}")
            raise
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


@app.route('/process', methods=['POST'])
def process_request():
    """
    Handle incoming requests for prompt enhancement.
    """
    try:
        if not llama:
            return jsonify({"error": "Llama API not properly configured"}), 500

        # Initialize response handler
        response_handler = ResponseHandler(logger)

        # Validate incoming request
        data = request.form.get('data')
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid JSON in request: {str(e)}"}), 400

        if 'prompt' not in data:
            return jsonify({"error": "No prompt provided"}), 400

        # Initialize the enhancer
        enhancer = PromptEnhancer(logger)
        
        ai_type = data.get('AIType', 'descriptive')
        style = data.get('style', 'professional')
        single_prompt = data.get('singlePrompt', False)

        logger.debug("=== Request Processing Start ===")
        logger.debug(f"Input data: {data}")
        logger.debug(f"AI Type: {ai_type}")
        logger.debug(f"Style: {style}")

        try:
            # Generate guidelines
            guideline_response = enhancer.generate_guidelines(
                prompt=data['prompt'],
                ai_type=ai_type,
                style=style
            )
            
            # Validate and fix Llama response before proceeding
            fixed_response = response_handler.validate_and_fix_llama_response(guideline_response)
            if not fixed_response:
                raise ValueError("Failed to validate Llama API response")

            # Continue with the enhanced response
            enhanced_response = enhancer.enhance_prompt(
                prompt=data['prompt'],
                guidelines=fixed_response['guidelines'],
                parameters=fixed_response['parameters'],
                style=style,
                ai_type=ai_type
            )

            if single_prompt and enhanced_response.get("prompts"):
                enhanced_response["prompts"] = [enhanced_response["prompts"][0]]

            response = {
                "original_prompt": data['prompt'],
                "response": enhanced_response,
                "guidelines": fixed_response['guidelines'],
                "parameters_used": fixed_response['parameters'],
                "raw_analysis": fixed_response.get('raw_analysis', {}),
                "ai_type": ai_type,
                "style": style
            }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error in prompt processing: {str(e)}")
            return jsonify({
                "error": f"Failed to process prompt: {str(e)}",
                "original_prompt": data['prompt']
            }), 500

    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/process', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', request.origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)
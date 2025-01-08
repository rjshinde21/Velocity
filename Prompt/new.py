import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
import uuid
from logging import Logger

from transformers import pipeline
from spacy import load
from keybert import KeyBERT
import textstat
from sentence_transformers import SentenceTransformer
from llamaapi import LlamaAPI
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/process": {
        "origins": ["http://localhost:*", "chrome-extension://*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Load environment variables
load_dotenv()
LLAMA_API_KEY = os.getenv('LLAMA_API_KEY')

class APIHandler:
    def __init__(self, api_key: str):
        self.llama = LlamaAPI(api_key)
        self.logger = logging.getLogger(__name__)

    def make_api_call(self, system_message: str, prompt: str, **params) -> Dict:
        try:
            system_message = f"""You are a strict JSON response generator.
            CRITICAL REQUIREMENTS:
            1. Respond ONLY with the specified JSON structure
            2. DO NOT include any explanatory text
            3. DO NOT use markdown formatting
            4. DO NOT include code blocks or ```json tags
            5. Ensure the response is a single valid JSON object
            
            {system_message}"""
            
            response = self.llama.run({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "model": "llama3.2-3b",
                "max_tokens": 2000,
                "stream": False,
                **params
            })
            
            return self._process_response(response)
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise

    def _validate_json_response(self, content: str) -> bool:
        try:
            # Original validation was too strict
            data = json.loads(content)
            # Remove overly restrictive word checks
            return isinstance(data, dict) and len(data) > 0
        except json.JSONDecodeError:
            return False

    def _process_response(self, response: Any) -> Dict:
        try:
            # Get response data
            response_data = response.json() if hasattr(response, 'json') else response
            
            # Extract content
            content = None
            if isinstance(response_data, dict):
                if 'choices' in response_data:
                    message = response_data['choices'][0].get('message', {})
                    content = message.get('content', '')
                else:
                    content = response_data.get('content', response_data)
            
            if not content:
                raise ValueError("No content found in response")
            
            # Clean content if it's a string
            if isinstance(content, str):
                content = content.strip()
                # Try to parse JSON if it looks like JSON
                if content.startswith('{') and content.endswith('}'):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass  # Keep as string if parsing fails
                    
            return {
                "content": content,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "llama3.2-3b"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            self.logger.error(f"Response data: {response_data if 'response_data' in locals() else 'No response data'}")
            return {
                "content": None,
                "error": str(e),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "llama3.2-3b",
                    "has_error": True
                }
            }

class InputProcessor:
    def __init__(self):
        self.nlp = load('en_core_web_sm')
        self.sentiment_analyzer = pipeline('sentiment-analysis')
        self.keyword_model = KeyBERT()
        self.logger = logging.getLogger(__name__)

    def process_input(self, prompt: str, ai_type: str, style: str) -> Dict:
        """Process and analyze input"""
        try:
            # Basic validation
            if not all([prompt, ai_type, style]):
                raise ValueError("Missing required input parameters")

            doc = self.nlp(prompt)
            
            return {
                "input": {
                    "original_prompt": prompt,
                    "ai_type": ai_type,
                    "style": style,
                    "timestamp": datetime.now().isoformat()
                },
                "analysis": {
                    "entities": [{"text": ent.text, "label": ent.label_} for ent in doc.ents],
                    "keywords": self.keyword_model.extract_keywords(prompt, top_n=5),
                    "sentiment": self.sentiment_analyzer(prompt)[0],
                    "complexity": {
                        "score": textstat.flesch_reading_ease(prompt),
                        "grade_level": textstat.coleman_liau_index(prompt)
                    }
                },
                "platform_context": self._get_platform_context(ai_type)
            }
        except Exception as e:
            self.logger.error(f"Input processing failed: {str(e)}")
            raise

    def _get_platform_context(self, ai_type: str) -> Dict:
        """Get platform-specific requirements"""
        return {
            "ChatGPT": {
                "max_tokens": 4000,
                "capabilities": ["context-awareness", "conversation"]
            },
            "Claude": {
                "max_tokens": 8000,
                "capabilities": ["analysis", "code-generation"]
            }
        }.get(ai_type, {"max_tokens": 2000, "capabilities": ["basic-completion"]})

class AnalysisPipeline:
    def __init__(self, api_handler: APIHandler):
        self.api_handler = api_handler
        self.logger = logging.getLogger(__name__)
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

    def analyze(self, context: Dict) -> Dict:
        """Run complete analysis pipeline"""
        try:
            # Initial API analysis
            analysis_response = self.api_handler.make_api_call(
                system_message=self._create_analysis_prompt(context),
                prompt=context["input"]["original_prompt"],
                temperature=0.3
            )
            
            # Get content from response
            raw_content = analysis_response.get("content", {})
            
            # If content is string, parse it
            if isinstance(raw_content, str):
                processed_analysis = self._process_analysis(raw_content)
            else:
                # Content is already a dict
                processed_analysis = raw_content
                
            semantic_analysis = self._analyze_semantics(context["input"]["original_prompt"])
            
            context["detailed_analysis"] = {
                "api_analysis": processed_analysis,
                "semantic_analysis": semantic_analysis,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0",
                    "has_errors": False
                }
            }
            
            return context
        except Exception as e:
            self.logger.error(f"Analysis pipeline failed: {str(e)}")
            # Return partial context instead of raising
            context["detailed_analysis"] = {
                "error": str(e),
                "semantic_analysis": self._analyze_semantics(context["input"]["original_prompt"]),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0",
                    "has_errors": True
                }
            }
            return context

    def _create_analysis_prompt(self, context: Dict) -> str:
        return f"""For the prompt: "{context['input']['original_prompt']}"
        Return this EXACT JSON ONLY:
        {{
            "analysis": {{
                "intent": "single sentence core intent",
                "context": ["2-3 key context points"],
                "requirements": ["2-3 main knowledge requirements"],
                "scope": ["2-3 scope/boundary points"]
            }}
        }}"""

    def _process_analysis(self, content: str) -> Dict:
        """Process API analysis response"""
        try:
            # Clean and parse JSON
            cleaned_content = re.sub(r'```json\s*|\s*```', '', content)
            cleaned_content = cleaned_content.strip()
            
            # Handle potential non-JSON content
            if not (cleaned_content.startswith('{') and cleaned_content.endswith('}')):
                # Try to extract JSON portion
                start_idx = cleaned_content.find('{')
                end_idx = cleaned_content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    cleaned_content = cleaned_content[start_idx:end_idx + 1]
                else:
                    # If no JSON found, create a structured response
                    return {
                        "content": cleaned_content,
                        "error": "Non-JSON response received",
                        "timestamp": datetime.now().isoformat()
                    }

            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Analysis processing failed: {str(e)}")
            self.logger.error(f"Content causing error: {cleaned_content}")
            # Return structured error response instead of raising
            return {
                "error": "JSON parsing failed",
                "raw_content": content,
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_semantics(self, text: str) -> Dict:
        """Perform semantic analysis"""
        try:
            embedding = self.semantic_model.encode(text)
            return {
                "embedding_dimension": len(embedding),
                "semantic_complexity": float(embedding.std()),
                "semantic_features": self._extract_semantic_features(text)
            }
        except Exception as e:
            self.logger.error(f"Semantic analysis failed: {str(e)}")
            raise

    def _extract_semantic_features(self, text: str) -> Dict:
        """Extract semantic features from text"""
        doc = load('en_core_web_sm')(text)
        return {
            "key_phrases": [chunk.text for chunk in doc.noun_chunks],
            "dependencies": [{"text": token.text, "dep": token.dep_} for token in doc],
            "pos_tags": [{"text": token.text, "pos": token.pos_} for token in doc]
        }

class GuidelineGenerator:
    def __init__(self, api_handler: APIHandler):
        self.api_handler = api_handler
        self.logger = logging.getLogger(__name__)

    def generate_guidelines(self, context: Dict) -> Dict:
        try:
            # Extract with new analysis structure
            analysis = context["detailed_analysis"]["api_analysis"]["analysis"]
            analysis_data = {
                "intent": analysis["primary_intent"],
                "context": analysis["intent_context"],
                "requirements": analysis["knowledge_requirements"],
                "expectations": analysis["response_expectations"],
                "original_prompt": context["input"]["original_prompt"],
                "style": context["input"]["style"],
                "ai_type": context["input"]["ai_type"]
            }
            
            guideline_response = self.api_handler.make_api_call(
                system_message=self._create_guideline_prompt(),
                prompt=json.dumps(analysis_data),
                temperature=0.4
            )
            
            guidelines = guideline_response.get("content", {})
            if isinstance(guidelines, str):
                try:
                    guidelines = self._process_guidelines(guidelines)
                except json.JSONDecodeError:
                    guidelines = self._generate_fallback_guidelines()
            
            context["guidelines"] = {
                "content": guidelines,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            return context
        except Exception as e:
            self.logger.error(f"Guideline generation failed: {str(e)}")
            context["guidelines"] = {
                "content": self._generate_fallback_guidelines(),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "is_fallback": True,
                    "error": str(e)
                }
            }
            return context
                    
        


    def _create_guideline_prompt(self) -> str:
        return """Based on the input data, return this EXACT JSON ONLY:
        {
            "guidelines": {
                "strategy": "one sentence approach",
                "elements": ["3-4 key components"],
                "style_rules": ["2-3 style rules"],
                "platform_rules": ["2-3 platform specifics"]
            }
        }"""


    def _generate_fallback_guidelines(self) -> Dict:
        """Generate basic guidelines when processing fails"""
        return {
            "core_approach": "Structure the prompt clearly and directly",
            "structure_elements": [
                "Clear objective statement",
                "Relevant context",
                "Specific requirements",
                "Output format specification"
            ],
            "style_adaptations": [
                "Maintain professional tone",
                "Use clear and concise language"
            ],
            "platform_specific": [
                "Follow platform best practices",
                "Optimize for platform capabilities"
            ]
        }
    
    def _format_response(self, context: Dict) -> Dict:
        try:
            return {
                "status": "success",
                "request_id": context["request_id"],
                "prompts": context.get("enhanced_prompts", {}).get("prompts", []),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "ai_type": context["input"]["ai_type"],
                    "style": context["input"]["style"],
                    "processing_summary": {
                        "original_intent": context["detailed_analysis"]["api_analysis"]["analysis"]["primary_intent"],
                        "enhancement_focus": context["guidelines"]["content"].get("prompt_strategy", "direct enhancement"),
                        "complexity_score": context["analysis"]["complexity"]["score"]
                    },
                    "processing_stages": context["processing_stages"]
                }
            }
        except Exception as e:
            self.logger.error(f"Response formatting failed: {str(e)}")
            
        

    def _process_guidelines(self, content: str) -> Dict:
        """Process guideline response"""
        try:
            # Clean the content
            cleaned_content = content.strip()
            cleaned_content = re.sub(r'```json\s*|\s*```', '', cleaned_content)
            
            # Extract JSON if embedded in other text
            json_start = cleaned_content.find('{')
            json_end = cleaned_content.rfind('}')
            if json_start != -1 and json_end != -1:
                cleaned_content = cleaned_content[json_start:json_end + 1]
            
            # Parse JSON
            parsed_content = json.loads(cleaned_content)
            
            # Validate structure
            if not isinstance(parsed_content, dict) or "guidelines" not in parsed_content:
                raise ValueError("Invalid guidelines structure")
            
            return parsed_content["guidelines"]
            
        except Exception as e:
            self.logger.error(f"Guideline processing failed: {str(e)}")
            return self._generate_fallback_guidelines()

class ParameterOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def optimize_parameters(self, context: Dict) -> Dict:
        """Optimize API parameters"""
        try:
            base_params = self._get_base_parameters(context["input"]["ai_type"])
            style_adjusted = self._adjust_for_style(base_params, context["input"]["style"])
            
            # Safely extract analysis data
            analysis_data = context.get("detailed_analysis", {}).get("api_analysis", {}).get("analysis", {})
            
            optimized = self._optimize_for_complexity(
                style_adjusted,
                analysis_data
            )
            
            context["parameters"] = {
                "values": optimized,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "optimization_factors": ["platform", "style", "complexity"]
                }
            }
            
            return context
        except Exception as e:
            self.logger.error(f"Parameter optimization failed: {str(e)}")
            # Return default parameters on error
            context["parameters"] = {
                "values": self._get_base_parameters(context["input"]["ai_type"]),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "optimization_factors": ["platform"],
                    "is_fallback": True
                }
            }
            return context

    def _get_base_parameters(self, ai_type: str) -> Dict:
        """Get base parameters for platform"""
        return {
            "ChatGPT": {"temperature": 0.7, "top_p": 0.9},
            "Claude": {"temperature": 0.8, "top_p": 0.95}
        }.get(ai_type, {"temperature": 0.7, "top_p": 0.9})

    def _adjust_for_style(self, params: Dict, style: str) -> Dict:
        """Adjust parameters for style"""
        style_adjustments = {
            "Creative": {"temperature": 0.2, "top_p": 0.05},
            "Technical": {"temperature": -0.2, "top_p": -0.05},
            "Concise": {"temperature": -0.1, "top_p": -0.1}
        }

        if style in style_adjustments:
            for param, adjustment in style_adjustments[style].items():
                params[param] = max(0.1, min(1.0, params[param] + adjustment))

        return params

    def _optimize_for_complexity(self, params: Dict, analysis: Dict) -> Dict:
        """Optimize based on complexity"""
        if "complexity" in analysis:
            complexity_score = analysis["complexity"].get("score", 50)
            if complexity_score > 70:
                params["temperature"] = max(0.1, params["temperature"] - 0.1)
            elif complexity_score < 30:
                params["temperature"] = min(1.0, params["temperature"] + 0.1)

        return params

class PromptEnhancer:
    def __init__(self, api_handler: APIHandler):
        self.api_handler = api_handler
        self.logger = logging.getLogger(__name__)

    def generate_enhanced_prompts(self, context: Dict) -> Dict:
        try:
            final_prompt = f"""Given this raw analysis:
            {json.dumps(context['detailed_analysis'])}
            
            And these guidelines:
            {json.dumps(context['guidelines'])}
            
            Generate three versions of: "{context['input']['original_prompt']}"
            For Platform: {context['input']['ai_type']}
            In Style: {context['input']['style']}
            
            Return this JSON ONLY:
            {{
                "prompts": [
                    {{"text": "clear, direct version"}},
                    {{"text": "contextual version"}},
                    {{"text": "detailed technical version"}}
                ]
            }}"""
            
            response = self.api_handler.make_api_call(
                system_message="You are a JSON generator. Return ONLY the exact JSON structure specified.",
                prompt=final_prompt,
                **context["parameters"]["values"]
            )
            
            enhanced_prompts = self._process_enhanced_prompts(response["content"])
            
            context["enhanced_prompts"] = {
                "prompts": enhanced_prompts,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {str(e)}")
            context["enhanced_prompts"] = {
                "error": str(e),
                "prompts": [],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "has_errors": True
                }
            }
            return context

    def _create_enhancement_prompt(self, context: Dict) -> str:
        intent = context['detailed_analysis']['api_analysis']['analysis']['primary_intent']
        guidelines = context['guidelines']['content']
        
        return f"""Transform: "{context['input']['original_prompt']}"
        
        
        Platform: {context['input']['ai_type']}
        Style: {context['input']['style']}
        
        Guidelines: {json.dumps(guidelines)}
        
        Generate THREE versions with different focuses:
        1. Direct Definition/Answer
        2. Contextual Understanding
        3. Technical Perspective
        
        Return ONLY this exact JSON:
        {{
            "prompts": [
                {{
                    "version": 1,
                    "text": "enhanced prompt focusing on clear definition"
                }},
                {{
                    "version": 2,
                    "text": "enhanced prompt with context and examples"
                }},
                {{
                    "version": 3,
                    "text": "enhanced prompt with technical depth"
                }}
            ]
        }}"""

    def _process_enhanced_prompts(self, content: str) -> List[Dict]:
        try:
            if isinstance(content, str):
                cleaned_content = content.strip()
                # Remove any markdown or JSON formatting
                cleaned_content = re.sub(r'```json\s*|\s*```', '', cleaned_content)
                data = json.loads(cleaned_content)
            else:
                data = content

            prompts = data.get("prompts", [])
            if not prompts:
                raise ValueError("No prompts found in response")

            # Standardize prompt format
            processed_prompts = []
            for prompt in prompts:
                if isinstance(prompt, dict):
                    text = prompt.get("text", prompt.get("prompt", ""))
                    if text and isinstance(text, str):
                        processed_prompts.append({
                            "prompt": text.strip(),
                            "metadata": {
                                "version": prompt.get("version", 0),
                                "timestamp": datetime.now().isoformat()
                            }
                        })

            return processed_prompts if processed_prompts else [
                {"prompt": "Could not generate enhanced prompt", "metadata": {"is_fallback": True}}
            ]
            
        except Exception as e:
            self.logger.error(f"Enhanced prompt processing failed: {str(e)}")
            return [{"prompt": "Could not process enhanced prompts", "metadata": {"error": str(e)}}]

    # def _create_enhancement_prompt(self, context: Dict) -> str:
    #     """Create single enhancement prompt combining message and context"""
    #     message = f"""Based on this context, generate 3 enhanced versions.
    #     Return ONLY this exact JSON structure:
    #     {{"prompts": [
    #         {{"prompt": "detailed description 1",
    #         "prompt": "detailed description 2",
    #         "prompt": "detailed description 3"}}
    #     ]}}"""

    #     context_data = {
    #         "original_prompt": context["input"]["original_prompt"],
    #         "style": context["input"]["style"],
    #         "platform": context["input"]["ai_type"],
    #     }
        
    #     return f"{message}\n\nContext: {json.dumps(context_data)}"



    def _validate_prompt(self, prompt: Dict) -> bool:
        """Validate individual prompt"""
        return (
            isinstance(prompt, dict) and
            "prompt" in prompt and
            isinstance(prompt["prompt"], str) and
            len(prompt["prompt"].strip()) > 0
        )

class EnhancementPipeline:
    def __init__(self, api_key: str):
        self.api_handler = APIHandler(api_key)
        self.input_processor = InputProcessor()
        self.analysis_pipeline = AnalysisPipeline(self.api_handler)
        self.guideline_generator = GuidelineGenerator(self.api_handler)
        self.parameter_optimizer = ParameterOptimizer()
        self.prompt_enhancer = PromptEnhancer(self.api_handler)
        self.logger = logging.getLogger(__name__)

    def process_request(self, prompt: str, ai_type: str, style: str) -> Dict:
        """
        Main pipeline processing method
        """
        try:
            # Create request context
            request_id = str(uuid.uuid4())
            context = {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "processing_stages": []
            }

            # Stage 1: Input Processing
            self.logger.info(f"[{request_id}] Starting input processing")
            input_context = self.input_processor.process_input(prompt, ai_type, style)
            context.update(input_context)
            context["processing_stages"].append({
                "name": "input_processing",
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })

            # Stage 2: Analysis
            self.logger.info(f"[{request_id}] Running analysis pipeline")
            analysis_context = self.analysis_pipeline.analyze(context)
            context.update(analysis_context)

            # Stage 3: Generate Guidelines
            self.logger.info(f"[{request_id}] Generating guidelines")
            guidelines_context = self.guideline_generator.generate_guidelines(context)
            context.update(guidelines_context)

            # Stage 4: Optimize Parameters
            self.logger.info(f"[{request_id}] Optimizing parameters")
            optimized_context = self.parameter_optimizer.optimize_parameters(context)
            context.update(optimized_context)

            # Stage 5: Generate Enhanced Prompts
            self.logger.info(f"[{request_id}] Generating enhanced prompts")
            final_context = self.prompt_enhancer.generate_enhanced_prompts(context)
            
            return self._format_response(final_context)

        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {str(e)}")
            return self._format_error_response(str(e))

    def _format_response(self, context: Dict) -> Dict:
        try:
            return {
                "status": "success",
                "request_id": context["request_id"],
                "prompts": context.get("enhanced_prompts", {}).get("prompts", []),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "ai_type": context["input"]["ai_type"],
                    "style": context["input"]["style"],
                    "processing_summary": {
                        "original_intent": context["detailed_analysis"]["api_analysis"]["analysis"]["primary_intent"],
                        "enhancement_approach": context["guidelines"]["content"]["prompt_strategy"],
                        "complexity_score": context["analysis"]["complexity"]["score"]
                    },
                    "processing_stages": context["processing_stages"]
                }
            }
        except Exception as e:
            self.logger.error(f"Response formatting failed: {str(e)}")
            return self._format_error_response(str(e))

    def _format_error_response(self, error: str) -> Dict:
        """Format error response"""
        return {
            "status": "error",
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "error_type": "pipeline_processing_error"
            }
        }
    
    def _validate_stage(self, stage_name: str, data: Dict, required_keys: List[str]) -> None:
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise ValueError(f"Stage {stage_name} missing required keys: {missing}")
        
        self.logger.info(f"Stage {stage_name} completed successfully")
        return True

# Flask API endpoint implementation
@app.route('/process', methods=['POST'])
def process_request():
    """Handle prompt enhancement requests"""
    try:
        # Validate request
        data = _validate_and_get_request_data(request)
        
        # Initialize and run pipeline with timeout
        pipeline = EnhancementPipeline(LLAMA_API_KEY)
        response = pipeline.process_request(
            prompt=data['prompt'],
            ai_type=data['AIType'],
            style=data['style']
        )
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "type": "validation_error",
            "timestamp": datetime.now().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "type": "processing_error",
            "timestamp": datetime.now().isoformat()
        }), 500

def _validate_and_get_request_data(request) -> Dict:
    """Validate and extract request data"""
    if request.is_json:
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        try:
            data = json.loads(request.form.get('data', '{}'))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in form data")
    else:
        raise ValueError(f"Unsupported Content-Type: {request.content_type}")

    # Validate required fields
    required_fields = {'prompt', 'AIType', 'style'}
    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    return data

@app.route('/process', methods=['OPTIONS'])
def handle_options():
    """Handle CORS preflight requests"""
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', request.origin or '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

if __name__ == '__main__':
    # Ensure all required environment variables are set
    if not LLAMA_API_KEY:
        raise ValueError("LLAMA_API_KEY environment variable not set")
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=2000, debug=True)
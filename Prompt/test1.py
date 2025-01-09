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
        """Make API call with retry logic"""
        try:
            response = self.llama.run({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "model": "llama-13b-chat",
                "stream": False,
                **params
            })
            
            return self._process_response(response)
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise

    def _process_response(self, response: Any) -> Dict:
        """Process API response"""
        try:
            if hasattr(response, 'json'):
                response_data = response.json()
            else:
                response_data = response

            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0].get('message', {}).get('content', '')
                return {
                    "content": content,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "model": "llama-13b-chat"
                    }
                }
            raise ValueError("Invalid response structure")
        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            raise

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

            # Process and enhance analysis
            processed_analysis = self._process_analysis(analysis_response["content"])
            semantic_analysis = self._analyze_semantics(context["input"]["original_prompt"])

            # Combine analyses
            context["detailed_analysis"] = {
                "api_analysis": processed_analysis,
                "semantic_analysis": semantic_analysis,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0"
                }
            }

            return context
        except Exception as e:
            self.logger.error(f"Analysis pipeline failed: {str(e)}")
            raise

    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create analysis prompt"""
        return f"""Analyze this request for {context['input']['ai_type']} implementation:

        Request: {context['input']['original_prompt']}
        Style: {context['input']['style']}

        Provide detailed analysis covering:
        1. Primary intent and objectives
        2. Technical requirements
        3. Implementation considerations
        4. Platform-specific optimizations

        Return analysis in JSON format."""

    def _process_analysis(self, content: str) -> Dict:
        """Process API analysis response"""
        try:
            # Clean and parse JSON
            cleaned_content = re.sub(r'```json\s*|\s*```', '', content)
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Analysis processing failed: {str(e)}")
            raise

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
        """Generate implementation guidelines"""
        try:
            # Generate guidelines
            response = self.api_handler.make_api_call(
                system_message=self._create_guideline_prompt(context),
                prompt=json.dumps(context["detailed_analysis"]),
                temperature=0.4
            )

            # Process guidelines
            processed_guidelines = self._process_guidelines(response["content"])
            
            # Add to context
            context["guidelines"] = {
                "content": processed_guidelines,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }

            return context
        except Exception as e:
            self.logger.error(f"Guideline generation failed: {str(e)}")
            raise

    def _create_guideline_prompt(self, context: Dict) -> str:
        """Create guideline generation prompt"""
        return f"""Create comprehensive guidelines for {context['input']['ai_type']} implementation.

        Original Request: {context['input']['original_prompt']}
        Style: {context['input']['style']}
        Analysis: {json.dumps(context['detailed_analysis'])}

        Provide detailed guidelines covering:
        1. Implementation strategy
        2. Platform-specific optimizations
        3. Style requirements
        4. Response structure

        Return in JSON format."""

    def _process_guidelines(self, content: str) -> Dict:
        """Process guideline response"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Guideline processing failed: {str(e)}")
            raise

class ParameterOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def optimize_parameters(self, context: Dict) -> Dict:
        """Optimize API parameters"""
        try:
            base_params = self._get_base_parameters(context["input"]["ai_type"])
            style_adjusted = self._adjust_for_style(base_params, context["input"]["style"])
            optimized = self._optimize_for_complexity(
                style_adjusted,
                context["detailed_analysis"]["api_analysis"]
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
            raise

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
        """Generate enhanced prompts"""
        try:
            response = self.api_handler.make_api_call(
                system_message=self._create_enhancement_prompt(context),
                prompt=self._create_enhancement_input(context),
                **context["parameters"]["values"]
            )

            enhanced_prompts = self._process_enhanced_prompts(response["content"])
            
            context["enhanced_prompts"] = {
                "prompts": enhanced_prompts,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "parameters_used": context["parameters"]["values"]
                }
            }

            return context
        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {str(e)}")
            raise

    def _create_enhancement_prompt(self, context: Dict) -> str:
        """Create enhancement system message"""
        return f"""Create three enhanced versions of this prompt for {context['input']['ai_type']}.

        Original: {context['input']['original_prompt']}
        Style: {context['input']['style']}
        Guidelines: {json.dumps(context['guidelines'])}

        Each version should:
        1. Be optimized for {context['input']['ai_type']}
        2. Follow {context['input']['style']} style
        3. Address core requirements
        4. Offer unique perspective

        Return in JSON format with exactly 3 prompts."""

    def _create_enhancement_input(self, context: Dict) -> str:
        """Create enhancement user input"""
        return json.dumps({
            "original_prompt": context["input"]["original_prompt"],
            "analysis": context["detailed_analysis"],
            "guidelines": context["guidelines"]
        })

    def _process_enhanced_prompts(self, content: str) -> List[Dict]:
        """Process enhanced prompts"""
        try:
            response_data = json.loads(content)
            prompts = response_data.get("prompts", [])
            
            # Validate and clean prompts
            return [
                {
                    "prompt": p["prompt"],
                    "focus": p.get("focus", "general"),
                    "perspective": p.get("perspective", "standard")
                }
                for p in prompts[:3]  # Ensure exactly 3 prompts
                if self._validate_prompt(p)
            ]
        except json.JSONDecodeError as e:
            self.logger.error(f"Prompt processing failed: {str(e)}")
            raise

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
                "timestamp": datetime.now().isoformat()
            }

            # Stage 1: Input Processing
            self.logger.info(f"[{request_id}] Starting input processing")
            input_context = self.input_processor.process_input(prompt, ai_type, style)
            context.update(input_context)

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
        """Format successful pipeline response"""
        return {
            "status": "success",
            "request_id": context["request_id"],
            "prompts": context.get("enhanced_prompts", {}).get("prompts", []),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "ai_type": context["input"]["ai_type"],
                "style": context["input"]["style"],
                "processing_stages": [
                    "input_processing",
                    "analysis",
                    "guidelines",
                    "parameter_optimization",
                    "prompt_enhancement"
                ]
            }
        }

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
    
@app.route('/process', methods=['POST'])
def process_request():
    """Handle prompt enhancement requests"""
    try:
        # Parse request data
        if request.is_json:
            data = request.get_json()
        elif request.content_type == 'application/x-www-form-urlencoded':
            data = json.loads(request.form.get('data', '{}'))
        else:
            return jsonify({
                "status": "error",
                "error": f"Unsupported Content-Type: {request.content_type}",
                "timestamp": datetime.now().isoformat()
            }), 415

        # Validate required fields
        if not all(key in data for key in ['prompt', 'AIType', 'style']):
            return jsonify({
                "status": "error",
                "error": "Missing required fields: prompt, AIType, style",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Initialize and run pipeline
        pipeline = EnhancementPipeline(LLAMA_API_KEY)
        response = pipeline.process_request(
            prompt=data['prompt'],
            ai_type=data['AIType'],
            style=data['style']
        )

        return jsonify(response)

    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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
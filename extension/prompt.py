from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import csv
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
from logging import Logger
import re
from spellchecker import SpellChecker
from llamaapi import LlamaAPI
from abc import ABC, abstractmethod
from dataclasses import dataclass



app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Llama API
try:
    llama = LlamaAPI(os.getenv('LLAMA_API_KEY'))
except Exception as e:
    logger.error(f"Failed to initialize Llama API: {str(e)}")
    llama = None

@dataclass
class ContextualAnalysis:
    domain: str
    purpose: str
    complexity: str
    constraints: List[str]
    key_concepts: List[str]
    target_audience: Optional[str]
    tone_requirements: Dict[str, float]
    technical_level: int  # 1-5 scale

@dataclass
class EnhancedGuidelines:
    content_structure: Dict[str, List[str]]
    style_requirements: Dict[str, str]
    quality_criteria: List[str]
    context_preservation: List[str]
    output_format: Dict[str, str]
    
class AdvancedPromptProcessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.domain_patterns = {
            "technical": r"\b(code|algorithm|function|api|database|system)\b",
            "creative": r"\b(story|article|blog|content|write|create)\b",
            "analytical": r"\b(analyze|research|study|investigate|evaluate)\b",
            "instructional": r"\b(explain|teach|guide|show|demonstrate)\b"
        }
        
        self.complexity_indicators = {
            "basic": ["simple", "basic", "straightforward"],
            "intermediate": ["moderate", "standard", "regular"],
            "advanced": ["complex", "sophisticated", "advanced", "expert"]
        }

        # Add constraint patterns for better identification
        self.constraint_patterns = {
            "time": r"\b(within|by|before|after|during)\b.*?\b\d+\s*(day|week|month|year|hour|minute)s?\b",
            "length": r"\b(maximum|minimum|max|min)\b.*?\b\d+\s*(word|character|sentence|paragraph)s?\b",
            "format": r"\b(format|style|structure)\b.*?\b(as|in|like|following)\b",
            "requirement": r"\b(must|should|need to|has to|require)\b.*?[^,.;]+",
            "limitation": r"\b(only|except|exclude|don't|cannot|can't)\b.*?[^,.;]+",
            "preference": r"\b(prefer|ideally|if possible|optionally)\b.*?[^,.;]+"
        }

        # Add tone and style identifiers
        self.tone_markers = {
            "formal": {"professional", "formal", "academic", "business"},
            "casual": {"casual", "informal", "friendly", "conversational"},
            "technical": {"technical", "detailed", "precise", "scientific"},
            "creative": {"creative", "imaginative", "artistic", "innovative"}
        }

    def _identify_constraints(self, text: str) -> List[str]:
        """
        Identifies constraints and requirements from the prompt text
        """
        constraints = []
        text = text.lower()

        # Check for explicit constraints using patterns
        for constraint_type, pattern in self.constraint_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                constraint = match.group(0).strip()
                if constraint:
                    constraints.append(f"{constraint_type.capitalize()}: {constraint}")

        # Look for numbered or bulleted requirements
        numbered_requirements = re.findall(r'^\d+\.\s*([^.\n]+)', text, re.MULTILINE)
        bulleted_requirements = re.findall(r'[-•]\s*([^.\n]+)', text, re.MULTILINE)
        
        constraints.extend([f"Listed Requirement: {req.strip()}" 
                          for req in numbered_requirements + bulleted_requirements])

        return list(set(constraints))  # Remove duplicates

    def _infer_target_audience(self, text: str, style: str) -> Optional[str]:
        """
        Infers the target audience from the prompt and style
        """
        # Common audience indicators
        audience_patterns = {
            "technical": r"\b(developer|engineer|technical|programmer|professional)\b",
            "general": r"\b(general|public|everyone|anybody|anyone)\b",
            "beginner": r"\b(beginner|novice|basic|starting|new|learner)\b",
            "expert": r"\b(expert|advanced|experienced|professional|specialist)\b"
        }

        # Check for explicit audience mentions
        for audience_type, pattern in audience_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return audience_type

        # Infer from style if no explicit mention
        style_audience_mapping = {
            "technical": "technical",
            "professional": "expert",
            "casual": "general",
            "instructional": "beginner"
        }

        return style_audience_mapping.get(style.lower(), "general")

    def _generate_tone_mapping(self, style: str, ai_type: str) -> Dict[str, float]:
        """
        Generates tone requirements with priority weights based on style and AI type
        """
        base_tones = {
            "professional": {
                "formal": 0.9,
                "precise": 0.8,
                "authoritative": 0.7
            },
            "creative": {
                "imaginative": 0.9,
                "engaging": 0.8,
                "expressive": 0.7
            },
            "technical": {
                "precise": 0.9,
                "analytical": 0.8,
                "objective": 0.7
            },
            "casual": {
                "conversational": 0.9,
                "friendly": 0.8,
                "approachable": 0.7
            }
        }

        # Adjust based on AI type
        ai_type_modifiers = {
            "chatbot": {"conversational": 0.2, "engaging": 0.1},
            "academic": {"formal": 0.2, "analytical": 0.1},
            "business": {"professional": 0.2, "precise": 0.1}
        }

        # Get base tones for the style
        tone_weights = base_tones.get(style.lower(), base_tones["professional"]).copy()

        # Apply AI-type specific modifications
        if ai_type.lower() in ai_type_modifiers:
            for tone, modifier in ai_type_modifiers[ai_type.lower()].items():
                if tone in tone_weights:
                    tone_weights[tone] += modifier
                else:
                    tone_weights[tone] = modifier

        return {k: min(v, 1.0) for k, v in tone_weights.items()}  # Cap at 1.0

    def _assess_technical_level(self, text: str, domain: str) -> int:
        """
        Assesses the technical level required (1-5 scale)
        1: Beginner, 2: Intermediate, 3: Advanced, 4: Expert, 5: Specialist
        """
        # Technical indicators with their weights
        technical_indicators = {
            r"\b(basic|simple|elementary|fundamental)\b": 1,
            r"\b(intermediate|moderate|standard)\b": 2,
            r"\b(advanced|complex|sophisticated)\b": 3,
            r"\b(expert|specialized|professional)\b": 4,
            r"\b(cutting-edge|state-of-the-art|bleeding-edge)\b": 5
        }

        # Domain-specific baseline levels
        domain_baselines = {
            "technical": 3,
            "analytical": 2,
            "creative": 1,
            "instructional": 1
        }

        baseline = domain_baselines.get(domain, 1)
        max_level = baseline

        # Check for technical indicators
        for pattern, level in technical_indicators.items():
            if re.search(pattern, text, re.IGNORECASE):
                max_level = max(max_level, level)

        return max_level

    def _build_context_primer(self, analysis: ContextualAnalysis) -> str:
        """
        Builds a context primer based on the analysis
        """
        return f"""Domain Context: {analysis.domain}
Purpose: {analysis.purpose}
Complexity Level: {analysis.complexity}
Technical Level: {analysis.technical_level}/5
Target Audience: {analysis.target_audience}

Key Concepts:
{', '.join(analysis.key_concepts)}

Tone Requirements:
{', '.join(f'{tone} ({priority:.1f})' for tone, priority in analysis.tone_requirements.items())}"""

    def _create_content_structure(self, analysis: ContextualAnalysis) -> Dict[str, List[str]]:
        """
        Creates content structure requirements based on analysis
        """
        common_structure = {
            "Introduction": [
                "Define context and scope",
                "Establish key objectives",
                "Set expectations"
            ],
            "Main Content": [
                "Address key concepts",
                "Maintain consistent technical level",
                "Follow logical progression"
            ],
            "Conclusion": [
                "Summarize key points",
                "Provide next steps or applications",
                "Ensure closure"
            ]
        }

        # Add domain-specific requirements
        if analysis.domain == "technical":
            common_structure["Technical Details"] = [
                "Include implementation specifics",
                "Address edge cases",
                "Provide error handling"
            ]
        elif analysis.domain == "creative":
            common_structure["Style Elements"] = [
                "Maintain consistent voice",
                "Use engaging language",
                "Include descriptive elements"
            ]

        return common_structure
        
    def analyze_context(self, prompt: str, ai_type: str, style: str) -> ContextualAnalysis:
        """Performs deep contextual analysis of the user's prompt"""
        # Identify domain
        domain = self._identify_domain(prompt)
        
        # Analyze purpose and complexity
        purpose = self._extract_purpose(prompt)
        complexity = self._assess_complexity(prompt)
        
        # Extract key concepts and constraints
        key_concepts = self._extract_key_concepts(prompt)
        constraints = self._identify_constraints(prompt)
        
        # Determine audience and tone based on style
        audience = self._infer_target_audience(prompt, style)
        tone_requirements = self._generate_tone_mapping(style, ai_type)
        
        # Assess technical level needed
        technical_level = self._assess_technical_level(prompt, domain)
        
        return ContextualAnalysis(
            domain=domain,
            purpose=purpose,
            complexity=complexity,
            constraints=constraints,
            key_concepts=key_concepts,
            target_audience=audience,
            tone_requirements=tone_requirements,
            technical_level=technical_level
        )
    
    def generate_enhanced_guidelines(self, analysis: ContextualAnalysis) -> EnhancedGuidelines:
        """Generates comprehensive guidelines based on contextual analysis"""
        # Generate content structure requirements
        content_structure = self._create_content_structure(analysis)
        
        # Define style requirements
        style_requirements = self._define_style_requirements(analysis)
        
        # Establish quality criteria
        quality_criteria = self._establish_quality_criteria(analysis)
        
        # Define context preservation rules
        context_preservation = self._define_context_preservation(analysis)
        
        # Specify output format
        output_format = self._specify_output_format(analysis)
        
        return EnhancedGuidelines(
            content_structure=content_structure,
            style_requirements=style_requirements,
            quality_criteria=quality_criteria,
            context_preservation=context_preservation,
            output_format=output_format
        )
    
    def enhance_prompt(self, original_prompt: str, analysis: ContextualAnalysis, 
                      guidelines: EnhancedGuidelines) -> str:
        """Creates an enhanced prompt incorporating analysis and guidelines"""
        # Build context primer
        context_primer = self._build_context_primer(analysis)
        
        # Create instruction set
        instruction_set = self._create_instruction_set(guidelines)
        
        # Generate format specifications
        format_specs = self._generate_format_specs(guidelines.output_format)
        
        # Combine into enhanced prompt
        enhanced_prompt = f"""
{context_primer}

Original Request: {original_prompt}

Instruction Set:
{instruction_set}

Output Specifications:
{format_specs}

Quality Requirements:
- Maintain consistent {analysis.domain} domain expertise throughout
- Adhere to {analysis.complexity} level complexity
- Ensure all key concepts {', '.join(analysis.key_concepts)} are addressed
- Follow specified tone requirements: {self._format_tone_requirements(analysis.tone_requirements)}

Constraints:
{self._format_constraints(analysis.constraints)}
"""
        return enhanced_prompt.strip()
    
    def _identify_domain(self, prompt: str) -> str:
        """Identifies the primary domain of the prompt using pattern matching"""
        domain_scores = {}
        for domain, pattern in self.domain_patterns.items():
            matches = len(re.findall(pattern, prompt.lower()))
            domain_scores[domain] = matches
        
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_purpose(self, prompt: str) -> str:
        """Extracts the primary purpose of the prompt"""
        purpose_patterns = {
            "generation": r"\b(create|generate|make|write)\b",
            "analysis": r"\b(analyze|examine|evaluate)\b",
            "explanation": r"\b(explain|describe|teach)\b",
            "transformation": r"\b(convert|transform|change)\b"
        }
        
        purpose_scores = {purpose: len(re.findall(pattern, prompt.lower()))
                         for purpose, pattern in purpose_patterns.items()}
        return max(purpose_scores.items(), key=lambda x: x[1])[0]
    
    def _assess_complexity(self, prompt: str) -> str:
        """Assesses the complexity level of the requested task"""
        complexity_scores = {}
        for level, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in prompt.lower())
            complexity_scores[level] = score
        
        return max(complexity_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_key_concepts(self, prompt: str) -> List[str]:
        """Extracts key concepts from the prompt using NLP techniques"""
        # This is a simplified version - in practice, you might want to use
        # more sophisticated NLP techniques like keyword extraction
        words = prompt.lower().split()
        # Remove common words and keep significant terms
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to"}
        key_concepts = [word for word in words if word not in common_words and len(word) > 3]
        return list(set(key_concepts))  # Remove duplicates
    
    def _create_instruction_set(self, guidelines: EnhancedGuidelines) -> str:
        """Creates a detailed instruction set based on guidelines"""
        instructions = []
        
        # Add content structure instructions
        for section, requirements in guidelines.content_structure.items():
            instructions.append(f"{section}:")
            instructions.extend([f"- {req}" for req in requirements])
        
        # Add style requirements
        instructions.append("\nStyle Requirements:")
        for aspect, requirement in guidelines.style_requirements.items():
            instructions.append(f"- {aspect}: {requirement}")
        
        return "\n".join(instructions)
    
    def _generate_format_specs(self, output_format: Dict[str, str]) -> str:
        """Generates detailed format specifications"""
        specs = ["Format Requirements:"]
        for element, specification in output_format.items():
            specs.append(f"- {element}: {specification}")
        return "\n".join(specs)
    
    def _format_tone_requirements(self, tone_reqs: Dict[str, float]) -> str:
        """Formats tone requirements into a readable string"""
        return ", ".join([f"{tone} (priority: {priority})" 
                         for tone, priority in tone_reqs.items()])
    
    def _format_constraints(self, constraints: List[str]) -> str:
        """Formats constraints into a readable string"""
        return "\n".join([f"- {constraint}" for constraint in constraints])

class PromptEnhancementSystem:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.processor = AdvancedPromptProcessor(logger)
    
    def process_prompt(self, prompt: str, ai_type: str, style: str) -> Dict[str, Any]:
        """Main processing pipeline for prompt enhancement"""
        try:
            # Perform contextual analysis
            analysis = self.processor.analyze_context(prompt, ai_type, style)
            self.logger.debug(f"Contextual analysis completed: {analysis}")
            
            # Generate enhanced guidelines
            guidelines = self.processor.generate_enhanced_guidelines(analysis)
            self.logger.debug(f"Enhanced guidelines generated: {guidelines}")
            
            # Create enhanced prompt
            enhanced_prompt = self.processor.enhance_prompt(prompt, analysis, guidelines)
            self.logger.debug(f"Enhanced prompt created: {enhanced_prompt}")
            
            return {
                "enhanced_prompt": enhanced_prompt,
                "analysis": analysis.__dict__,
                "guidelines": guidelines.__dict__
            }
            
        except Exception as e:
            self.logger.error(f"Error in prompt enhancement: {str(e)}")
            raise


@dataclass
class ProcessedPrompt:
    prompt: str
    categories: str
    tokens: int
    corrections_made: Dict[str, str]

class BasePreprocessor(ABC):
    """Abstract base class for prompt preprocessing"""
    
    @abstractmethod
    def process_prompt(self, raw_prompt: str, category_data: Dict[str, Any]) -> ProcessedPrompt:
        pass
    
    def clean_text(self, text: str) -> str:
        """Shared text cleaning functionality"""
        pass

class LegacyPromptPreprocessor(BasePreprocessor):
    """Original preprocessor with style-focused processing"""
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

class EnhancedPromptPreprocessor(BasePreprocessor):
    """Advanced preprocessor with domain and intent analysis"""
    def __init__(self, logger: Logger):
        self.logger = logger
        self.spell = SpellChecker()
        
        # Domain identifiers to help understand context
        self.domain_markers = {
            "email": { "draft", "compose", "email", "mail", "message", "response"},
            "code": {"function", "code", "program", "script", "algorithm", "debug"},
            "creative": {"story", "article", "blog", "creative", "write", "content"},
            "analysis": {"analyze", "research", "investigate", "study", "examine"},
            "technical": {"technical", "documentation", "guide", "manual", "specification"}
        }
        
        # Intent classifiers
        self.intent_patterns = {
            "creation": {"create", "make", "generate", "write", "develop"},
            "modification": {"modify", "change", "update", "improve", "enhance"},
            "analysis": {"analyze", "examine", "review", "assess", "evaluate"},
            "explanation": {"explain", "describe", "elaborate", "clarify"}
        }
        
        # Task complexity indicators
        self.complexity_markers = {
            "simple": {"simple", "basic", "quick", "brief"},
            "detailed": {"detailed", "comprehensive", "thorough", "complete"},
            "advanced": {"advanced", "complex", "sophisticated", "expert"}
        }
    def process_prompt(self, raw_prompt: str, category_data: Dict[str, Any]) -> ProcessedPrompt:
        # Clean and normalize text
        cleaned_text = self._basic_cleanup(raw_prompt)
        
        # Extract key components
        analysis = self._analyze_prompt(cleaned_text)
        
        # Structure the prompt
        structured_prompt = self._structure_prompt(cleaned_text, analysis)
        
        return ProcessedPrompt(
            prompt=structured_prompt,
            categories=str(analysis),
            tokens=len(cleaned_text.split()),
            corrections_made={}  # No corrections in enhanced processor
        )
    def _structure_prompt(self, text: str, analysis: Dict) -> str:
        """
        Create structured prompt format optimized for LLM processing
        """
        # Create the base structure
        structured = (
            f"TASK ANALYSIS:\n"
            f"Domain: {analysis['domain']}\n"
            f"Intent: {', '.join(analysis['intents'])}\n"
            f"Complexity: {analysis['complexity']}\n\n"
            f"ORIGINAL CONTENT:\n"
            f"{text}\n"
        )
        
        # Add constraints if they exist
        if analysis['constraints']:
            constraints_text = "CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in analysis['constraints'])
            structured += f"\n{constraints_text}"
        
        return structured.strip()


    def preprocess(self, raw_prompt: str) -> Tuple[Dict, str]:
        """
        Main preprocessing pipeline that prepares prompts for enhancement
        """
        # Clean and normalize text
        cleaned_text = self._basic_cleanup(raw_prompt)
        
        # Extract key components
        analysis = self._analyze_prompt(cleaned_text)
        
        # Structure the prompt for LLM processing
        structured_prompt = self._structure_prompt(cleaned_text, analysis)
        
        return analysis, structured_prompt

    def _basic_cleanup(self, text: str) -> str:
        """Basic text normalization"""
        # Remove excessive punctuation and spaces
        text = re.sub(r'[!.?]+(?=[!.?])', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common filler phrases
        fillers = {"please", "if possible", "I want", "I need", "could you"}
        for filler in fillers:
            text = re.sub(rf'\b{filler}\b', '', text, flags=re.IGNORECASE)
            
        return text.strip()

    def _analyze_prompt(self, text: str) -> Dict:
        """
        Analyze prompt to understand domain, intent, and complexity
        """
        words = text.lower().split()
        word_set = set(words)
        
        # Identify primary domain
        domain_scores = {
            domain: len(word_set.intersection(markers)) 
            for domain, markers in self.domain_markers.items()
        }
        primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
        
        # Identify user intent
        intents = [
            intent for intent, markers in self.intent_patterns.items()
            if word_set.intersection(markers)
        ]
        
        # Assess complexity
        complexity = "simple"  # default
        for level, markers in self.complexity_markers.items():
            if word_set.intersection(markers):
                complexity = level
                break
        
        # Extract any specific requirements or constraints
        constraints = []
        if "must" in text.lower():
            constraints.extend(re.findall(r'must\s+([^,.;]+)', text.lower()))
        
        return {
            "domain": primary_domain,
            "intents": intents or ["creation"],  # default to creation
            "complexity": complexity,
            "constraints": constraints,
            "word_count": len(words)
        }

def _structure_prompt(self, text: str, analysis: Dict) -> str:
    """
    Create structured prompt format optimized for LLM processing
    """
    # Create the base structure
    structured = (
        f"TASK ANALYSIS:\n"
        f"Domain: {analysis['domain']}\n"
        f"Intent: {', '.join(analysis['intents'])}\n"
        f"Complexity: {analysis['complexity']}\n\n"
        f"ORIGINAL CONTENT:\n"
        f"{text}\n"
    )
    
    # Add constraints if they exist
    if analysis['constraints']:
        constraints_text = "CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in analysis['constraints'])
        structured += f"\n{constraints_text}"
    
    return structured.strip()

class CompositePreprocessor:
    """Combines multiple preprocessing strategies for comprehensive analysis"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.legacy_processor = LegacyPromptPreprocessor(logger)
        self.enhanced_processor = EnhancedPromptPreprocessor(logger)
    
    def process(self, raw_prompt: str, category_data: Dict[str, Any]) -> Tuple[ProcessedPrompt, Dict]:
        """
        Complete preprocessing pipeline combining style, domain, and intent analysis
        """
        # Process with legacy processor for style and basic cleaning
        basic_processed = self.legacy_processor.process_prompt(raw_prompt, category_data)
        
        # Process with enhanced processor for domain and intent
        analysis, structured = self.enhanced_processor.preprocess(basic_processed.prompt)
        
        return basic_processed, {
            "analysis": analysis,
            "structured_prompt": structured,
            "tokens": basic_processed.tokens
        }
    

class PromptParameters:
    """Manages and combines different parameter sets for LLM requests"""
    
    def __init__(self, style: str, domain: str, complexity: str):
        self.style = style
        self.domain = domain
        self.complexity = complexity
        
    def get_combined_parameters(self) -> Dict:
        """
        Combines style, domain, and complexity parameters intelligently
        """
        base_params = get_style_parameters(self.style)
        
        # Adjust parameters based on domain
        domain_adjustments = {
            "code": {
                "temperature": lambda x: x * 0.8,  # Reduce creativity for code
                "top_p": lambda x: x * 0.9
            },
            "creative": {
                "temperature": lambda x: x * 1.2,  # Increase creativity
                "presence_penalty": lambda x: x * 1.3
            }
        }
        
        # Apply domain-specific adjustments
        if self.domain in domain_adjustments:
            for param, adjust_func in domain_adjustments[self.domain].items():
                if param in base_params:
                    base_params[param] = adjust_func(base_params[param])
                    
        # Adjust based on complexity
        complexity_adjustments = {
            "simple": {"max_tokens": 900},
            "detailed": {"max_tokens": 900},
            "advanced": {"max_tokens": 900}
        }
        
        base_params.update(complexity_adjustments.get(self.complexity, {}))
        
        return base_params




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


def get_style_parameters(writing_style: str) -> dict:
    """
    Returns optimized Llama API parameters based on the writing style.
    Each parameter set is specifically tuned for the style characteristics.
    
    Args:
        writing_style (str): The selected writing style ('descriptive', 'creative', 
                           'professional', or 'concise')
    
    Returns:
        dict: Complete parameter configuration for the Llama API
    """
    # Base parameters that apply to all styles
    base_params = {
        "stream": False,
        "min_tokens": 50,  # Ensure minimum coherent response
    }
    
    style_params = {
        # Descriptive Style Parameters
        # Optimized for rich, detailed descriptions with vivid imagery
        "descriptive": {
            **base_params,
            "max_tokens": 2000,           # Allow for detailed descriptions
            "temperature": 0.75,         # Moderate creativity for vivid details
            "top_p": 0.92,              # Broader vocabulary for rich descriptions
            "top_k": 45,                # Diverse word choice
            "presence_penalty": 0.4,     # Reduce repetition
            "frequency_penalty": 0.3,    # Encourage varied vocabulary
            "repetition_penalty": 1.2,   # Prevent description patterns
            "length_penalty": 1.1,       # Slightly favor longer descriptions
            "sequence_bias": {
                "vivid": 1.2,           # Boost vivid descriptive words
                "detailed": 1.2,
                "imagine": 1.1
            }
        },
        
        # Creative Style Parameters
        # Optimized for unique and imaginative elements
        "creative": {
            **base_params,
            "max_tokens": 600,           # Balance between length and focus
            "temperature": 0.85,         # High creativity
            "top_p": 0.95,              # Very broad vocabulary
            "top_k": 50,                # Maximum word diversity
            "presence_penalty": 0.6,     # Strongly discourage repetition
            "frequency_penalty": 0.5,    # Strongly encourage unique words
            "repetition_penalty": 1.3,   # Heavily prevent patterns
            "length_penalty": 1.0,       # Neutral length
            "sequence_bias": {
                "unique": 1.3,          # Boost creative elements
                "innovative": 1.2,
                "imaginative": 1.2
            }
        },
        
        # Professional Style Parameters
        # Optimized for formal and business-appropriate tone
        "professional": {
            **base_params,
            "max_tokens": 500,           # Controlled length
            "temperature": 0.45,         # Lower creativity for consistency
            "top_p": 0.85,              # Controlled vocabulary
            "top_k": 35,                # More focused word choice
            "presence_penalty": 0.2,     # Light repetition control
            "frequency_penalty": 0.1,    # Slight vocabulary variation
            "repetition_penalty": 1.1,   # Light pattern control
            "length_penalty": 0.95,      # Slightly favor conciseness
            "sequence_bias": {
                "professional": 1.2,     # Boost formal language
                "formal": 1.2,
                "business": 1.1
            }
        },
        
        # Concise Style Parameters
        # Optimized for brief, clear, essential content
        "concise": {
            **base_params,
            "max_tokens": 900,           # Limited length
            "temperature": 0.35,         # Low creativity for clarity
            "top_p": 0.8,               # Focused vocabulary
                                        # Very focused word choice
            "presence_penalty": 0.15,    # Minimal repetition control
            "frequency_penalty": 0.1,    # Minimal vocabulary variation
            "repetition_penalty": 1.15,  # Light pattern control
            "length_penalty": 0.85,      # Favor brevity
            "sequence_bias": {
                "clear": 1.3,           # Boost clarity and brevity
                "concise": 1.3,
                "brief": 1.2
            }
        }
    }
    
    return style_params.get(writing_style, style_params["professional"])

# First, let's create a new class for request analysis and guideline generation
class RequestAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger
        # Task type identifiers
        self.task_types = {
            "search": {
                "markers": {"find", "search", "look for", "what are", "who is", "where is", "when"},
                "requirements": {
                    "time_relevance": True,
                    "source_quality": True,
                    "fact_verification": True
                }
            },
            "document_analysis": {
                "markers": {"analyze", "review", "examine", "summarize", "extract"},
                "requirements": {
                    "depth": True,
                    "key_metrics": True,
                    "insights": True
                }
            },
            "code_generation": {
                "markers": {"code", "function", "program", "script", "algorithm"},
                "requirements": {
                    "language": True,
                    "documentation": True,
                    "testing": True
                }
            },
            "creative_writing": {
                "markers": {"write", "create", "story", "article", "blog"},
                "requirements": {
                    "style": True,
                    "structure": True,
                    "tone": True
                }
            }
        }

    def analyze_request(self, text: str) -> Dict[str, Any]:
        """Analyze the request to determine type and requirements"""
        words = text.lower().split()
        word_set = set(words)

        # Identify task type
        task_scores = {}
        for task, details in self.task_types.items():
            score = len(word_set.intersection(details["markers"]))
            task_scores[task] = score

        primary_task = max(task_scores.items(), key=lambda x: x[1])[0] if any(task_scores.values()) else "general"

        return {
            "task_type": primary_task,
            "requirements": self.task_types.get(primary_task, {}).get("requirements", {}),
            "context_words": list(word_set)
        }

    def generate_guidelines(self, analysis: Dict[str, Any]) -> str:
        """Generate specific guidelines based on request analysis"""
        task_type = analysis["task_type"]
        
        guidelines = {
            "search": """
Guidelines for Search Query Enhancement:
1. Temporal Context:
   - Specify time period relevance
   - Include recency requirements
   - Note any historical context needs

2. Source Requirements:
   - Define source authority level
   - Specify verification requirements
   - Include diversity of sources

3. Result Structure:
   - Define ordering criteria
   - Specify result format
   - Include ranking parameters
""",
            "document_analysis": """
Guidelines for Document Analysis Enhancement:
1. Analysis Depth:
   - Specify level of detail required
   - Define key areas of focus
   - Include comparative requirements

2. Output Structure:
   - Define format requirements
   - Specify section organization
   - Include visualization needs

3. Insight Requirements:
   - Define key metric focus
   - Specify trend analysis needs
   - Include correlation requirements
""",
            "code_generation": """
Guidelines for Code Generation Enhancement:
1. Technical Specifications:
   - Define language and version
   - Specify framework requirements
   - Include performance criteria

2. Documentation Requirements:
   - Specify documentation style
   - Define comment density
   - Include example requirements

3. Quality Standards:
   - Define testing requirements
   - Specify error handling
   - Include edge case coverage
""",
            "creative_writing": """
Guidelines for Creative Content Enhancement:
1. Style Requirements:
   - Define tone and voice
   - Specify language level
   - Include stylistic elements

2. Structure Specifications:
   - Define format requirements
   - Specify section organization
   - Include flow requirements

3. Content Elements:
   - Define required components
   - Specify character/plot elements
   - Include thematic requirements
"""
        }.get(task_type, """
Guidelines for General Enhancement:
1. Clarity and Structure:
   - Ensure clear organization
   - Maintain logical flow
   - Include all necessary context

2. Content Requirements:
   - Define scope clearly
   - Specify detail level
   - Include all relevant elements

3. Quality Standards:
   - Ensure accuracy
   - Maintain consistency
   - Include verification points
""")
        
        return guidelines

def generate_contextual_guidelines(prompt: str) -> str:
    """
    First API call to generate context-specific guidelines based on deep analysis of user input
    """
    try:
        system_context = """You are an advanced AI analysis system specializing in understanding user requests and generating detailed guidelines. Your task is to:

1. Perform Deep Content Analysis:
   - Understand the core domain and technical requirements
   - Identify implicit and explicit needs
   - Recognize context and dependencies
   - Map potential edge cases and challenges

2. Generate Domain-Specific Guidelines:
   - Create detailed, structured guidelines
   - Focus on best practices and standards
   - Include technical specifications
   - Address potential pitfalls
   - Set clear quality benchmarks

Your output should be a comprehensive markdown document that can guide an AI system in providing optimal responses."""

        analysis_prompt = f"""Analyze this user request and create detailed technical guidelines:

User Request: "{prompt}"

Perform a comprehensive analysis considering:
1. Domain Expertise Required
2. Technical Requirements
3. Best Practices
4. Quality Standards
5. Edge Cases
6. Implementation Considerations

Generate thorough guidelines that would help an AI system provide the most accurate and helpful response.
Format your response as a detailed markdown document with clear sections and explanatory subsections.
Focus on technical accuracy and completeness."""

        # Make first API call for guidelines
        guidelines_request = {
            "model": "llama3.2-11b-vision",
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": analysis_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95
        }

        guidelines_response = llama.run(guidelines_request)
        guidelines = guidelines_response.json()['choices'][0]['message']['content']
        logger.debug(f"Generated Guidelines:\n{guidelines}")
        
        return guidelines

    except Exception as e:
        logger.error(f"Guidelines generation error: {str(e)}")
        raise


# New API endpoint for guideline generation
@app.route('/analyze', methods=['POST'])
def analyze_request():
    try:
        form_data = request.form.get('data')
        if not form_data:
            return jsonify({"error": "No data provided"}), 400

        data = json.loads(form_data)
        if 'prompt' not in data:
            return jsonify({"error": "No prompt provided"}), 400

        analyzer = RequestAnalyzer(logger)
        analysis = analyzer.analyze_request(data['prompt'])
        guidelines = analyzer.generate_guidelines(analysis)

        return jsonify({
            "analysis": analysis,
            "guidelines": guidelines
        })

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500


def call_llama_api(prompt: str, writing_style: str, guidelines: str) -> str:
    """
    Enhanced Llama API call with advanced prompt engineering optimized for LLM processing patterns.
    Implements context layering, clear instruction boundaries, and style-specific optimizations.
    """
    try:
        # Get optimized parameters for the writing style
        style_params = get_style_parameters(writing_style)
        
        # Create a context-rich system message that guides the LLM's processing
        system_context = f"""You are an expert prompt engineer with deep expertise in AI/ML and natural language processing. Your specialty is crafting prompts that align with LLM processing patterns and contextual understanding.

Specific Guidelines for this Request:
{guidelines}

Core Capabilities:
1. Context Analysis: You excel at identifying key semantic elements and their relationships
2. Pattern Recognition: You understand how LLMs process and generate text sequences
3. Style Integration: You specialize in {writing_style} content, maintaining consistent tone and structure
4. Output Control: You ensure generated content strictly adheres to specified formats and requirements

Process Approach:
1. Analyze input context for key concepts and relationships
2. Apply {writing_style} style parameters while maintaining semantic coherence
3. Structure output to maximize contextual relevance and minimize hallucination
4. Ensure each generated prompt maintains contextual consistency with the source concept

Remember: Focus on semantic preservation and contextual alignment in all outputs."""

        # Enhanced user message structure with contextual framing
        enhanced_prompt = f"""Context Analysis Task:
Original Concept: {prompt}
Required Style: {writing_style}

Task Requirements:
1. Generate three semantically distinct but conceptually aligned prompts
2. Each prompt must maintain full contextual relevance to the original concept
3. Apply {writing_style} style characteristics while preserving core meaning
4. Ensure each variation explores a unique aspect while maintaining semantic coherence

Output Specifications:
- Maintain consistent semantic alignment
- Preserve key contextual elements
- Apply style-specific language patterns
- Ensure format compliance

Return strictly formatted JSON object:
{{
    "prompts": [
        {{"prompt": "<contextually enhanced version 1>"}},
        {{"prompt": "<contextually enhanced version 2>"}},
        {{"prompt": "<contextually enhanced version 3>"}}
    ]
}}

Important:
- Each prompt must maintain complete semantic alignment with original context
- No deviation from core concept meaning
- Strict adherence to specified format
- No additional commentary or explanations"""

        api_request_json = {
            "model": "llama3.2-11b-vision",
            "messages": [
                {
                    "role": "system", 
                    "content": system_context
                },
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ],
            **style_params  # Apply style-specific parameters
        }
        
        logger.debug(f"Sending request to Llama API: {api_request_json}")
        response = llama.run(api_request_json)
        response_json = response.json()
        logger.debug(f"Received response from Llama API: {response_json}")
        
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            raise Exception("No completion found in response")
            
    except Exception as e:
        logger.error(f"Llama API error: {str(e)}")
        raise
    
def validate_request_data(form_data: dict) -> Tuple[dict, Optional[str]]:
    """
    Validates and processes incoming request data.
    Returns (data_dict, error_message). If error_message is None, validation passed.
    """
    try:
        if not form_data:
            return None, "No data provided"
            
        data = json.loads(form_data)
        if 'prompt' not in data:
            return None, "No prompt provided"
            
        # Validate and set defaults for required fields
        data['AIType'] = data.get('AIType', 'default')
        data['style'] = data.get('style', 'professional')
        
        return data, None
        
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON format: {str(e)}"

def process_prompt_enhancement(prompt: str, ai_type: str, writing_style: str, preprocessor: CompositePreprocessor) -> Tuple[Dict, Optional[str]]:
    """
    Enhanced two-step prompt processing with guidelines integration
    """
    try:
        # Step 1: Generate contextual guidelines
        logger.debug("Generating contextual guidelines...")
        guidelines = generate_contextual_guidelines(prompt)
        
        # Step 2: Process through regular preprocessing pipeline
        logger.debug("Processing through preprocessing pipeline...")
        processed_prompt, analysis_data = preprocessor.process(prompt, {})
        
        # Combine the analysis with guidelines
        combined_context = {
            "guidelines": guidelines,
            "analysis": analysis_data["analysis"],
            "structured_prompt": analysis_data["structured_prompt"]
        }
        
        # Step 3: Make the final API call with enhanced context
        logger.debug("Making final API call with combined context...")
        response_text = call_llama_api(
            prompt=processed_prompt.prompt,
            writing_style=writing_style,
            guidelines=guidelines  # Pass the generated guidelines
        )
        
        normalized_response = normalize_json_response(response_text)
        
        # Prepare comprehensive response
        response_data = {
            "response": json.dumps(normalized_response, ensure_ascii=False),
            "corrections": processed_prompt.corrections_made if processed_prompt.corrections_made else None,
            "metadata": {
                "ai_type": ai_type,
                "style": writing_style,
                "analysis": analysis_data,
                "guidelines_used": guidelines,  # Include guidelines in metadata
                "token_count": processed_prompt.tokens
            }
        }
        
        logger.debug("Successfully processed prompt with guidelines")
        return response_data, None
        
    except Exception as e:
        logger.error(f"Error in prompt enhancement: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, f"Prompt processing error: {str(e)}"

@app.route('/process', methods=['POST'])
def process_request():
    """
    Main request handler for prompt enhancement endpoint.
    Coordinates validation, preprocessing, and response generation.
    """
    try:
        logger.debug(f"Received request: {request.form}")
        
        # Validate API configuration
        if not llama:
            return jsonify({"error": "Llama API not properly configured"}), 500
        
        # Validate request data
        form_data = request.form.get('data')
        data, validation_error = validate_request_data(form_data)
        if validation_error:
            logger.error(f"Validation error: {validation_error}")
            return jsonify({"error": validation_error}), 400

        # Initialize enhancement system
        enhancement_system = PromptEnhancementSystem(logger)

        # Process the prompt
        result = enhancement_system.process_prompt(
            prompt=data['prompt'],
            ai_type=data['AIType'],
            style=data['style']
        )

        # Use the enhanced prompt in your Llama API call
        response_text = call_llama_api(
            prompt=result['enhanced_prompt'],
            writing_style=data['style'],
            guidelines=json.dumps(result['guidelines'])
        )
        
        normalized_response = normalize_json_response(response_text)
        
        return jsonify({
            "response": normalized_response,
            "analysis": result['analysis'],
            "guidelines": result['guidelines']
        })
        
        # # Initialize preprocessor
        # preprocessor = CompositePreprocessor(logger)
        
        # # Process the prompt
        # response_data, processing_error = process_prompt_enhancement(
        #     prompt=data['prompt'],
        #     ai_type=data['AIType'],
        #     writing_style=data['style'],
        #     preprocessor=preprocessor
        # )
        
        # if processing_error:
        #     logger.error(f"Processing error: {processing_error}")
        #     return jsonify({"error": processing_error}), 500
            
        # logger.debug("Successfully processed request")
        # return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in process_request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500




if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    app.run(host='0.0.0.0', port=2000, debug=True)
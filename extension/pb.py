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

#     def enhance_prompt(self, original_prompt: str, analysis: ContextualAnalysis, 
#                       guidelines: EnhancedGuidelines) -> str:
#         """Creates an enhanced prompt incorporating analysis and guidelines"""
#         # Build context primer
#         context_primer = self._build_context_primer(analysis)
        
#         # Create instruction set
#         instruction_set = self._create_instruction_set(guidelines)
        
#         # Generate format specifications
#         format_specs = self._generate_format_specs(guidelines.output_format)
        
#         # Combine into enhanced prompt
#         enhanced_prompt = f"""
# {context_primer}

# Original Request: {original_prompt}

# Instruction Set:
# {instruction_set}

# Output Specifications:
# {format_specs}

# Quality Requirements:
# - Maintain consistent {analysis.domain} domain expertise throughout
# - Adhere to {analysis.complexity} level complexity
# - Ensure all key concepts {', '.join(analysis.key_concepts)} are addressed
# - Follow specified tone requirements: {self._format_tone_requirements(analysis.tone_requirements)}

# Constraints:
# {self._format_constraints(analysis.constraints)}
# """
#         return enhanced_prompt.strip()

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

     # 3. Style and Tone Methods
    def _define_style_requirements(self, analysis: ContextualAnalysis) -> Dict[str, str]:
        """
    Defines detailed style requirements based on context analysis
    """
        # Base style requirements for all content
        style_requirements = {
        "language_level": self._determine_language_level(analysis),
        "tone": self._determine_tone_style(analysis),
        "formatting": self._determine_formatting_style(analysis),
        "terminology": self._determine_terminology_requirements(analysis)
        }
    
    # Add domain-specific style requirements
        domain_specific = self._get_domain_specific_style(analysis.domain, analysis.technical_level)
        style_requirements.update(domain_specific)
    
        return style_requirements

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

    def _determine_language_level(self, analysis: ContextualAnalysis) -> str:
        """
        Determines appropriate language level based on audience and technical level
        """
    # Map technical level to language complexity
        level_mapping = {
        1: "simple and accessible",
        2: "moderately technical",
        3: "technical with clear explanations",
        4: "highly technical",
        5: "expert-level technical"
        }
    
        base_level = level_mapping.get(analysis.technical_level, "moderately technical")
    
    # Adjust based on target audience
        audience_adjustments = {
        "technical": " with industry-standard terminology",
        "general": " with simplified explanations",
        "beginner": " with detailed explanations of technical terms",
        "expert": " assuming domain expertise"
        }
    
        audience_modifier = audience_adjustments.get(analysis.target_audience, "")
        return base_level + audience_modifier

    # 4. Format and Structure Methods
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

    # 5. Output Formatting Methods
    def _format_enhanced_prompt(self, original_prompt: str, context_primer: str,
                              instruction_set: str, format_specs: str,
                              analysis: ContextualAnalysis,
                              guidelines: EnhancedGuidelines) -> str:
        """Helper method to format the final enhanced prompt"""
        return f"""
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
""".strip()

    def _format_tone_requirements(self, tone_reqs: Dict[str, float]) -> str:
        """Formats tone requirements into a readable string"""
        return ", ".join([f"{tone} (priority: {priority})" 
                         for tone, priority in tone_reqs.items()])

    def _format_constraints(self, constraints: List[str]) -> str:
        """Formats constraints into a readable string"""
        return "\n".join([f"- {constraint}" for constraint in constraints])
    
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

    def _determine_tone_style(self, analysis: ContextualAnalysis) -> str:
        """Determines appropriate tone based on analysis"""
         # Get the primary tone (highest priority)
        primary_tone = max(analysis.tone_requirements.items(), key=lambda x: x[1])[0]
    
        tone_styles = {
        "formal": "maintain professional and academic tone",
        "conversational": "use engaging and approachable language",
        "technical": "focus on precision and clarity",
        "creative": "employ expressive and imaginative language",
        "precise": "use clear and unambiguous language",
        "authoritative": "maintain expert voice and credibility"
    }
    
        return tone_styles.get(primary_tone, "maintain clear and professional tone")

    def _determine_formatting_style(self, analysis: ContextualAnalysis) -> str:
        """Determines appropriate formatting style"""
        domain_formats = {
        "technical": "use clear headings and technical illustrations",
        "creative": "employ narrative structure with engaging formatting",
        "analytical": "utilize structured sections with clear data presentation",
        "instructional": "implement step-by-step format with examples"
        }
    
        base_format = domain_formats.get(analysis.domain, "maintain clear section organization")
    
    # Add complexity-specific formatting
        complexity_formats = {
        "basic": " with straightforward layout",
        "intermediate": " with moderate detail separation",
        "advanced": " with comprehensive section breakdown"
        }
    
        return base_format + complexity_formats.get(analysis.complexity, "")

    def _determine_terminology_requirements(self, analysis: ContextualAnalysis) -> str:
        """Determines terminology requirements"""
        if analysis.domain == "technical":
            if analysis.target_audience in ["beginner", "general"]:
                return "explain technical terms, use consistent terminology"
            else:
                return "use industry-standard technical terminology"
        elif analysis.domain == "creative":
            return "use engaging vocabulary appropriate for target audience"
        elif analysis.domain == "analytical":
            return "employ precise technical terms with clear definitions"
        else:
            return "maintain consistent terminology throughout"

    def _get_domain_specific_style(self, domain: str, technical_level: int) -> Dict[str, str]:
        """Provides domain-specific style requirements"""
        domain_styles = {
        "technical": {
            "code_style": "follow language-specific conventions and best practices",
            "documentation": "include clear comments and documentation" if technical_level > 2 else "provide basic documentation"
        },
        "creative": {
            "narrative_style": "maintain consistent voice and perspective",
            "descriptive_elements": "use vivid and engaging descriptions"
        },
        "analytical": {
            "data_presentation": "present analysis clearly with supporting evidence",
            "logical_flow": "maintain clear analytical progression"
        }
        }
    
        return domain_styles.get(domain, {
        "general_style": "maintain clear and consistent presentation",
        "organization": "use logical content structure"
    })

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

    def _establish_quality_criteria(self, analysis: ContextualAnalysis) -> List[str]:
        """Establishes quality criteria based on the analysis"""
        # Base quality criteria for all content
        base_criteria = [
        "Content is well-organized and structured",
        "Language is appropriate for the target audience",
        "Maintains consistent tone and style throughout",
        f"Adheres to {analysis.complexity} level complexity"
        ]
    
       # Domain-specific quality criteria
        domain_criteria = {
            "technical": [
                "Technical accuracy and precision",
                "Clear and correct use of technical terms",
                "Proper documentation and examples",
                "Follows industry best practices"
            ],
            "creative": [
                "Engaging and original content",
                "Consistent narrative voice",
                "Effective use of creative elements",
                "Clear and compelling structure"
            ],
            "analytical": [
                "Logical flow of analysis",
                "Well-supported conclusions",
                "Clear presentation of data",
                "Comprehensive coverage of key points"
            ],
            "instructional": [
                "Clear learning progression",
                "Effective examples and explanations",
                "Appropriate level of detail",
                "Practical applications included"
            ]
        }
    
    # Add domain-specific criteria if available
        if analysis.domain in domain_criteria:
            base_criteria.extend(domain_criteria[analysis.domain])
    
    # Add audience-specific criteria
        if analysis.target_audience:
            audience_criteria = {
               "technical": ["Meets professional technical standards"],
               "beginner": ["Concepts are thoroughly explained"],
               "expert": ["Advanced concepts are appropriately covered"],
               "general": ["Content is accessible and clear"]
            }
            if analysis.target_audience in audience_criteria:
                base_criteria.extend(audience_criteria[analysis.target_audience])
    
        return base_criteria

    def _define_context_preservation(self, analysis: ContextualAnalysis) -> List[str]:
        """Defines rules for preserving context throughout the content"""
        preservation_rules = [
           f"Maintain consistent {analysis.domain} domain expertise level",
           f"Keep technical level appropriate for {analysis.target_audience}",
        "Preserve key concepts and terminology"
        ]
    
    # Add complexity-specific rules
        if analysis.complexity == "advanced":
           preservation_rules.extend([
            "Maintain advanced concept relationships",
            "Preserve technical depth and precision",
            "Ensure complex ideas are properly connected"
           ])
        elif analysis.complexity == "intermediate":
           preservation_rules.extend([
            "Balance technical depth with clarity",
            "Maintain consistent level of detail",
            "Ensure concepts build progressively"
           ])
        else:  # basic
           preservation_rules.extend([
            "Keep explanations clear and straightforward",
            "Use consistent basic terminology",
            "Maintain focus on core concepts"
           ])
    
    # Add tone-specific rules
        for tone, priority in analysis.tone_requirements.items():
           if priority > 0.7:  # Only include high-priority tones
               preservation_rules.append(f"Maintain {tone} tone throughout")
    
        return preservation_rules

    def _specify_output_format(self, analysis: ContextualAnalysis) -> Dict[str, str]:
        """Specifies output format requirements based on analysis"""
        # Base format specifications
        format_specs = {
            "structure": "Clear sections with logical progression",
            "formatting": "Consistent formatting throughout",
            "language": f"Appropriate for {analysis.target_audience} audience"
        }
    
        # Add domain-specific format requirements
        domain_formats = {
            "technical": {
                "code_blocks": "Properly formatted and commented",
                "technical_diagrams": "Clear and well-labeled",
                "documentation": "Comprehensive and structured"
            },
            "creative": {
                "narrative_structure": "Engaging flow and progression",
                "stylistic_elements": "Consistent creative elements",
                "formatting": "Enhances readability and engagement"
            },
            "analytical": {
                "data_presentation": "Clear and organized",
                "analysis_structure": "Logical flow with clear conclusions",
                "citations": "Properly formatted references"
            },
            "instructional": {
                "lesson_structure": "Clear learning progression",
                "examples": "Well-formatted and relevant",
                "practice_elements": "Clearly distinguished from content"
            }
        }
    
        if analysis.domain in domain_formats:
            format_specs.update(domain_formats[analysis.domain])
        
        # Add complexity-specific format requirements
        complexity_formats = {
            "basic": {
                "layout": "Simple and clear structure",
                "sections": "Well-defined basic sections"
            },
            "intermediate": {
                "layout": "Balanced structure with clear hierarchies",
                "sections": "Organized with subsections as needed"
            },
            "advanced": {
                "layout": "Sophisticated structure with detailed organization",
                "sections": "Complex hierarchical organization"
            }
        }
        
        if analysis.complexity in complexity_formats:
            format_specs.update(complexity_formats[analysis.complexity])
        
        return format_specs

        
    
    
    
  
    
    
    
    
    
    
    
    
    
    
    
    
    
    

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

class EnhancedLlamaHandler:
    def __init__(self, logger: Logger):
        self.logger = logger

    def _process_parameter_recommendations(self, parameter_json: Dict) -> Dict[str, Any]:
        """
        Process and validate parameter recommendations.
        """
        
        try:
            # Extract core parameters with defaults
            processed_params = {
                "temperature": float(parameter_json.get("temperature", {}).get("value", 0.7)),
                "top_p": float(parameter_json.get("top_p", {}).get("value", 0.9)),
                "max_tokens": int(parameter_json.get("max_tokens", {}).get("value", 2000)),
                "presence_penalty": float(parameter_json.get("presence_penalty", {}).get("value", 0.0)),
                "frequency_penalty": float(parameter_json.get("frequency_penalty", {}).get("value", 0.0))
            }

            # Validate ranges
            processed_params["temperature"] = min(max(processed_params["temperature"], 0.0), 1.0)
            processed_params["top_p"] = min(max(processed_params["top_p"], 0.0), 1.0)
            processed_params["max_tokens"] = min(max(processed_params["max_tokens"], 50), 4000)

            return processed_params

        except Exception as e:
            self.logger.error(f"Parameter processing failed: {str(e)}")
            return self._get_default_parameters()

    def _get_default_parameters(self) -> Dict[str, Any]:
       """
       Returns default parameters if optimization fails.
       """
       return {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2000,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
       }

    def generate_contextual_guidelines(self, prompt: str, analysis: Dict[str, Any], ai_type: str, style: str) -> Dict[str, Any]:
        """
        Generates both guidelines and parameter recommendations in a single API call.
        """
        try:
            system_message = f"""You are an advanced prompt engineering expert specialized in {ai_type} content.
Your task is to analyze this prompt and generate both enhancement guidelines and parameter recommendations."""

            analysis_prompt = f"""Original Prompt: "{prompt}"
Target AI Model: {ai_type}
Writing Style: {style}
Analysis: {json.dumps(analysis, indent=2)}

Provide a comprehensive response with two main sections:

1. ENHANCEMENT GUIDELINES
Provide detailed guidelines for enhancing this prompt, considering:
- Input structure and format for {ai_type}
- Required specifications and details
- Quality criteria and best practices
- Style integration requirements

2. PARAMETER RECOMMENDATIONS
Recommend specific parameter values with explanations:
- temperature: (creativity vs precision)
- top_p: (vocabulary breadth)
- presence_penalty: (repetition control)
- frequency_penalty: (vocabulary variation)"""

            guideline_request = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 2000,
                "stream": False
            }

            self.logger.debug("Generating guidelines and parameter recommendations")
            response = llama.run(guideline_request)
            content = response.json()['choices'][0]['message']['content']

            try:
                sections = content.split("2. PARAMETER RECOMMENDATIONS")
                guidelines = sections[0].replace("1. ENHANCEMENT GUIDELINES", "").strip()
                parameter_text = sections[1]
                parameter_json = self._extract_parameter_json(parameter_text)
                optimized_params = self._process_parameter_recommendations(parameter_json)

                return {
                    "guidelines": guidelines,
                    "parameters": optimized_params,
                    "parameter_reasoning": parameter_json
                }
            except Exception as e:
                self.logger.error(f"Error parsing guidelines/parameters: {str(e)}")
                return {
                    "guidelines": content,
                    "parameters": self._get_default_parameters(),
                    "parameter_reasoning": "Parameter parsing failed, using defaults"
                }

        except Exception as e:
            self.logger.error(f"Guideline generation failed: {str(e)}")
            raise
    

    def _extract_parameter_json(self, parameter_text: str) -> Dict:
        """
        Extracts and validates parameter recommendations from text.
        """
        try:
            # Find the JSON block in the text
            start = parameter_text.find('{')
            end = parameter_text.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in parameter text")
                
            json_text = parameter_text[start:end]
            return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"Parameter JSON extraction failed: {str(e)}")
            raise

    def enhance_prompt(self, prompt: str, guideline_response: Dict[str, Any], style: str, ai_type: str) -> str:
        """
        Enhances prompts using the guidelines and optimized parameters from the first call.
        """
        try:
            guidelines = guideline_response["guidelines"]
            optimized_params = guideline_response["parameters"]
            
            system_message = f"""You are a prompt engineering expert specialized in {ai_type} content with a focus on {style} style. 
    Your task is to enhance the given prompt following the provided guidelines."""

            user_message = f"""Original Prompt: "{prompt}"
    Enhancement Guidelines: {guidelines}

    Create three enhanced versions of this prompt, each optimized for {ai_type}:
    1. A structure-focused version
    2. A detail-focused version
    3. A style-focused version

    Return in JSON format:
    {{
        "prompts": [
            {{"prompt": "First version"}},
            {{"prompt": "Second version"}},
            {{"prompt": "Third version"}}
        ]
    }}"""

            enhancement_request = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            **optimized_params  # Use the optimized parameters from the first call
        }

            self.logger.debug(f"Generating enhanced prompts with parameters: {json.dumps(optimized_params, indent=2)}")
            response = llama.run(enhancement_request)
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
           self.logger.error(f"Prompt enhancement failed: {str(e)}")
           raise

def generate_contextual_guidelines(self, prompt: str, analysis: Dict[str, Any], ai_type: str, style: str) -> Dict[str, Any]:
        """
        Generates both guidelines and parameter recommendations in a single API call.
        """
        try:
            system_message = f"""You are an advanced prompt engineering expert specialized in {ai_type} content.
Your task is to analyze this prompt and generate both enhancement guidelines and parameter recommendations."""

            analysis_prompt = f"""Original Prompt: "{prompt}"
Target AI Model: {ai_type}
Writing Style: {style}
Analysis: {json.dumps(analysis, indent=2)}

Provide a comprehensive response with two main sections:

1. ENHANCEMENT GUIDELINES
Provide detailed guidelines for enhancing this prompt, considering:
- Input structure and format for {ai_type}
- Required specifications and details
- Quality criteria and best practices
- Style integration requirements

2. PARAMETER RECOMMENDATIONS
Recommend specific parameter values with explanations:
- temperature: (creativity vs precision)
- top_p: (vocabulary breadth)
- presence_penalty: (repetition control)
- frequency_penalty: (vocabulary variation)"""

            guideline_request = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 2000,
                "stream": False
            }

            self.logger.debug("Generating guidelines and parameter recommendations")
            response = llama.run(guideline_request)
            content = response.json()['choices'][0]['message']['content']

            try:
                sections = content.split("2. PARAMETER RECOMMENDATIONS")
                guidelines = sections[0].replace("1. ENHANCEMENT GUIDELINES", "").strip()
                parameter_text = sections[1]
                parameter_json = self._extract_parameter_json(parameter_text)
                optimized_params = self._process_parameter_recommendations(parameter_json)

                return {
                    "guidelines": guidelines,
                    "parameters": optimized_params,
                    "parameter_reasoning": parameter_json
                }
            except Exception as e:
                self.logger.error(f"Error parsing guidelines/parameters: {str(e)}")
                return {
                    "guidelines": content,
                    "parameters": self._get_default_parameters(),
                    "parameter_reasoning": "Parameter parsing failed, using defaults"
                }

        except Exception as e:
            self.logger.error(f"Guideline generation failed: {str(e)}")
            raise

def generate_guidelines(analysis: Dict[str, Any]) -> str:
        """
        Generate more specific and detailed guidelines based on task type and requirements.
        """
        task_type = analysis["task_type"]
        requirements = analysis.get("requirements", {})
        
        # Base guidelines structure
        guidelines = {
            "creative_writing": {
                "Content Structure": [
                    "Define clear sections and their purposes",
                    "Specify word count or length requirements",
                    "Include progression and flow requirements"
                ],
                "Style Requirements": [
                    "Specify language level and tone",
                    "Define voice and perspective",
                    "Include any genre-specific conventions"
                ],
                "Quality Criteria": [
                    "Define success metrics",
                    "Specify required elements",
                    "Include any constraints or limitations"
                ],
                "Format Specifications": [
                    "Layout and presentation requirements",
                    "Any specific formatting needs",
                    "Visual organization guidelines"
                ]
            },
            # Add other task types here...
        }
        
        # Get task-specific guidelines
        task_guidelines = guidelines.get(task_type, {})
        
        # Format guidelines as detailed string
        formatted_guidelines = "Enhancement Guidelines:\n\n"
        for category, items in task_guidelines.items():
            formatted_guidelines += f"{category}:\n"
            for item in items:
                formatted_guidelines += f"- {item}\n"
            formatted_guidelines += "\n"
        
        return formatted_guidelines

# def generate_contextual_guidelines(prompt: str) -> str:
#         """
#         First API call to generate highly specific, context-aware guidelines
#         focused on prompt enhancement rather than response generation.
#         """
#         try:
#             system_context = """You are an advanced prompt engineering system specializing in enhancing user prompts to make them more effective. Your task is to:

#     1. Analyze User Intent and Context:
#     - Identify the core objective of the prompt
#     - Understand the specific domain context
#     - Recognize implicit user expectations
#     - Map relationships between concepts
#     - Identify potential contextual constraints

#     2. Generate Enhancement Guidelines:
#     - Focus on prompt improvement, not response generation
#     - Maintain strict contextual relevance
#     - Preserve user's original intent
#     - Add necessary context and specificity
#     - Ensure domain alignment

#     3. Define Quality Benchmarks:
#     - Contextual coherence requirements
#     - Domain-specific terminology standards
#     - Structural clarity expectations
#     - Precision and specificity metrics

#     Your output must be a structured set of guidelines that helps transform the original prompt into a more effective version while maintaining its core intent and context."""

#             # Enhanced analysis prompt focusing on prompt improvement
#             analysis_prompt = f"""Analyze this user prompt and create specific enhancement guidelines:

#     Original Prompt: "{prompt}"

#     Perform a comprehensive prompt analysis considering:

#     1. Core Intent Analysis:
#     - What is the user trying to achieve?
#     - What domain knowledge is required?
#     - What specific outcomes are expected?
#     - What constraints are implied?

#     2. Context Mapping:
#     - Key domain concepts and their relationships
#     - Required background information
#     - Implicit assumptions
#     - Scope boundaries

#     3. Enhancement Requirements:
#     - Areas where specificity is needed
#     - Missing context that should be included
#     - Structural improvements needed
#     - Terminology standardization required

#     4. Prompt-Specific Guidelines:
#     - How to maintain core intent while enhancing clarity
#     - How to add context without changing meaning
#     - How to improve specificity while preserving purpose
#     - How to standardize terminology for the domain

#     Generate guidelines specifically for enhancing this prompt, not for generating responses.
#     Focus on making the prompt more effective while maintaining tight contextual binding.
#     Ensure all guidelines are directly relevant to the user's domain and intended outcome."""

#             enhancement_requirements = f"""
#     Additional Enhancement Requirements:

#     1. Contextual Preservation:
#     - Original intent must remain unchanged
#     - Core concepts must be preserved
#     - User's domain context must be maintained
#     - Target outcome must stay aligned

#     2. Specificity Enhancement:
#     - Add precise domain terminology
#     - Include necessary technical context
#     - Clarify implicit assumptions
#     - Define scope boundaries

#     3. Structural Optimization:
#     - Organize concepts logically
#     - Establish clear relationships
#     - Maintain information hierarchy
#     - Ensure completeness

#     4. Quality Control:
#     - Verify contextual coherence
#     - Ensure domain alignment
#     - Maintain semantic precision
#     - Preserve user intent

#     The enhanced prompt must be more effective than the original while remaining true to its purpose."""

#             # Make API call with enhanced context
#             guidelines_request = {
#                 "model": "llama3.2-11b-vision",
#                 "messages": [
#                     {"role": "system", "content": system_context},
#                     {"role": "user", "content": analysis_prompt},
#                     {"role": "system", "content": enhancement_requirements}
#                 ],
#                 "temperature": 0.7,
#                 "max_tokens": 2000,
#                 "top_p": 0.95
#             }

#             guidelines_response = llama.run(guidelines_request)
#             guidelines = guidelines_response.json()['choices'][0]['message']['content']
            
#             # Add explicit reminder about prompt enhancement vs response generation
#             guidelines += "\n\nNOTE: These guidelines are for enhancing the prompt itself, not for generating responses. The enhanced prompt should maintain tight contextual binding while improving clarity, specificity, and effectiveness."
            
#             logger.debug(f"Generated Guidelines:\n{guidelines}")
            
#             return guidelines

#         except Exception as e:
#             logger.error(f"Guidelines generation error: {str(e)}")
#             raise


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

def get_ai_type_parameters(ai_type: str) -> Dict[str, Any]:
    """
    Returns AI type-specific parameters with guaranteed defaults.
    All required keys are present regardless of AI type.
    """
    # Default configuration that will be present for all types
    default_params = {
        "temperature": 0.7,
        "top_p": 0.9,
        "formatting": {
            "use_sensory_details": False,
            "include_descriptions": False,
            "detail_level": "medium"
        },
        "style_focus": "general purpose",
        "output_structure": "standard format"
    }
    
    # Type-specific configurations
    type_configs = {
        "descriptive": {
            "temperature": 0.7,
            "top_p": 0.9,
            "formatting": {
                "use_sensory_details": True,
                "include_descriptions": True,
                "detail_level": "high"
            },
            "style_focus": "detailed observation",
            "output_structure": "descriptive narrative"
        },
        "creative": {
            "temperature": 0.85,
            "top_p": 0.95,
            "formatting": {
                "use_metaphors": True,
                "include_imagery": True,
                "detail_level": "high"
            },
            "style_focus": "creative expression",
            "output_structure": "creative narrative"
        },
        "technical": {
            "temperature": 0.3,
            "top_p": 0.8,
            "formatting": {
                "use_technical_terms": True,
                "include_specifications": True,
                "detail_level": "precise"
            },
            "style_focus": "technical accuracy",
            "output_structure": "technical documentation"
        },
        "analytical": {
            "temperature": 0.4,
            "top_p": 0.85,
            "formatting": {
                "use_logic_flow": True,
                "include_analysis": True,
                "detail_level": "comprehensive"
            },
            "style_focus": "analytical thinking",
            "output_structure": "analytical framework"
        }
    }
    
    # Get the type-specific config or use default
    config = type_configs.get(ai_type.lower(), default_params)
    
    # Ensure all required keys exist by merging with defaults
    result = default_params.copy()
    result.update(config)
    
    logger.debug(f"AI type parameters for {ai_type}: {result}")
    
    return result


def call_llama_api(prompt: str, writing_style: str, guidelines: str, ai_type: str) -> str:
    """
    Enhanced Llama API call with proper response handling.
    """
    try:
        # Get AI type parameters with guaranteed defaults
        ai_params = get_ai_type_parameters(ai_type)
        
        system_message = """You are a prompt engineering expert. Your task is to enhance the given prompt into three distinct versions. Each version should be more detailed and effective than the original while maintaining the core intent. Do not provide responses to the prompt - only create enhanced versions of the prompt itself."""

        user_message = f"""Original prompt: "{prompt}"
Writing style: {writing_style}
Guidelines: {guidelines}

Please create three enhanced versions of this prompt:
1. A structure-focused version that organizes the requirements clearly
2. A detail-focused version that adds specific criteria and metrics
3. A style-focused version that enhances tone and presentation requirements

Return your response in this exact JSON format:
{{
    "prompts": [
        {{"prompt": "Enhanced version 1 here"}},
        {{"prompt": "Enhanced version 2 here"}},
        {{"prompt": "Enhanced version 3 here"}}
    ]
}}"""

        api_request = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": float(ai_params["temperature"]),
            "top_p": float(ai_params["top_p"]),
            "max_tokens": 2000,
            "stream": False
        }
        
        logger.debug(f"Sending request to Llama API with parameters: {api_request}")
        
        # Make the API call
        response = llama.run(api_request)
        # Add error checking for response
        if not response or not response.json():
            raise Exception("Empty response from API")
            
        response_data = response.json()
        if 'choices' not in response_data or not response_data['choices']:
            raise Exception("No choices in API response")
            
        content = response_data['choices'][0]['message']['content']
        if not content.strip():
            raise Exception("Empty content in API response")
        
        # Ensure valid JSON format
        try:
            json_response = json.loads(content)
        except json.JSONDecodeError:
            # If not valid JSON, format it properly
            json_response = {
                "prompts": [
                    {"prompt": content.strip()}
                ]
            }
        
        # Ensure proper structure
        if "prompts" not in json_response:
            json_response = {
                "prompts": [
                    {"prompt": str(json_response)}
                ]
            }
        
        return json.dumps(json_response)
            
    except Exception as e:
        logger.error(f"Error in prompt enhancement: {str(e)}")
        # Return properly formatted error response
        return json.dumps({
            "prompts": [
                {"prompt": f"Error enhancing prompt: {str(e)}"}
            ]
        })

def normalize_json_response(response_text: str) -> dict:
    """
    Normalizes the enhanced prompt response.
    """
    try:
        data = json.loads(response_text)
        if isinstance(data, dict) and "enhanced_prompt" in data:
            return data
        else:
            # Try to extract enhanced prompt from text
            cleaned_text = response_text.strip()
            return {"enhanced_prompt": cleaned_text}
    except json.JSONDecodeError:
        # If not valid JSON, treat entire response as enhanced prompt
        return {"enhanced_prompt": response_text.strip()}
    
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
    try:
        if not llama:
            return jsonify({"error": "Llama API not properly configured"}), 500
        
        form_data = request.form.get('data')
        data, validation_error = validate_request_data(form_data)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        # Extract required variables
        ai_type = data.get('AIType', 'descriptive')
        style = data.get('style', 'professional')

        # Initialize handlers
        analyzer = RequestAnalyzer(logger)
        llama_handler = EnhancedLlamaHandler(logger)

        # Get analysis first
        analysis = analyzer.analyze_request(data['prompt'])

        # Step 1: Get both guidelines and parameters
        guideline_response = llama_handler.generate_contextual_guidelines(
            prompt=data['prompt'],
            analysis=analysis,
            ai_type=ai_type,
            style=style
        )

        # Step 2: Generate enhanced prompts using the optimized parameters
        enhanced_prompts = llama_handler.enhance_prompt(
            prompt=data['prompt'],
            guideline_response=guideline_response,
            style=style,
            ai_type=ai_type
        )

        return jsonify({
            "original_prompt": data['prompt'],
            "response": json.loads(enhanced_prompts),
            "analysis": analysis,
            "guidelines": guideline_response["guidelines"],
            "parameters_used": guideline_response["parameters"],
            "parameter_reasoning": guideline_response["parameter_reasoning"],
            "ai_type": ai_type,
            "style": style
        })

    except Exception as e:
        logger.error(f"Error in request processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    app.run(host='0.0.0.0', port=2000, debug=True)
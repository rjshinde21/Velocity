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


class EnhancedPromptPreprocessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.logger.info("Initializing EnhancedPromptPreprocessor with NLP models...")
        try:
            self.model_manager = ModelManager()
            self.nlp = self.model_manager.models['nlp']
            self.sentiment_analyzer = self.model_manager.models['sentiment_analyzer']
            self.keyword_model = self.model_manager.models['keyword_model']
            self.semantic_model = self.model_manager.models['semantic_model']
            self.logger.info("Successfully initialized all NLP models")
        except Exception as e:
            self.logger.error(f"Failed to initialize NLP models: {str(e)}")
            raise



    def _calculate_specificity(self, doc) -> float:
        """
        Calculate the specificity of the text based on linguistic features
        
        Args:
            doc (spaCy Doc): Processed document
        
        Returns:
            Float representing specificity score (0-1)
        """
        # Specificity is determined by:
        # 1. Ratio of specific nouns to total nouns
        # 2. Presence of precise descriptors
        # 3. Absence of vague terms
        
        # Count total and specific nouns
        total_nouns = len([token for token in doc if token.pos_ == "NOUN"])
        specific_nouns = len([
            token for token in doc 
            if token.pos_ == "NOUN" and not token.is_stop
        ])
        
        # Count precise descriptors (adjectives that are not general)
        precise_descriptors = len([
            token for token in doc 
            if token.pos_ == "ADJ" and token.text.lower() not in ['good', 'bad', 'nice', 'great']
        ])
        
        # Count vague terms
        vague_terms = len([
            token for token in doc 
            if token.text.lower() in ['thing', 'stuff', 'something', 'anything', 
                                    'whatever', 'somehow', 'kind of', 'sort of']
        ])
        
        # Calculate specificity components
        noun_specificity = specific_nouns / total_nouns if total_nouns > 0 else 0
        descriptor_impact = min(precise_descriptors * 0.1, 0.3)
        vague_term_penalty = min(vague_terms * 0.2, 0.4)
        
        # Combine components
        specificity_score = noun_specificity + descriptor_impact - vague_term_penalty
        
        return max(min(specificity_score, 1.0), 0.0)
    def _analyze_semantic_relationships(self, doc) -> Dict:
        """
        Analyze semantic relationships between sentences and tokens
        """
        try:
            sentences = list(doc.sents)
            embeddings = self.semantic_model.encode([sent.text for sent in sentences])
            
            relationships = []
            for i in range(len(embeddings) - 1):
                try:
                    # Calculate cosine similarity between consecutive sentence embeddings
                    similarity = np.dot(embeddings[i], embeddings[i+1]) / \
                        (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i+1]))
                    
                    relationships.append({
                        'sentence_pair': (i, i+1),
                        'similarity_score': float(similarity),
                        'relationship_type': self._determine_relationship_type(similarity)
                    })
                except Exception as e:
                    self.logger.warning(f"Error calculating semantic relationship: {e}")
                    relationships.append({
                        'sentence_pair': (i, i+1),
                        'similarity_score': 0.0,
                        'relationship_type': 'unknown'
                    })
            
            return {
                'sentence_relationships': relationships,
                'coherence_score': float(np.mean([r['similarity_score'] for r in relationships]) 
                                        if relationships else 0.0)
            }
        except Exception as e:
            self.logger.error(f"Semantic relationship analysis failed: {e}")
            return {
                'sentence_relationships': [],
                'coherence_score': 0.0
            }

    def analyze_prompt(self, prompt_input: Union[str, Dict]) -> Dict:
        """
        Analyzes prompt to extract key insights using deep NLP processing.
        
        Args:
            prompt_input: Either a string prompt or a dict containing prompt data
            
        Returns:
            Dict containing comprehensive prompt analysis
        """
        try:
            self.logger.info("Starting enhanced prompt analysis")
            
            # Extract prompt string if input is dict
            prompt = prompt_input['original_prompt'] if isinstance(prompt_input, dict) else prompt_input
            self.logger.debug(f"Processing prompt: {prompt[:100]}...")
            
            # Process with spaCy
            doc = self.nlp(prompt)
            
            # Extract linguistic features
            linguistic_features = {
                "sentence_count": len(list(doc.sents)),
                "complexity_metrics": {
                    "flesch_score": textstat.flesch_reading_ease(prompt),
                    "grade_level": textstat.coleman_liau_index(prompt)
                },
                "structural_features": self._calculate_sentence_complexity(doc),
                "semantic": self._analyze_semantic_relationships(doc),
                "discourse": self._analyze_discourse_structure(doc)
            }
            
            # Run sentiment analysis
            sentiment_result = self.sentiment_analyzer(prompt)[0]
            
            # Extract keywords using KeyBERT
            keywords = self.keyword_model.extract_keywords(
                prompt,
                top_n=5,
                stop_words='english'
            )
            
            # Named Entity Recognition
            named_entities = [
                (ent.text, ent.label_, self._calculate_entity_confidence(ent))
                for ent in doc.ents
            ]
            
            # Technical analysis
            technical_assessment = self._assess_technical_complexity(doc)
            
            # Domain analysis
            domain_context = self._analyze_domain_context(doc)
            
            # Combine all analyses
            return {
                "content_analysis": {
                    "named_entities": named_entities,
                    "keywords": [kw[0] for kw in keywords],
                    "sentiment": {
                        "label": sentiment_result['label'],
                        "score": sentiment_result['score']
                    }
                },
                "linguistic_features": linguistic_features,
                "technical_assessment": technical_assessment,
                "domain_context": domain_context,
                "complexity_score": linguistic_features["complexity_metrics"]["grade_level"],
                "sentence_count": linguistic_features["sentence_count"],
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "version": "2.0"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Prompt analysis failed: {str(e)}")
            return self._create_fallback_preprocessing(prompt)

    def _determine_relationship_type(self, similarity_score: float) -> str:
        """
        Determine the type of semantic relationship based on similarity score
        """
        if similarity_score > 0.8:
            return 'strong_continuation'
        elif similarity_score > 0.5:
            return 'moderate_continuation'
        else:
            return 'weak_continuation'

    def _calculate_sentence_complexity(self, doc) -> Dict:
        """Calculate sentence complexity metrics"""
        sentences = list(doc.sents)
        return {
            "max_depth": max((len(list(sent.rights)) + len(list(sent.lefts))) for sent in sentences) if sentences else 0,
            "avg_depth": sum((len(list(sent.rights)) + len(list(sent.lefts))) for sent in sentences) / len(sentences) if sentences else 0,
            "compound_sentences": sum(1 for sent in sentences if "and" in sent.text.lower() or "but" in sent.text.lower() or "or" in sent.text.lower())
        }

    def _analyze_discourse_structure(self, doc) -> Dict:
        """
        Analyze discourse markers and structural elements
        """
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
                if any(structure.values()) else 'none'
        }

    def _analyze_domain_context(self, doc) -> Dict:
        """
        Analyze domain-specific context and terminology
        """
        domain_keywords = {
            'Technical': ['code', 'develop', 'algorithm', 'system', 'software', 'programming'],
            'Creative': ['write', 'design', 'imagine', 'story', 'creative', 'art'],
            'Business': ['strategy', 'plan', 'market', 'business', 'sales', 'management'],
            'Academic': ['research', 'study', 'analysis', 'academic', 'scientific'],
            'Personal': ['help', 'advice', 'personal', 'guidance']
        }
        
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in doc.text.lower() for keyword in keywords):
                detected_domains.append(domain)
        
        # Extract domain-specific terms
        domain_terms = [
            token.text for token in doc 
            if token.pos_ == "NOUN" and not token.is_stop
        ]
        
        return {
            'detected_domains': detected_domains,
            'domain_terms': domain_terms,
            'primary_domain': detected_domains[0] if detected_domains else 'general'
        }

    def _check_ambiguity(self, doc) -> Dict:
        """
        Analyze the ambiguity in the text
        
        Args:
            doc (spaCy Doc): Processed document
        
        Returns:
            Dict containing ambiguity metrics
        """
        ambiguity_indicators = {
            'multiple_meanings': self._detect_multiple_meanings(doc),
            'vague_terms': self._identify_vague_terms(doc),
            'complex_sentences': self._analyze_sentence_complexity(doc)
        }
        
        # Calculate overall ambiguity score
        ambiguity_score = self._calculate_ambiguity_score(ambiguity_indicators)
        
        return {
            'has_ambiguity': ambiguity_score > 0.5,
            'ambiguity_details': ambiguity_indicators,
            'ambiguity_score': ambiguity_score
        }

    def _detect_multiple_meanings(self, doc) -> List[str]:
        """
        Detect words with multiple potential meanings
        """
        multiple_meaning_words = []
        for token in doc:
            # Check for tokens with multiple possible parts of speech
            if len([pos for pos in token.pos_]) > 1:
                multiple_meaning_words.append(token.text)
        return multiple_meaning_words

    def _identify_vague_terms(self, doc) -> List[str]:
        """
        Identify vague or imprecise terms
        """
        vague_terms = [
            'thing', 'stuff', 'something', 'anything', 
            'whatever', 'somehow', 'kind of', 'sort of'
        ]
        return [token.text for token in doc if token.text.lower() in vague_terms]

    def _analyze_sentence_complexity(self, doc) -> List[Dict]:
        """
        Analyze sentence complexity as a factor of ambiguity
        """
        complex_sentences = []
        for sent in doc.sents:
            # Check sentence depth and number of clauses
            depth = len(list(sent.subtree))
            clauses = len([token for token in sent if token.dep_ in ['ROOT', 'conj']])
            
            if depth > 10 or clauses > 2:
                complex_sentences.append({
                    'text': sent.text,
                    'depth': depth,
                    'clause_count': clauses
                })
        return complex_sentences

    def _calculate_ambiguity_score(self, ambiguity_indicators: Dict) -> float:
        """
        Calculate an overall ambiguity score
        """
        # Weighted scoring of different ambiguity factors
        multiple_meaning_weight = min(len(ambiguity_indicators['multiple_meanings']) * 0.1, 0.5)
        vague_terms_weight = min(len(ambiguity_indicators['vague_terms']) * 0.2, 0.4)
        complex_sentences_weight = min(len(ambiguity_indicators['complex_sentences']) * 0.1, 0.3)
        
        return multiple_meaning_weight + vague_terms_weight + complex_sentences_weight

    def _extract_domain_context(self, doc) -> Dict:
        """
        Analyze domain-specific context and terminology
        """
        domain_keywords = {
            'Technical': ['code', 'develop', 'algorithm', 'system', 'software', 'programming'],
            'Creative': ['write', 'design', 'imagine', 'story', 'creative', 'art'],
            'Business': ['strategy', 'plan', 'market', 'business', 'sales', 'management'],
            'Academic': ['research', 'study', 'analysis', 'academic', 'scientific'],
            'Personal': ['help', 'advice', 'personal', 'guidance']
        }
        
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in doc.text.lower() for keyword in keywords):
                detected_domains.append(domain)
        
        # Extract domain-specific terms
        domain_terms = [
            token.text for token in doc 
            if token.pos_ == "NOUN" and not token.is_stop
        ]
        
        return {
            'detected_domains': detected_domains,
            'domain_terms': domain_terms,
            'primary_domain': detected_domains[0] if detected_domains else 'general'
        }

    def _assess_technical_complexity(self, doc) -> Dict:
        """
        Assess the technical complexity of the prompt
        """
        # Calculate sentence depth
        max_depth = max(
            (len(list(sent.rights)) + len(list(sent.lefts))) 
            for sent in doc.sents
        ) if list(doc.sents) else 0
        
        # Count technical terms
        technical_term_count = len([
            token for token in doc 
            if token.pos_ == "NOUN" and not token.is_stop
        ])
        
        # Assess verb complexity
        verb_complexity = len([
            token for token in doc 
            if token.pos_ == "VERB" and token.dep_ in ['ROOT', 'xcomp', 'ccomp']
        ])
        
        return {
            'max_sentence_depth': max_depth,
            'technical_term_count': technical_term_count,
            'verb_complexity': verb_complexity,
            'complexity_score': self._calculate_complexity_score(
                max_depth, 
                technical_term_count, 
                verb_complexity
            )
        }

    def _calculate_complexity_score(self, depth: int, term_count: int, verb_complexity: int) -> float:
        """
        Calculate an overall complexity score
        """
        # Base complexity calculation
        complexity = (
            (depth * 0.3) +  # Sentence structure complexity
            (term_count * 0.2) +  # Technical term density
            (verb_complexity * 0.5)  # Verb complexity
        )
        
        # Normalize to 0-100 scale
        return min(max(complexity, 0), 100)

    def _extract_linguistic_features(self, doc) -> Dict:
        return {
            "verbs": [token.text for token in doc if token.pos_ == "VERB"],
            "nouns": [token.text for token in doc if token.pos_ == "NOUN"],
            "adjectives": [token.text for token in doc if token.pos_ == "ADJ"],
            "dependencies": [f"{token.text}:{token.dep_}" for token in doc],
            "has_questions": any(token.text.lower() in ["what", "why", "how", "when", "where", "who"] 
                            for token in doc)
        }

    def analyze_prompt_with_cot(self, prompt: str, steps: int = 3) -> Dict:
        """
        Apply Chain-of-Thought (CoT) preprocessing
        
        Args:
            prompt (str): Original user prompt
            steps (int): Number of reasoning steps to generate
        
        Returns:
            Dict containing CoT analysis and insights
        """
        base_analysis = self.analyze_prompt(prompt)
        
        # Generate reasoning steps
        reasoning_steps = self._generate_reasoning_steps(prompt, steps)
        
        base_analysis['chain_of_thought'] = {
            'reasoning_steps': reasoning_steps,
            'complexity': len(reasoning_steps)
        }
        
        return base_analysis

    def _generate_reasoning_steps(self, prompt: str, num_steps: int) -> List[str]:
        """
        Generate reasoning steps using semantic analysis
        
        Args:
            prompt (str): Original user prompt
            num_steps (int): Number of reasoning steps to generate
        
        Returns:
            List of reasoning steps
        """
        doc = self.nlp(prompt)
        steps = []
        
        # Extract key concepts and dependencies
        key_concepts = [chunk.text for chunk in doc.noun_chunks]
        action_verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        
        # Generate reasoning steps
        for i in range(num_steps):
            step = f"Step {i+1}: {action_verbs[i % len(action_verbs)]} {key_concepts[i % len(key_concepts)]}"
            steps.append(step)
        
        return steps

    def preprocess_prompt(self, prompt: str) -> Dict:
        """Main preprocessing function"""
        self.logger.info(f"Starting prompt preprocessing for text length: {len(prompt)}")
        try:
            # Log input text characteristics
            self.logger.debug(f"Input prompt: {prompt[:100]}...")
            
            # Step 1: Spell check
            self.logger.info("Performing spell check and text cleaning...")
            cleaned_text, spelling_corrections = self._clean_and_spell_check(prompt)
            if spelling_corrections:
                self.logger.info(f"Found {len(spelling_corrections)} spelling corrections")
                self.logger.debug(f"Spelling corrections: {spelling_corrections}")
            
            # Step 2: NLP Analysis
            self.logger.info("Performing deep NLP analysis...")
            nlp_analysis = self._perform_analysis(cleaned_text)
            self.logger.debug(f"NLP analysis results: {json.dumps(nlp_analysis, indent=2)}")
            
            # Step 3: Intent Analysis
            self.logger.info("Analyzing intent...")
            intent_analysis = self._analyze_intent(cleaned_text)
            self.logger.debug(f"Intent analysis results: {json.dumps(intent_analysis, indent=2)}")
            
            # Step 4: Quality Metrics
            self.logger.info("Calculating quality metrics...")
            quality_metrics = self._calculate_quality_metrics(cleaned_text)
            
            result = {
                "processed_text": cleaned_text,
                "spelling_corrections": spelling_corrections,
                "nlp_analysis": nlp_analysis,
                "intent_analysis": intent_analysis,
                "quality_metrics": quality_metrics,
                "original_text": prompt,
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "preprocessing_version": "2.0"
                }
            }
            
            self.logger.info("Preprocessing completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Preprocessing failed: {str(e)}")
            self.logger.exception("Full traceback:")
            return self._create_fallback_preprocessing(prompt)

    def _classify_primary_intent(self, actions: List[Dict], doc) -> Dict:
        """
        Classify the primary intent of the prompt based on actions and linguistic analysis
        
        Args:
            actions (List[Dict]): List of extracted actions
            doc (spaCy Doc): Processed document
        
        Returns:
            Dict containing intent classification details
        """
        # Define intent categories with associated keywords
        intent_categories = {
            'task_completion': ['create', 'develop', 'build', 'generate', 'implement', 'make'],
            'information_gathering': ['explain', 'describe', 'analyze', 'understand', 'breakdown', 'define'],
            'problem_solving': ['solve', 'resolve', 'fix', 'address', 'troubleshoot', 'improve'],
            'creative_generation': ['write', 'design', 'compose', 'imagine', 'draft', 'invent'],
            'strategic_planning': ['plan', 'strategy', 'roadmap', 'outline', 'propose', 'structure']
        }
        
        # Extract primary verbs
        primary_verbs = [action['verb'].lower() for action in actions]
        
        # Classify intent based on verb matches
        detected_intents = []
        for category, keywords in intent_categories.items():
            if any(verb in keywords for verb in primary_verbs):
                detected_intents.append(category)
        
        # Fallback to general classification if no specific intent detected
        primary_intent = detected_intents[0] if detected_intents else 'general_inquiry'
        
        # Calculate intent confidence
        intent_confidence = self._calculate_intent_confidence(doc)
        
        # Extract key nouns to provide additional context
        key_nouns = [token.text for token in doc if token.pos_ == 'NOUN' and not token.is_stop]
        
        return {
            'primary_category': primary_intent,
            'possible_intents': detected_intents,
            'confidence_score': intent_confidence,
            'key_nouns': key_nouns[:5],  # Limit to top 5 key nouns
            'raw_actions': actions
        }

    def _extract_requirements(self, doc) -> List[Dict]:
        """
        Extract detailed requirements from the document
        
        Args:
            doc (spaCy Doc): Processed document
        
        Returns:
            List of extracted requirements
        """
        requirements = []
        
        # Extract noun chunks as potential requirements
        for chunk in doc.noun_chunks:
            requirement = {
                'text': chunk.text,
                'root': chunk.root.text,
                'type': chunk.root.pos_
            }
            requirements.append(requirement)
        
        # Extract verb phrases with their objects
        for token in doc:
            if token.pos_ == 'VERB':
                objects = [child.text for child in token.children if child.dep_ in ['dobj', 'pobj']]
                if objects:
                    requirements.append({
                        'text': f"{token.text} {' '.join(objects)}",
                        'type': 'action_requirement'
                    })
        
        return requirements

    def _perform_analysis(self, prompt: str) -> Dict:
        """
            Performs the core analysis of the prompt.
            """
        doc = self.nlp(prompt)
            
        return {
                "linguistic_analysis": self._extract_linguistic_features(doc),
                "semantic_analysis": self._analyze_semantic_relationships(doc),
                "discourse_analysis": self._analyze_discourse_structure(doc),
                "domain_analysis": self._analyze_domain_context(doc),
                "technical_assessment": self._assess_technical_complexity(doc),
            }

    def _create_fallback_preprocessing(self, prompt: str) -> Dict:
        """
            Create a fallback preprocessing result when analysis fails
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
  

    def _clean_and_spell_check(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Clean text without spell checking
        Returns cleaned text and an empty corrections dictionary for compatibility
        """
        # Basic text cleaning
        cleaned_text = text.strip()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove extra whitespace
        
        # Return cleaned text with empty corrections dict to maintain interface
        return cleaned_text, {}

    def _is_special_term(self, word: str) -> bool:
        """
        Check if word is a special term (kept for future reference)
        """
        # Common AI model names
        ai_terms = {'gpt', 'chatgpt', 'dalle', 'midjourney', 'claude', 'gemini'}
        
        # Common technical terms
        tech_terms = {'api', 'json', 'html', 'css', 'url', 'sql'}
        
        return (
            word.lower() in ai_terms or 
            word.lower() in tech_terms or
            any(char.isdigit() for char in word) or
            '@' in word or  # Email addresses
            '/' in word or  # URLs/paths
            word.startswith(('http', 'www'))  # URLs
        ) 

    def _analyze_intent(self, text: str) -> Dict:
        """
        Enhanced intent analysis with domain awareness
        """
        doc = self.nlp(text)
        
        # Extract action verbs and their objects
        actions = []
        for token in doc:
            if token.pos_ == "VERB":
                # Get verb objects
                verb_objects = [child.text for child in token.children 
                              if child.dep_ in ['dobj', 'pobj']]
                actions.append({
                    "verb": token.text,
                    "objects": verb_objects,
                    "lemma": token.lemma_
                })

        # Classify primary intent
        intent_classification = self._classify_primary_intent(actions, doc)
        
        # Extract task requirements
        requirements = self._extract_requirements(doc)
        
        return {
            "primary_intent": intent_classification,
            "actions": actions,
            "requirements": requirements,
            "confidence_score": self._calculate_intent_confidence(doc),
            "domain_context": self._extract_domain_context(doc)
        }

    def _calculate_intent_confidence(self, doc) -> float:
        """Calculate confidence score for intent classification"""
        # Base confidence from sentence structure clarity
        base_confidence = 0.7
        
        # Adjust based on presence of clear action verbs
        verb_count = len([token for token in doc if token.pos_ == "VERB"])
        if verb_count > 0:
            base_confidence += 0.1
            
        # Adjust based on presence of clear objects
        obj_count = len([token for token in doc if token.dep_ in ['dobj', 'pobj']])
        if obj_count > 0:
            base_confidence += 0.1
            
        # Penalize for ambiguity
        ambiguous_terms = len([token for token in doc 
                             if token.text.lower() in ['maybe', 'perhaps', 'possibly']])
        base_confidence -= (ambiguous_terms * 0.1)
        
        return min(max(base_confidence, 0.1), 1.0)

    def _calculate_quality_metrics(self, text: str) -> Dict:
        """
        Calculate various text quality metrics
        """
        doc = self.nlp(text)
        
        return {
            "readability": {
                "flesch_score": textstat.flesch_reading_ease(text),
                "grade_level": textstat.coleman_liau_index(text)
            },
            "structure": {
                "sentence_count": len(list(doc.sents)),
                "word_count": len([token for token in doc if not token.is_punct]),
                "avg_word_length": sum(len(token.text) for token in doc if not token.is_punct) / 
                                 len([token for token in doc if not token.is_punct]) if doc else 0
            },
            "clarity": {
                "has_ambiguity": self._check_ambiguity(doc),
                "specificity_score": self._calculate_specificity(doc)
            }
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
        

class AsyncPipelineCoordinator:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.preprocessor = EnhancedPromptPreprocessor(logger)
        self.guidelines_generator = GuidelinesStage(logger)
        self.context_tracker = ContextTracker()
        # self.spell_checker = SpellChecker()
        
    async def coordinate_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict:
        try:
            # Create tasks for parallel execution
            preprocessing_task = asyncio.create_task(
                self.run_preprocessing(prompt)
            )
            
            guidelines_task = asyncio.create_task(
                self.run_guidelines(prompt, ai_type, style)
            )
            
            # Wait for both tasks to complete
            preprocessing_result, guidelines_result = await asyncio.gather(
                preprocessing_task,
                guidelines_task,
                return_exceptions=True
            )
            
            # Validate results and handle any errors
            self._validate_stage_results(preprocessing_result, guidelines_result)
            
            # Combine results for enhancement stage
            combined_context = self._merge_stage_results(
                preprocessing_result, 
                guidelines_result
            )
            
            return combined_context
            
        except Exception as e:
            self.logger.error(f"Pipeline coordination failed: {str(e)}")
            raise

    async def run_preprocessing(self, prompt: str) -> Dict:
        """Run NLP preprocessing asynchronously"""
        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(
                executor,
                self._execute_preprocessing,
                prompt
            )

    async def run_guidelines(self, prompt: str, ai_type: str, style: str) -> Dict:
        """Run guidelines generation asynchronously"""
        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(
                executor,
                self._execute_guidelines,
                prompt,
                ai_type,
                style
            )


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

    async def make_api_call(self, system_message: str, prompt: str, **params) -> Dict:
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llama.run({
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "model": "llama3.2-1b",
                    "stream": False,
                    **params
                })
            )

            if hasattr(response, 'json'):
                response_data = response.json()
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
        self._model_cache = {}
        
        def _lazy_load_model(self, model_name: str):
            if model_name not in self._model_cache:
                if model_name == 'nlp':
                    self._model_cache[model_name] = self.model_manager.models['nlp']
                elif model_name == 'sentiment':
                    self._model_cache[model_name] = self.model_manager.models['sentiment_analyzer']
                # Add other models...
            return self._model_cache[model_name]

    def _determine_relationship_type(self, similarity_score: float) -> str:
        """Determine relationship type based on similarity score"""
        if similarity_score > 0.8:
            return 'strong_continuation'
        elif similarity_score > 0.5:
            return 'moderate_continuation'
        else:
            return 'weak_continuation'
        
    def _analyze_flow_pattern(self, relationships: List[Dict]) -> Dict:
        """
        Analyzes the overall flow pattern of ideas across sentences by examining
        the sequence of relationship types and transition strengths.
        
        Args:
            relationships: List of relationship dictionaries containing similarity scores
                        and relationship types between consecutive sentences
        
        Returns:
            Dict containing flow pattern analysis results
        """
        try:
            if not relationships:
                return {
                    'pattern_type': 'unknown',
                    'coherence_level': 'unknown',
                    'transitions': []
                }

            # Analyze transition patterns
            transitions = []
            for i in range(len(relationships)):
                rel = relationships[i]
                transition = {
                    'position': i,
                    'type': rel['relationship_type'],
                    'strength': rel.get('transition_strength', {}).get('strength', 'unknown'),
                    'similarity': rel['similarity_score']
                }
                transitions.append(transition)

            # Determine overall pattern type
            strong_connections = sum(1 for t in transitions if t['type'] == 'strong_continuation')
            weak_connections = sum(1 for t in transitions if t['type'] == 'weak_continuation')
            
            if strong_connections > len(transitions) * 0.7:
                pattern_type = 'strongly_connected'
            elif weak_connections > len(transitions) * 0.7:
                pattern_type = 'loosely_connected'
            else:
                pattern_type = 'mixed_connection'

            # Calculate overall coherence
            average_similarity = sum(t['similarity'] for t in transitions) / len(transitions) if transitions else 0
            
            coherence_level = 'high' if average_similarity > 0.8 else \
                            'medium' if average_similarity > 0.5 else 'low'

            return {
                'pattern_type': pattern_type,
                'coherence_level': coherence_level,
                'transitions': transitions,
                'metrics': {
                    'average_similarity': average_similarity,
                    'strong_connections_ratio': strong_connections / len(transitions) if transitions else 0,
                    'weak_connections_ratio': weak_connections / len(transitions) if transitions else 0
                }
            }

        except Exception as e:
            self.logger.error(f"Error analyzing flow pattern: {e}")
            return {
                'pattern_type': 'unknown',
                'coherence_level': 'unknown',
                'transitions': [],
                'error': str(e)
            }
        
    def _create_fallback_relationship(self, index: int) -> Dict:
        """
        Creates a fallback relationship entry when similarity calculation fails.
        
        Args:
            index: Index of the relationship in the sequence
            
        Returns:
            Dict containing fallback relationship data
        """
        self.logger.debug(f"Creating fallback relationship for index {index}")
        return {
            'sentence_pair': (index, index + 1),
            'similarity_score': 0.0,
            'relationship_type': 'unknown',
            'transition_strength': {
                'has_transition_words': False,
                'shared_concepts': 0,
                'strength': 'weak'
            }
        }

    def _calculate_term_relevance(self, token) -> float:
        """
        Calculates relevance score for a domain term based on multiple factors.
        
        Args:
            token: spaCy token object
            
        Returns:
            float: Relevance score between 0 and 1
        """
        self.logger.debug(f"Calculating relevance for term: {token.text}")
        
        # Base relevance score
        relevance = 0.5
        
        # Adjust based on token position
        if token.i < len(token.doc) * 0.2:  # Term appears early
            relevance += 0.1
            
        # Adjust based on dependencies
        if any(child.dep_ in ['nsubj', 'dobj'] for child in token.children):
            relevance += 0.1
            
        # Adjust based on frequency
        frequency = sum(1 for t in token.doc if t.lower_ == token.lower_)
        if frequency > 1:
            relevance += 0.1
            
        # Adjust based on technical nature
        if self._is_technical_term(token.text):
            relevance += 0.2
            
        return min(relevance, 1.0)

    def _extract_main_concept(self, sentence: str) -> str:
        """
        Extracts the main concept from a sentence using syntactic dependencies.
        Called by _extract_key_concepts but not defined.
        
        Args:
            sentence: Input sentence string
        
        Returns:
            str: Main concept from the sentence
        """
        doc = self.nlp(sentence)
        
        # Look for subject-verb-object patterns first
        for token in doc:
            if token.dep_ == "ROOT":
                # Get subject
                subjects = [child for child in token.children if child.dep_ == "nsubj"]
                if subjects:
                    return subjects[0].text
        
        # Fallback to first noun phrase if no clear subject
        for chunk in doc.noun_chunks:
            return chunk.text
            
        # Final fallback to first token if no noun phrases
        return doc[0].text
    
    def _calculate_hierarchical_domain_scores(self, doc, domain_categories: Dict) -> Dict:
        """
        Calculates hierarchical scores for different domain categories.
        Called by _analyze_domain_context but not defined.
        
        Args:
            doc: spaCy Doc object
            domain_categories: Dictionary of domain categories and their keywords
        
        Returns:
            Dict: Hierarchical domain scores
        """
        scores = {
            domain: {
                subdomain: 0 for subdomain in subcategories.keys()
            } for domain, subcategories in domain_categories.items()
        }
        
        # Process each token
        for token in doc:
            term = token.text.lower()
            
            # Check each domain and subdomain
            for domain, subcategories in domain_categories.items():
                for subdomain, keywords in subcategories.items():
                    if term in keywords:
                        scores[domain][subdomain] += 1
        
        # Calculate domain totals
        domain_totals = {
            domain: sum(subdomain_scores.values())
            for domain, subdomain_scores in scores.items()
        }
        
        return {
            'detailed_scores': scores,
            'domain_totals': domain_totals
        }
    
    def _analyze_domain_relationships(self, domain_scores: Dict) -> Dict:
        """
        Analyzes relationships between different domains based on their scores.
        Called by _analyze_domain_context but not defined.
        
        Args:
            domain_scores: Dictionary containing domain scores
            
        Returns:
            Dict: Analysis of domain relationships
        """
        detailed_scores = domain_scores.get('detailed_scores', {})
        domain_totals = domain_scores.get('domain_totals', {})
        
        # Calculate domain overlaps
        overlaps = {}
        domains = list(domain_totals.keys())
        
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                shared_terms = set(
                    term for term, score in detailed_scores[domain1].items()
                    if score > 0 and detailed_scores[domain2].get(term, 0) > 0
                )
                overlaps[f"{domain1}-{domain2}"] = len(shared_terms)
        
        return {
            'overlaps': overlaps,
            'relationships': self._calculate_domain_overlap(domain_totals)
        }
    
    def _calculate_confidence_scores(self, domain_scores: Dict) -> Dict:
        """
        Calculates confidence scores for domain classification.
        Called by _analyze_domain_context but not defined.
        
        Args:
            domain_scores: Dictionary containing domain scores
            
        Returns:
            Dict: Confidence scores for each domain
        """
        totals = domain_scores.get('domain_totals', {})
        overall_total = sum(totals.values())
        
        if overall_total == 0:
            return {'confidence_scores': {}, 'overall_confidence': 0.0}
        
        # Calculate normalized confidence scores
        confidence_scores = {
            domain: (score / overall_total) if overall_total > 0 else 0.0
            for domain, score in totals.items()
        }
        
        # Calculate overall confidence
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0.0
        
        return {
            'confidence_scores': confidence_scores,
            'overall_confidence': max_confidence,
            'confidence_level': 'high' if max_confidence > 0.7 else
                            'medium' if max_confidence > 0.4 else 'low'
        }

    def _infer_intent_from_verbs(self, verbs: List[str]) -> List[str]:
        """
        Infers possible intents from verb patterns when no direct matches found.
        
        Args:
            verbs: List of verbs found in the prompt
            
        Returns:
            List[str]: Inferred intent types
        """
        self.logger.debug(f"Inferring intent from verbs: {verbs}")
        
        # Map verbs to intent categories
        verb_intent_mapping = {
            'create': 'task_completion',
            'analyze': 'information_gathering',
            'solve': 'problem_solving',
            'design': 'creative_generation',
            'plan': 'strategic_planning'
        }
        
        inferred_intents = set()
        for verb in verbs:
            for known_verb, intent in verb_intent_mapping.items():
                if self._calculate_verb_similarity(verb, known_verb) > 0.8:
                    inferred_intents.add(intent)
                    self.logger.debug(f"Inferred intent '{intent}' from verb '{verb}'")
                    
        return list(inferred_intents) if inferred_intents else ['general']

    def _calculate_verb_similarity(self, verb1: str, verb2: str) -> float:
        """
        Calculates semantic similarity between two verbs using embeddings.
        
        Args:
            verb1: First verb to compare
            verb2: Second verb to compare
            
        Returns:
            float: Similarity score between 0 and 1
        """
        try:
            embeddings = self.semantic_model.encode([verb1, verb2])
            similarity = np.dot(embeddings[0], embeddings[1]) / \
                        (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Error calculating verb similarity: {e}")
            return 0.0
        
    def _calculate_domain_overlap(self, domain_scores: Dict[str, int]) -> Dict[str, float]:
        """
        Calculates overlap between different domains based on shared terminology.
        
        Args:
            domain_scores: Dictionary mapping domains to their term frequency scores
            
        Returns:
            Dictionary containing overlap ratios between domains
        """
        overlaps = {}
        total_terms = sum(domain_scores.values())
        
        if total_terms == 0:
            return {'overlap_ratio': 0.0}
            
        # Calculate normalized overlap ratios
        primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
        primary_score = domain_scores[primary_domain]
        
        for domain, score in domain_scores.items():
            if domain != primary_domain and score > 0:
                overlaps[f"{primary_domain}_{domain}"] = score / primary_score
                
        return {
            'primary_domain': primary_domain,
            'overlap_ratios': overlaps,
            'overlap_score': len([s for s in domain_scores.values() if s > 0]) / len(domain_scores)
        }

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


    def analyze_prompt(self, prompt_input: Union[str, Dict]) -> Dict:
        """
        Enhanced prompt analysis with deeper NLP insights and domain understanding.
        """
        self.logger.info(f"Starting enhanced prompt analysis")
        self.logger.debug(f"Input type: {type(prompt_input)}")
        
        # Extract prompt string if input is dict
        prompt = prompt_input['original_prompt'] if isinstance(prompt_input, dict) else prompt_input
        self.logger.debug(f"Processing prompt: {prompt[:100]}...")
        prompt = self._normalize_input(prompt_input)
        analysis_result = self._perform_analysis(prompt)

        
        
        # Perform linguistic analysis using spaCy
        doc = self.nlp(prompt)
        self.logger.debug(f"Found {len(list(doc.sents))} sentences, {len(doc)} tokens")
        
        # Extract domain-specific patterns
        linguistic_patterns = {
            'technical_terms': [],
            'action_verbs': [],
            'domain_concepts': [],
            'modifiers': []
        }
        self.logger.info("Extracting linguistic patterns")
        self.logger.debug(f"Found patterns: {linguistic_patterns}")

        # Enhanced token analysis with domain understanding
        for token in doc:
            if token.pos_ == 'VERB':
                linguistic_patterns['action_verbs'].append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'tense': token.morph.get('Tense', [''])[0]
                })
            elif token.pos_ == 'NOUN' and not token.is_stop:
                linguistic_patterns['domain_concepts'].append({
                    'text': token.text,
                    'is_technical': self._is_technical_term(token.text)
                })
            elif token.pos_ in ['ADJ', 'ADV']:
                linguistic_patterns['modifiers'].append(token.text)

        # Enhanced sentiment analysis with context
        sentiment_result = self.sentiment_analyzer(prompt)[0]
        sentiment_context = self._analyze_sentiment_context(doc, sentiment_result)

        # Improved keyword extraction with domain weighting
        keywords = self.keyword_model.extract_keywords(
            prompt, 
            top_n=5,
            stop_words='english'
        )

        # Enhanced named entity recognition with confidence scores
        named_entities = [{
            'text': ent.text,
            'label': ent.label_,
            'confidence': self._calculate_entity_confidence(ent)
        } for ent in doc.ents]

        # Extract technical complexity metrics
        complexity_metrics = {
            "flesch_score": textstat.flesch_reading_ease(prompt),
            "grade_level": textstat.coleman_liau_index(prompt),
            "sentence_count": len(list(doc.sents)),
            "word_count": len([token for token in doc if not token.is_punct]),
            "technical_density": self._calculate_technical_density(doc)
        }

        # Generate semantic insights
        semantic_insights = self._analyze_semantic_relationships(doc)

        return {
            "content_analysis": {
                "named_entities": named_entities,
                "keywords": [kw[0] for kw in keywords],
                "topics": self._extract_topics(prompt),
                "sentiment": {
                    "label": sentiment_result['label'],
                    "score": sentiment_result['score'],
                    "context": sentiment_context
                }
            },
            "analysis": analysis_result,
            "linguistic_features": {
                "patterns": linguistic_patterns,
                "complexity_metrics": complexity_metrics,
                "semantic_insights": semantic_insights
            },
            "domain_analysis": self._analyze_domain_context(doc),
            "technical_assessment": {
                "complexity_level": self._assess_technical_complexity(doc),
                "domain_specific_terms": self._extract_domain_terms(doc),
                "implementation_requirements": self._extract_implementation_requirements(doc)
            }
        }
    
    def _perform_analysis(self, prompt: str) -> Dict:
        """
            Performs the core analysis of the prompt.
            """
        doc = self.nlp(prompt)
            
        return {
                "linguistic_analysis": self._extract_linguistic_features(doc),
                "semantic_analysis": self._analyze_semantic_relationships(doc),
                "discourse_analysis": self._analyze_discourse_structure(doc),
                "domain_analysis": self._analyze_domain_context(doc),
                "technical_assessment": self._assess_technical_complexity(doc),
            }


    def _is_technical_term(self, term: str) -> bool:
        """
        Determines if a word is a technical term by checking against common technical 
        patterns and domain-specific vocabularies.
        """
        technical_indicators = {
            'prefixes': ['cyber', 'multi', 'meta', 'inter', 'micro', 'macro'],
            'suffixes': ['tion', 'ology', 'metric', 'ware', 'wise'],
            'common_tech_words': ['api', 'data', 'code', 'algorithm', 'system', 'interface']
        }
        
        term_lower = term.lower()
        return any([
            any(term_lower.startswith(prefix) for prefix in technical_indicators['prefixes']),
            any(term_lower.endswith(suffix) for suffix in technical_indicators['suffixes']),
            term_lower in technical_indicators['common_tech_words']
        ])
    
    def _calculate_entity_confidence(self, entity) -> float:
        """
        Calculates a confidence score for named entity recognition based on 
        multiple factors including context and pattern matching.
        """
        base_score = 0.8  # Base confidence score
        
        # Adjust score based on entity type
        type_scores = {
            'PERSON': 0.9,
            'ORG': 0.85,
            'GPE': 0.95,
            'PRODUCT': 0.8,
            'EVENT': 0.75
        }
        
        # Adjust based on entity length (longer entities tend to be more reliable)
        length_factor = min(len(entity.text.split()) * 0.05, 0.15)
        
        # Get base type score or default to 0.7
        type_score = type_scores.get(entity.label_, 0.7)
        
        return min(base_score + type_score + length_factor, 1.0)
    
    def _analyze_semantic_relationships(self, doc) -> Dict:
        """Enhanced semantic analysis with contextual understanding"""
        # Extract sentences and their embeddings
        sentences = [sent.text for sent in doc.sents]
        embeddings = self.semantic_model.encode(sentences)
        
        # Build semantic graph
        semantic_graph = self._build_semantic_graph(sentences, embeddings)
        
        # Analyze discourse patterns
        discourse_patterns = self._analyze_discourse_patterns(doc)
        
        # Analyze semantic coherence
        coherence_analysis = self._analyze_semantic_coherence(semantic_graph)
        
        return {
            'semantic_graph': semantic_graph,
            'discourse_patterns': discourse_patterns,
            'coherence_metrics': coherence_analysis,
            'key_concepts': self._extract_key_concepts(semantic_graph)
        }
    
    def _analyze_transition_strength(self, sent1, sent2) -> Dict:
        """
        Analyzes the strength of transitions between sentences by looking at 
        connecting words and shared concepts.
        """
        transition_words = set(['however', 'therefore', 'thus', 'consequently', 'moreover'])
        shared_entities = set(token.text for token in sent1).intersection(set(token.text for token in sent2))
        
        return {
            'has_transition_words': any(word in sent2.text.lower() for word in transition_words),
            'shared_concepts': len(shared_entities),
            'strength': 'strong' if len(shared_entities) > 2 else 'moderate' if len(shared_entities) > 0 else 'weak'
        }
    
    def _analyze_domain_context(self, doc) -> Dict:
        """Enhanced domain analysis with multi-level categorization"""
        domain_categories = {
            'technical': {
                'programming': ['code', 'algorithm', 'function'],
                'data_science': ['analysis', 'dataset', 'model'],
                'infrastructure': ['system', 'network', 'server']
            },
            'business': {
                'strategy': ['plan', 'objective', 'goal'],
                'finance': ['revenue', 'cost', 'budget'],
                'marketing': ['campaign', 'audience', 'brand']
            }
            # Add more domains
        }
        
        # Hierarchical domain scoring
        domain_scores = self._calculate_hierarchical_domain_scores(doc, domain_categories)
        
        # Domain overlap analysis
        domain_relationships = self._analyze_domain_relationships(domain_scores)
        
        return {
            'primary_domain': self._determine_primary_domain(domain_scores),
            'domain_hierarchy': domain_scores,
            'domain_relationships': domain_relationships,
            'confidence_scores': self._calculate_confidence_scores(domain_scores)
        }

    def _assess_technical_complexity(self, doc) -> Dict:
        """Enhanced technical complexity assessment"""
        # Analyze code-like patterns
        code_patterns = self._identify_code_patterns(doc)
        
        # Assess technical vocabulary
        technical_terms = self._extract_technical_terms(doc)
        
        # Calculate complexity metrics
        complexity_metrics = {
            'cyclomatic': self._calculate_cyclomatic_complexity(doc),
            'halstead': self._calculate_halstead_metrics(doc),
            'cognitive': self._assess_cognitive_complexity(doc)
        }
        
        return {
            'complexity_metrics': complexity_metrics,
            'technical_patterns': code_patterns,
            'technical_vocabulary': technical_terms,
            'implementation_requirements': self._extract_implementation_requirements(doc)
        }

    def _assess_requirement_priority(self, sentence) -> str:
        """
        Assesses the priority level of a requirement based on language indicators
        and context.
        """
        text = sentence.text.lower()
        priority_indicators = {
            'high': ['must', 'critical', 'essential', 'required'],
            'medium': ['should', 'important', 'needed'],
            'low': ['could', 'might', 'optional']
        }
        
        for priority, indicators in priority_indicators.items():
            if any(indicator in text for indicator in indicators):
                return priority
                
        return 'medium'  # Default priority if no clear indicators

    def _extract_domain_terms(self, doc) -> List[Dict]:
        """
        Extracts domain-specific terminology from the document with context 
        and relevance scores.
        """
        domain_terms = []
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                self._is_technical_term(token.text)):
                
                domain_terms.append({
                    'term': token.text,
                    'context': self._extract_term_context(token),
                    'relevance': self._calculate_term_relevance(token)
                })
                
        return domain_terms

    def _extract_term_context(self, token) -> Dict:
        """
        Extracts the contextual information around a specific term including
        modifiers and related concepts.
        """
        return {
            'modifiers': [child.text for child in token.children if child.dep_ in ['amod', 'advmod']],
            'related_terms': [child.text for child in token.children if child.dep_ in ['compound', 'nmod']],
            'sentence_position': token.i / len(token.doc)
        }

    def _calculate_technical_density(self, doc) -> float:
        """Calculate the density of technical terms in the text."""
        technical_terms = self._extract_domain_terms(doc)
        total_words = len([token for token in doc if not token.is_punct])
        return len(technical_terms) / total_words if total_words > 0 else 0

    def _analyze_sentiment_context(self, doc, sentiment_result: Dict) -> Dict:
        """Analyze the context around sentiment expressions."""
        return {
            "modifiers": [token.text for token in doc if token.dep_ == 'amod'],
            "intensifiers": [token.text for token in doc if token.dep_ == 'advmod'],
            "negations": [token.text for token in doc if token.dep_ == 'neg']
        }

    def _extract_implementation_requirements(self, doc) -> List[Dict]:
        """Extract implementation requirements from the text."""
        requirements = []
        for sent in doc.sents:
            if any(term in sent.text.lower() for term in ["must", "should", "need", "require"]):
                requirements.append({
                    "text": sent.text,
                    "priority": self._assess_requirement_priority(sent)
                })
        return requirements
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
    
    def _build_semantic_graph(self, sentences: List[str], embeddings: np.ndarray) -> Dict:
        """
        Builds a semantic graph representation of sentence relationships.
        This is called by _analyze_semantic_relationships() but wasn't defined.
        """
        graph = {}
        try:
            for i, (sent, emb) in enumerate(zip(sentences, embeddings)):
                connections = []
                for j, other_emb in enumerate(embeddings):
                    if i != j:
                        similarity = np.dot(emb, other_emb) / \
                                (np.linalg.norm(emb) * np.linalg.norm(other_emb))
                        if similarity > 0.5:  # Threshold for meaningful connections
                            connections.append({
                                'target_sentence': j,
                                'similarity': float(similarity),
                                'relationship_type': self._determine_relationship_type(similarity)
                            })
                graph[i] = {
                    'sentence': sent,
                    'connections': connections,
                    'centrality': len(connections)
                }
            return graph
        except Exception as e:
            self.logger.error(f"Error building semantic graph: {e}")
            return {}
        
    def _analyze_discourse_patterns(self, doc) -> Dict:
        """
        Analyzes discourse patterns in the text.
        Called by _analyze_semantic_relationships() but wasn't defined.
        """
        patterns = {
            'connectives': [],
            'topic_shifts': [],
            'rhetorical_structures': []
        }
        
        # Analyze connecting words and phrases
        discourse_markers = {
            'addition': ['moreover', 'furthermore', 'additionally'],
            'contrast': ['however', 'nevertheless', 'although'],
            'causation': ['therefore', 'consequently', 'thus'],
            'sequence': ['firstly', 'subsequently', 'finally']
        }
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            for category, markers in discourse_markers.items():
                for marker in markers:
                    if marker in sent_text:
                        patterns['connectives'].append({
                            'marker': marker,
                            'category': category,
                            'sentence': sent.text
                        })
        
        # Analyze topic shifts
        prev_topic = None
        for sent in doc.sents:
            current_topic = self._extract_sentence_topic(sent)
            if prev_topic and current_topic != prev_topic:
                patterns['topic_shifts'].append({
                    'from_topic': prev_topic,
                    'to_topic': current_topic,
                    'sentence': sent.text
                })
            prev_topic = current_topic
        
        return patterns
    
    def _analyze_semantic_coherence(self, semantic_graph: Dict) -> Dict:
        """
        Analyzes the semantic coherence of the text based on the semantic graph.
        Called by _analyze_semantic_relationships() but wasn't defined.
        """
        try:
            # Calculate global coherence metrics
            all_similarities = []
            for node in semantic_graph.values():
                similarities = [conn['similarity'] for conn in node['connections']]
                if similarities:
                    all_similarities.extend(similarities)
            
            # Calculate various coherence metrics
            coherence_metrics = {
                'global_coherence': float(np.mean(all_similarities)) if all_similarities else 0.0,
                'coherence_variance': float(np.std(all_similarities)) if all_similarities else 0.0,
                'connectivity_density': len(all_similarities) / len(semantic_graph) if semantic_graph else 0.0
            }
            
            # Identify coherence patterns
            coherence_patterns = {
                'strong_connections': sum(1 for s in all_similarities if s > 0.8),
                'weak_connections': sum(1 for s in all_similarities if s < 0.5),
                'average_connections_per_sentence': len(all_similarities) / len(semantic_graph) if semantic_graph else 0
            }
            
            return {
                'metrics': coherence_metrics,
                'patterns': coherence_patterns,
                'coherence_assessment': self._assess_coherence_level(coherence_metrics)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing semantic coherence: {e}")
            return {
                'metrics': {},
                'patterns': {},
                'coherence_assessment': 'unknown'
            }
        
    def _extract_key_concepts(self, semantic_graph: Dict) -> List[Dict]:
        """
        Extracts key concepts from the semantic graph based on centrality and connections.
        """
        concepts = []
        try:
            # Sort nodes by centrality
            central_nodes = sorted(
                semantic_graph.items(),
                key=lambda x: x[1]['centrality'],
                reverse=True
            )
            
            # Extract top concepts
            for node_id, node_data in central_nodes[:5]:  # Top 5 most central concepts
                concepts.append({
                    'concept': self._extract_main_concept(node_data['sentence']),
                    'centrality_score': node_data['centrality'],
                    'connected_concepts': [
                        self._extract_main_concept(semantic_graph[conn['target_sentence']]['sentence'])
                        for conn in node_data['connections']
                    ]
                })
            
            return concepts
        except Exception as e:
            self.logger.error(f"Error extracting key concepts: {e}")
            return []
        
    def _extract_sentence_topic(self, sent) -> str:
        """
        Extracts the main topic of a sentence using NLP analysis.
        """
        # Extract noun phrases as potential topics
        noun_phrases = [chunk.text for chunk in sent.noun_chunks]
        
        if not noun_phrases:
            return None
            
        # Use the first noun phrase as the topic
        # This is a simplified approach - could be enhanced with more sophisticated topic modeling
        return noun_phrases[0]
    
    def _assess_coherence_level(self, coherence_metrics: Dict) -> str:
        """
        Assesses the overall coherence level based on computed metrics.
        """
        global_coherence = coherence_metrics.get('global_coherence', 0)
        connectivity = coherence_metrics.get('connectivity_density', 0)
        
        if global_coherence > 0.8 and connectivity > 0.7:
            return 'high'
        elif global_coherence > 0.6 and connectivity > 0.5:
            return 'medium'
        else:
            return 'low'
        
    def _normalize_input(self, prompt_input: Union[str, Dict]) -> str:
        """
        Normalizes the input prompt to ensure consistent processing.
        """
        if isinstance(prompt_input, dict):
            return prompt_input.get('original_prompt', '')
        return str(prompt_input)

  


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




class AnalysisStage(PipelineStage):
    def __init__(self, logger: Logger, api_handler: APIHandler, context_tracker: ContextTracker):
        super().__init__(logger, api_handler, context_tracker)
        self.preprocessor = EnhancedPromptPreprocessor(logger)

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
            prompt, ai_type, style = self._validate_pipeline_context(pipeline_context)

            # preprocessing_result = await self._execute_preprocessing(prompt)
            # self.logger.debug(f"Preprocessing result: {preprocessing_result}")

            # Create analysis-focused system message
            system_message = """You are a prompt engineering technique expert.
Your task is to analyze user requests and determine the most effective prompt engineering approach.
You must identify one primary technique that best suits the user's needs.

IMPORTANT: You must provide detailed technique requirements including both primary factors and constraints.

Return ONLY a JSON response with your analysis and selected technique.
DO NOT include any explanations or additional text outside the JSON structure."""

            analysis_prompt = f"""Analyze this request to determine the most suitable prompt engineering technique:

Request: "{prompt}"

Select ONE technique from:
1. Chain-of-Thought (CoT): Best for complex reasoning, step-by-step problem solving
2. Tree of Thoughts (ToT): For creative tasks, multiple solution paths
3. Auto-CoT: For automated reasoning chain generation
4. Few-shot: For tasks needing examples
5. Zero-shot: For straightforward, clear instructions

CRITICAL: You must provide comprehensive technique requirements.

Return in this EXACT format:
{{
    "selected_technique": "technique_name",
    "reasoning": "brief explanation of selection",
    "request_characteristics": ["characteristic1", "characteristic2"],
    "technique_requirements": {{
        "primary_factors": [
            "specific implementation requirement 1",
            "specific implementation requirement 2"
        ],
        "constraints": [
            "specific constraint 1",
            "specific constraint 2"
        ]
    }}
}}"""
           

            response = await self.api_handler.make_api_call(
                system_message=system_message,
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=1000
            )

            # processed_response = self._process_analysis_response(response.get("content", ""), pipeline_context)
            technique_info = self._process_technique_selection(response.get("content", ""))

            return {
                "analysis_results": {
                    
                    "technique": technique_info,
                    "original_prompt": prompt,
                    "ai_type": ai_type,
                    "style": style
                },
                "_metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "analysis"
                }
            }

        except Exception as e:
            self.logger.error(f"Analysis stage failed: {str(e)}", exc_info=True)
            return self._create_fallback_analysis(pipeline_context)

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

    async def _execute_preprocessing(self, prompt: str) -> Dict:
        """Execute preprocessing with proper error handling"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.preprocessor.analyze_prompt,
                prompt
            )
        except Exception as e:
            self.logger.error(f"Preprocessing failed: {str(e)}")
            return self.preprocessor._create_fallback_preprocessing(prompt)

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

    

    # def _clean_json_content(self, content: str) -> str:
    #     """Clean and extract JSON from response content"""
    #     try:
    #         # Remove any markdown formatting
    #         content = re.sub(r'```json\s*|\s*```', '', content)
            
    #         # Find JSON boundaries
    #         start = content.find('{')
    #         end = content.rfind('}') + 1
            
    #         if start != -1 and end > start:
    #             return content[start:end]
                
    #         raise ValueError("No valid JSON found in content")
            
    #     except Exception as e:
    #         self.logger.error(f"JSON cleaning failed: {str(e)}")
    #         raise

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
    


    async def execute(self, pipeline_context: Dict) -> Dict:
        try:
            # Enhanced context extraction
            analysis = pipeline_context.get("stage_results", {}).get("analysis", {}).get("analysis_results", {})
            technique_info = analysis.get("technique", {})
            original_prompt = analysis.get("original_prompt", "")
            ai_type = analysis.get("ai_type", "")
            style = analysis.get("style", "professional")

            system_message = self._create_system_message(analysis, ai_type, style)

            # Ultra-Precise System Message
#             system_message = f"""You are a WORLD-CLASS prompt engineering expert specializing in {ai_type} systems.
# Your task is to provide SPECIFIC, FOCUSED GUIDANCE for constructing prompts based on:
# 1. The user's specific request and context
# 2. {ai_type}'s specific capabilities and interaction patterns,the user is writing the prompts on this specific ai platform.
# 3. {style} style requirements
# RETURN ONLY:
# 1. Core Prompt Requirements - What MUST be included
# 2. Style-Specific Guidelines - How to maintain {style} style,In the "Style-Specific Guidelines" section, include common mistakes or pitfalls to avoid when maintaining the specified style.
# 3. AI-Specific Optimizations - Best practices for {ai_type}
# 4. Key Considerations - Critical factors for this specific request
# 5. Ensure all guidelines are directly tied to the user's intent, as identified in the analysis stage.
# 6.Suggest at least one way the user can validate the prompt's effectiveness in meeting their specific needs.

# Keep responses CONCISE and ACTIONABLE. 

# CRITICAL GUIDELINE COMPOSITION INSTRUCTIONS:
# CRITICAL - 

# DO NOT GENERATE ANYTHIN WITHOUT CONFIRMING THE UNDERSTANDING OF MY REQUEST, IF THERE IS ANY CLARITY MISSING , ASK ME FOLLOW UP QUESTIONS BEFORE GENERATING AND ONLY THEN GENERATE.
# 1. MAXIMUM response length: 500 words
# 2. Provide concise, bullet-pointed strategies for each section.
# 3. DO NOT GENERATE ANY EXAMPLES AS IT WILL LEAD TO HALLUCNIATIONS FOR PROMPT CREATION
# FAILURE TO MEET THESE REQUIREMENTS RESULTS IN IMMEDIATE REGENERATION OF THE RESPONSE."""

 
            user_message = f"""Generate focused guidelines for constructing prompts for:

CONTEXT:
Original Request: "{original_prompt}"
Selected Technique: {technique_info.get('name')}
Technique Reasoning: {technique_info.get('reasoning')}

REQUIREMENTS:
- AI Platform: {ai_type}
- Response Style: {style}
- Technique Implementation: {technique_info.get('name')}

Generate comprehensive guidelines that integrate:
1. {technique_info.get('name')} implementation strategies
2. {style} style requirements
3. {ai_type} platform optimization

Focus on creating guidelines that will help generate prompts that:
1. Follow {technique_info.get('name')} principles correctly
2. Maintain {style} style consistently
3. Optimize for {ai_type} capabilities"""

            # Enhanced API Call with More Generous Creativity Parameters
            response = await self.api_handler.make_api_call(
            system_message=system_message,
            prompt=user_message
        )
            
            # Advanced Response Processing
            formatted_response = {
            "content": response.get("content", ""),
            "context": {
                "prompt": original_prompt,
                "ai_type": ai_type,
                "style": style
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

    def _create_system_message(self, analysis_result: Dict, ai_type: str, style: str) -> str:
        # Extract prompt engineering technique from analysis
        technique = analysis_result.get("technique", {})
        technique_name = technique.get("name", "Chain-of-Thought")
        technique_reasoning = technique.get("reasoning", "")

        return f"""You are a WORLD-CLASS prompt engineering expert specializing in {ai_type} systems.
    Your task is to provide SPECIFIC, FOCUSED GUIDANCE for constructing prompts using the {technique_name} technique.

    CONTEXT AND REQUIREMENTS:
    1. Prompt Engineering Technique: {technique_name}
    - Reasoning: {technique_reasoning}
    - Implementation Requirements: Follow {technique_name} specific patterns
    2. AI System: {ai_type} specific capabilities and interaction patterns
    3. Style: {style} communication requirements

    GENERATE GUIDELINES COVERING:
    1. {technique_name} Implementation:
    - How to structure the prompt following {technique_name} principles
    - Key elements that must be included
    - Common pitfalls to avoid

    2. Style-Specific Guidelines:
    - How to maintain {style} style
    - Style integration with {technique_name}
    - Common style-related mistakes to avoid

    3. {ai_type} Optimization:
    - Platform-specific best practices
    - Integration with {technique_name}
    - Key considerations for this AI platform

    4. Success Criteria:
    - How to validate prompt effectiveness
    - Quality indicators to check
    - Implementation validation steps

    CRITICAL GUIDELINES FOR COMPOSITION:
    1. Maximum response length: 500 words
    2. Provide concise, actionable strategies
    3. Focus on practical implementation
    4. Ensure all guidelines align with {technique_name} principles
    """
        
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

    def _create_system_message(self, ai_type: str, style: str) -> str:
        # First, let's define AI-specific characteristics
        ai_characteristics = {
            'ChatGPT': {
                'capabilities': ['natural language understanding', 'contextual awareness'],
                'constraints': ['token limit', 'recency cutoff'],
                'interaction_patterns': ['dialogue-based', 'context-window aware']
            },
            'Claude': {
                'capabilities': ['long-form content', 'complex reasoning'],
                'constraints': ['specific formatting requirements'],
                'interaction_patterns': ['detailed instruction following']
            }
            # Add other AI types
        }

        # Then, define style characteristics
        style_characteristics = {
            'descriptive': {
                'sentence_patterns': ['detailed explanations', 'rich descriptions'],
                'vocabulary_level': 'comprehensive',
                'organization': 'hierarchical'
            },
            'professional': {
                'sentence_patterns': ['clear statements', 'formal structure'],
                'vocabulary_level': 'industry-standard',
                'organization': 'logical'
            }
            # Add other styles
        }

        return f"""You are a specialized prompt engineering expert for {ai_type} systems.
        System Characteristics to Consider:
        - Capabilities: {', '.join(ai_characteristics[ai_type]['capabilities'])}
        - Constraints: {', '.join(ai_characteristics[ai_type]['constraints'])}
        - Interaction Patterns: {', '.join(ai_characteristics[ai_type]['interaction_patterns'])}
        
        Style Requirements ({style}):
        - Sentence Structure: {', '.join(style_characteristics[style]['sentence_patterns'])}
        - Vocabulary Level: {style_characteristics[style]['vocabulary_level']}
        - Organization: {style_characteristics[style]['organization']}
        
        Your task is to generate prompts that:
        1. Leverage {ai_type}'s specific capabilities
        2. Work within its constraints
        3. Follow {style} communication patterns
        4. Maintain consistency in tone and approach"""




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

    async def execute(self, pipeline_context: Dict) -> Dict:
        try:
            self.logger.info("Starting enhancement stage execution")
            
            # Extract and resolve any coroutines from context
            analysis = await self._resolve_coroutine(
                pipeline_context.get("stage_results", {}).get("analysis", {}).get("analysis_results", {})
            )
            guidelines = await self._resolve_coroutine(
                pipeline_context.get("stage_results", {}).get("guidelines", {}).get("content", "")
            )
            
            # Now we can safely log the resolved context
            original_prompt = analysis.get("original_prompt", "")
            ai_type = analysis.get("ai_type", "")
            style = analysis.get("style", "")

            self.logger.debug(f"Original Prompt: {original_prompt}")
            self.logger.debug(f"AI Type: {ai_type}")
            self.logger.debug(f"Style: {style}")
            self.logger.debug(f"Guidelines: {guidelines}")
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
            response = await self.api_handler.make_api_call(
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
                content = response.get("content", "")
                self.logger.debug(f"Raw response content: {content}")
                
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed = json.loads(json_str)
                    
                    if "prompts" not in parsed or not isinstance(parsed["prompts"], list):
                        raise ValueError("Invalid response structure - missing prompts array")
                    
                    prompts = parsed["prompts"][:3]
                    while len(prompts) < 3:
                        prompts.append({"prompt": f"Additional enhanced version of: {original_prompt}"})
                    
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

    async def _resolve_coroutine(self, value: Any) -> Any:
        """Helper method to resolve coroutines and return regular values"""
        if asyncio.iscoroutine(value):
            return await value
        elif isinstance(value, dict):
            return {k: await self._resolve_coroutine(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [await self._resolve_coroutine(item) for item in value]
        return value

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
        
    # def _create_system_message(self, ai_type: str, style: str) -> str:
    #     return f"""You are a prompt enhancement expert for {ai_type} systems.
    #     Generate three optimized versions of the original prompt that are:
    #     1. Adapted specifically for {ai_type} capabilities
    #     2. Following {style} style strictly
    #     3. Direct and implementation-ready
        
    #     Return ONLY in this exact JSON structure:
    #     {{
    #         "prompts": [
    #             {{ "prompt": "first_enhanced_version" }},
    #             {{ "prompt": "second_enhanced_version" }},
    #             {{ "prompt": "third_enhanced_version" }}
    #         ]
    #     }}"""

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
        self.logger.info("Initializing Enhanced Prompt Pipeline...")
        self.api_handler = APIHandler(logger)
        self.preprocessor = EnhancedPromptPreprocessor(logger)  # Use new preprocessor
        self.context_tracker = ContextTracker()
        self.analysis_stage = AnalysisStage(logger, self.api_handler, self.context_tracker)
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

    def analyze_prompt(self, prompt: str) -> Dict:
        """Enhanced prompt analysis focusing on actionable insights"""
        doc = self.nlp(prompt)
        
        # Extract actionable patterns
        command_patterns = self._extract_command_patterns(doc)
        domain_requirements = self._extract_domain_requirements(doc)
        technical_constraints = self._extract_technical_constraints(doc)
        
        return {
            "execution_patterns": {
                "primary_command": command_patterns['primary'],
                "modifiers": command_patterns['modifiers'],
                "constraints": command_patterns['constraints']
            },
            "domain_context": {
                "technical_level": self._assess_technical_level(doc),
                "domain_specific_terms": domain_requirements['terms'],
                "required_expertise": domain_requirements['expertise_level']
            },
            "implementation_requirements": {
                "explicit_constraints": technical_constraints['explicit'],
                "implicit_requirements": technical_constraints['implicit'],
                "success_criteria": self._extract_success_criteria(doc)
            }
        }

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
    # async def execute_pipeline(self, prompt: str, ai_type: str, style: str) -> Dict:
    #     """Execute pipeline with parallel preprocessing and guidelines"""
    #     try:
    #         self.logger.info(f"Starting pipeline execution for AI type: {ai_type}, style: {style}")
            
    #         # Create base context
    #         base_context = {
    #             "request_id": str(uuid.uuid4()),
    #             "original_prompt": prompt,
    #             "ai_type": ai_type,
    #             "style": style,
    #             "timestamp": datetime.datetime.now().isoformat(),
    #             "stage_results": {},
    #             "context_chain": []
    #         }
            
    #         self.logger.debug(f"Created base context: {json.dumps(base_context, indent=2)}")

    #         # Create tasks for parallel execution
    #         self.logger.info("Initiating parallel preprocessing and guidelines generation")
            
    #         preprocessing_task = asyncio.create_task(
    #             self._execute_preprocessing(prompt)
    #         )
            
    #         guidelines_task = asyncio.create_task(
    #             self._execute_guidelines(base_context)
    #         )

    #         analysis_result = await self._execute_analysis(prompt, ai_type, style)
    #         base_context["stage_results"]["analysis"] = analysis_result

            
    #         # Wait for both tasks to complete
    #         preprocessing_result, guidelines_result = await asyncio.gather(
    #             preprocessing_task,
    #             guidelines_task,
    #             return_exceptions=True
    #         )

            
    #         self._log_stage_result("analysis", analysis_result)
            
    #         # Handle potential errors from parallel execution
    #         if isinstance(preprocessing_result, Exception):
    #             self.logger.error(f"Preprocessing failed: {str(preprocessing_result)}")
                
                
    #         if isinstance(guidelines_result, Exception):
    #             self.logger.error(f"Guidelines generation failed: {str(guidelines_result)}")
    #             guidelines_result = self._create_fallback_guidelines(base_context)

    #         # Update context with results
    #         base_context["stage_results"].update({
    #         "preprocessing": preprocessing_result if not isinstance(preprocessing_result, Exception) else self._create_fallback_preprocessing(prompt),
    #         "guidelines": guidelines_result if not isinstance(guidelines_result, Exception) else self._create_fallback_guidelines(base_context),
    #         "analysis": analysis_result if not isinstance(analysis_result, Exception) else self._create_fallback_analysis(prompt, ai_type, style)
    #     })
            
    #         self.logger.info("Preprocessing and guidelines generation completed")
    #         self.logger.debug(f"Updated context: {json.dumps(base_context, indent=2)}")

    #         # Execute enhancement stage with combined results
    #         self.logger.info("Starting enhancement stage")
    #         enhancement_result = await self._execute_enhancement(base_context)
    #         self._log_stage_result("enhancement", enhancement_result)
    #         base_context["stage_results"]["enhancement"] = enhancement_result
            
    #         self.logger.info("Pipeline execution completed successfully")
    #         return self._format_final_response(base_context)

    #     except Exception as e:
    #         self.logger.error(f"Pipeline execution failed: {str(e)}")
    #         self.logger.exception("Full traceback:")
    #         return self._create_error_response(str(e))

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

            # Execute stages sequentially and resolve results
            analysis_result = await self._execute_analysis(prompt, ai_type, style)
            base_context["stage_results"]["analysis"] = await self._resolve_result(analysis_result)
            
            guidelines_result = await self._execute_guidelines(base_context)
            base_context["stage_results"]["guidelines"] = await self._resolve_result(guidelines_result)
            
            enhancement_result = await self._execute_enhancement(base_context)
            base_context["stage_results"]["enhancement"] = await self._resolve_result(enhancement_result)

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
    async def _execute_preprocessing(self, prompt: str) -> Dict:
        """Execute preprocessing in thread pool"""
        self.logger.info("Executing preprocessing stage")
        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(
                executor,
                self.preprocessor.preprocess_prompt,
                prompt
            )

    def _log_stage_result(self, stage_name: str, result: Any):
        """Enhanced stage result logging"""
        if isinstance(result, Exception):
            self.logger.error(f"{stage_name} stage failed: {str(result)}")
            self.logger.debug(f"{stage_name} full error: {traceback.format_exc()}")
        else:
            self.logger.info(f"{stage_name} stage completed successfully")
            self.logger.debug(f"{stage_name} result: {json.dumps(result, indent=2)}")

    async def _execute_guidelines(self, context: Dict) -> Dict:
        """Execute guidelines stage in thread pool"""
        self.logger.info("Executing guidelines stage")
        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(
                executor,
                self.guidelines_stage.execute,
                context
            )

    async def _execute_enhancement(self, context: Dict) -> Dict:
        """Execute enhancement stage"""
        self.logger.info("Executing enhancement stage")
        return await self.enhancement_stage.execute(context)

    def _format_final_response(self, context: Dict) -> Dict:
        """Format the final pipeline response"""
        self.logger.info("Formatting final response")
        try:
            response = {
                "status": "success",
                "request_id": context["request_id"],
                "metadata": {
                    "timestamp": context["timestamp"],
                    "ai_type": context["ai_type"],
                    "style": context["style"]
                },
                "stages": context["stage_results"],
                "enhancement_result": context["stage_results"].get("enhancement", {}).get("result", {})
            }
            self.logger.debug(f"Final response: {json.dumps(response, indent=2)}")
            return response
        except Exception as e:
            self.logger.error(f"Error formatting final response: {str(e)}")
            return self._create_error_response(str(e))

    async def _execute_analysis(self, prompt: str, ai_type: str, style: str) -> Dict:
        try:
            self.logger.info(f"Starting analysis for prompt: '{prompt[:50]}...'")
            
            # Get preprocessing results from context
            preprocessing_result = await self._execute_preprocessing(prompt)
            
            analysis_context = {
                "original_prompt": prompt,
                "ai_type": ai_type,
                "style": style,
                "preprocessing_results": preprocessing_result
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

    def _validate_stage_result(self, result: Dict, stage_name: str) -> bool:
        try:
            if not isinstance(result, dict):
                self.logger.error(f"{stage_name} stage returned invalid result type: {type(result)}")
                return False
                
            required_fields = {
                "analysis": ["content", "analysis_results"],
                "preprocessing": ["linguistic_features", "basic_analysis"],
                "guidelines": ["implementation_strategy", "success_indicators"],
                "enhancement": ["prompts", "context"]
            }
            
            fields = required_fields.get(stage_name, [])
            if not all(field in result for field in fields):
                self.logger.error(f"{stage_name} stage missing required fields: {fields}")
                return False
            
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
        self.preprocessor = EnhancedPromptPreprocessor()
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
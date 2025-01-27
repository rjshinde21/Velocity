import os
import json
import ast
from groq import Groq
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Retrieve the API key for Groq from the environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Initialize the Groq client with the API key
CLIENT = Groq(api_key=GROQ_API_KEY)

# Define the model to be used for the analysis
MODEL = "llama-3.3-70b-versatile"

# System message for analyzing and enhancing the user's prompt
SYSTEM_MESSAGE_MAIN = """
You are a system that performs a comprehensive analysis and enhancement of USER PROMPT. Also mention prompt engineering technique implemented. Do NOT answer the user's prompt. 
Please provide a detailed response in one sentence. Also track improvement metrics such as clarity, context, specificity score out of 1
output response and prompt engineering technique implemented in the following dictionary format;
'text': response,
 'technique': prompt engineering technique implemented,
  'improvement_metrics':{
      'clarity': evaluate: clarity score of enhanced USER PROMPT - clarity score of USER PROMPT and put + befor it if increased else put -,
      'context': evaluate: clarity score of enhanced USER PROMPT - clarity score of USER PROMPT and put + befor it if increased else put -,
      'specificity': evaluate: clarity score of enhanced USER PROMPT - clarity score of USER PROMPT and put + befor it if increased else put -,
  }
don't write anything except above format
"""

# System message for scoring the user's prompt based on clarity and context
SYSTEM_MESSAGE_USER_PROMPT_SCORE = """
You are a system that performs a comprehensive analysis of USER PROMPT and evaluates context score, and clarity score out of 1. Also identify missing elements such as array type, sorting order, performance requirements, etc.
Output context score, clarity score, and missing elements in the following dictionary format;
'missing_elements':['first missing element', 'second missing element', 'third missing element', and so on...],
 'context_score': context score,
 'clarity_score': clarity score
 don't write anything except above format
"""

# System message for recommending suitable LLMs based on prompt complexity and task type
SYSTEM_MESSAGE_LLM_MODEL_AND_REASONING = """
You are a system that performs a comprehensive analysis of USER PROMPT and recommends suitable LLMs based on prompt complexity, required capabilities, task type (creative, analytical, code, etc.)
and provides reasoning for model selection.
Output recommended LLMs and their respective reasoning for model selection in the following dictionary format;
'model': first recommended LLM,
'reasoning': reasoning for the respective model selection,
'model': second recommended LLM,
'reasoning': reasoning for the respective model selection,
    and so on...
don't write anything except above format
"""

# User's initial prompt asking for code to sort an array
USER_PROMPT = "what are powerplants"

# Create the messages to send to the LLM for the different analyses
messages_main = [
    {"role": "system", "content": SYSTEM_MESSAGE_MAIN},
    {"role": "user", "content": USER_PROMPT},
]

messages_user_prompt_score = [
    {"role": "system", "content": SYSTEM_MESSAGE_USER_PROMPT_SCORE},
    {"role": "user", "content": USER_PROMPT},
]

messages_llm_model_and_reasoning = [
    {"role": "system", "content": SYSTEM_MESSAGE_LLM_MODEL_AND_REASONING},
    {"role": "user", "content": USER_PROMPT},
]

# Function to call the LLM model and retrieve the response
def call_llm(messages):
    response = CLIENT.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=4096,
    )
    return response

# Get response from the LLM for analyzing the user's prompt
response_main = call_llm(messages_main)

# Get response from the LLM for evaluating the user's prompt score
response_user_prompt_score = call_llm(messages_user_prompt_score)

# Get response from the LLM for recommending suitable models and reasoning
response_llm_model_and_reasoning = call_llm(messages_llm_model_and_reasoning)

# Prepare the user input data
user_input = {
    "Input": {
        "prompt": USER_PROMPT
    }
}

def safe_literal_eval(response_content):
    try:
        # Attempt to parse as JSON
        return json.loads(response_content)
    except json.JSONDecodeError:
        print("JSON parsing failed, trying literal_eval...")
        try:
            # Attempt to fix the string for Python parsing
            sanitized_content = response_content.replace("'", "\"")  # Convert single quotes to double quotes
            return ast.literal_eval(sanitized_content)
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

# Prepare the expected output with enhanced prompt, analysis, and recommended LLMs
expected_output = {
    "Expected Output": {
        "analysis": safe_literal_eval(response_user_prompt_score.choices[0].message.content),
        "recommended_llm": safe_literal_eval(response_llm_model_and_reasoning.choices[0].message.content),
        "enhanced_prompt": safe_literal_eval(response_main.choices[0].message.content),
    }
}

# Combine the user input and expected output into a structured JSON format and print
final_data = json.dumps([user_input, expected_output], indent=4)
print(final_data)
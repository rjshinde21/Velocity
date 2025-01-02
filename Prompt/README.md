# AI-Powered Prompt Processing API

This Flask-based API enhances and processes text prompts using advanced NLP techniques and the Llama API. It offers robust prompt preprocessing, contextual analysis, and AI-generated improvements for various applications.

The project provides a flexible backend service for generating high-quality text responses based on user-provided prompts. It integrates with external AI services and includes various preprocessing steps to improve the quality of generated text.

## Repository Structure

- `app.py`: Main Flask application with route handlers and core functionality
- `backend.py`: Additional Flask routes and category processing logic
- `pb.py`: Advanced prompt processing and contextual analysis
- `x.py`: Alternative implementation of the main Flask application
- `package.json`: Node.js project configuration and dependencies
- `.env`: Environment variables file (not included in the repository)

## Usage Instructions

### Installation

1. Ensure you have Python 3.7+ installed
2. Clone the repository
3. Install dependencies:
   ```
   pip install flask flask-cors python-dotenv pyspellchecker llamaapi google-generativeai
   ```
4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Llama API key: `LLAMA_API_KEY=your_api_key_here`

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```
2. The server will run on `http://localhost:2000` by default

### API Endpoints

#### POST /process

Process a text prompt and generate improved versions.

Request body:
```json
{
  "prompt": "Your text prompt here",
  "AIType": "default",
  "style": "professional"
}
```

Response:
```json
{
  "response": {
    "prompts": [
      {"prompt": "Improved prompt 1"},
      {"prompt": "Improved prompt 2"},
      {"prompt": "Improved prompt 3"}
    ]
  }
}
```

#### GET /get_categories

Retrieve structured category data.

Response:
```json
[
  {
    "name": "Category Name",
    "dropdowns": [
      {
        "name": "Dropdown Name",
        "items": [
          {"name": "Item 1"},
          {"name": "Item 2"}
        ]
      }
    ]
  }
]
```

### Integration

To integrate this API into your project:

1. Send POST requests to `/process` with your prompt data
2. Handle the response to use the improved prompts in your application
3. Use the `/get_categories` endpoint to populate category-related UI elements

### Troubleshooting

- If you encounter "Llama API not properly configured" errors, ensure your `.env` file contains the correct API key
- For JSON parsing errors, verify that your request body is properly formatted
- Check the server logs for detailed error messages and stack traces

## Data Flow

1. Client sends a POST request to `/process` with prompt data
2. The server preprocesses the prompt:
   - Corrects spelling
   - Removes redundant phrases
   - Extracts style information
3. The processed prompt is sent to the Llama API
4. Llama API returns improved prompts
5. The server normalizes and formats the response
6. Improved prompts are sent back to the client

```
Client -> Flask Server -> Prompt Preprocessor -> Llama API
                                              -> Response Normalization
                                              -> Client
```

## Infrastructure

The project primarily uses Flask for the web server and integrates with external services. Key infrastructure components include:

- Flask web server
- Llama API integration
- Google's Generative AI (optional, based on `backend.py`)
- Spell checking library
- JSON processing for request/response handling

Note: This project does not have a dedicated infrastructure stack defined in the provided files.
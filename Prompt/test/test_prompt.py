from Prompt.prompt import app, EnhancedPromptPipeline
from Prompt.prompt import app, process_request
from flask import Flask
from flask import Flask, json
from flask import Flask, jsonify
from flask import Flask, jsonify, request
from flask import Flask, request, jsonify
from flask.testing import FlaskClient
from Prompt.prompt import app, EnhancedPromptPipeline
from Prompt.prompt import app, process_request
from Prompt.prompt import process_request
from unittest.mock import patch, MagicMock
import datetime
import json
import pytest

class TestPrompt:

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('prompt.request')
    def test_process_request_2(self, mock_request):
        """
        Testcase 2 for def process_request():
        Path constraints: not (request.is_json) and request.content_type == 'application/x-www-form-urlencoded', not (not form_data)
        returns: jsonify({
                    "status": "error",
                    "error": "Invalid JSON in form data",
                    "timestamp": datetime.datetime.now().isoformat()
                }), 400
        """
        # Setup
        mock_request.is_json = False
        mock_request.content_type = 'application/x-www-form-urlencoded'
        mock_request.form = {'data': 'invalid json data'}

        # Execute
        with patch('prompt.jsonify') as mock_jsonify:
            mock_jsonify.side_effect = lambda x: x
            result, status_code = process_request()

        # Assert
        assert status_code == 400
        assert result['status'] == 'error'
        assert result['error'] == 'Invalid JSON in form data'
        assert 'timestamp' in result
        
        # Verify that the timestamp is a valid ISO format string
        try:
            datetime.datetime.fromisoformat(result['timestamp'])
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    @patch('Prompt.prompt.request')
    def test_process_request_3(self, mock_request):
        """
        Testcase 3 for def process_request():
        Path constraints: not (request.is_json) and request.content_type == 'application/x-www-form-urlencoded', not form_data
        returns: jsonify({
                        "status": "error",
                        "error": "No data provided in form",
                        "timestamp": datetime.datetime.now().isoformat()
                    }), 400
        """
        # Setup
        mock_request.is_json = False
        mock_request.content_type = 'application/x-www-form-urlencoded'
        mock_request.form = MagicMock()
        mock_request.form.get.return_value = None  # Simulating no form data

        # Execute
        with app.test_request_context():
            response, status_code = process_request()

        # Assert
        assert status_code == 400
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data['status'] == 'error'
        assert response_data['error'] == 'No data provided in form'
        assert 'timestamp' in response_data
        
        # Verify the timestamp is in the correct format
        try:
            datetime.datetime.fromisoformat(response_data['timestamp'])
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")

    def test_process_request_4(self, client):
        """
        Test case for process_request() when form data is present but contains invalid JSON.
        """
        # Mock the request object
        with patch('prompt.request') as mock_request:
            # Set up the mock request
            mock_request.is_json = False
            mock_request.content_type = 'application/x-www-form-urlencoded'
            mock_request.form = {'data': 'invalid json data'}

            # Call the function
            response = process_request()

            # Assert the response
            assert response.status_code == 400
            data = json.loads(response.get_data(as_text=True))
            assert data['status'] == 'error'
            assert data['error'] == 'Invalid JSON in form data'
            assert 'timestamp' in data
            
            # Verify the timestamp is in the correct format
            try:
                datetime.datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pytest.fail("Timestamp is not in ISO format")

    def test_process_request_5(self, app):
        """
        Test case for process_request() when the Content-Type is unsupported.
        """
        with app.test_request_context('/process', method='POST', 
                                      content_type='application/xml'):
            # Mock the request object
            request.is_json = False
            request.content_type = 'application/xml'

            # Call the function
            response, status_code = process_request()

            # Parse the JSON response
            response_data = json.loads(response.get_data(as_text=True))

            # Assert the response structure and status code
            assert status_code == 415
            assert response_data['status'] == 'error'
            assert response_data['error'] == 'Unsupported Content-Type: application/xml'
            assert 'timestamp' in response_data

            # Verify the timestamp is in the correct format
            try:
                datetime.datetime.fromisoformat(response_data['timestamp'])
            except ValueError:
                pytest.fail("Timestamp is not in ISO format")

    def test_process_request_6(self, client):
        """
        Test case for process_request() when JSON data is missing 'prompt'.
        """
        # Prepare test data
        test_data = {"some_key": "some_value"}  # Missing 'prompt' key

        # Mock request.is_json to return True
        with patch('prompt.request') as mock_request:
            mock_request.is_json = True
            mock_request.get_json.return_value = test_data

            # Make a POST request to /process
            response = client.post('/process', json=test_data)

            # Assert the response
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert response_data['status'] == 'error'
            assert response_data['error'] == 'Missing prompt in request data'
            assert 'timestamp' in response_data

            # Verify the timestamp is in ISO format
            try:
                datetime.datetime.fromisoformat(response_data['timestamp'])
            except ValueError:
                pytest.fail("Timestamp is not in ISO format")

    def test_process_request_7(self, client: FlaskClient):
        """
        Test successful processing of a JSON request with valid prompt data.
        """
        # Prepare test data
        test_data = {
            "prompt": "Test prompt",
            "AIType": "analytical",
            "style": "concise"
        }

        # Mock EnhancedPromptPipeline
        mock_pipeline = MagicMock()
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "result": "Mocked pipeline result"
        }

        # Patch EnhancedPromptPipeline to return our mock
        with patch('prompt.EnhancedPromptPipeline', return_value=mock_pipeline):
            # Send POST request
            response = client.post('/process', 
                                   data=json.dumps(test_data),
                                   content_type='application/json')

            # Assert response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['status'] == 'success'
            assert response_data['result'] == 'Mocked pipeline result'

            # Verify that execute_pipeline was called with correct arguments
            mock_pipeline.execute_pipeline.assert_called_once_with(
                prompt=test_data['prompt'],
                ai_type=test_data['AIType'],
                style=test_data['style']
            )

    def test_process_request_empty_form_data(self, client):
        """Test process_request with empty form data"""
        response = client.post('/process', data={}, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'No data provided in form' in data['error']

    def test_process_request_empty_input(self, client):
        """Test process_request with empty input"""
        response = client.post('/process', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing prompt in request data' in data['error']

    def test_process_request_invalid_content_type(self, client):
        """Test process_request with invalid content type"""
        response = client.post('/process', data='invalid data', content_type='text/plain')
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Unsupported Content-Type' in data['error']

    def test_process_request_invalid_json(self, client):
        """Test process_request with invalid JSON in form data"""
        response = client.post('/process', data={'data': 'invalid json'}, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid JSON in form data' in data['error']

    def test_process_request_large_input(self, client):
        """Test process_request with a very large input"""
        large_prompt = 'a' * 1000000  # 1 million characters
        response = client.post('/process', json={'prompt': large_prompt})
        assert response.status_code == 200  # Assuming the server can handle large inputs
        data = json.loads(response.data)
        assert 'status' in data

    def test_process_request_missing_prompt(self, client):
        """Test process_request with missing prompt in JSON data"""
        response = client.post('/process', json={'AIType': 'descriptive'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing prompt in request data' in data['error']

    def test_process_request_no_form_data(self, client):
        """
        Test process_request when no form data is provided in a form-urlencoded request.
        """
        with patch('prompt.request') as mock_request:
            # Set up the mock request
            mock_request.is_json = False
            mock_request.content_type = 'application/x-www-form-urlencoded'
            mock_request.form = {'data': ''}

            # Make the request
            response = process_request()

            # Parse the JSON response
            response_data = json.loads(response.get_data(as_text=True))

            # Assertions
            assert response.status_code == 400
            assert response_data['status'] == 'error'
            assert response_data['error'] == 'No data provided in form'
            assert 'timestamp' in response_data

            # Check if the timestamp is a valid ISO format
            try:
                datetime.datetime.fromisoformat(response_data['timestamp'])
            except ValueError:
                pytest.fail("Timestamp is not in valid ISO format")

    @patch('Prompt.prompt.EnhancedPromptPipeline')
    def test_process_request_pipeline_exception(self, mock_pipeline, client):
        """Test process_request when pipeline execution raises an exception"""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.execute_pipeline.side_effect = Exception("Pipeline error")
        mock_pipeline.return_value = mock_pipeline_instance

        response = client.post('/process', json={'prompt': 'Test prompt'})
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Pipeline error' in data['error']

    def test_process_request_special_characters(self, client):
        """Test process_request with special characters in the prompt"""
        special_prompt = "!@#$%^&*()_+{}|:<>?~`-=[]\\;',./\n\t"
        response = client.post('/process', json={'prompt': special_prompt})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
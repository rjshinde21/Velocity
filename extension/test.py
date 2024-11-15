from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def test():
    return jsonify({"message": "Server is running!"})

@app.route('/test', methods=['GET'])
def test_categories():
    return jsonify([
        {
            "name": "Test Category",
            "items": ["Test Item 1", "Test Item 2"]
        }
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
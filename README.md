ClipForge AI

An open-source starter project for an AI-powered video clipping API.

Current Features

- FastAPI application
- Health-check endpoint
- Clip request endpoint
- Request validation using Pydantic
- Automated API tests

Project Structure

clipforge-ai/
├── clipforge/
│   └── main.py
├── tests/
│   └── test_api.py
└── requirements.txt

Installation

git clone https://github.com/Madarax018/clipforge-ai.git
cd clipforge-ai
pip install -r requirements.txt

Run the API

uvicorn clipforge.main:app --reload

Open "http://127.0.0.1:8000/docs" to explore the API.

Run Tests

pytest

Current Limitations

Actual video downloading, AI clip detection, and video rendering are not implemented yet.

Roadmap

- [ ] Video download support
- [ ] AI-powered highlight detection
- [ ] Automatic clip generation
- [ ] Vertical video export
- [ ] Subtitle generation

License

MIT License

# Contributing

## Setup

```bash
git clone https://github.com/kairav7220/email-agent.git
cd email-agent
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Development

- Fork the repo, create a feature branch.
- Test locally: `python app.py` then visit `http://localhost:5000`
- To test with real emails, set `EMAIL_ADDRESS` and `EMAIL_PASSWORD` in `.env`
- Ensure `.env` is in `.gitignore` before committing.

## PR Guidelines

- One feature/fix per PR.
- If changing the LLM provider, test with all three (Groq, Mistral, Gemini) before submitting.
- Update `knowledge_base.txt` if adding business context fields.
- Update `requirements.txt` if adding dependencies.

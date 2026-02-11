# Email Summarizer

A Python web application that authenticates with Gmail via OAuth, fetches emails from a specified sender, and uses Claude API to generate AI-powered summaries.

## Features

- **Google OAuth Authentication** - Securely connect your Gmail with read-only access
- **Email Filtering** - Fetch emails from any specific sender
- **AI Summarization** - Get concise, actionable summaries powered by Claude
- **Configurable Summary Length** - Choose between 3-10 line summaries

## Prerequisites

- Python 3.10+
- Google Cloud Project with Gmail API enabled
- Anthropic API key

## Setup

### 1. Clone and Install Dependencies

```bash
cd email-summarizer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Configure OAuth Consent Screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in the required fields (App name, User support email, Developer email)
   - Add scope: `https://www.googleapis.com/auth/gmail.readonly`
   - Add your email as a test user (required while in testing mode)
5. Create OAuth Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URI: `http://localhost:8000/auth/callback`
   - Save the **Client ID** and **Client Secret**

### 3. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Navigate to API Keys and create a new key

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
SECRET_KEY=<generate with: openssl rand -hex 32>
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
ANTHROPIC_API_KEY=sk-ant-your-api-key
DATABASE_URL=sqlite+aiosqlite:///./email_summarizer.db
TOKEN_ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000 in your browser.

## Usage

1. Click "Login with Google" on the home page
2. Authorize the application to read your emails
3. Enter the email address of the sender you want to summarize
4. Choose the number of summary lines (3-10)
5. Click "Generate Summary" to get your AI-powered summary

## Project Structure

```
email-summarizer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment settings
│   ├── auth/
│   │   ├── oauth.py         # Google OAuth flow
│   │   └── router.py        # Auth routes
│   ├── gmail/
│   │   ├── service.py       # Gmail API client
│   │   └── parser.py        # Email content extraction
│   ├── summarizer/
│   │   ├── service.py       # Claude API integration
│   │   └── prompts.py       # Prompt templates
│   ├── db/
│   │   ├── database.py      # SQLAlchemy setup
│   │   └── models.py        # User model
│   └── templates/           # Jinja2 HTML templates
├── static/css/style.css
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Security Notes

- OAuth refresh tokens are encrypted at rest using Fernet encryption
- Session cookies are HTTP-only and signed
- Only `gmail.readonly` scope is requested
- Email content is never persisted after summarization

## API Endpoints

- `GET /` - Home page
- `GET /dashboard` - Main dashboard (requires auth)
- `GET /auth/login` - Initiate Google OAuth
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Log out
- `POST /api/summarize` - Generate email summary
- `GET /health` - Health check

## License

MIT

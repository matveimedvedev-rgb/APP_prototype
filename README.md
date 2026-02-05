# Webglazer

A Django web application that analyzes websites, extracts features using OpenAI, and provides findability analysis to help improve how easily users can discover your website's capabilities.

## Features

- **Website Analysis**: Enter a URL to automatically extract key features using AI
- **Feature Management**: Edit, add, and delete features in a spreadsheet-like interface
- **AI Page Generation**: Generate AI-optimized pages based on your website and features
- **Findability Analysis**: Get comprehensive reports on how well users can find your features through search

## Requirements

- Python 3.8+
- Django 5.2+
- OpenAI API key
- Internet connection (for fetching websites)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd website_feature_finder
```

### 2. Create and activate virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django python-dotenv openai requests beautifulsoup4
```

### 4. Set up environment variables

Create a `.env` file in the project root (same level as `manage.py`):

```env
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=1
SECRET_KEY=your_secret_key_here
```

**Important**: 
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- For production, generate a secure `SECRET_KEY` (you can use `python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- Set `DEBUG=0` for production

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional, for admin access)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Step 1: Analyze a Website

1. Navigate to the home page (`http://127.0.0.1:8000/`)
2. Enter a website URL (e.g., `https://example.com`)
3. Click "Analyze"
4. The app will fetch the website, extract text, and use OpenAI to identify features
5. You'll be redirected to the Features Table page

### Step 2: Manage Features

1. On the Features Table page, you can:
   - Edit existing features inline
   - Add new features using "Add Row"
   - Delete features using the "Delete" button
   - Click "Save All" to persist changes

### Step 3: Generate AI Pages (Optional)

1. On the Features Table page, click "Generate AI Pages"
2. The app will create 3-5 AI-optimized pages based on your website and features
3. View generated pages by clicking the links
4. Pages are accessible at `/ai/<slug>/` but not indexed by search engines

### Step 4: Run Findability Analysis

1. Navigate to the Findability page
2. Click "Run Findability Analysis"
3. The app will:
   - Generate simulated user queries
   - Analyze how well your website supports those queries
   - Provide a comprehensive report with:
     - Overall findability score (0-100)
     - Per-feature findability notes
     - Content gaps
     - Recommendations for pages/FAQs to add
     - Suggested wording improvements

## Project Structure

```
website_feature_finder/
├── analyzer/              # Main app
│   ├── models.py          # AnalysisSession model
│   ├── views.py           # View functions
│   ├── templates/         # HTML templates
│   └── admin.py           # Admin configuration
├── config/                # Django project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # URL routing
├── .env                   # Environment variables (not in git)
├── .gitignore             # Git ignore rules
├── manage.py              # Django management script
└── README.md              # This file
```

## API Endpoints

- `/` - Website analysis page
- `/features/` - Features table page
- `/findability/` - Findability analysis page
- `/health/` - Health check endpoint (returns JSON)
- `/ai/<slug>/` - View AI-generated pages
- `/admin/` - Django admin interface

## Safety Features

- **URL Validation**: Only HTTP/HTTPS URLs allowed, basic security checks
- **Size Limits**: Website content limited to 50KB, text extraction limited to 8KB
- **Timeouts**: 10-second timeout for website fetching
- **Input Validation**: Feature length limits, empty input checks
- **Error Logging**: Comprehensive logging without leaking sensitive information
- **Robots Protection**: AI-generated pages not indexed by search engines

## Development

### Running Tests

```bash
python manage.py test
```

### Accessing Admin

1. Create a superuser: `python manage.py createsuperuser`
2. Navigate to `http://127.0.0.1:8000/admin/`
3. Login and manage AnalysisSession records

### Viewing Logs

Logs are output to the console. In production, configure Django logging in `settings.py`.

## Troubleshooting

### "OpenAI API key not configured"

- Ensure `.env` file exists in the project root
- Check that `OPENAI_API_KEY` is set correctly
- Restart the server after changing `.env`

### "Failed to fetch website"

- Check your internet connection
- Verify the URL is accessible
- Some websites may block automated requests

### "Template not found" errors

- Ensure you're running from the correct directory
- Check that templates are in `analyzer/templates/analyzer/`
- Restart the server

## Production Deployment

Before deploying:

1. Set `DEBUG=0` in `.env`
2. Generate a secure `SECRET_KEY`
3. Set `ALLOWED_HOSTS` in `settings.py`
4. Configure proper database (PostgreSQL recommended)
5. Set up static file serving
6. Configure proper logging
7. Use HTTPS
8. Set up environment variables securely (not in `.env` file)

## License

This is a prototype application for demonstration purposes.

## Support

For issues or questions, check the code comments or Django/OpenAI documentation.


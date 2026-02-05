from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import os
import re
import json
import logging
import requests
from urllib.parse import urlparse
from html.parser import HTMLParser
from dotenv import load_dotenv
from openai import OpenAI
from .models import AnalysisSession

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def get_or_create_session(request):
    """Get or create an AnalysisSession for the current Django session."""
    session_id = request.session.get('analysis_session_id')
    if session_id:
        try:
            session = AnalysisSession.objects.get(id=session_id)
            return session
        except AnalysisSession.DoesNotExist:
            pass
    
    # Create new session
    session = AnalysisSession.objects.create()
    request.session['analysis_session_id'] = session.id
    return session

def health(request):
    """Health check endpoint that returns status and OpenAI API key presence."""
    openai_key = os.getenv('OPENAI_API_KEY', '')
    has_openai_key = bool(openai_key and openai_key != 'your_key_here')
    
    return JsonResponse({
        'ok': True,
        'has_openai_key': has_openai_key
    })

class TextExtractor(HTMLParser):
    """Extract readable text from HTML, skipping navigation, cookies, and other non-content."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'meta', 'head', 'noscript', 'nav', 'footer', 'header'}
        self.skip_classes = {'cookie', 'banner', 'popup', 'modal', 'navigation', 'menu', 'sidebar'}
        self.in_skip = False
        self.current_tag = None
        self.current_attrs = {}
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
        # Skip certain tags entirely
        if tag in self.skip_tags:
            self.in_skip = True
            return
        
        # Skip elements with certain class names (cookies, banners, etc.)
        class_attr = self.current_attrs.get('class', '')
        if isinstance(class_attr, str):
            class_lower = class_attr.lower()
            for skip_class in self.skip_classes:
                if skip_class in class_lower:
                    self.in_skip = True
                    return
        
        # Skip elements with certain IDs
        id_attr = self.current_attrs.get('id', '')
        if isinstance(id_attr, str):
            id_lower = id_attr.lower()
            if any(skip in id_lower for skip in ['cookie', 'banner', 'popup', 'modal', 'nav', 'menu']):
                self.in_skip = True
                return
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags or self.in_skip:
            self.in_skip = False
        elif tag in {'p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.text.append(' ')
        self.current_tag = None
        self.current_attrs = {}
    
    def handle_data(self, data):
        if not self.in_skip:
            cleaned = data.strip()
            # Skip very short text that's likely navigation/menu items
            if cleaned and len(cleaned) > 2:
                # Skip common navigation text patterns
                if cleaned.lower() not in ['home', 'about', 'contact', 'login', 'sign in', 'menu', 'close', '×']:
                    self.text.append(cleaned)
    
    def get_text(self, max_length=10000):
        """Get extracted text, limited to max_length characters."""
        text = ' '.join(self.text)
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        if len(text) > max_length:
            text = text[:max_length] + '...'
        return text


def validate_url(url):
    """
    Validate URL format and safety.
    Returns (is_valid: bool, error_message: str or None)
    """
    if not url or not isinstance(url, str):
        return False, "URL is required"
    
    url = url.strip()
    if len(url) > 2048:  # RFC 7230 max URL length
        return False, "URL is too long (maximum 2048 characters)"
    
    parsed = urlparse(url)
    
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format. Please include http:// or https://"
    
    # Only allow http and https
    if parsed.scheme not in ('http', 'https'):
        return False, "Only HTTP and HTTPS URLs are allowed"
    
    # Basic security: prevent localhost/internal IPs in production (can be relaxed for dev)
    if parsed.hostname:
        hostname_lower = parsed.hostname.lower()
        if hostname_lower in ('localhost', '127.0.0.1', '0.0.0.0'):
            # Allow localhost in development
            pass
        elif hostname_lower.startswith('192.168.') or hostname_lower.startswith('10.'):
            return False, "Internal/private IP addresses are not allowed"
    
    return True, None


def fetch_website_text(url, timeout=10, max_size=500000):
    """
    Fetch website HTML and extract readable text.
    Returns (success: bool, text: str or error_message: str)
    Increased max_size to 500KB to handle larger websites.
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            logger.warning(f"URL validation failed: {error_msg} for URL: {url[:50]}...")
            return False, error_msg
        
        # Fetch with timeout and size limit
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; WebsiteFeatureFinder/1.0)'
        }
        logger.info(f"Fetching website: {url}")
        response = requests.get(url, timeout=timeout, headers=headers, stream=True)
        response.raise_for_status()
        
        # Check content size (warn but don't fail immediately - we'll extract text anyway)
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > max_size:
            logger.warning(f"Website large: {content_length} bytes for URL: {url[:50]}... (will extract text anyway)")
        
        # Read content with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size:
                logger.warning(f"Content size limit reached for URL: {url[:50]}... (stopping read, extracting text from what we have)")
                break  # Stop reading but continue with what we have
        
        # Extract text from HTML
        html_content = content.decode('utf-8', errors='ignore')
        extractor = TextExtractor()
        extractor.feed(html_content)
        text = extractor.get_text(max_length=8000)  # Limit text sent to OpenAI
        
        if not text or len(text.strip()) < 50:
            logger.warning(f"Insufficient text extracted from URL: {url[:50]}...")
            return False, "Could not extract enough readable text from the website"
        
        logger.info(f"Successfully extracted {len(text)} characters from URL: {url[:50]}...")
        return True, text
    
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout for URL: {url[:50]}...")
        return False, "Request timed out. The website may be slow or unreachable."
    except requests.exceptions.RequestException as e:
        # Don't log full exception to avoid leaking sensitive info
        logger.error(f"Request failed for URL: {url[:50]}... Error type: {type(e).__name__}")
        return False, f"Failed to fetch website: {str(e)[:200]}"  # Limit error message length
    except Exception as e:
        logger.exception(f"Unexpected error fetching URL: {url[:50]}...")
        return False, "An unexpected error occurred while fetching the website"


def extract_features_with_openai(website_url, website_text):
    """
    Use OpenAI to extract features from website text.
    Returns (success: bool, features: list or error_message: str)
    """
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if not openai_key or openai_key == 'your_key_here':
        return False, "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file."
    
    try:
        # Remove proxy-related env vars that might interfere with OpenAI client
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ.pop(var)
        
        client = OpenAI(api_key=openai_key, timeout=60.0)
        
        # Restore proxy vars if they existed
        for var, value in original_proxies.items():
            os.environ[var] = value
        
        prompt = f"""Analyze the following website content and extract a concise list of features, capabilities, or key selling points.

Website URL: {website_url}

Website Content:
{website_text}

Return a JSON array of feature strings (5-30 items). Each feature should be a concise, clear description (1-10 words).
Focus on:
- Product/service features
- Key capabilities
- Unique selling points
- Important functionality

Return ONLY a valid JSON array, no other text. Example format:
["Feature 1", "Feature 2", "Feature 3"]"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts features from website content. Always return valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        content = content.strip()
        
        features = json.loads(content)
        
        if not isinstance(features, list):
            return False, "OpenAI returned invalid format (expected a list)"
        
        if len(features) < 1:
            return False, "No features were extracted"
        
        # Validate and clean features
        cleaned_features = []
        for feature in features:
            if isinstance(feature, str) and feature.strip():
                cleaned_features.append(feature.strip())
        
        if not cleaned_features:
            return False, "No valid features were extracted"
        
        return True, cleaned_features
    
    except json.JSONDecodeError as e:
        return False, f"Failed to parse OpenAI response as JSON: {str(e)}"
    except Exception as e:
        return False, f"OpenAI API error: {str(e)}"


@require_http_methods(["GET", "POST"])
def website_analysis(request):
    """Page 1: Website analysis page."""
    session = get_or_create_session(request)
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        website_url = request.POST.get('website_url', '').strip()
        
        # Validate URL input
        if not website_url:
            error_message = "Please enter a website URL"
            logger.warning("Empty website URL submitted")
        else:
            # Additional validation
            is_valid, validation_error = validate_url(website_url)
            if not is_valid:
                error_message = validation_error
                logger.warning(f"URL validation failed: {validation_error}")
            else:
                # Fetch website text
                fetch_success, fetch_result = fetch_website_text(website_url)
            
            if not fetch_success:
                error_message = fetch_result
            else:
                # Extract features with OpenAI
                extract_success, extract_result = extract_features_with_openai(website_url, fetch_result)
                
                if not extract_success:
                    error_message = extract_result
                else:
                    # Save to session
                    session.website_url = website_url
                    session.features = extract_result
                    session.save()
                    
                    # Redirect to features page
                    return redirect('features_table')
    
    context = {
        'session': session,
        'session_id': session.id,
        'features_count': session.features_count,
        'ai_pages_count': session.ai_pages_count,
        'has_findability_report': session.has_findability_report,
        'error_message': error_message,
        'success_message': success_message,
    }
    return render(request, 'analyzer/website_analysis.html', context)

@require_http_methods(["GET", "POST"])
def features_table(request):
    """Page 2: Features table page."""
    session = get_or_create_session(request)
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        # Check if this is a generate AI pages request
        if 'generate_ai_pages' in request.POST:
            # This will be handled by generate_ai_pages view
            pass
        else:
            # Get features from form (can be multiple with same name)
            features_list = request.POST.getlist('features')
            
            # Validate and clean features
            if not features_list:
                error_message = "No features provided"
                logger.warning("Empty features list submitted")
            else:
                # Filter out empty features and validate length
                cleaned_features = []
                for f in features_list:
                    f_clean = f.strip()
                    if f_clean:
                        # Limit feature length
                        if len(f_clean) > 500:
                            logger.warning(f"Feature truncated from {len(f_clean)} to 500 characters")
                            f_clean = f_clean[:500]
                        cleaned_features.append(f_clean)
                
                if not cleaned_features:
                    error_message = "At least one non-empty feature is required"
                    logger.warning("All features were empty after cleaning")
                elif len(cleaned_features) > 100:
                    error_message = "Too many features (maximum 100 allowed)"
                    logger.warning(f"Too many features: {len(cleaned_features)}")
                else:
                    # Save to session
                    session.features = cleaned_features
                    session.save()
                    success_message = f"Successfully saved {len(cleaned_features)} feature(s)"
                    logger.info(f"Saved {len(cleaned_features)} features to session {session.id}")
    
    context = {
        'session': session,
        'session_id': session.id,
        'features': session.features if isinstance(session.features, list) else [],
        'features_count': session.features_count,
        'ai_pages': session.ai_pages if isinstance(session.ai_pages, list) else [],
        'ai_pages_count': session.ai_pages_count,
        'has_findability_report': session.has_findability_report,
        'error_message': error_message,
        'success_message': success_message,
    }
    return render(request, 'analyzer/features_table.html', context)

def generate_ai_pages_with_openai(website_url, features_list, num_pages=50):
    """
    Use OpenAI to generate AI-oriented pages based on website URL and features.
    Uses batching for large page counts to avoid token limits.
    Args:
        website_url: The website URL
        features_list: List of features
        num_pages: Number of pages to generate (10-300, default: 50)
    Returns (success: bool, pages: list or error_message: str)
    """
    # Validate and clamp num_pages
    try:
        num_pages = int(num_pages)
        num_pages = max(10, min(300, num_pages))  # Clamp between 10 and 300
    except (ValueError, TypeError):
        num_pages = 50  # Default to 50 if invalid
    
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if not openai_key or openai_key == 'your_key_here':
        return False, "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file."
    
    try:
        # Remove proxy-related env vars that might interfere with OpenAI client
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ.pop(var)
        
        client = OpenAI(api_key=openai_key, timeout=60.0)
        
        # Restore proxy vars if they existed
        for var, value in original_proxies.items():
            os.environ[var] = value
        
        features_text = '\n'.join([f"- {f}" for f in features_list[:20]])  # Limit to 20 features
        
        # Determine batch size based on number of pages
        # For large requests, batch in chunks of 20-30 pages per API call
        if num_pages <= 30:
            batch_size = num_pages
            batches = 1
        else:
            batch_size = 25  # Generate 25 pages per batch
            batches = (num_pages + batch_size - 1) // batch_size  # Ceiling division
        
        all_pages = []
        
        for batch_num in range(batches):
            # Calculate how many pages to generate in this batch
            pages_in_batch = min(batch_size, num_pages - len(all_pages))
            
            if pages_in_batch <= 0:
                break
            
            # Adjust prompt for batch context
            batch_context = ""
            if batches > 1:
                batch_context = f"\n\nThis is batch {batch_num + 1} of {batches}. Generate exactly {pages_in_batch} unique pages. Ensure all pages are different from previous batches."
            
            prompt = f"""Generate {pages_in_batch} AI-oriented web pages for a website. These pages are specifically designed for AI scrapers and LLM consumption to improve AI rankings. They should be:

1. Highly structured and machine-readable
2. Rich in semantic information and context
3. Optimized for AI understanding (not human SEO)
4. Include clear feature descriptions, use cases, and capabilities
5. Use structured data patterns that AI systems can easily parse
6. Focus on factual, comprehensive information about the website's offerings

Website URL: {website_url}

Key Features:
{features_text}
{batch_context}

Generate pages that would be useful for:
- AI assistants understanding what the website offers
- AI crawlers and LLM training data
- Improving AI rankings and discoverability
- Providing detailed, structured information about features

For each page, return a JSON object with:
- slug: URL-friendly identifier (lowercase, hyphens, no spaces) - MUST be unique
- title: Clear, descriptive title optimized for AI understanding
- content: Full HTML content with:
  * Clear semantic structure (use proper HTML tags: <h1>, <h2>, <p>, <ul>, <li>)
  * Rich context about features, benefits, and use cases
  * Structured information that AI systems can parse
  * Comprehensive descriptions (not marketing fluff)
  * Technical details and capabilities
  * Use cases and examples

The content should be written for AI consumption - focus on clarity, completeness, and machine-readability over human marketing appeal.

Return a JSON array of exactly {pages_in_batch} page objects. Example format:
[
  {{"slug": "features-overview", "title": "Features Overview", "content": "<h1>Features Overview</h1><p>...</p>"}},
  {{"slug": "capabilities", "title": "Capabilities", "content": "<h1>Capabilities</h1><p>...</p>"}}
]

Return ONLY valid JSON, no markdown code blocks or other text."""

            # Calculate max_tokens for this batch
            # Estimate: ~800-1200 tokens per page
            estimated_tokens = max(4000, pages_in_batch * 1000)
            max_tokens = min(16000, estimated_tokens)  # Cap at 16k (model limit)
            
            logger.info(f"Generating batch {batch_num + 1}/{batches}: {pages_in_batch} pages (max_tokens: {max_tokens})")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates AI-oriented web pages. Always return valid JSON arrays with the exact number of pages requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'```\s*$', '', content)
            content = content.strip()
            
            batch_pages = json.loads(content)
            
            if not isinstance(batch_pages, list):
                logger.warning(f"Batch {batch_num + 1} returned invalid format, skipping")
                continue
            
            # Validate and clean pages from this batch
            for page in batch_pages:
                if isinstance(page, dict) and 'slug' in page and 'title' in page and 'content' in page:
                    # Ensure slug is URL-friendly and unique
                    slug = re.sub(r'[^a-z0-9-]', '', page['slug'].lower().replace(' ', '-'))
                    if slug:
                        # Check for duplicate slugs
                        existing_slugs = {p.get('slug') for p in all_pages}
                        original_slug = slug
                        counter = 1
                        while slug in existing_slugs:
                            slug = f"{original_slug}-{counter}"
                            counter += 1
                        
                        all_pages.append({
                            'slug': slug,
                            'title': str(page['title']).strip(),
                            'content': str(page['content']).strip()
                        })
            
            logger.info(f"Batch {batch_num + 1} completed: {len(batch_pages)} pages generated, {len(all_pages)} total so far")
            
            # If we've reached the target, stop
            if len(all_pages) >= num_pages:
                break
        
        # Trim to exact number requested
        all_pages = all_pages[:num_pages]
        
        if not all_pages:
            return False, "No valid pages were generated"
        
        logger.info(f"Total pages generated: {len(all_pages)} (requested: {num_pages})")
        return True, all_pages
    
    except json.JSONDecodeError as e:
        return False, f"Failed to parse OpenAI response as JSON: {str(e)}"
    except Exception as e:
        logger.exception(f"Error generating AI pages: {str(e)}")
        return False, f"OpenAI API error: {str(e)}"


@require_http_methods(["POST"])
def generate_ai_pages(request):
    """Generate AI pages and store them in the session."""
    session = get_or_create_session(request)
    
    if not session.website_url:
        messages.error(request, "Please analyze a website first before generating AI pages.")
        return redirect('features_table')
    
    if not session.features or len(session.features) == 0:
        messages.error(request, "Please add features first before generating AI pages.")
        return redirect('features_table')
    
    # Get number of pages from form (default to 50)
    try:
        num_pages = int(request.POST.get('pages_count', 50))
        num_pages = max(10, min(300, num_pages))  # Clamp between 10 and 300
    except (ValueError, TypeError):
        num_pages = 50
    
    # Generate pages with OpenAI
    success, result = generate_ai_pages_with_openai(session.website_url, session.features, num_pages)
    
    if not success:
        messages.error(request, f"Failed to generate AI pages: {result}")
    else:
        # Save to session
        session.ai_pages = result
        session.save()
        messages.success(request, f"Successfully generated {len(result)} AI page(s)! (Requested: {num_pages})")
    
    return redirect('features_table')


@require_http_methods(["POST"])
def delete_all_ai_pages(request):
    """Delete all AI-generated pages from the session."""
    session = get_or_create_session(request)
    
    if session.ai_pages and len(session.ai_pages) > 0:
        session.ai_pages = []
        session.save()
        messages.success(request, "All AI pages have been deleted.")
        logger.info(f"Deleted all AI pages from session {session.id}")
    else:
        messages.info(request, "No AI pages to delete.")
    
    return redirect('features_table')


def ai_page(request, slug):
    """
    View an AI-generated page.
    These pages are optimized for AI scrapers/bots and AI rankings (SiteBuddy SEO for AI).
    Human users can also view them for preview purposes.
    """
    # Check User-Agent to determine if request is from AI scraper or human browser
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # List of known AI crawlers/bots (add more as needed)
    ai_crawlers = [
        'gptbot',           # OpenAI GPTBot
        'chatgpt',          # ChatGPT
        'chatgpt-user',     # ChatGPT user agent
        'anthropic-ai',      # Anthropic Claude
        'claude',           # Claude
        'google-ai',         # Google AI
        'googlebot',        # Google (may include AI features)
        'bingbot',          # Bing (may include AI features)
        'ccbot',            # Common Crawl
        'facebookexternalhit',  # Facebook crawler
        'linkedinbot',      # LinkedIn
        'twitterbot',       # Twitter/X
        'slackbot',         # Slack
        'whatsapp',         # WhatsApp
        'telegrambot',      # Telegram
        'discordbot',       # Discord
        'crawler',          # Generic crawler
        'spider',           # Generic spider
        'bot',              # Generic bot (check last to avoid false positives)
    ]
    
    # Check if it's a known AI/bot crawler
    is_ai_crawler = any(crawler in user_agent for crawler in ai_crawlers)
    
    session = get_or_create_session(request)
    
    # Find the page by slug
    page = None
    if session.ai_pages and isinstance(session.ai_pages, list):
        for p in session.ai_pages:
            if isinstance(p, dict) and p.get('slug') == slug:
                page = p
                break
    
    if not page:
        from django.http import Http404
        raise Http404("AI page not found")
    
    context = {
        'page': page,
        'session': session,
        'is_ai_crawler': is_ai_crawler,
    }
    
    response = render(request, 'analyzer/ai_page.html', context)
    
    # Set appropriate robots headers
    if is_ai_crawler:
        # Allow AI crawlers to index - this is for AI rankings
        response['X-Robots-Tag'] = 'index, follow'
    else:
        # For human users: noindex to prevent traditional search engine indexing
        # But pages are still accessible for preview
        response['X-Robots-Tag'] = 'noindex, nofollow'
    
    return response


def run_findability_analysis_with_openai(website_url, features_list, ai_pages_list=None):
    """
    Use OpenAI to run findability analysis.
    Returns (success: bool, report: dict or error_message: str)
    """
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if not openai_key or openai_key == 'your_key_here':
        return False, "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file."
    
    try:
        # Remove proxy-related env vars that might interfere with OpenAI client
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ.pop(var)
        
        client = OpenAI(api_key=openai_key, timeout=60.0)
        
        # Restore proxy vars if they existed
        for var, value in original_proxies.items():
            os.environ[var] = value
        
        features_text = '\n'.join([f"- {f}" for f in features_list[:30]])  # Limit to 30 features
        
        # Prepare AI pages content summary if available
        ai_pages_summary = ""
        if ai_pages_list and len(ai_pages_list) > 0:
            ai_pages_summary = "\n\nAI-Generated Pages Available:\n"
            for page in ai_pages_list[:5]:  # Limit to 5 pages
                if isinstance(page, dict):
                    ai_pages_summary += f"- {page.get('title', 'Untitled')}: {page.get('content', '')[:200]}...\n"
        
        prompt = f"""You are analyzing the findability of a website. Your task is to:

1. Generate 15-25 realistic user search queries that people might use to find this website's features
2. Analyze how well the website content supports these queries
3. Create a comprehensive findability report

Website URL: {website_url}

Key Features:
{features_text}
{ai_pages_summary}

Generate a JSON report with the following structure:
{{
    "overall_score": <number 0-100>,
    "simulated_queries": [<list of 15-25 search query strings>],
    "per_feature_notes": [
        {{"feature": "<feature name>", "note": "<findability assessment>"}},
        ...
    ],
    "content_gaps": [
        "<gap description 1>",
        "<gap description 2>",
        ...
    ],
    "recommendations": {{
        "pages_to_add": [
            "<recommended page/section 1>",
            "<recommended page/section 2>",
            ...
        ],
        "faq_suggestions": [
            "<FAQ question 1>",
            "<FAQ question 2>",
            ...
        ]
    }},
    "wording_improvements": [
        "<suggestion 1>",
        "<suggestion 2>",
        ...
    ]
}}

The overall_score should reflect how easily users can find information about the features (0 = very poor, 100 = excellent).
Return ONLY valid JSON, no markdown code blocks or other text."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in website findability and SEO analysis. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        content = content.strip()
        
        report = json.loads(content)
        
        if not isinstance(report, dict):
            return False, "OpenAI returned invalid format (expected a dictionary)"
        
        # Validate required fields
        if 'overall_score' not in report:
            return False, "Report missing overall_score"
        
        # Ensure score is between 0-100
        if isinstance(report.get('overall_score'), (int, float)):
            report['overall_score'] = max(0, min(100, int(report['overall_score'])))
        else:
            report['overall_score'] = 0
        
        # Ensure lists exist
        if 'simulated_queries' not in report:
            report['simulated_queries'] = []
        if 'per_feature_notes' not in report:
            report['per_feature_notes'] = []
        if 'content_gaps' not in report:
            report['content_gaps'] = []
        if 'recommendations' not in report:
            report['recommendations'] = {'pages_to_add': [], 'faq_suggestions': []}
        if 'wording_improvements' not in report:
            report['wording_improvements'] = []
        
        return True, report
    
    except json.JSONDecodeError as e:
        return False, f"Failed to parse OpenAI response as JSON: {str(e)}"
    except Exception as e:
        return False, f"OpenAI API error: {str(e)}"


@require_http_methods(["POST"])
def run_findability_analysis(request):
    """Run findability analysis and store the report."""
    session = get_or_create_session(request)
    
    if not session.website_url:
        messages.error(request, "Please analyze a website first before running findability analysis.")
        return redirect('findability')
    
    if not session.features or len(session.features) == 0:
        messages.error(request, "Please add features first before running findability analysis.")
        return redirect('findability')
    
    # Run analysis with OpenAI
    success, result = run_findability_analysis_with_openai(
        session.website_url,
        session.features,
        session.ai_pages if isinstance(session.ai_pages, list) else None
    )
    
    if not success:
        messages.error(request, f"Failed to run findability analysis: {result}")
    else:
        # Save to session
        session.findability_report = result
        session.save()
        messages.success(request, "Findability analysis completed successfully!")
    
    return redirect('findability')


def findability(request):
    """Page 3: Findability analysis page."""
    session = get_or_create_session(request)
    context = {
        'session': session,
        'session_id': session.id,
        'features_count': session.features_count,
        'ai_pages_count': session.ai_pages_count,
        'has_findability_report': session.has_findability_report,
        'findability_report': session.findability_report if session.has_findability_report else None,
    }
    return render(request, 'analyzer/findability.html', context)

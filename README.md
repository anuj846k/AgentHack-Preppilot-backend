# PrepPilot - Meeting Preparation Tool

## Overview

PrepPilot is an intelligent meeting preparation system that automatically researches attendees, analyzes their professional backgrounds, and generates comprehensive meeting preparation documents. The system combines multiple data sources including LinkedIn profiles, GitHub contributions, and real-time web search to create detailed attendee profiles and meeting insights.

## Architecture

The system is built using FastAPI and consists of several specialized tools that work together to create a comprehensive meeting preparation workflow. Each tool is designed to handle a specific aspect of attendee research and document generation.

## Tool Components

### 1. Meeting Data Extraction (`get_meeting_email.py`)

**Purpose**: Extracts meeting information and attendee details from email data using Portia's AI planning system.

**Key Features**:

- Processes email data to identify meeting attendees
- Extracts attendee names and email addresses
- Generates email summaries for each attendee
- Uses AI to structure and validate attendee information
- Handles edge cases like missing names by deriving them from email addresses

**Technical Implementation**:

- Uses Portia's PlanBuilderV2 for structured data extraction
- Implements Pydantic models for data validation
- Includes error handling for malformed data
- Supports both direct API calls and fallback mechanisms

**Output**: Structured JSON containing meeting title, organizer, and attendee list with email summaries.

### 2. Attendee Enrichment (`enrich_tools.py`)

**Purpose**: Enhances attendee data by researching their LinkedIn profiles and professional backgrounds.

**Key Features**:

- Generates targeted LinkedIn search queries for each attendee
- Extracts LinkedIn profile URLs from search results
- Fetches comprehensive profile data including work history, education, skills
- Handles multiple data formats and API responses
- Implements intelligent URL filtering and deduplication

**Technical Implementation**:

- Uses Portia's MCP (Model Context Protocol) for web search
- Integrates with Apify's LinkedIn scraper for profile data
- Implements robust error handling for failed enrichments
- Supports both synchronous and asynchronous processing

**Output**: Enriched attendee data with LinkedIn profile information, work history, skills, and professional background.

### 3. GitHub Profile Analysis (`githubProfileAnalsyer.py`)

**Purpose**: Analyzes GitHub profiles to understand technical skills, contributions, and project history.

**Key Features**:

- Fetches comprehensive GitHub profile data using Apify's scraper
- Analyzes pinned repositories and contribution patterns
- Extracts technical skills and programming languages
- Identifies open source contributions and project diversity
- Provides insights into coding activity and expertise areas

**Technical Implementation**:

- Uses Apify's GitHub profile scraper via MCP
- Implements username validation and URL construction
- Handles rate limiting and API errors gracefully
- Processes structured data into actionable insights

**Output**: Detailed GitHub analysis including tech stack, contributions, achievements, and activity patterns.

### 4. GitHub URL Extraction (`github_url_extractor.py`)

**Purpose**: Intelligently identifies and extracts GitHub URLs from attendee data.

**Key Features**:

- Scans attendee profiles for GitHub URLs
- Uses keyword matching to identify technical professionals
- Filters for relevant engineering and development roles
- Handles various URL formats and edge cases
- Provides fallback mechanisms for missing data

**Technical Implementation**:

- Uses regex patterns to identify GitHub URLs
- Implements keyword-based filtering for technical roles
- Handles both direct URLs and embedded links
- Supports multiple data structure formats

**Output**: List of valid GitHub URLs for further analysis.

### 5. Web Search Integration (`search_tool.py`)

**Purpose**: Provides real-time web search capabilities for additional context and information.

**Key Features**:

- Integrates with Perplexity API for intelligent web search
- Searches for company news, industry trends, and recent developments
- Provides context-aware search results
- Handles complex queries and returns structured data

**Technical Implementation**:

- Uses Perplexity's MCP server for search functionality
- Implements query processing and result parsing
- Handles API rate limiting and error responses
- Returns structured JSON responses

**Output**: Relevant search results and contextual information for meeting preparation.

### 6. Document Generation (`create_meet_summary.py`)

**Purpose**: Generates comprehensive meeting preparation documents from all collected data.

**Key Features**:

- Creates structured markdown documents
- Organizes information into logical sections
- Includes meeting overview, attendee profiles, and insights
- Provides conversation starters and discussion points
- Identifies collaboration opportunities

**Technical Implementation**:

- Uses OpenAI's GPT models for intelligent document generation
- Implements structured prompts for consistent formatting
- Handles large datasets and complex information
- Generates actionable insights and recommendations

**Output**: Comprehensive markdown document ready for meeting preparation.

### 7. Google Docs Integration (`google_docs_creation.py`)

**Purpose**: Converts markdown documents into formatted Google Docs for easy sharing and collaboration.

**Key Features**:

- Creates Google Docs with proper formatting
- Converts markdown headers to document styles
- Handles bullet points, tables, and text formatting
- Supports rich text and link preservation
- Provides direct sharing links

**Technical Implementation**:

- Uses Google Docs API for document creation
- Implements OAuth2 authentication flow
- Handles markdown-to-document conversion
- Manages document permissions and sharing

**Output**: Formatted Google Doc with meeting preparation content.

## API Endpoints

The system exposes several REST API endpoints for different functionalities:

- `GET /` - Health check and basic information
- `GET /get-meetings` - Retrieve meeting data for a specific date
- `POST /research-attendees` - Research and enrich attendee information
- `POST /analyze-github` - Analyze GitHub profiles for attendees
- `POST /generate-summary` - Generate meeting summary document
- `POST /search-information` - Search for additional context and information
- `POST /create-docs` - Create Google Doc from markdown content
- `POST /run-full-meeting-workflow` - Execute complete workflow end-to-end

## Data Flow

1. **Meeting Data Extraction**: System extracts attendee information from email data
2. **Attendee Enrichment**: LinkedIn profiles are researched and enriched with professional data
3. **GitHub Analysis**: Technical profiles are analyzed for skills and contributions
4. **Web Search**: Additional context is gathered through intelligent web search
5. **Document Generation**: All data is synthesized into comprehensive meeting preparation documents
6. **Document Export**: Final documents are formatted and exported to Google Docs

## Technical Requirements

- Python 3.13+
- FastAPI for API framework
- Portia SDK for AI planning and execution
- Google APIs for document creation
- Perplexity API for web search
- Apify for LinkedIn and GitHub data extraction
- OAuth2 authentication for Google services

## Environment Variables

- `PERPLEXITY_API_KEY` - For web search functionality
- `APIFY_TOKEN` - For LinkedIn and GitHub data extraction
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` - For Google Docs integration
- `OPENAI_API_KEY` - For AI-powered document generation
- `PORTIA_API_KEY`- For Portia powered functionalities

## Deployment

The system is designed for deployment on cloud platforms like Render, with proper environment variable configuration and dependency management. The FastAPI application can be deployed using standard Python deployment practices with uvicorn as the ASGI server.

## Security Considerations

- API keys are stored as environment variables
- OAuth2 authentication for Google services
- Rate limiting and error handling for external APIs
- Secure handling of user data and credentials
- Proper input validation and sanitization

This comprehensive toolset provides a complete solution for automated meeting preparation, combining multiple data sources and AI capabilities to create detailed, actionable meeting preparation documents.

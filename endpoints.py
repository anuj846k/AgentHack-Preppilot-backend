from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from combinedTools.get_meeting_email import get_meetings_and_emails
from combinedTools.enrich_tools import research_attendees
from combinedTools.github_url_extractor import find_github_urls
from combinedTools.githubProfileAnalsyer import analyze_github_profile
from combinedTools.create_meet_summary import create_meeting_summary
from combinedTools.google_docs_creation import create_google_docs_summary
from combinedTools.search_tool import search_company_news
import datetime

from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi.responses import Response
import json

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== MODELS ======
class DateRequest(BaseModel):
    date: str


class AttendeeRequest(BaseModel):
    meetings: dict


class GithubRequest(BaseModel):
    enriched_data: dict


class SummaryRequest(BaseModel):
    enriched_data: dict
    github_analyses: list


class DocsRequest(BaseModel):
    markdown: str
    search_markdown: Optional[str] = None


class SearchRequest(BaseModel):
    query: str


# ====== ENDPOINTS ======


@app.get("/")
def root():
    return {"message": "Hello from endpoints.py"}


@app.get("/get-meetings")
def get_meetings(date: str = None):
    if not date:
        date = datetime.date.today().isoformat()
    meetings = get_meetings_and_emails(date)
    return {"meetings": meetings}


@app.post("/research-attendees")
def research_attendees_api(req: AttendeeRequest):
    enriched = research_attendees(req.meetings)
    return {"enriched_data": enriched}


@app.post("/analyze-github")
def analyze_github_api(req: GithubRequest):
    urls = find_github_urls(req.enriched_data)
    analyses = []
    for url in urls:
        username = url.split("/")[-1]
        if username:
            analysis = analyze_github_profile(username)
            analyses.append(analysis)
    return {"github_analyses": analyses}


@app.post("/generate-summary")
def generate_summary_api(req: SummaryRequest):
    summary_file = create_meeting_summary(req.enriched_data, req.github_analyses)
    return {"summary_file": summary_file}


@app.post("/search-information")
def search_company_news_api(req: SearchRequest):
    try:
        result = search_company_news(req.query)
        return result["content"][0]["text"]

    except Exception as e:
        return {"success": False, "error": str(e), "query": req.query}


@app.post("/create-docs")
def create_docs_api(req: DocsRequest):
     if req.search_markdown:
        combined_markdown = req.markdown + "\n\n" + req.search_markdown
     else:
        combined_markdown = req.markdown
     doc_url = create_google_docs_summary(combined_markdown)
     return {"doc_url": doc_url}


# @app.get("/proxy-image")
# def proxy_image(url: str):
#     import requests
#     response = requests.get(url)
#     return Response(response.content, media_type=response.headers.get('content-type'))


# @app.get("/proxy-linkedin-image")
# async def proxy_linkedin_image(url: str):
#     try:
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#             'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Referer': 'https://www.linkedin.com/',
#         }

#         response = requests.get(url, headers=headers, timeout=10)
#         response.raise_for_status()

#         return Response(
#             content=response.content,
#             media_type=response.headers.get('content-type', 'image/jpeg')
#         )
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=f"Failed to fetch image: {str(e)}")


#   ------ One click endpoint ----- to trigger all tools at once


@app.post("/run-full-meeting-workflow")
def run_full_meeting_workflow():
    todaysDate = datetime.date.today().isoformat()

    try:
        meetings = get_meetings_and_emails(todaysDate)

        print("\n--- Meeting Data and past conversations with Attendees: ---", meetings)
        enriched_data = research_attendees(meetings)

        print("\n--- Full Enriched Attendee Data ---")
        if hasattr(enriched_data, "model_dump"):
            print(json.dumps(enriched_data.model_dump(), indent=2))
        else:
            print(json.dumps(enriched_data, indent=2))
        print("\n--- Finding GitHub URLs in Attendee Data ---")
        github_urls = find_github_urls(enriched_data)
        print(f"Extracted GitHub URLs: {github_urls}")

        all_analyses = []

        if github_urls:
            for url in github_urls:
                try:
                    username = url.split("/")[-1]
                    if username:
                        print(f"\n--- Analyzing GitHub Profile: {username} ---")
                        analysis = analyze_github_profile(username)
                        all_analyses.append(analysis)
                        print(f"Successfully analyzed GitHub profile: {username}")

                except Exception as analysis_error:
                    print(f"Failed to analyze profile at {url}: {analysis_error}")

        if all_analyses:
            print("\n--- GitHub Profile Analyses ---")
            print(json.dumps(all_analyses, indent=2))

        # Generate the meeting summary document
        print("\n--- Generating Meeting Summary Document ---")
        summary_file = create_meeting_summary(enriched_data, all_analyses)
        if summary_file:
            print(f"Meeting summary generated successfully: {summary_file}")

        ## create doc of summary in google docs:
        doc_url = create_google_docs_summary(summary_file)
        if doc_url:
            print(
                f"Google Docs summary created successfully Click here to view: {doc_url}"
            )
        return {
            "doc_url": doc_url if doc_url else None,
            "summary": summary_file if summary_file else None,
            "message": "Full meeting workflow completed successfully!",
            "meetings": meetings,
            "enriched_data": enriched_data,
            "github_analyses": all_analyses,
        }
    except (ValueError, FileNotFoundError) as e:
        print(f"\nAn error occurred: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

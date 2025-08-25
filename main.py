from combinedTools.get_meeting_email import get_meetings_and_emails
from combinedTools.enrich_tools import research_attendees
from combinedTools.github_url_extractor import find_github_urls
from combinedTools.githubProfileAnalsyer import analyze_github_profile
from combinedTools.create_meet_summary import create_meeting_summary
from combinedTools.google_docs_creation import create_google_docs_summary
import datetime
import json


if __name__ == "__main__":
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
    except (ValueError, FileNotFoundError) as e:
        print(f"\nAn error occurred: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

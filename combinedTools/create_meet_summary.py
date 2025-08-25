from dotenv import load_dotenv
from portia import (
    Config,
    LLMProvider,
    LogLevel,
)
from portia.model import Message
import json
import os
from datetime import datetime

load_dotenv()


def create_meeting_summary(enriched_data, github_analyses, perplexity_result=None):
    """
    Create a meeting summary document from the data passed from main.py

    Args:
        enriched_data: The enriched attendee data from research_attendees()
        github_analyses: List of GitHub profile analyses
        perplexity_result: Optional perplexity search results
    """

    try:
        enriched_json = json.dumps(enriched_data, ensure_ascii=False, default=str)
        github_json = json.dumps(github_analyses, ensure_ascii=False, default=str)

        if perplexity_result:
            perplexity_json = json.dumps(
                perplexity_result, ensure_ascii=False, default=str
            )
        else:
            perplexity_json = json.dumps(
                {"content": "No additional research data available"}, ensure_ascii=False
            )

        combined_json = json.dumps(
            {
                "enriched_data": enriched_json,
                "github_data": github_json,
                "perplexity_result": perplexity_json,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        print(f"Error converting data to JSON: {e}")
        return None

    prompt = f"""
Generate a comprehensive meeting preparation document in markdown format from the following JSON data.
Give only markdown straight nothing like ``` markdown only just markdown content
## Document Structure:
1. **Meeting Overview** - Title, organizer, date, and context
2. **Attendee Profiles** - Detailed information about each person
3. **Key Insights & Analysis** - What I found about each attendee
4. **Conversation Starters & Ice Breakers** - Specific topics to discuss
5. **Potential Discussion Points** - Based on their backgrounds and interests
6. **Collaboration Opportunities** - Areas where they might work together

## For Each Attendee, Include:
- **Professional Background**: Current role, company, experience
- **Key Skills & Expertise**: Technical skills, languages, certifications
- **Recent Experience**: Notable positions, achievements, projects
- **GitHub/Online Presence**: Activity, contributions, interests
- **Interesting Facts**: Unique aspects of their background

## Key Insights & Analysis:
- What makes each person unique and interesting
- Their career progression and achievements
- Technical expertise and specializations
- Recent projects and contributions

## Conversation Starters & Ice Breakers:
- Ask about recent projects or achievements
- Discuss industry trends and technology developments
- Share insights about AI/ML developments
- Ask about their experience with different technologies
- Discuss hackathons, open source contributions, or side projects

## Potential Discussion Points:
- Current projects and challenges
- Technology stack preferences and experiences
- Industry trends and future directions
- Potential collaboration opportunities
- Knowledge sharing and mentorship possibilities

## Collaboration Opportunities:
- AI/ML project collaboration
- Product development insights sharing
- Open source project contributions
- Knowledge sharing and mentorship

## Format Requirements:
- Use clear markdown formatting with headers, lists, and tables
- Make it easy to read and reference during the meeting
- Include specific, actionable insights
- Keep it professional but approachable

JSON Data: {combined_json}
"""

    config = Config.from_default(
        llm_provider=LLMProvider.OPENAI,
        default_log_level=LogLevel.DEBUG,
        env={"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")},
    )

    print("Generating meeting summary document...")
    try:
        model = config.get_default_model()

        messages = [
            Message(
                role="system",
                content="""You are an expert meeting preparation assistant. Your task is to analyze attendee data and create comprehensive meeting preparation documents that:

1. **Analyze Attendee Backgrounds**: Extract and present key information about each person's experience, skills, and achievements
2. **Identify Key Insights**: Highlight what makes each person unique and interesting
3. **Generate Conversation Starters**: Create specific, relevant topics to discuss based on their backgrounds
4. **Suggest Discussion Points**: Identify areas of mutual interest and potential collaboration
5. **Provide Actionable Information**: Give concrete details and insights that can be used during the meeting

Focus on providing the actual research and analysis, not instructions for the user to do research. Present all the information in a clear, organized format that's ready to use.""",
            ),
            Message(role="user", content=prompt),
        ]

        response = model.get_response(messages)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_summary_{timestamp}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.content)

        print(f"=== MEETING SUMMARY SAVED ===")
        print(f"File saved as: {filename}")
        print(f"File size: {len(response.content)} characters")
        print("=== END SUMMARY ===")

        print("\n=== GENERATED CONTENT ===")
        print(response.content)
        print("=== END CONTENT ===")

        return response.content

    except Exception as e:
        print(f"Error generating meeting summary: {e}")
        print("Please check your API keys and try again.")
        return None


if __name__ == "__main__":
    print("This script should be called from main.py with actual data")

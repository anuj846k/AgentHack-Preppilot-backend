import os
import json
import re
import logging
from dotenv import load_dotenv
from portia import (
    Config,
    DefaultToolRegistry,
    PlanRunState,
    Portia,
    McpToolRegistry,
    LLMProvider,
    StorageClass,
    LogLevel,
)
from portia.cli import CLIExecutionHooks
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from portia.builder.plan_builder_v2 import PlanBuilderV2
from portia.builder.reference import Input, StepOutput

load_dotenv()
logging.basicConfig(level=logging.INFO)


class SearchQueries(BaseModel):
    queries: List[str] = Field(
        description="A list of generated search queries for attendees."
    )


class UrlList(BaseModel):
    urls: List[str] = Field(
        description="A list of found LinkedIn URLs or 'Not found' strings."
    )


class EnrichedAttendee(BaseModel):
    name: str
    email: str
    enriched: Dict[str, Any] | str


class FinalOutput(BaseModel):
    meeting_title: str
    organizer_email: str
    attendees: List[EnrichedAttendee]


def generate_search_queries(original_json):
    """Generate LinkedIn search queries for each attendee"""
    attendees = original_json.get("attendees", [])
    queries = []
    for attendee in attendees:
        name = attendee.get("name", "")
        email = attendee.get("email", "")
        query = f'site:linkedin.com intext:"{name}" OR "{email}"'
        queries.append(query)
    return {"queries": queries}


def extract_first_query(queries_dict):
    """Extract the first query from the generated search queries."""
    queries = queries_dict.get("queries", [])
    if queries:
        return queries[0]
    return ""


def extract_linkedin_urls(search_results):
    """Extract LinkedIn profile URLs from search results"""
    urls = []
    for result in search_results.get("urls", []):
        if "linkedin.com/in/" in str(result):
            urls.append(str(result))
        else:
            urls.append("Not found")
    return {"urls": urls}


def filter_valid_urls(url_list: UrlList):
    urls = []
    for url in url_list.urls:
        s = str(url)
        if "linkedin.com/in/" in s:
            s = s.split("?")[0].split("#")[0]
            urls.append(s)
    deduped = []
    seen = set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return {"urls": deduped}


def extract_cookies_for_apify(cookies_list):
    """Extract cookies in the format expected by Apify"""
    return [
        {"name": cookie["name"], "value": cookie["value"]} for cookie in cookies_list
    ]


def extract_urls_from_dict(url_dict):
    """Extract the urls array from the filter_valid_urls output"""
    return url_dict.get("urls", [])


def research_attendees(input_json: dict) -> dict:
    """Enriches meeting attendee information with LinkedIn data using Portia and Apify."""
    config = Config.from_default(
        llm_provider=LLMProvider.OPENAI,
        storage_class=StorageClass.CLOUD,
        default_log_level=LogLevel.DEBUG,
    )
    portia = Portia(
        config=config,
        tools=DefaultToolRegistry(config)
        + McpToolRegistry.from_stdio_connection(
            server_name="apify",
            command="npx",
            args=[
                "-y",
                "@apify/actors-mcp-server",
                "--actors",
                "curious_coder/linkedin-profile-scraper",
            ],
            env={"APIFY_TOKEN": os.getenv("APIFY_TOKEN")},
        ),
        execution_hooks=CLIExecutionHooks(),
    )
    available_tools = [t.id for t in portia.tool_registry.get_tools()]
    logging.info(f"Available tools: {available_tools}")
    apify_tool_id = next(
        (
            tid
            for tid in available_tools
            if "linkedin" in tid and "scraper" in tid and "mcp:apify" in tid
        ),
        None,
    )
    if not apify_tool_id:
        raise ValueError(
            "Could not find the Apify LinkedIn scraper tool in the registry."
        )
    logging.info(f"Found Apify tool with ID: {apify_tool_id}")
    try:
        with open("linkedin_cookies.json", "r") as f:
            cookie_list = json.load(f)
    except FileNotFoundError:
        logging.error("CRITICAL: linkedin_cookies.json not found. Cannot proceed.")
        raise
    except json.JSONDecodeError:
        logging.error("CRITICAL: Could not decode JSON from linkedin_cookies.json.")
        raise
    # DEBUG: Print cookie data before passing to plan
    print("\n=== COOKIE DEBUG INFO ===")
    print(f"Cookie list type: {type(cookie_list)}")
    print(f"Cookie list length: {len(cookie_list)}")
    print("First 3 cookies:")
    for i, cookie in enumerate(cookie_list[:3]):
        print(f" Cookie {i+1}: {cookie}")
    print("=== END COOKIE DEBUG ===\n")
    try:
        extracted_cookies = extract_cookies_for_apify(cookie_list)
        print("=== EXTRACTED COOKIES DEBUG ===")
        print(f"Extracted cookies type: {type(extracted_cookies)}")
        print(f"Extracted cookies length: {len(extracted_cookies)}")
        print("First 3 extracted cookies:")
        for i, cookie in enumerate(extracted_cookies[:3]):
            print(f" Extracted Cookie {i+1}: {cookie}")
        print("=== END EXTRACTED COOKIES DEBUG ===\n")
    except Exception as e:
        print(f"Error in extract_cookies_for_apify: {e}")
    logging.info("Building the plan with PlanBuilderV2...")
    plan = (
        PlanBuilderV2("Enrich meeting attendees with LinkedIn data")
        .input(
            name="original_json",
            description="The original JSON object with meeting details and attendees.",
        )
        .input(name="cookies", description="LinkedIn authentication cookies.")
        .function_step(
            function=generate_search_queries,
            args={"original_json": Input("original_json")},
            step_name="Generate Search Queries",
        )
        .function_step(
            function=extract_first_query,
            args={"queries_dict": StepOutput("Generate Search Queries")},
            step_name="Extract First Query",
        )
        .invoke_tool_step(
            tool="portia:tavily::search",
            args={"search_query": StepOutput("Extract First Query")},
            output_schema=UrlList,
            step_name="Find LinkedIn URLs",
        )
        .function_step(
            function=filter_valid_urls,
            args={"url_list": StepOutput("Find LinkedIn URLs")},
            step_name="Filter Valid URLs",
        )
        .function_step(
            function=extract_urls_from_dict,
            args={"url_dict": StepOutput("Filter Valid URLs")},
            step_name="Extract URLs Array",
        )
        .function_step(
            function=extract_cookies_for_apify,
            args={"cookies_list": Input("cookies")},
            step_name="Extract Cookies for Apify",
        )
        .invoke_tool_step(
            tool=apify_tool_id,
            args={
                "urls": StepOutput("Extract URLs Array"),
                "cookie": StepOutput("Extract Cookies for Apify"),
                "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            },
            step_name="Scrape LinkedIn Profiles",
        )
        .llm_step(
            task="Attach each raw scraped profile object to the corresponding attendee as 'enriched'. If none, set 'enriched' to 'Not found'. Do not omit fields.",
            inputs=[Input("original_json"), StepOutput("Scrape LinkedIn Profiles")],
            output_schema=FinalOutput,
            step_name="Merge Data",
        )
        .final_output(output_schema=FinalOutput)
        .build()
    )
    logging.info("Plan built successfully.")
    logging.info("Executing the plan for each attendee...")

    meeting_title = input_json.get("meeting_title")
    organizer_email = input_json.get("organizer_email")
    attendees = input_json.get("attendees", [])
    enriched_attendees = []

    for attendee in attendees:
        single_input = {
            "meeting_title": meeting_title,
            "organizer_email": organizer_email,
            "attendees": [attendee],
        }
        plan_run = portia.run_plan(
            plan,
            plan_run_inputs={
                "original_json": single_input,
                "cookies": cookie_list,
            },
        )
        while plan_run.state == PlanRunState.NEED_CLARIFICATION:
            for clarification in plan_run.get_outstanding_clarifications():
                print(
                    f"Clarification needed for {attendee['name']}: {clarification.user_guidance}"
                )
                user_response = input("Please provide your response: ")
                plan_run = portia.resolve_clarification(
                    clarification, user_response, plan_run
                )
            plan_run = portia.resume(plan_run)
        if plan_run.state == PlanRunState.FAILED:
            logging.error(
                f"Plan failed for {attendee['name']}. Error details: {str(plan_run.outputs.final_output)}"
            )
            enriched_attendees.append(
                EnrichedAttendee(
                    name=attendee["name"],
                    email=attendee["email"],
                    enriched="Failed to enrich",
                )
            )
            continue
        if plan_run.state == PlanRunState.COMPLETE and plan_run.outputs.final_output:
            raw_output = plan_run.outputs.final_output.value
            if isinstance(raw_output, BaseModel):
                enriched = raw_output.attendees[0].enriched
                if isinstance(enriched, str):
                    try:
                        enriched = json.loads(enriched)
                    except json.JSONDecodeError:
                        enriched = "Parsing error in enrched data"
                enriched_attendees.append(
                    EnrichedAttendee(
                        name=attendee["name"],
                        email=attendee["email"],
                        enriched=enriched,
                    )
                )
            else:
                enriched_attendees.append(
                    EnrichedAttendee(
                        name=attendee["name"],
                        email=attendee["email"],
                        enriched=raw_output,
                    )
                )
        else:
            enriched_attendees.append(
                EnrichedAttendee(
                    name=attendee["name"], email=attendee["email"], enriched="Not found"
                )
            )

    return FinalOutput(
        meeting_title=meeting_title,
        organizer_email=organizer_email,
        attendees=enriched_attendees,
    )


if __name__ == "__main__":
    sample_input = {
        "meeting_title": "Portia meet",
        "meeting_time": "2025-08-20T10:00:00Z",
        "organizer_email": "anuj846k@gmail.com",
        "attendees": [
            {
                "name": "Anuj Kumar",
                "email": "anuj846k@gmail.com",
                "email_summaries": [
                    "Expressed interest to the organizer in booking hundreds of products for testing and indicated eagerness for future collaboration.",
                    "Forwarded information about the AI Student Pack to the organizer, detailing free and discounted AI tools for students and educators, and included specifics on the offer and claiming process.",
                ],
            },
            {
                "name": "Kshitij Akarsh",
                "email": "kshitijakarsh@gmail.com",
                "email_summaries": [
                    "Emailed the organizer regarding a 'portia meet', discussing the adoption of Portia and outlining a related business plan.",
                    "Sent a brief greeting email to the organizer with the message 'Hellohi'.",
                    "Forwarded an email from a faculty member to the organizer about the completion and submission of 20 programs for a practical exam, including relevant instructions and deadlines for students.",
                ],
            },
        ],
    }

    try:
        final_result = research_attendees(sample_input)
        # enriched_data = final_result.copy()
        # enriched_data["attendees"] = [
        #     attendee.model_dump() for attendee in final_result["attendees"]
        # ]

        print("\n--- Enriched Attendee Data ---")
        print(json.dumps(final_result.model_dump(), indent=2))
    except (ValueError, FileNotFoundError) as e:
        print(f"\nAn error occurred: {e}")

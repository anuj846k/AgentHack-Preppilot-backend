from portia import (
    Config,
    DefaultToolRegistry,
    PlanRunState,
    MultipleChoiceClarification,
    Portia,
    LLMProvider,
    StorageClass,
    LogLevel,
)

from portia.cli import CLIExecutionHooks
from dotenv import load_dotenv
import datetime
import json
import re
from portia.builder.plan_builder_v2 import PlanBuilderV2
from portia.builder.reference import Input, StepOutput
from typing import List, Dict, Any
from pydantic import BaseModel, Field

load_dotenv()


class AttendeeWithSummary(BaseModel):
    name: str = Field(description="The full name of the attendee.")
    email: str = Field(description="The email address of the attendee.")
    email_summaries: List[str] = Field(
        description="A list of summaries from the email history."
    )


class AttendeeList(BaseModel):
    attendees: List[AttendeeWithSummary] = Field(description="A list of attendees .")


class MeetingReport(BaseModel):
    meeting_title: str
    meeting_time: str
    organizer_email: str
    attendees: List[AttendeeWithSummary]


def derive_name_from_email(email):
    if not email or "@" not in email:
        return email

    prefix = email.split("@")[0]
    parts = re.split(r"[0-9_]+", prefix)
    parts = [p for p in parts if p]

    if len(parts) == 1:
        word = parts[0]
        split_at = len(word) - 6
        if split_at > 2:
            parts = [word[:split_at], word[split_at:]]

    return " ".join(p.capitalize() for p in parts)


def process_final_output(report) -> dict:
    """Process the final output and ensure names are not null."""
    try:
        if hasattr(report, "model_dump"):
            report_data = report.model_dump()
        elif isinstance(report, str):
            cleaned_str = re.sub(r"^```json\s*|\s*```$", "", report.strip())
            report_data = json.loads(cleaned_str)
        else:
            report_data = report

        if "attendees" in report_data:
            for attendee in report_data["attendees"]:
                name = attendee.get("name", "")
                email = attendee.get("email", "")

                if (
                    not name
                    or name is None
                    or name.isspace()
                    or name == email
                    or "@" in name
                    or name.lower() == email.split("@")[0].lower()
                ):
                    attendee["name"] = derive_name_from_email(email)

        return report_data
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"Error processing final output: {e}")
        if hasattr(report, "model_dump"):
            return report.model_dump()
        return report


def get_meetings_and_emails(todaysDate: str) -> dict:
    config = Config.from_default(
        llm_provider=LLMProvider.OPENAI,
        storage_class=StorageClass.CLOUD,
    )
    portia = Portia(
        config=config,
        tools=DefaultToolRegistry(config),
        execution_hooks=CLIExecutionHooks(),
    )

    if "T" in todaysDate:
        date_part = todaysDate.split("T")[0]
    else:
        date_part = todaysDate

    start_time = f"{date_part}T00:00:00"
    end_time = f"{date_part}T23:59:59"

    plan = (
        PlanBuilderV2("Get Meeting Details and Summarize Attendee Emails")
        .input(
            name="start_time",
            description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS)",
        )
        .input(
            name="end_time", description="End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
        )
        .invoke_tool_step(
            tool="portia:google:gcalendar:get_events_by_properties",
            args={
                "start_time": Input("start_time"),
                "end_time": Input("end_time"),
                "max_results": 50,
            },
            step_name="Find Todays Events",
        )
        .llm_step(
            task="From the fetched events, select the VERY FIRST event. Then, extract the following details into a simple JSON object: meeting_title (from 'summary'), meeting_time (from 'start.date' or 'start.dateTime'), organizer_email (from 'organizer.email'), and attendees (the full list of attendee objects). If no events are found, return an empty object.",
            inputs=[StepOutput("Find Todays Events")],
            step_name="Extract First Event Details",
        )
        .llm_step(
            task="From the event details, create a new list of attendees that excludes the organizer. Use the 'organizer_email' to filter the 'attendees' list.",
            inputs=[StepOutput("Extract First Event Details")],
            step_name="Filter Organizer",
        )
        .llm_step(
            task="For each attendee in the filtered list, generate a Gmail search query using this format: '((from:ORGANIZER_EMAIL to:ATTENDEE_EMAIL) OR (from:ATTENDEE_EMAIL to:ORGANIZER_EMAIL))'. Output ONLY a JSON array of objects: [{'attendee_email': EMAIL, 'search_query': QUERY}] for all attendees. Use organizer_email from input. No other text.",
            inputs=[
                StepOutput("Extract First Event Details"),
                StepOutput("Filter Organizer"),
            ],
            step_name="Generate Search Queries",
        )
        .invoke_tool_step(
            tool="portia:google:gmail:search_email",
            args={
                "query": "((from:anuj846k@gmail.com to:kshitijakarsh@gmail.com) OR (from:kshitijakarsh@gmail.com to:anuj846k@gmail.com))"
            },
            step_name="Search Gmail for First Attendee",
        )
        .invoke_tool_step(
            tool="portia:google:gmail:search_email",
            args={
                "query": "((from:anuj846k@gmail.com to:mounir.mouawad@gmail.com) OR (from:mounir.mouawad@gmail.com to:anuj846k@gmail.com))"
            },
            step_name="Search Gmail for Second Attendee",
        )
        .llm_step(
            task="For each attendee and their email search results, create a concise summary of the email history found. Clean messages to plain text (strip HTML/links/images/signatures), keep newest to oldest. Then summarize into detailed sentences. If no emails are found, email_summaries = []. IMPORTANT: Each attendee object MUST include 'name', 'email', and 'email_summaries' fields. For the 'name' field, derive it from the email using the pattern: split on numbers/underscores and capitalize each part. Output UPDATED attendees array with all required fields. ONLY the JSON attendees array, no other text.",
            inputs=[
                StepOutput("Extract First Event Details"),  
                StepOutput("Filter Organizer"),  
                StepOutput(
                    "Search Gmail for First Attendee"
                ),  
                StepOutput(
                    "Search Gmail for Second Attendee"
                ),  
            ],
            output_schema=AttendeeList,
            step_name="Summarize Email Results",
        )
        .llm_step(
            task="Construct the final JSON report. Use the 'meeting_title', 'meeting_time', and 'organizer_email' from the initial event details. Use the list of attendees with their email summaries from the previous step. IMPORTANT: Exclude the organizer from the attendees list - only include attendees who are NOT the organizer. The final structure must match the MeetingReport schema exactly.",
            inputs=[
                StepOutput("Extract First Event Details"),
                StepOutput("Summarize Email Results"),
            ],
            output_schema=MeetingReport,
            step_name="Assemble Final Report",
        )
        .function_step(
            function=process_final_output,
            args={"report": StepOutput("Assemble Final Report")},
            step_name="Final Validation and Formatting",
        )
        .final_output()
        .build()
    )

    plan_run = portia.run_plan(
        plan, plan_run_inputs={"start_time": start_time, "end_time": end_time}
    )

    while plan_run.state == PlanRunState.NEED_CLARIFICATION:
        for clarification in plan_run.get_outstanding_clarifications():
            print(f"Clarification needed: {clarification.user_guidance}")
            user_response = input("Please provide your response: ")
            plan_run = portia.resolve_clarification(
                clarification, user_response, plan_run
            )
        plan_run = portia.resume(plan_run)

    if plan_run.state == PlanRunState.FAILED:
        print(f"Plan failed. Last successful step outputs: {plan_run.outputs}")
        raise ValueError("The meeting and email plan failed to execute.")

    if plan_run.state == PlanRunState.COMPLETE and plan_run.outputs.final_output:
        return plan_run.outputs.final_output.value

    raise ValueError("The meeting and email plan did not complete successfully.")


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    print("TODAYS DATE:", today)
    try:
        result = get_meetings_and_emails(today)
        print("Meeting data retrieved successfully:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

"""
GitHub Profile Analysis Tool for Portia

This tool fetches comprehensive GitHub profile information including:
- Open source contributions
- Tech stack analysis
- Pinned projects
- Repository statistics
- Skills and expertise

Uses Apify's saswave/github-profile-scraper via MCP. Requires APIFY_TOKEN env var.
"""

import os
import json
import logging
from typing import Dict, List, Any
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
from portia.builder.plan_builder_v2 import PlanBuilderV2
from portia.builder.reference import Input, StepOutput
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


def build_github_urls(username: str) -> List[str]:
    """Construct GitHub profile URLs from username at runtime"""
    return [f"https://github.com/{username}"]


def create_github_profile_plan():
    """Create a Portia plan for analyzing GitHub profiles using Apify MCP"""
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
                "saswave/github-profile-scraper",
            ],
            env={"APIFY_TOKEN": os.getenv("APIFY_TOKEN")},
        ),
        execution_hooks=CLIExecutionHooks(),
    )

    available_tools = [t.id for t in portia.tool_registry.get_tools()]
    logging.info(f"Available tools: {available_tools}")

    # Flexible search for tool ID (handles slash/underscore variations)
    apify_tool_id = next(
        (
            tid
            for tid in available_tools
            if "saswave_slash_github_profile_scraper" in tid and "mcp:apify" in tid
        ),
        None,
    )
    if not apify_tool_id:
        raise ValueError(
            "GitHub profile scraper not found in registry. Check actor ID format and Apify trial status."
        )
    logging.info(f"Found Apify tool with ID: {apify_tool_id}")

    plan = (
        PlanBuilderV2("Analyze GitHub Profile")
        .input(
            name="github_username",
            description="GitHub username to analyze",
        )
        .llm_step(
            task="Validate the GitHub username and ensure it's in the correct format (alphanumeric with hyphens/underscores). If valid, output ONLY the username as a single string with no additional text. If invalid, output 'INVALID' and clarify why.",
            inputs=[Input("github_username")],
            step_name="Validate Username",
        )
        .function_step(
            function=build_github_urls,
            args={"username": StepOutput("Validate Username")},
            step_name="Build GitHub URLs",
        )
        .invoke_tool_step(
            tool=apify_tool_id,
            args={
                "peoples_links": StepOutput("Build GitHub URLs"),
            },
            step_name="Scrape GitHub Profile",
        )
        .llm_step(
            task="""Analyze the scraped GitHub profile data and create a comprehensive summary based on the actual data structure:

            The data contains:
            - Basic profile info: name, username, followers, following, bio, location, emails, organization, websites
            - Achievements: GitHub badges and achievements
            - Social links: X (Twitter), LinkedIn
            - Highlights: GitHub Pro status, etc.
            - Pinned repositories: name, url, description, languages, stars, forks
            - README content: detailed profile information and skills

            Create a structured analysis in JSON format with these keys:

            "profile_overview": Extract name, username, bio, location, followers/following, organization, websites, emails

            "pinned_repositories": List repository names, descriptions, URLs, languages, stars, forks, project types

            "achievements": List GitHub badges, achievements, Pro status, highlights

            "tech_stack": Dictionary of languages/technologies with estimated usage percentages from pinned repos and README

            "skills_assessment": List of extracted skills from README, bio, repo descriptions

            "activity_summary": Summary of social presence, community engagement, project diversity, recent activity

            "social_links": Dictionary of Twitter/X, LinkedIn, personal website, email contacts

            Output ONLY the JSON object with no additional text.""",
            inputs=[StepOutput("Scrape GitHub Profile")],
            step_name="Analyze Data",
        )
        .final_output()
        .build()
    )

    return plan


def analyze_github_profile(username: str) -> Dict[str, Any]:
    """Run the plan to analyze a GitHub profile using Apify scraper"""
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
                "saswave/github-profile-scraper",
            ],
            env={"APIFY_TOKEN": os.getenv("APIFY_TOKEN")},
        ),
        execution_hooks=CLIExecutionHooks(),
    )

    plan = create_github_profile_plan()

    plan_run = portia.run_plan(
        plan,
        plan_run_inputs={"github_username": username},
    )

    while plan_run.state == PlanRunState.NEED_CLARIFICATION:
        for clarification in plan_run.get_outstanding_clarifications():
            print(f"Clarification needed: {clarification.user_guidance}")
            user_response = input("Response: ")
            plan_run = portia.resolve_clarification(
                clarification, user_response, plan_run
            )
        plan_run = portia.resume(plan_run)

    if plan_run.state == PlanRunState.COMPLETE and plan_run.outputs.final_output:
        final_output = plan_run.outputs.final_output.value
        # Since no model, assume LLM outputs JSON string - parse it
        try:
            return json.loads(final_output)
        except json.JSONDecodeError:
            return {"result": str(final_output), "error": "Failed to parse JSON"}
    raise Exception("Analysis failed")


if __name__ == "__main__":
    username = input("Enter GitHub username: ")
    try:
        result = analyze_github_profile(username)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

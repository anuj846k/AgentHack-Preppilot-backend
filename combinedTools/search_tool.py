import logging
import json
import os
from dotenv import load_dotenv
from portia import (
    Config,
    McpToolRegistry,
    Portia,
    StorageClass,
)
from portia.cli import CLIExecutionHooks

load_dotenv()


def search_company_news(query: str) -> str:
    """Search company/news/attendee info via Perplexity and return clean summary or text."""
    my_config = Config.from_default(storage_class=StorageClass.CLOUD)

    registry = McpToolRegistry.from_stdio_connection(
        server_name="perplexity-ask",
        command="npx",
        args=["-y", "server-perplexity-ask"],
        env={"PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY")},
    )

    portia = Portia(
        config=my_config,
        tools=registry,
        execution_hooks=CLIExecutionHooks(),
    )
    available_tools = [t.id for t in portia.tool_registry.get_tools()]
    logging.info(f"Available tools: {available_tools}")

    finalResult = portia.run(query).outputs.final_output
    raw_value = finalResult.value
    parsed = json.loads(raw_value)
    
    return parsed




# search_company_news("OpenAI launches new API features")

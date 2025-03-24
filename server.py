"""
Model Context Protocol server for Wordware integration.
"""

import os
import json
import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from wordware_mcp.tools.research import ResearchAgent

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("wordware-tools")

# Initialize our agents
research_agent = ResearchAgent()

@mcp.tool()
async def research_founder(full_name: str, company: str = "", url: str = "") -> str:
    """
    Research information about a founder or executive.
    
    Args:
        full_name: The full name of the person to research
        company: The company the person is associated with (optional)
        url: A relevant URL for additional context (optional)
        
    Returns:
        A detailed profile of the person from various sources
    """
    result = await research_agent.research_person(full_name, company, url)
    return await research_agent.format_person_research(result)

@mcp.tool()
async def research_topic(query: str) -> str:
    """
    Research a general topic and provide comprehensive information.
    
    Args:
        query: The topic or specific question to research
        
    Returns:
        Comprehensive research findings on the topic
    """
    results = await research_agent.research_topic(query)
    return await research_agent.format_topic_research(results)

def load_config():
    """Load configuration from the specified file."""
    config_path = os.environ.get("CONFIG_PATH", "./config.json")
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Wordware MCP server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                      help="Transport to use (stdio or sse)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (for sse transport)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (for sse transport)")
    
    args = parser.parse_args()
    
    config = load_config()
    print(f"Loaded configuration: {config}")
    
    print(f"Starting Wordware MCP server with {args.transport} transport...")
    
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=args.host, port=args.port) 
"""
Model Context Protocol server for Wordware integration with dynamic tool loading.
"""

import os
import json
import argparse
import logging
import asyncio
import traceback
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP
from wordware_mcp.client import WordwareClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Path to the configuration file
CONFIG_PATH = os.environ.get("CONFIG_PATH", "./tools_config.json")


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    id: str


class ToolConfigFile(BaseModel):
    """Structure of the configuration file."""
    tools: List[ToolConfig]


class DynamicMCPServer:
    """MCP server with dynamic tool loading."""
    
    def __init__(self, name: str = "wordware-tools"):
        """Initialize the MCP server."""
        self.mcp = FastMCP(name)
        self.wordware_client = WordwareClient()
        self.tool_configs = []
        self.tools_cache = {}
    
    async def load_config(self) -> None:
        """Load tool configuration from file."""
        try:
            with open(CONFIG_PATH, "r") as f:
                config_data = json.load(f)
                
            config = ToolConfigFile(**config_data)
            self.tool_configs = config.tools
            logger.info(f"Loaded configuration with {len(self.tool_configs)} tools")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.tool_configs = []
    
    async def register_tools(self) -> None:
        """Register tools based on the configuration."""
        for tool_config in self.tool_configs:
            await self.register_tool(tool_config.id)
    
    async def register_tool(self, tool_id: str) -> None:
        """Register a specific tool by ID."""
        try:
            # Get tool details from Wordware API
            logger.info(f"Fetching tool details for ID: {tool_id}")
            tool_details = await self.wordware_client.get_tool_metadata(tool_id)
            
            if not tool_details or "data" not in tool_details:
                logger.error(f"Failed to get information for tool {tool_id}")
                return
            
            tool_data = tool_details["data"]
            attributes = tool_data.get("attributes", {})
            
            # Extract tool information
            # Remove all characters except letters and spaces, then replace spaces with underscores
            raw_title = attributes.get("title", "")
            # Keep only letters and spaces (no digits or other symbols)
            clean_title = ''.join(c for c in raw_title if c.isalpha() or c.isspace())
            # Replace spaces with underscores and convert to lowercase
            tool_name = clean_title.lower().replace(" ", "_")
            
            # Check for empty name and add prefix if name is empty
            if not tool_name:
                tool_name = f"wordware_tool_{tool_id[-8:]}"
            
            # Get description and input schema
            description = attributes.get("description", "")
            input_schema = attributes.get("inputSchema", {})
            
            # Check if we need to extract properties from the nested "kwargs" object
            properties = input_schema.get("properties", {})
            
            # If there is only one field "kwargs" in properties and it contains an object with properties,
            # we'll use its properties directly
            has_kwargs_wrapper = False
            kwargs_properties = None
            
            if len(properties) == 1 and "kwargs" in properties and "properties" in properties["kwargs"]:
                kwargs_properties = properties["kwargs"].get("properties", {})
                if kwargs_properties:
                    logger.info(f"Tool {tool_id} has kwargs wrapper in schema, extracting inner properties")
                    has_kwargs_wrapper = True
                    # Remember that we need to wrap parameters in kwargs when calling
                    self.tools_cache[tool_id] = {
                        "id": tool_id,
                        "name": tool_name,
                        "description": description,
                        "requires_kwargs_wrapper": True
                    }
            

            json_schema_description = ""
            if has_kwargs_wrapper:
                json_schema_description = json.dumps(kwargs_properties, indent=2)
            else:
                json_schema_description = json.dumps(properties, indent=2)
                self.tools_cache[tool_id] = {
                    "id": tool_id,
                    "name": tool_name,
                    "description": description,
                    "requires_kwargs_wrapper": False
                }
            
            # Complete description with schema at the beginning
            full_description = f"## Input Schema\n\n```json\n{json_schema_description}\n```\n\n## Description\n\n{description}"

            self.mcp.add_tool(
                self.create_tool_function(tool_id, tool_name),
                name=tool_name,
                description=full_description
            )
            
            logger.info(f"Tool registered: {tool_name} ({tool_id})")
            
        except Exception as e:
            logger.error(f"Error registering tool {tool_id}: {e}")
            traceback.print_exc()
    
    def create_tool_function(self, tool_id: str, tool_name: str):
        """Create a function for an MCP tool."""
        async def tool_function(**kwargs):
            """Dynamically created tool function."""
            logger.info(f"Executing tool {tool_name} with arguments: {kwargs}")

            if len(kwargs) == 1 and 'kwargs' in kwargs and isinstance(kwargs['kwargs'], str):
                kwargs_value = kwargs['kwargs'].strip('`')
                if kwargs_value.startswith('{') and kwargs_value.endswith('}'):
                    try:
                        logger.info(f"Attempting to parse JSON string in kwargs: {kwargs_value}")
                        parsed_json = json.loads(kwargs_value)

                        processed_inputs = parsed_json
                        logger.info(f"Successfully parsed JSON string. Using parsed inputs: {processed_inputs}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing kwargs JSON string: {e}")

                        processed_inputs = kwargs
                else:
                    processed_inputs = kwargs
            else:
                # Process input parameters - normalize any keys with backticks
                processed_inputs = {}
                for key, value in kwargs.items():
                    # Remove backticks from keys if present
                    clean_key = key.strip('`')
                    # Remove backticks from string values if present
                    if isinstance(value, str):
                        clean_value = value.strip('`')
                    else:
                        clean_value = value
                    processed_inputs[clean_key] = clean_value
            
            logger.info(f"Processed inputs: {processed_inputs}")
            
            # Check if this tool requires kwargs wrapper
            tool_info = self.tools_cache.get(tool_id, {})
            requires_kwargs_wrapper = tool_info.get("requires_kwargs_wrapper", False)
            
            # If the tool requires wrapping, wrap parameters in kwargs
            if requires_kwargs_wrapper:
                final_inputs = {"kwargs": processed_inputs}
                logger.info(f"Tool {tool_name} requires kwargs wrapper. Final inputs: {final_inputs}")
            else:
                final_inputs = processed_inputs
                logger.info(f"Tool {tool_name} does not require kwargs wrapper. Using direct parameters.")
            
            # Direct parameter passing to run_generic_tool
            try:
                logger.info(f"Calling run_generic_tool with tool_id={tool_id} and inputs={final_inputs}")
                
                # Create a new event loop if needed to avoid closed loop errors
                try:
                    # Check current event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        logger.warning("Current event loop is closed. Creating a new one.")
                        asyncio.set_event_loop(asyncio.new_event_loop())
                        loop = asyncio.get_event_loop()
                    
                    # Execute the tool with the processed parameters directly
                    result = await self.wordware_client.run_generic_tool(tool_id, final_inputs)
                    logger.debug(f"Raw result from tool {tool_name}: {result}")
                except RuntimeError as e:
                    if "Event loop is closed" in str(e):
                        logger.error(f"Event loop closed during tool execution: {e}")
                        try:
                            logger.info("Attempting to create a new event loop and retry")
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            client = WordwareClient()
                            result = await client.run_generic_tool(tool_id, final_inputs)
                            await client.close()
                        except Exception as retry_error:
                            logger.error(f"Retry also failed: {retry_error}", exc_info=True)
                            return f"❌ Error: Failed to execute tool after retry: {str(retry_error)}"
                    else:
                        logger.error(f"Runtime error during tool execution: {e}", exc_info=True)
                        return f"❌ Error: Runtime error: {str(e)}"
                except Exception as e:
                    logger.error(f"Exception during tool execution: {e}", exc_info=True)
                    return f"❌ Error: {str(e)}"
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Error executing tool {tool_name}: {e}\n{error_details}")
                return f"❌ Error: Failed to execute tool: {str(e)}"
            
            # Format the result
            if "output" in result:
                output = result["output"]
                
                # If there's a completion_output, return it
                if "completion_output" in output:
                    completion = output["completion_output"]
                    logger.info(f"Tool {tool_name} completed with completion_output")
                    if isinstance(completion, str):
                        return completion
                    elif isinstance(completion, dict) and "result" in completion:
                        return completion["result"]
                    else:
                        return json.dumps(completion, ensure_ascii=False, indent=2)
                
                # Special handling for research results
                if any(key.startswith("research") for key in output.keys()):
                    logger.info(f"Formatting research results for tool {tool_name}")
                    research_result = "# Research Results\n\n"
                    
                    # Process main research sections
                    sections = {
                        "person": "## Person Information",
                        "company": "## Company Information",
                        "competition": "## Competitor Analysis",
                        "questions": "## Interview Questions",
                        "summary": "## Summary",
                    }
                    
                    # First process special sections
                    for key_prefix, section_title in sections.items():
                        matching_keys = [k for k in output.keys() if key_prefix in k.lower()]
                        if matching_keys:
                            research_result += f"{section_title}\n\n"
                            for k in matching_keys:
                                content = output[k]
                                if isinstance(content, str):
                                    research_result += f"{content}\n\n"
                                else:
                                    try:
                                        research_result += f"{json.dumps(content, ensure_ascii=False, indent=2)}\n\n"
                                    except:
                                        research_result += f"[Content cannot be displayed]\n\n"
                    
                    # Then process other keys
                    other_keys = [k for k in output.keys() 
                                 if not any(prefix in k.lower() for prefix in sections.keys())
                                 and k != "completion_output"]
                    
                    if other_keys:
                        research_result += "## Additional Information\n\n"
                        for k in other_keys:
                            content = output[k]
                            if isinstance(content, str):
                                research_result += f"### {k}\n\n{content}\n\n"
                            else:
                                try:
                                    research_result += f"### {k}\n\n```json\n{json.dumps(content, ensure_ascii=False, indent=2)}\n```\n\n"
                                except:
                                    research_result += f"### {k}\n\n[Content cannot be displayed]\n\n"
                    
                    return research_result
                
                # For Notion saving results
                if any(key.startswith("notion") or key.startswith("save") for key in output.keys()):
                    logger.info(f"Formatting Notion results for tool {tool_name}")
                    result_output = "# Notion Save Result\n\n"
                    
                    # Search for URL or other information about created page
                    url_keys = [k for k in output.keys() if "url" in k.lower()]
                    for k in url_keys:
                        if isinstance(output[k], str) and output[k].startswith("http"):
                            result_output += f"✅ Page successfully created: {output[k]}\n\n"
                    
                    # If URL not found, show available information
                    if not url_keys:
                        result_output += "Operation completed. Details:\n\n"
                        for k, v in output.items():
                            if k != "completion_output":
                                if isinstance(v, str):
                                    result_output += f"- **{k}**: {v}\n"
                                else:
                                    try:
                                        result_output += f"- **{k}**: {json.dumps(v, ensure_ascii=False)}\n"
                                    except:
                                        result_output += f"- **{k}**: [Complex data]\n"
                    
                    return result_output
                
                # General case - format all data
                logger.info(f"Formatting general results for tool {tool_name}")
                formatted_result = f"# Results for {tool_name}\n\n"
                for key, value in output.items():
                    if key != "completion_output":
                        formatted_result += f"## {key}\n\n"
                        if isinstance(value, str):
                            formatted_result += f"{value}\n\n"
                        else:
                            try:
                                formatted_result += f"```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n\n"
                            except:
                                formatted_result += "[Content cannot be displayed]\n\n"
                
                return formatted_result
            
            # If there was an error
            if "error" in result:
                logger.error(f"Tool {tool_name} execution error: {result['error']}")
                return f"❌ Error: {result['error']}"
            
            # If nothing else matched
            try:
                return json.dumps(result, ensure_ascii=False, indent=2)
            except:
                return "Received data that cannot be displayed"
        
        return tool_function
    
    async def initialize(self) -> None:
        """Initialize the server."""
        logger.info("Initializing MCP server")
        await self.load_config()
        await self.register_tools()
        logger.info("Initialization complete")
    
    def run(self, **kwargs):
        """Run the MCP server."""
        # First run initialization
        logger.info(f"Starting MCP server with parameters: {kwargs}")
        asyncio.run(self.initialize())
        
        # Then run the server
        self.mcp.run(**kwargs)


def load_config() -> Dict[str, Any]:
    """Load configuration from the specified file."""
    config_path = os.environ.get("CONFIG_PATH", "./config.json")
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Wordware MCP server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                      help="Transport to use (stdio or sse)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (for sse transport)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (for sse transport)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        
    config = load_config()
    logger.info(f"Loaded configuration: {config}")
    
    logger.info(f"Starting Wordware MCP server with {args.transport} transport...")
    
    # Create and run the dynamic MCP server
    server = DynamicMCPServer()
    
    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", host=args.host, port=args.port)

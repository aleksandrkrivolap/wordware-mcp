# Wordware MCP

A Model Context Protocol (MCP) server that integrates Wordware's powerful agent capabilities with Claude and other MCP-compatible AI assistants.

## Overview

This project creates a bridge between AI assistants like Claude and Wordware's specialized agent capabilities through Anthropic's Model Context Protocol (MCP). The integration dynamically loads tools from Wordware API based on configuration, allowing Claude to access any specialized Wordware flow.

## Features

- **🔄 Dynamic Tool Loading** - Automatically loads tools from Wordware API based on configuration
- **🧠 Intelligent Schema Detection** - Automatically detects and adapts to different tool input schemas
- **🔍 Advanced Parameter Processing** - Handles various input formats (JSON, nested structures, strings)
- **⚙️ Robust Error Handling** - Comprehensive error logging and event loop management
- **🔑 Simple Authentication** - Easy setup to connect your Wordware account

## Prerequisites

- Python 3.8+
- Wordware API credentials
- Claude Desktop or other MCP-compatible client

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wordware-mcp.git
cd wordware-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Wordware API credentials
```

## Configuration

Create a `tools_config.json` file with the following structure:

```json
{
  "tools": [
    {
      "id": "your-tool-id-1"
    },
    {
      "id": "your-tool-id-2"
    },
    {
      "id": "your-tool-id-3"
    }
  ]
}
```

You can specify any Wordware tool ID in this configuration file, and the server will dynamically load and register them as MCP tools. The tool metadata, including input schema and description, will be fetched directly from the Wordware API.

To specify a custom configuration file path, use the `CONFIG_PATH` environment variable.

## Running the Server

```bash
# Run with default settings
python server.py

# Run with debug logging
python server.py --debug

# Run with SSE transport on a specific port
python server.py --transport sse --host 127.0.0.1 --port 8000

# Or install in Claude Desktop
mcp install python server.py --name "Wordware Tools"
```

## How It Works

The Wordware MCP server operates as follows:

1. **Tool Configuration Loading** - Reads the list of tool IDs from the configuration file
2. **Dynamic Tool Registration** - For each tool ID:
   - Fetches metadata from the Wordware API
   - Detects input schema requirements
   - Creates a corresponding MCP tool function
   - Registers the tool with the MCP server
3. **Request Processing** - When a tool is called:
   - Processes input parameters in various formats (JSON objects, strings, nested structures)
   - Adapts parameters format based on tool requirements
   - Sends the properly formatted request to the Wordware API
4. **Response Handling** - Processes Wordware API responses:
   - Parses the Server-Sent Events (SSE) stream
   - Collects all output values
   - Formats the response for Claude in a user-friendly way

## Advanced Features

### Intelligent Parameter Handling

The server automatically handles different input parameter formats:

- Direct parameters: `{"Full Name": "John Doe", "Company": "Acme Inc."}`
- JSON string in kwargs: `{"kwargs": "{\"Full Name\": \"John Doe\", \"Company\": \"Acme Inc.\"}"}`
- Nested parameters: `{"kwargs": {"Full Name": "John Doe", "Company": "Acme Inc."}}`

### Input Schema Detection

The server analyzes each tool's input schema to determine the correct format:
- Detects if a tool requires parameters wrapped in a `kwargs` object
- Extracts inner properties for better documentation
- Adapts the parameter format for each tool automatically

### Error Handling and Recovery

Robust error handling includes:
- Event loop monitoring and recovery
- Detailed logging of all requests and responses
- Graceful handling of HTTP errors and timeouts
- Comprehensive error messages for troubleshooting

## Troubleshooting

- **Tool not showing in Claude Desktop**: Ensure the server is running and properly registered in Claude Desktop settings
- **Authentication errors**: Check that your Wordware API key is correctly set in the `.env` file
- **Parameter validation errors**: Verify the input format matches the tool's requirements
- **Event loop errors**: If you see "Event loop is closed" errors, try restarting the server

## Development

To extend or modify the server:

```bash
# Run with debug logging
python server.py --debug

# Check the logs for detailed information
tail -f /path/to/your/logs/mcp.log
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [Wordware](https://wordware.ai/) for their agent platform
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) for the protocol implementation 
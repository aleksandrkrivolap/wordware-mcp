# Wordware MCP

A Model Context Protocol (MCP) server that integrates Wordware's powerful agent capabilities with Claude and other MCP-compatible AI assistants.

![Wordware MCP](https://mintlify.s3.us-west-1.amazonaws.com/wordware/images/get-started/api/trigger-api.png)

## Overview

This project creates a bridge between AI assistants like Claude and Wordware's specialized agent capabilities through Anthropic's Model Context Protocol (MCP). This integration allows Claude to offload specialized tasks to purpose-built Wordware flows for enhanced capabilities.

## Features

- **🔍 Research Agent** - Delegate in-depth research tasks to specialized Wordware flows
- **📝 Notion Saver** - Save AI assistant outputs directly to Notion via Wordware
- **🤔 ReAct Agent** - Enable deeper reflection on complex problems through Wordware's ReAct pattern
- **⏱️ Asynchronous Tools** - Support for long-running operations with status checks
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

Create a `config.json` file with the following structure:

```json
{
  "research_flow_id": "your-research-flow-id",
  "notion_flow_id": "your-notion-flow-id",
  "react_flow_id": "your-react-flow-id",
  "notion_database_id": "your-default-notion-database-id"
}
```

Or set the path to your configuration file using the `CONFIG_PATH` environment variable.

## Running the Server

```bash
# Run directly
python server.py

# Or using the MCP CLI
mcp run server.py

# Or install in Claude Desktop
mcp install server.py --name "Wordware Tools"
```

## Usage Examples

### Research Agent

Use Claude to delegate research tasks to specialized Wordware agents:

```
User: "Research the funding history of Anthropic"
Claude: "I'll use the Wordware Research Agent to find detailed information..."
[Claude processes this through Wordware's specialized research flow]
Claude: "According to my research, Anthropic has received funding from..."
```

### Notion Integration

Save content directly to your Notion workspace:

```
User: "Save this meeting summary to my Notion workspace"
Claude: "I'll save that for you using the Wordware Notion integration..."
[Claude sends content to Wordware, which handles the Notion API interaction]
Claude: "Your meeting summary has been saved to your Notion workspace"
```

### ReAct Agent

Leverage advanced reasoning capabilities:

```
User: "I need to solve this complex problem about optimizing our customer support workflow"
Claude: "Let me think through this carefully using the ReAct framework..."
[Claude delegates to Wordware's ReAct agent for step-by-step reasoning]
Claude: "After careful analysis, here's my recommendation..."
```

## How It Works

This project leverages the official MCP Python SDK to create a server that exposes Wordware's capabilities as MCP tools:

1. **Tool Registration** - Publishing available Wordware flows as MCP tools
2. **Request Processing** - Converting MCP tool calls to Wordware API requests
3. **Asynchronous Operations** - Managing long-running tasks with status updates
4. **Authentication** - Securely handling user credentials for both services

## Development

### Project Structure

```
wordware-mcp/
├── wordware_mcp/
│   ├── client.py         # Wordware API client
│   ├── tools/            # MCP tool implementations
│   │   ├── research.py   # Research agent
│   │   ├── notion.py     # Notion integration
│   │   └── react.py      # ReAct agent
├── server.py             # MCP server using the Python SDK
├── .env.example          # Example environment variables
└── config.json           # Configuration file
```

### Adding New Tools

To create a new tool that integrates with a Wordware flow:

1. Create a new Python file in the `wordware_mcp/tools` directory
2. Implement a class that extends the `Tool` class from `mcp.server.fastmcp`
3. Register your tool in `server.py`

## MCP Protocol Implementation

This project implements the MCP protocol as specified in the [official documentation](https://modelcontextprotocol.io/). It provides:

- Tool discovery via the `/.well-known/mcp-tools` endpoint
- JSON schema definitions for each tool
- Proper handling of both synchronous and asynchronous tool patterns

## Troubleshooting

- **Tool not showing in Claude Desktop**: Ensure the server is running and properly registered in Claude Desktop settings
- **Authentication errors**: Check that your Wordware API key is correctly set in the `.env` file
- **Flow execution failures**: Verify that the flow IDs in your configuration match the actual flows in your Wordware account

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Acknowledgements

- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [Wordware](https://wordware.ai/) for their agent platform
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) for the protocol implementation

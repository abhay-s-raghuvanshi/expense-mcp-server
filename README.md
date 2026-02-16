# Expense MCP Server

A Model Context Protocol (MCP) server for tracking and managing expenses. This server enables AI assistants to help you manage your finances through natural language interactions.

## Overview

The Expense MCP Server implements the Model Context Protocol to provide expense tracking capabilities to AI tools like Claude Desktop, Cursor, and other MCP-compatible clients. Track expenses, categorize spending, and get insights into your financial habits through conversational AI.

## Features

- **Add Expenses**: Record expenses with categories, amounts, and descriptions
- **View Expenses**: Retrieve and filter expenses by date, category, or amount
- **Expense Summaries**: Get spending summaries and financial insights
- **Member Management**: Track expenses for multiple members or groups
- **Persistent Storage**: All data is stored locally in JSON format

## Prerequisites

- Python 3.10 or higher
- uv (Python package manager)

## Installation

### 1. Install uv

If you haven't already installed uv:

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the Repository

```bash
git clone https://github.com/shivamprasad1001/expense-mcp-server.git
cd expense-mcp-server
```

### 3. Install Dependencies

```bash
uv sync
```

## Finding Your uv Path

To avoid configuration errors, you'll need the absolute path to your `uv` executable.

**macOS/Linux**:
```bash
which uv
```

**Windows (PowerShell)**:
```powershell
where.exe uv
```

The command will output something like:
- macOS: `/Users/yourusername/.local/bin/uv` or `/opt/homebrew/bin/uv`
- Linux: `/home/yourusername/.local/bin/uv`
- Windows: `C:\Users\YourUsername\.local\bin\uv.exe`

## Configuration

### For Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "/ABSOLUTE/PATH/TO/uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/expense-mcp-server",
        "run",
        "expense-mcp-server"
      ]
    }
  }
}
```

**Example (macOS)**:
```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "/Users/johndoe/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/johndoe/projects/expense-mcp-server",
        "run",
        "expense-mcp-server"
      ]
    }
  }
}
```

**Example (Windows)**:
```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "C:\\Users\\JohnDoe\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\JohnDoe\\projects\\expense-mcp-server",
        "run",
        "expense-mcp-server"
      ]
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "/ABSOLUTE/PATH/TO/uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/expense-mcp-server",
        "run",
        "expense-mcp-server"
      ]
    }
  }
}
```

### For Other MCP Clients

Refer to your MCP client's documentation for configuration. Generally, you'll need to specify:
- **Command**: Absolute path to `uv` (e.g., `/Users/username/.local/bin/uv`)
- **Args**: `["--directory", "/absolute/path/to/expense-mcp-server", "run", "expense-mcp-server"]`

## Usage

Once configured, restart your AI assistant (Claude Desktop/Cursor) to load the MCP server. You can then interact with the expense tracker through natural language:

### Example Interactions

- "Add a $50 expense for groceries"
- "Show me all my expenses this month"
- "How much did I spend on restaurants?"
- "What's my total spending this week?"
- "Add a $25 expense for transportation"
- "List all expenses over $100"
- "Add a new member named John"
- "Show me all members and their expenses"

## Available Tools

The MCP server exposes the following tools for AI assistants:

- `add_expense`: Record a new expense with amount, category, and description
- `list_expenses`: View all expenses or filter by criteria (date, category, amount)
- `get_summary`: Get spending summaries, totals, and statistics
- `add_member`: Add a new member for expense tracking
- `list_members`: View all members
- `delete_expense`: Remove an expense by ID
- `update_expense`: Modify an existing expense

## Data Storage

All expense data is stored locally in `members.json` in the project directory. This file contains:
- Member information
- Expense records with timestamps
- Categories and metadata

**Data Privacy**: All your data stays on your local machine. Nothing is sent to external servers.

## Development

### Project Structure

```
expense-mcp-server/
├── main.py              # Main MCP server implementation
├── members.json         # Data storage (created on first run)
├── pyproject.toml       # Project configuration
├── uv.lock             # Dependency lock file
└── README.md           # This file
```

### Running in Development Mode

```bash
# Navigate to project directory
cd expense-mcp-server

# Run the server
uv run expense-mcp-server
```

### Testing with MCP Inspector

You can test the MCP server using the MCP Inspector tool:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/expense-mcp-server run expense-mcp-server
```

The inspector provides a web interface to test all available tools and resources.

## Troubleshooting

### Common Issues

**"command not found: uv"**
- Make sure you've installed uv and it's in your PATH
- Use the absolute path to uv in your configuration (see "Finding Your uv Path" section)

**"No module named 'mcp'"**
- Run `uv sync` in the project directory to install dependencies

**Changes not reflecting in Claude Desktop**
- Restart Claude Desktop completely after configuration changes
- Check the Developer Tools in Claude Desktop (View > Developer Tools) for errors

**Server not starting**
- Verify all paths in the configuration are absolute paths
- Ensure the `members.json` file is writable
- Check Python version with `python --version` (must be 3.10+)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Roadmap

- [ ] Add budget tracking and alerts
- [ ] Export expenses to CSV/Excel
- [ ] Support for multiple currencies
- [ ] Recurring expense tracking
- [ ] Category-based analytics and charts
- [ ] Receipt image storage (with OCR)

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/shivamprasad1001/expense-mcp-server/issues)
- Check the [Model Context Protocol documentation](https://modelcontextprotocol.io)
- Join the MCP community discussions

## About MCP

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of MCP like a USB-C port for AI - it provides a standardized way to connect AI models to different data sources and tools.

Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Author

Created by [shivamprasad1001](https://github.com/shivamprasad1001)

---

**Important**: Always use absolute paths in your MCP configuration to avoid "command not found" errors. Replace placeholder paths with your actual system paths.
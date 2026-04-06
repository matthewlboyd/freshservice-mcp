# Freshservice MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects Claude to your Freshservice ITSM instance.

## Supported modules

| Module | Operations |
|--------|-----------|
| **Tickets** | Create, view, list, update, delete, filter, get field definitions |
| **Conversations** | List, reply to ticket, add notes (public/private), delete notes |
| **Changes** | Create, view, list, update, close, delete, filter, tasks, notes |
| **Assets** | Create, view, list, update, delete, search, filter, get types |
| **Problems** | Create, view, list |
| **Agents** | List, view, filter |
| **Requesters** | Create, list, view, filter |
| **Agent Groups** | List, view |
| **Requester Groups** | List, view |
| **Products** | List, view |
| **Workspaces** | List |
| **Canned Responses** | List folders, list responses, view |
| **Solution Categories** | Create, list, view |
| **Solution Folders** | Create, list, view |
| **Solution Articles** | Create, list, view, search |
| **Departments** | List, view |
| **Locations** | List |
| **Software** | List, view |
| **Vendors** | List |
| **Service Catalog** | List items, view item |
| **Announcements** | List |
| **Contracts** | List, view |
| **Purchase Orders** | List |

## Prerequisites

- **Python 3.10+**
- **uv** — fast Python package manager
- **Claude Desktop** or **Claude Code** (see [Setup](#setup) below)
- A **Freshservice account** with an API key

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with Homebrew
brew install uv
```

### Get your Freshservice API key

1. Log in to your Freshservice portal
2. Click your **profile picture** → **Profile Settings**
3. Your API key is shown on the right side under **Change Password**

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/matthewlboyd/freshservice-mcp.git
cd freshservice-mcp
```

### 2a. Configure Claude Desktop

**Option A — macOS install script (recommended):**

```bash
./install.sh
```

This handles everything automatically: prompts for your repo path, API key, and domain, writes the config, tests the connection, and restarts Claude Desktop.

**Option B — Manual setup (all platforms):**

Open the Claude Desktop config file in any text editor:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Paste the following into the file, replacing the placeholder values. If the file doesn't exist yet, create it with just this content:

```json
{
  "mcpServers": {
    "freshservice": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/full/path/to/freshservice-mcp",
        "freshservice-mcp"
      ],
      "env": {
        "FRESHSERVICE_APIKEY": "your_api_key_here",
        "FRESHSERVICE_DOMAIN": "yourcompany.freshservice.com"
      }
    }
  }
}
```

`FRESHSERVICE_DOMAIN` should be just the hostname — no `https://` prefix.

If you're behind a corporate proxy with SSL inspection, add `SSL_CERT_FILE` to the `env` block pointing at your CA bundle:

```json
"env": {
  "FRESHSERVICE_APIKEY": "your_api_key_here",
  "FRESHSERVICE_DOMAIN": "yourcompany.freshservice.com",
  "SSL_CERT_FILE": "/path/to/your/ca-bundle.crt"
}
```

> Already have other MCP servers? Add just the `"freshservice": { ... }` block inside your existing `"mcpServers"` object instead of replacing the whole file.

**Restart Claude Desktop** — quit and reopen it. The first launch will automatically install dependencies (takes ~30 seconds). You should see a hammer icon (🔨) in the chat input, indicating MCP tools are available.

### 2b. Configure Claude Code

**Recommended: project-local scope**

```bash
claude mcp add freshservice \
  --scope local \
  --env FRESHSERVICE_APIKEY=your_api_key_here \
  --env FRESHSERVICE_DOMAIN=yourcompany.freshservice.com \
  -- uv run --directory /full/path/to/freshservice-mcp freshservice-mcp
```

`--scope local` stores the config in `.claude/settings.local.json`, which is **gitignored by default** — your API key will not be committed to version control.

**Alternative: user scope (available in all your projects)**

```bash
claude mcp add freshservice \
  --scope user \
  --env FRESHSERVICE_APIKEY=your_api_key_here \
  --env FRESHSERVICE_DOMAIN=yourcompany.freshservice.com \
  -- uv run --directory /full/path/to/freshservice-mcp freshservice-mcp
```

> **Security note:** Never use `--scope project` with credentials hardcoded in the command — the `project` scope writes to `.mcp.json`, which is typically committed to version control. Use `local` or `user` scope, or pass credentials via environment variables already set in your shell.

If you're behind a corporate proxy with SSL inspection, add `--env SSL_CERT_FILE=/path/to/your/ca-bundle.crt` to the command above.

**Verify the server is registered:**

```bash
claude mcp list
```

You should see `freshservice` in the output. No restart is needed — Claude Code picks up MCP servers at the start of each session.

## Example prompts

### Tickets
- "Show me all open urgent tickets"
- "Create a ticket for a VPN connectivity issue — assign to the Network team, high priority"
- "Update ticket #4521 to resolved"
- "Find all tickets created this week by john@example.com"

### Changes
- "Create a change request for server maintenance this Saturday, 10pm–2am"
- "Show all changes awaiting approval"
- "Close change #89 — migration completed successfully"

### Assets
- "List all laptops in the asset inventory"
- "Search for assets tagged 'datacenter'"
- "Show all unassigned hardware assets"

### Knowledge Base
- "Search the knowledge base for VPN setup instructions"
- "Create a new solution article on how to reset your password"
- "List all articles in the Onboarding folder"

### General
- "How many open tickets are assigned to the Help Desk group?"
- "List all active agents and their departments"
- "Show me all software registered in the system"

## Running the tests

The test suite covers all 62 tools and the API client (117 tests total). No Freshservice credentials are needed — all tests use mocked HTTP calls.

**Install dev dependencies:**

```bash
uv pip install -e ".[dev]"
```

**Run all tests:**

```bash
uv run pytest tests/ -v
```

**Run a specific module's tests:**

```bash
uv run pytest tests/test_tickets.py -v
```

**Test files:**

| File | What it covers |
|------|---------------|
| `test_client.py` | HTTP client — auth, domain normalisation, error handling |
| `test_tickets.py` | Ticket tools |
| `test_conversations.py` | Reply, notes, delete note |
| `test_changes.py` | Change request tools |
| `test_assets.py` | Asset tools |
| `test_people.py` | Agents, requesters, groups |
| `test_knowledge_base.py` | Solution categories, folders, articles |
| `test_misc.py` | Problems, products, workspaces, canned responses, departments, locations, software, vendors, service catalog, announcements, contracts, purchase orders |

## Troubleshooting

**Tools don't appear in Claude Desktop**
Make sure the path in `--directory` is the absolute path to the repo and that you've fully quit and restarted Claude (not just closed the window).

**Tools don't appear in Claude Code**
Run `claude mcp list` to confirm the server is registered. If it is, start a new `claude` session — MCP servers are loaded at session start. If it's missing, re-run the `claude mcp add` command.

**Authentication error (401)**
Your API key is incorrect. Double-check it in Freshservice → Profile Settings. Copy it using the copy icon rather than selecting the text manually.

**403 Forbidden**
The API key doesn't have permission for that operation, or the domain is wrong. Confirm `FRESHSERVICE_DOMAIN` is just the hostname (e.g. `yourcompany.freshservice.com`), with no `https://` prefix.

**SSL certificate errors**
If you're behind a corporate proxy with SSL inspection, requests will fail with a certificate verification error. Set the `SSL_CERT_FILE` environment variable to the path of your organisation's CA bundle. In Claude Desktop, add it to the `"env"` block in `claude_desktop_config.json`. In Claude Code, pass `--env SSL_CERT_FILE=/path/to/ca-bundle.crt` when running `claude mcp add`.

**Rate limiting (429)**
Freshservice enforces per-minute API rate limits based on your plan. Wait a moment and try again.

**Filter queries returning errors**
Filter strings must use double-quoted field values. Example: `"status:2 AND priority:4"` not `status:2 AND priority:4`.

**Checking logs**
If something isn't working, check the MCP server logs:
- **macOS:** `~/Library/Logs/Claude/mcp-server-freshservice.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp-server-freshservice.log`

## License

MIT

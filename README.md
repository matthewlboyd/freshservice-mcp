# Freshservice MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects Claude to your Freshservice ITSM instance. Ask Claude in plain English to manage tickets, changes, assets, the knowledge base, and much more — no API docs required.

## What you can do

Once set up, you can say things like:

> *"Show me all open urgent tickets assigned to the Network team"*
> *"Create a change request for Saturday's server maintenance window"*
> *"Search the knowledge base for password reset instructions"*
> *"List all laptops in the asset inventory and show which are unassigned"*

---

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

---

## Prerequisites

- **Python 3.10+**
- **uv** — fast Python package manager
- **Claude Desktop** — [download here](https://claude.ai/download)
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

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/StackEng/freshservice-mcp.git
cd freshservice-mcp
```

### 2. Configure Claude Desktop

**Option A — macOS install script (recommended):**

```bash
./install.sh
```

This handles everything automatically: prompts for your repo path, API key, and domain, writes the config, tests the connection, and restarts Claude Desktop.

---

**Option B — Manual setup (all platforms):**

Open the Claude Desktop config file in any text editor:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Paste the following into the file, replacing the three placeholder values. If the file doesn't exist yet, create it with just this content:

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

- `/full/path/to/freshservice-mcp` — absolute path to the cloned repo (`pwd` on macOS/Linux, or copy from Explorer's address bar on Windows)
- `your_api_key_here` — your Freshservice API key
- `yourcompany.freshservice.com` — your Freshservice domain, no `https://`

> Already have other MCP servers? Add just the `"freshservice": { ... }` block inside your existing `"mcpServers"` object instead of replacing the whole file.

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. The first launch will automatically install dependencies (takes ~30 seconds). You should see a hammer icon (🔨) in the chat input, indicating MCP tools are available.

---

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

---

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

---

## Troubleshooting

**Tools don't appear in Claude Desktop**
Make sure the path in `--directory` is the absolute path to the repo and that you've fully quit and restarted Claude (not just closed the window).

**Authentication error (401)**
Your API key is incorrect. Double-check it in Freshservice → Profile Settings. Copy it using the copy icon rather than selecting the text manually.

**403 Forbidden**
The API key doesn't have permission for that operation, or the domain is wrong. Confirm `FRESHSERVICE_DOMAIN` is just the hostname (e.g. `yourcompany.freshservice.com`), with no `https://` prefix.

**Rate limiting (429)**
Freshservice enforces per-minute API rate limits based on your plan. Wait a moment and try again.

**Filter queries returning errors**
Filter strings must use double-quoted field values. Example: `"status:2 AND priority:4"` not `status:2 AND priority:4`.

**Checking logs**
If something isn't working, check the MCP server logs:
- **macOS:** `~/Library/Logs/Claude/mcp-server-freshservice.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp-server-freshservice.log`

---

## License

MIT

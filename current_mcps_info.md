# Information on Current Project MCP Servers and Tools

---

## Current Project MCP Servers

This document provides a comprehensive, detailed, and project-specific overview of all Model Context Protocol (MCP) servers currently integrated with the current project's Windsurf Editor IDE configuration (see `mcp_config.json`). These MCP servers form the backbone of Windsurf’s AI-powered, agentic workflows, enabling the IDE to interact with code repositories, file systems, search engines, knowledge graphs, programming assistants, and other productivity tools through standardized, natural-language-driven APIs.

**Contents:**

* A summary table for all configured MCP servers in this project
* Detailed sections for each MCP server, covering:

  * Overview and main functions
  * Installation/configuration in Windsurf
  * Available tools, methods, and key parameters
  * Usage examples
  * Best practices or special project considerations
  * Links to official docs and implementation guides

Sensitive information (such as API keys) is redacted. All documentation links are provided as active markdown links.

Can you please use this info to complete the following table?

### Current MCP Servers Overview Table

| MCP Server | Category / Primary Use‑Case | Key Capabilities (summary) | Representative Tools / APIs | Required Env Vars | OS / Platform Notes | Docs / Source |
|------------|----------------------------|----------------------------|-----------------------------|-------------------|---------------------|---------------|
| **desktop-commander** | Desktop Automation & Control | File System access, Execute commands, Work with code and text, run processes, and automate tasks | `read_multiple_files`, `search_files` , `write_file`, `execute_command`, `list_directory`,  `move_file` | Internal config options and parameters | Cross‑platform | [git](https://github.com/wonderwhy-er/desktop-commander) |
| **sequential‑thinking** | Reflective step‑wise reasoning | Dynamic “chain‑of‑thought”, branching, revisions, adjustable step count | `sequentialthinking` | – | Cross‑platform | [link](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) |
| **context7** | Live library documentation retrieval | Pulls **version‑specific** docs & code samples into LLM prompts; avoids hallucinations | `resolve‑library‑id`, `get‑library‑docs` | – | Cross‑platform | [site](https://context7.com) / [git](https://github.com/upstash/context7) |
| **brave‑search** | Web & local search | Brave Web Search + Local business search; pagination, freshness filters, smart fallback | `brave_web_search`, `brave_local_search` | `BRAVE_API_KEY` (redacted) | Cross‑platform | [git](https://github.com/w-jeon/mcp-brave-search) |
| **memory** | Knowledge‑graph long‑term memory | Persistent entities, relations, atomic observations; full CRUD + graph read/search | `create_entities`, `create_relations`, `read_graph` | – | Cross‑platform | [git](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) |
| **github** | GitHub repo & PR automation | Create/update files, branches, issues, PRs, code/issue/user search, batch pushes | `create_or_update_file`, `push_files`, `create_pull_request` | `GITHUB_PERSONAL_ACCESS_TOKEN` (redacted) | Cross‑platform | [git](https://github.com/modelcontextprotocol/servers/tree/main/src/github) |
| **fetcher** | Web page content extraction | Playwright‑based JS rendering; Readability main‑content; HTML/MD output; batch fetch | `fetch_url`, `fetch_urls` | – | Cross‑platform | [git](https://github.com/jae-jae/fetcher-mcp) |
| **excel** | Excel workbook manipulation | Read/write cells & formulas, sheet/table ops, screen capture (Win) | `excel_read_sheet`, `excel_write_to_sheet`, `excel_create_table` | `EXCEL_MCP_PAGING_CELLS_LIMIT` (optional) | **Windows‑only** for live features | [git](https://github.com/negokaz/excel-mcp-server) |
| **mcp‑sequentialthinking‑tools** | Reasoning **+ tool recommender** | Sequential thinking **with confidence‑scored MCP tool suggestions** per step | `sequentialthinking_tools` | – | Cross‑platform | [git](https://github.com/spences10/mcp-sequentialthinking-tools) |
| **code‑reasoning** | Code‑focused structured reasoning | Hybrid prompt; branchable, revision‑aware programming analysis & debugging | `code-reasoning` | – | Cross‑platform | [git](https://github.com/mikeysrecipes/code-reasoning) |
| **docs‑manager** | Markdown docs lifecycle | Read/write/edit with YAML front‑matter, nav generation, health checks, LLM export | `read_doc`, `edit_doc`, `generate_navigation` | – | Cross‑platform | [git](https://github.com/alekspetrov/mcp-docs-service) |
| **postgres‑mcp** | PostgreSQL Database Interaction (read–write) | Database health analysis, index optimization, query analysis, schema management, SQL execution with configurable access modes | `execute_sql`, `list_objects`, `get_object_details`, `analyze_workload_indexes`, `analyze_db_health` | PostgreSQL db connection string | Cross‑platform | [git](https://github.com/crystaldba/postgres-mcp) |

* For full command details, environment variable requirements, and further examples, see the per-server sections below.
* [Direct links to the official documentation](#) and GitHub repositories are included throughout.

---

### Sequential Thinking MCP Server

**Source/Docs:**
- [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)

#### **Overview**
The Sequential Thinking MCP server enables dynamic, flexible, and reflective problem-solving. It breaks down complex problems into manageable steps, supports revision and branching, and helps generate and verify solution hypotheses. This is ideal for multi-step processes, planning, iterative analysis, and situations where context must be maintained across evolving tasks.

#### Features
-   Break down complex problems into manageable steps
-   Revise and refine thoughts as understanding deepens
-   Branch into alternative paths of reasoning
-   Adjust the total number of thoughts dynamically
-   Generate and verify solution hypotheses


#### **Installation & Configuration**

* Add to `mcp_config.json` as:

  ```json
  {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    }
  }
  ```
* No special environment variables required.

#### **Available Tools & Methods**

- **sequentialthinking** (main tool):
  - A detailed tool for dynamic and reflective problem-solving through thoughts. This tool helps analyze problems through a flexible thinking process that can adapt and evolve. Each thought can build on, question, or revise previous insights as understanding deepens. When to use this tool: - Breaking down complex problems into steps - Planning and design with room for revision - Analysis that might need course correction - Problems where the full scope might not be clear initially - Problems that require a multi-step solution - Tasks that need to maintain context over multiple steps - Situations where irrelevant information needs to be filtered out Key features: - You can adjust total_thoughts up or down as you progress - You can question or revise previous thoughts - You can add more thoughts even after reaching what seemed like the end - You can express uncertainty and explore alternative approaches - Not every thought needs to build linearly - you can branch or backtrack - Generates a solution hypothesis - Verifies the hypothesis based on the Chain of Thought steps - Repeats the process until satisfied - Provides a correct answer Parameters explained: - thought: Your current thinking step, which can include: - Regular analytical steps - Revisions of previous thoughts - Questions about previous decisions - Realizations about needing more analysis - Changes in approach - Hypothesis generation - Hypothesis verification - next_thought_needed: True if you need more thinking, even if at what seemed like the end - thought_number: Current number in sequence (can go beyond initial total if needed) - total_thoughts: Current estimate of thoughts needed (can be adjusted up/down) - is_revision: A boolean indicating if this thought revises previous thinking - revises_thought: If is_revision is true, which thought number is being reconsidered - branch_from_thought: If branching, which thought number is the branching point - branch_id: Identifier for the current branch (if any) - needs_more_thoughts: If reaching end but realizing more thoughts needed You should: 1. Start with an initial estimate of needed thoughts, but be ready to adjust 2. Feel free to question or revise previous thoughts 3. Don't hesitate to add more thoughts if needed, even at the "end" 4. Express uncertainty when present 5. Mark thoughts that revise previous thinking or branch into new paths 6. Ignore information that is irrelevant to the current step 7. Generate a solution hypothesis when appropriate 8. Verify the hypothesis based on the Chain of Thought steps 9. Repeat the process until satisfied with the solution 10. Provide a single, ideally correct answer as the final output 11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached
  - Enables stepwise problem breakdown, branch reasoning, and iterative refinement.
  - Each "thought" can question or revise previous steps, branch, or add more steps even after initial solution.
  - Tracks:
    - `thought` (step content)
    - `thought_number`, `total_thoughts`
    - `is_revision`, `revises_thought`
    - `branch_from_thought`, `branch_id`
    - `next_thought_needed`, `needs_more_thoughts`

##### **Key Parameters**
| Parameter           | Type     | Description                                 |
|---------------------|----------|---------------------------------------------|
| `thought`           | string   | The current thinking step                   |
| `nextThoughtNeeded` | boolean  | Is another thought needed?                  |
| `thoughtNumber`     | integer  | Current step number                         |
| `totalThoughts`     | integer  | Estimated total steps (can be updated)      |
| `isRevision`        | boolean  | Is this a revision of earlier step?         |
| `revisesThought`    | integer  | If revision, which step is being reconsidered|
| `branchFromThought` | integer  | Branching from which step                   |
| `branchId`          | string   | Identifier for the current branch           |
| `needsMoreThoughts` | boolean  | More thoughts needed after initial solution |

##### **Usage Example**
- **Breaking down a research question:**
  - Start with a high-level plan (estimate `total_thoughts`)
  - Refine approach as deeper insight is gained
  - Branch when alternate solutions are identified
  - Mark and document revisions for traceability
- **Typical usage prompt:**
  > "Break down the process of building a reproducible data pipeline for legacy datasets into steps. Use Sequential Thinking and document any revisions or uncertainties encountered along the way."

##### **Best Practices**
- Start with an estimate, but be flexible to revise as complexity emerges.
- Use revision and branching explicitly; do not force strictly linear progressions.
- Only set `next_thought_needed` to `false` when a complete, validated solution is reached.
- Document all branch points and revisions for auditability.

##### Usage

The Sequential Thinking tool is designed for:

-   Breaking down complex problems into steps
-   Planning and design with room for revision
-   Analysis that might need course correction
-   Problems where the full scope might not be clear initially
-   Tasks that need to maintain context over multiple steps
-   Situations where irrelevant information needs to be filtered out


---

### context7

**Source/Docs:**

* [Official Site](https://context7.com/)
* [MCP Server UI](https://glama.ai/mcp/servers/@upstash/context7-mcp)
* [GitHub](https://github.com/upstash/context7)

#### Overview

Context7 is an MCP server that fetches up-to-date, version-specific documentation and code examples for programming libraries, placing them directly into LLM (Large Language Model) prompts in real-time. Its primary goal is to avoid “hallucinated” or outdated responses when using generative AI for coding or documentation—making it essential for developer productivity and reliability.

No special environment variables are required for default usage.

A Model Context Protocol server that fetches up-to-date, version-specific documentation and code examples from libraries directly into LLM prompts, helping developers get accurate answers without outdated or hallucinated information.

Context7 MCP pulls up-to-date, version-specific documentation and code examples straight from the source — and places them directly into your prompt.

Add `use context7` to your prompt in Cursor:

Create a basic Next.js project with app router. use context7

Create a script to delete the rows where the city is "" given PostgreSQL credentials. use context7

Context7 fetches up-to-date code examples and documentation right into your LLM's context.

-   1️⃣ Write your prompt naturally
-   2️⃣ Tell the LLM to `use context7`
-   3️⃣ Get working code answers

No tab-switching, no hallucinated APIs that don't exist, no outdated code generations.

**Core use cases:**

* Retrieve accurate, current API docs, usage, and examples for software libraries (e.g., Python, JS, SQL).
* Insert these directly into AI assistant prompts to enhance accuracy and trustworthiness.
* Reduce context-switching by avoiding separate browser/API lookups.

### **Installation & Configuration**

Add to `mcp_config.json` as:

```json
{
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp@latest"]
  }
}
```

**Example activation in a prompt:**
Simply instruct the LLM (in Cursor, Claude, etc.) to “use context7,” e.g.

> “Create a script to delete the rows where the city is '' given PostgreSQL credentials. Use context7.”

#### **Available Tools & Methods**

-   `resolve-library-id`: Resolves a general library name into a Context7-compatible library ID. Resolves a package/product name to a Context7-compatible library ID and returns a list of matching libraries. You MUST call this function before 'get-library-docs' to obtain a valid Context7-compatible library ID. Selection Process: 1. Analyze the query to understand what library/package the user is looking for 2. Return the most relevant match based on: - Name similarity to the query (exact matches prioritized) - Description relevance to the query's intent - Documentation coverage (prioritize libraries with higher Code Snippet counts) - Trust score (consider libraries with scores of 7-10 more authoritative) Response Format: - Return the selected library ID in a clearly marked section - Provide a brief explanation for why this library was chosen - If multiple good matches exist, acknowledge this but proceed with the most relevant one - If no good matches exist, clearly state this and suggest query refinements For ambiguous queries, request clarification before proceeding with a best-guess match.
    -   `libraryName` (required)
-   `get-library-docs`: Fetches up-to-date documentation for a library. You must call 'resolve-library-id' first to obtain the exact Context7-compatible library ID required to use this tool.
    -   `context7CompatibleLibraryID` (required)
    -   `topic` (optional): Focus the docs on a specific topic (e.g., "routing", "hooks")
    -   `tokens` (optional, default 10000): Max number of tokens to return. Values less than the configured `DEFAULT_MINIMUM_TOKENS` value or the default value of 10000 are automatically increased to that value.

##### **resolve-library-id**

* Resolves a general library name to a Context7-compatible library ID.
* **Parameters:**

  * `libraryName` (required): Name of library or package to search for.
* **Usage:**

  1. Analyzes the query to identify target library.
  2. Returns the best match and explanation.
  3. For ambiguous queries, requests clarification.

##### **get-library-docs**

* Fetches the latest, version-specific documentation for a given library ID.
* **Parameters:**

  * `context7CompatibleLibraryID` (required): Obtained from `resolve-library-id`.
  * `topic` (optional): E.g., "routing", "hooks".
  * `tokens` (optional, default 10000): Maximum tokens to return (automatically set higher if too low).

#### **Usage Example**

**Step-by-step LLM workflow:**

1. User prompt: “Show me how to implement JWT authentication with Express. Use context7.”
2. MCP server resolves `express` library, fetches latest documentation on JWT authentication.
3. LLM’s answer is grounded in the actual up-to-date Express docs, with code snippets.

#### **Best Practices & Project Guidance**

* Always call `resolve-library-id` before `get-library-docs` for optimal accuracy.
* For broad or ambiguous queries (e.g., “show me charting libraries”), clarify which library is most relevant.
* Prefer higher-trust and better-documented packages (Context7 returns trust scores).
* Use the `topic` parameter to avoid retrieving irrelevant portions of the documentation.

#### **Official Documentation and Links**

* [Context7 Home](https://context7.com/)
* [Context7 GitHub](https://github.com/upstash/context7)
* [Cursor “use context7” Examples](https://context7.com/docs/examples)

---

### Brave Search

**Source/Docs:**

* [Glama.ai MCP UI](https://glama.ai/mcp/servers/@w-jeon/mcp-brave-search)
* [GitHub](https://github.com/w-jeon/mcp-brave-search)


#### **Overview**

This MCP server integrates the [Brave Search API](https://search.brave.com/) into Windsurf, enabling both broad web search and local business search via natural language. It provides advanced filtering, pagination, and “smart fallback” (switches to web search when local search yields no results).

**Core use cases:**

* Researching topics, retrieving recent news, and exploring web content directly from the IDE.
* Finding local businesses, restaurants, and services with detailed metadata (location, hours, contact, ratings).
* Automated or LLM-driven workflows requiring up-to-date web data for context enrichment.

#### Features

-   **Web Search**: General queries, news, articles, with pagination and freshness controls
-   **Local Search**: Find businesses, restaurants, and services with detailed information
-   **Flexible Filtering**: Control result types, safety levels, and content freshness
-   **Smart Fallbacks**: Local search automatically falls back to web when no results are found

#### **Installation & Configuration**

Configured in `mcp_config.json`:

```json
{
  "brave-search": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-brave-search"
    ],
    "env": {
      "BRAVE_API_KEY": "[REDACTED]"
    }
  }
}
```

* **API key required:** Must be supplied as `BRAVE_API_KEY` in the environment.


#### **Available Tools & Methods**

- **brave_web_search** -- Performs a web search using the Brave Search API, ideal for general queries, news, articles, and online content. Use this for broad information gathering, recent events, or when you need diverse web sources. Supports pagination, content filtering, and freshness controls. Maximum 20 results per request, with offset for pagination.
  - Execute web searches with pagination and filtering
  - Inputs:
    - `query` (string): Search terms
    - `count` (number, optional): Results per page (max 20)
    - `offset` (number, optional): Pagination offset (max 9)

- **brave_local_search** -- Searches for local businesses and places using Brave's Local Search API. Best for queries related to physical locations, businesses, restaurants, services, etc. Returns detailed information including: - Business names and addresses - Ratings and review counts - Phone numbers and opening hours Use this when the query implies 'near me' or mentions specific locations. Automatically falls back to web search if no local results are found.
  - Search for local businesses and services
  - Inputs:
    - `query` (string): Local search terms
    - `count` (number, optional): Number of results (max 20)
  - Automatically falls back to web search if no local results found

##### Tools Summary Table

| Tool Name                | Description                                                               |
| ------------------------ | ------------------------------------------------------------------------- |
| **brave\_web\_search**   | Performs a Brave web search for general queries, news, articles, etc.     |
| **brave\_local\_search** | Searches for local businesses and places, returns detailed business info. |


**Web search supports:**

* Pagination (up to 20 results per call, `offset` for paging)
* Content filtering and freshness controls
* Filtering by result type and safety level

**Local search returns:**

* Names, addresses, ratings, reviews, phone numbers, opening hours, etc.
* If no local results, automatically falls back to web search.

#### **Usage Examples**

* **Web search:**
  Prompt: “Find the latest research on NTv2 grid transformation accuracy.”
  → Calls `brave_web_search` with query `"NTv2 grid transformation accuracy"`.
* **Local business search:**
  Prompt: “Find coffee shops open near me with Wi-Fi.”
  → Calls `brave_local_search`, returns detailed business results.

#### **Best Practices & Project Guidance**

* Use `count` and `offset` to control pagination for larger queries.
* Specify safety level or freshness if topic relevance or timeliness is critical.
* For best LLM context enrichment, summarize or filter results as needed before inserting into workflow.

#### **Official Documentation and Links**

* [Brave Search MCP Server (GitHub)](https://github.com/w-jeon/mcp-brave-search)
* [Online Tool Documentation (Glama.ai)](https://glama.ai/mcp/servers/@w-jeon/mcp-brave-search)
* [Brave Search API Reference](https://search.brave.com/)

---

### Knowledge Graph Memory Server

**Source/Docs:**
- [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- [Glama.ai MCP Server UI](https://glama.ai/mcp/servers/@modelcontextprotocol/knowledge-graph-memory-server)

#### **Overview**

The Memory MCP server provides a persistent, local knowledge graph for long-term memory and relationship modeling within your LLM/AI workflows. Its entity-relationship model allows Claude or other agents to remember facts, users, events, and project-specific information across sessions.

**Core use cases:**
- Track project-specific entities (users, organizations, datasets, tasks) and their attributes or relationships.
- Store atomic observations/facts about each entity (e.g., “Dataset X has CRS EPSG:4326”).
- Relate entities (e.g., “Person A works at Organization B”).
- Provide project context, history, and dynamic state to LLM-driven workflows.


#### **Installation & Configuration**

Example config in `mcp_config.json`:
```json
{
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
}
```
- No required environment variables.


#### Core Concepts

##### Entities
Entities are the primary nodes in the knowledge graph. Each entity has:
- A unique name (identifier)
- An entity type (e.g., "person", "organization", "event")
- A list of observations

Example:
```json
{
  "name": "John_Smith",
  "entityType": "person",
  "observations": ["Speaks fluent Spanish"]
}
```

##### Relations
Relations define directed connections between entities. They are always stored in active voice and describe how entities interact or relate to each other.

Example:
```json
{
  "from": "John_Smith",
  "to": "Anthropic",
  "relationType": "works_at"
}
```
##### Observations
Observations are discrete pieces of information about an entity. They are:

- Stored as strings
- Attached to specific entities
- Can be added or removed independently
- Should be atomic (one fact per observation)

Example:
```json
{
  "entityName": "John_Smith",
  "observations": [
    "Speaks fluent Spanish",
    "Graduated in 2019",
    "Prefers morning meetings"
  ]
}
```

#### **Available Tools & Methods**

- **create_entities**
  - Create multiple new entities in the knowledge graph
  - Input: `entities` (array of objects)
    - Each object contains:
      - `name` (string): Entity identifier
      - `entityType` (string): Type classification
      - `observations` (string[]): Associated observations
  - Ignores entities with existing names

- **create_relations**
  - Create multiple new relations between entities
  - Input: `relations` (array of objects)
    - Each object contains:
      - `from` (string): Source entity name
      - `to` (string): Target entity name
      - `relationType` (string): Relationship type in active voice
  - Skips duplicate relations

- **add_observations**
  - Add new observations to existing entities
  - Input: `observations` (array of objects)
    - Each object contains:
      - `entityName` (string): Target entity
      - `contents` (string[]): New observations to add
  - Returns added observations per entity
  - Fails if entity doesn't exist

- **delete_entities**
  - Remove entities and their relations
  - Input: `entityNames` (string[])
  - Cascading deletion of associated relations
  - Silent operation if entity doesn't exist

- **delete_observations**
  - Remove specific observations from entities
  - Input: `deletions` (array of objects)
    - Each object contains:
      - `entityName` (string): Target entity
      - `observations` (string[]): Observations to remove
  - Silent operation if observation doesn't exist

- **delete_relations**
  - Remove specific relations from the graph
  - Input: `relations` (array of objects)
    - Each object contains:
      - `from` (string): Source entity name
      - `to` (string): Target entity name
      - `relationType` (string): Relationship type
  - Silent operation if relation doesn't exist

- **read_graph**
  - Read the entire knowledge graph
  - No input required
  - Returns complete graph structure with all entities and relations

- **search_nodes**
  - Search for nodes based on query
  - Input: `query` (string)
  - Searches across:
    - Entity names
    - Entity types
    - Observation content
  - Returns matching entities and their relations

- **open_nodes**
  - Retrieve specific nodes by name
  - Input: `names` (string[])
  - Returns:
    - Requested entities
    - Relations between requested entities
  - Silently skips non-existent nodes

##### Tools Summary Table

| Tool Name           | Description                                                                        |
|---------------------|------------------------------------------------------------------------------------|
| **create_entities** | Create new entities (nodes) in the graph with type and observations.               |
| **create_relations**| Add directed relations between entities.                                           |
| **add_observations**| Add facts/observations to existing entities.                                       |
| **delete_entities** | Remove entities and all their relations.                                           |
| **delete_observations**| Remove specific observations from entities.                                     |
| **delete_relations**| Remove specific relations from the graph.                                          |
| **read_graph**      | Return the complete entity/relation graph structure.                               |
| **search_nodes**    | Search for nodes by name/type/observation content.                                 |
| **open_nodes**      | Retrieve nodes (and relations) by specific name(s).                                |

##### **Entity Model Example**

```json
{
  "name": "John_Smith",
  "entityType": "person",
  "observations": ["Speaks fluent Spanish", "Graduated in 2019"]
}
```

##### **Relation Model Example**

```json
{
  "from": "John_Smith",
  "to": "Arizona_State_University",
  "relationType": "graduated_from"
}
```

#### **Usage Examples**

- **Track database migration tasks:**
  Create an entity for each dataset, attach observations about conversion state, and relate them to project milestones.
- **Record user/project context:**
  Add user entities, link them to ongoing tasks, and store observations for workflow automation or status reporting.

#### **Best Practices & Project Guidance**

- Store atomic (single fact) observations for clarity and searchability.
- Use active voice for relations (e.g., “works_at”, “depends_on”).
- Clean up (delete) unused entities/relations to avoid clutter and drift.
- Leverage `read_graph` for exporting or visualizing current project memory.

#### **Official Documentation and Links**

- [Memory MCP Server GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- [Online Tool Documentation (Glama.ai)](https://glama.ai/mcp/servers/@modelcontextprotocol/knowledge-graph-memory-server)

---

### GitHub MCP Server


**Source/Docs:**
- [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

#### **Overview**

The GitHub MCP server provides full-featured GitHub API integration, allowing your LLM agent or workflow to manage repositories, files, issues, pull requests, code search, and more—all via natural language or tool calls.

**Core use cases:**
- Create, update, or delete files in any GitHub repo (with access).
- Manage issues, pull requests, and code reviews for open-source or private projects.
- Search repositories, code, or users directly from the IDE.
- Push batches of files, automate documentation updates, or trigger CI/CD workflows.

#### Features

- **Automatic Branch Creation**: When creating/updating files or pushing changes, branches are automatically created if they don't exist
- **Comprehensive Error Handling**: Clear error messages for common issues
- **Git History Preservation**: Operations maintain proper Git history without force pushing
- **Batch Operations**: Support for both single-file and multi-file operations
- **Advanced Search**: Support for searching code, issues/PRs, and users

#### **Installation & Configuration**

Configured as follows in `mcp_config.json`:
```json
{
  "github": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-github"
    ],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "[REDACTED]"
    }
  }
}
```
- Requires a GitHub Personal Access Token with appropriate repo and workflow scopes.
- **Redact tokens in shared or public documentation.**


#### **Available Tools & Methods**


1. `create_or_update_file`
   - Create or update a single file in a repository
   - Inputs:
     - `owner` (string): Repository owner (username or organization)
     - `repo` (string): Repository name
     - `path` (string): Path where to create/update the file
     - `content` (string): Content of the file
     - `message` (string): Commit message
     - `branch` (string): Branch to create/update the file in
     - `sha` (optional string): SHA of file being replaced (for updates)
   - Returns: File content and commit details

2. `push_files`
   - Push multiple files in a single commit
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `branch` (string): Branch to push to
     - `files` (array): Files to push, each with `path` and `content`
     - `message` (string): Commit message
   - Returns: Updated branch reference

3. `search_repositories`
   - Search for GitHub repositories
   - Inputs:
     - `query` (string): Search query
     - `page` (optional number): Page number for pagination
     - `perPage` (optional number): Results per page (max 100)
   - Returns: Repository search results

4. `create_repository`
   - Create a new GitHub repository
   - Inputs:
     - `name` (string): Repository name
     - `description` (optional string): Repository description
     - `private` (optional boolean): Whether repo should be private
     - `autoInit` (optional boolean): Initialize with README
   - Returns: Created repository details

5. `get_file_contents`
   - Get contents of a file or directory
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `path` (string): Path to file/directory
     - `branch` (optional string): Branch to get contents from
   - Returns: File/directory contents

6. `create_issue`
   - Create a new issue
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `title` (string): Issue title
     - `body` (optional string): Issue description
     - `assignees` (optional string[]): Usernames to assign
     - `labels` (optional string[]): Labels to add
     - `milestone` (optional number): Milestone number
   - Returns: Created issue details

7. `create_pull_request`
   - Create a new pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `title` (string): PR title
     - `body` (optional string): PR description
     - `head` (string): Branch containing changes
     - `base` (string): Branch to merge into
     - `draft` (optional boolean): Create as draft PR
     - `maintainer_can_modify` (optional boolean): Allow maintainer edits
   - Returns: Created pull request details

8. `fork_repository`
   - Fork a repository
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `organization` (optional string): Organization to fork to
   - Returns: Forked repository details

9. `create_branch`
   - Create a new branch
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `branch` (string): Name for new branch
     - `from_branch` (optional string): Source branch (defaults to repo default)
   - Returns: Created branch reference

10. `list_issues`
    - List and filter repository issues
    - Inputs:
      - `owner` (string): Repository owner
      - `repo` (string): Repository name
      - `state` (optional string): Filter by state ('open', 'closed', 'all')
      - `labels` (optional string[]): Filter by labels
      - `sort` (optional string): Sort by ('created', 'updated', 'comments')
      - `direction` (optional string): Sort direction ('asc', 'desc')
      - `since` (optional string): Filter by date (ISO 8601 timestamp)
      - `page` (optional number): Page number
      - `per_page` (optional number): Results per page
    - Returns: Array of issue details

11. `update_issue`
    - Update an existing issue
    - Inputs:
      - `owner` (string): Repository owner
      - `repo` (string): Repository name
      - `issue_number` (number): Issue number to update
      - `title` (optional string): New title
      - `body` (optional string): New description
      - `state` (optional string): New state ('open' or 'closed')
      - `labels` (optional string[]): New labels
      - `assignees` (optional string[]): New assignees
      - `milestone` (optional number): New milestone number
    - Returns: Updated issue details

12. `add_issue_comment`
    - Add a comment to an issue
    - Inputs:
      - `owner` (string): Repository owner
      - `repo` (string): Repository name
      - `issue_number` (number): Issue number to comment on
      - `body` (string): Comment text
    - Returns: Created comment details

13. `search_code`
    - Search for code across GitHub repositories
    - Inputs:
      - `q` (string): Search query using GitHub code search syntax
      - `sort` (optional string): Sort field ('indexed' only)
      - `order` (optional string): Sort order ('asc' or 'desc')
      - `per_page` (optional number): Results per page (max 100)
      - `page` (optional number): Page number
    - Returns: Code search results with repository context

14. `search_issues`
    - Search for issues and pull requests
    - Inputs:
      - `q` (string): Search query using GitHub issues search syntax
      - `sort` (optional string): Sort field (comments, reactions, created, etc.)
      - `order` (optional string): Sort order ('asc' or 'desc')
      - `per_page` (optional number): Results per page (max 100)
      - `page` (optional number): Page number
    - Returns: Issue and pull request search results

15. `search_users`
    - Search for GitHub users
    - Inputs:
      - `q` (string): Search query using GitHub users search syntax
      - `sort` (optional string): Sort field (followers, repositories, joined)
      - `order` (optional string): Sort order ('asc' or 'desc')
      - `per_page` (optional number): Results per page (max 100)
      - `page` (optional number): Page number
    - Returns: User search results

16. `list_commits`
   - Gets commits of a branch in a repository
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `page` (optional string): page number
     - `per_page` (optional string): number of record per page
     - `sha` (optional string): branch name
   - Returns: List of commits

17. `get_issue`
   - Gets the contents of an issue within a repository
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `issue_number` (number): Issue number to retrieve
   - Returns: Github Issue object & details

18. `get_pull_request`
   - Get details of a specific pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
   - Returns: Pull request details including diff and review status

19. `list_pull_requests`
   - List and filter repository pull requests
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `state` (optional string): Filter by state ('open', 'closed', 'all')
     - `head` (optional string): Filter by head user/org and branch
     - `base` (optional string): Filter by base branch
     - `sort` (optional string): Sort by ('created', 'updated', 'popularity', 'long-running')
     - `direction` (optional string): Sort direction ('asc', 'desc')
     - `per_page` (optional number): Results per page (max 100)
     - `page` (optional number): Page number
   - Returns: Array of pull request details

20. `create_pull_request_review`
   - Create a review on a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
     - `body` (string): Review comment text
     - `event` (string): Review action ('APPROVE', 'REQUEST_CHANGES', 'COMMENT')
     - `commit_id` (optional string): SHA of commit to review
     - `comments` (optional array): Line-specific comments, each with:
       - `path` (string): File path
       - `position` (number): Line position in diff
       - `body` (string): Comment text
   - Returns: Created review details

21. `merge_pull_request`
   - Merge a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
     - `commit_title` (optional string): Title for merge commit
     - `commit_message` (optional string): Extra detail for merge commit
     - `merge_method` (optional string): Merge method ('merge', 'squash', 'rebase')
   - Returns: Merge result details

22. `get_pull_request_files`
   - Get the list of files changed in a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
   - Returns: Array of changed files with patch and status details

23. `get_pull_request_status`
   - Get the combined status of all status checks for a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
   - Returns: Combined status check results and individual check details

24. `update_pull_request_branch`
   - Update a pull request branch with the latest changes from the base branch (equivalent to GitHub's "Update branch" button)
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
     - `expected_head_sha` (optional string): The expected SHA of the pull request's HEAD ref
   - Returns: Success message when branch is updated

25. `get_pull_request_comments`
   - Get the review comments on a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
   - Returns: Array of pull request review comments with details like the comment text, author, and location in the diff

26. `get_pull_request_reviews`
   - Get the reviews on a pull request
   - Inputs:
     - `owner` (string): Repository owner
     - `repo` (string): Repository name
     - `pull_number` (number): Pull request number
   - Returns: Array of pull request reviews with details like the review state (APPROVED, CHANGES_REQUESTED, etc.), reviewer, and review body


##### Tools Summary Table

| Tool Name                  | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **create_or_update_file**  | Create or update a single file in a repo (with automatic branch creation).  |
| **push_files**             | Commit and push multiple files at once.                                     |
| **search_repositories**    | Search for repositories by query.                                           |
| **create_repository**      | Create a new GitHub repository.                                             |
| **get_file_contents**      | Retrieve file or directory content.                                         |
| **create_issue**           | Open a new issue in a repository.                                           |
| **create_pull_request**    | Create a new PR between branches.                                           |
| **fork_repository**        | Fork a repository to a user/org.                                            |
| **create_branch**          | Create a new branch from an existing branch.                                |
| **list_issues**            | List/filter issues by state, label, etc.                                    |
| **update_issue**           | Edit an existing issue.                                                     |
| **add_issue_comment**      | Comment on an issue.                                                        |
| **search_code**            | Search for code snippets across repos.                                      |
| **search_issues**          | Search for issues and PRs by query.                                         |
| **search_users**           | Find GitHub users.                                                          |
| **list_commits**           | Get branch commits.                                                         |
| **get_issue**, **get_pull_request**, **list_pull_requests**, etc. | Full-featured repo management.   |
| **merge_pull_request**, **get_pull_request_files**, etc.         | PR operations and review tools.    |

#### **Usage Examples**

- **Commit a documentation update:**
  “Push updated `README.md` and `CONTRIBUTING.md` to the `main` branch of `TeotihuacanProject/kb`. Add a summary in the commit message.”
- **Open a new feature issue:**
  “Create an issue in `user/repo` titled 'Implement data migration for legacy Access DB' with description and tag it as `migration`.”
- **Search for RAG pipelines:**
  “Search for public repos mentioning 'RAG pipeline' and return their descriptions.”

#### **Best Practices & Project Guidance**

- Use `push_files` for atomic multi-file commits—improves auditability and reduces commit spam.
- Leverage advanced search syntax (by label, state, assignee) for efficient workflow automation.
- When using automated workflows, always specify branches and commit messages clearly.

#### **Official Documentation and Links**

- [GitHub MCP Server GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [GitHub API Reference](https://docs.github.com/en/rest)


---

### Fetcher MCP Server

**Source/Docs:**
- [GitHub](https://github.com/jae-jae/fetcher-mcp)

#### **Overview**

Fetcher is an MCP server for retrieving and extracting content from web pages—including those that require JavaScript execution—using the Playwright headless browser. It is optimized for extracting main content, ignoring ads/navigation, and can output in both Markdown and HTML formats.

**Core use cases:**
- Fetch technical docs, tutorials, or any web content directly into the LLM context.
- Process JavaScript-heavy pages that regular scrapers cannot.
- Batch fetch and process multiple web pages for research, KB construction, or QA.

#### Features

- **JavaScript Support**: Unlike traditional web scrapers, Fetcher MCP uses Playwright to execute JavaScript, making it capable of handling dynamic web content and modern web applications.
- **Intelligent Content Extraction**: Built-in Readability algorithm automatically extracts the main content from web pages, removing ads, navigation, and other non-essential elements.
- **Flexible Output Format**: Supports both HTML and Markdown output formats, making it easy to integrate with various downstream applications.
- **Parallel Processing**: The `fetch_urls` tool enables concurrent fetching of multiple URLs, significantly improving efficiency for batch operations.
- **Resource Optimization**: Automatically blocks unnecessary resources (images, stylesheets, fonts, media) to reduce bandwidth usage and improve performance.
- **Robust Error Handling**: Comprehensive error handling and logging ensure reliable operation even when dealing with problematic web pages.
- **Configurable Parameters**: Fine-grained control over timeouts, content extraction, and output formatting to suit different use cases.

#### **Installation & Configuration**

Configured in `mcp_config.json`:
```json
{
  "fetcher": {
    "command": "npx",
    "args": ["-y", "fetcher-mcp"]
  }
}
```
- No environment variables required for default operation.

#### **Available Tools & Methods**


- `fetch_url` - Retrieve web page content from a specified URL
  - Uses Playwright headless browser to parse JavaScript
  - Supports intelligent extraction of main content and conversion to Markdown
  - Supports the following parameters:
    - `url`: The URL of the web page to fetch (required parameter)
    - `timeout`: Page loading timeout in milliseconds, default is 30000 (30 seconds)
    - `waitUntil`: Specifies when navigation is considered complete, options: 'load', 'domcontentloaded', 'networkidle', 'commit', default is 'load'
    - `extractContent`: Whether to intelligently extract the main content, default is true
    - `maxLength`: Maximum length of returned content (in characters), default is no limit
    - `returnHtml`: Whether to return HTML content instead of Markdown, default is false
    - `waitForNavigation`: Whether to wait for additional navigation after initial page load (useful for sites with anti-bot verification), default is false
    - `navigationTimeout`: Maximum time to wait for additional navigation in milliseconds, default is 10000 (10 seconds)
    - `disableMedia`: Whether to disable media resources (images, stylesheets, fonts, media), default is true
    - `debug`: Whether to enable debug mode (showing browser window), overrides the --debug command line flag if specified
- `fetch_urls` - Batch retrieve web page content from multiple URLs in parallel
  - Uses multi-tab parallel fetching for improved performance
  - Returns combined results with clear separation between webpages
  - Supports the following parameters:
    - `urls`: Array of URLs to fetch (required parameter)
    - Other parameters are the same as `fetch_url`

##### Tools Summary Table

| Tool Name      | Description                                                                           |
|----------------|---------------------------------------------------------------------------------------|
| **fetch_url**  | Retrieve main content from a single URL, with support for JS and Markdown extraction. |
| **fetch_urls** | Batch fetch multiple URLs concurrently (parallel processing).                         |

**Parameters for both tools include:**
- `url` or `urls`: Target URL(s).
- `timeout`: Page load timeout (default 30s).
- `extractContent`: Extract main content only (default true).
- `maxLength`: Limit on output length.
- `returnHtml`: Output in HTML instead of Markdown.
- `disableMedia`: Block images, stylesheets, media (default true).
- `waitForNavigation`: For additional navigation/anti-bot (default false).

#### **Usage Examples**

- **Single page fetch:**
  “Fetch the Markdown main content of https://docs.sqlalchemy.org/.”
- **Batch fetch:**
  “Download and extract docs from all major tools in the Teotihuacan pipeline: SQLAlchemy, Pandas, QGIS user manual.”

#### **Best Practices & Project Guidance**

- Use `disableMedia` to save bandwidth unless image content is critical.
- When processing dynamic or login-protected sites, additional Playwright configuration may be required.
- Limit `maxLength` or use batch fetching for very large documentation sets.

#### **Official Documentation and Links**

- [Fetcher MCP Server GitHub](https://github.com/jae-jae/fetcher-mcp)

---

### Excel MCP Server

**Source/Docs:**
- [GitHub](https://github.com/negokaz/excel-mcp-server)

#### **Overview**

The Excel MCP server enables LLM-driven workflows to read, write, and manipulate Microsoft Excel files, including support for formulas, sheet management, and table creation. On Windows, it also supports live editing and screen capture for enhanced documentation or QA.

**Core use cases:**
- Programmatic spreadsheet manipulation (e.g., updating project data logs, archiving tables).
- Automated QA or data extraction from Excel-based legacy datasets.
- Creating tables, copying sheets, and writing formulas from AI/LLM scripts.


#### Features

- Read/Write text values
- Read/Write formulas
- Create new sheets

**🪟Windows only:**
- Live editing
- Capture screen image from a sheet


#### **Installation & Configuration**

Configured in `mcp_config.json`:
```json
{
  "excel": {
    "command": "npx",
    "args": ["-y", "@negokaz/excel-mcp-server"],
    "env": {
      "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
    }
  }
}
```
- Paging limit can be set for large sheets (default: 4000 cells per operation).
- Windows-only features for live editing and screen capture.

#### **Available Tools & Methods**


`excel_describe_sheets` -- List all sheet information of specified Excel file.
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file

`excel_read_sheet` -- Read values from Excel sheet with pagination.
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file
- `sheetName`
    - Sheet name in the Excel file
- `range`
    - Range of cells to read in the Excel sheet (e.g., "A1:C10"). [default: first paging range]
- `knownPagingRanges`
    - List of already read paging ranges
- `showFormula`
    - Show formula instead of value

`excel_screen_capture` -- **[Windows only]** Take a screenshot of the Excel sheet with pagination.
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file
- `sheetName`
    - Sheet name in the Excel file
- `range`
    - Range of cells to read in the Excel sheet (e.g., "A1:C10"). [default: first paging range]
- `knownPagingRanges`
    - List of already read paging ranges

`excel_write_to_sheet` -- Write values to the Excel sheet.
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file
- `sheetName`
    - Sheet name in the Excel file
- `newSheet`
    - Create a new sheet if true, otherwise write to the existing sheet
- `range`
    - Range of cells to read in the Excel sheet (e.g., "A1:C10").
- `values`
    - Values to write to the Excel sheet. If the value is a formula, it should start with "="

`excel_create_table` -- Create a table in the Excel sheet
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file
- `sheetName`
    - Sheet name where the table is created
- `range`
    - Range to be a table (e.g., "A1:C10")
- `tableName`
    - Table name to be created

`excel_copy_sheet` -- Copy existing sheet to a new sheet
**Arguments:**
- `fileAbsolutePath`
    - Absolute path to the Excel file
- `srcSheetName`
    - Source sheet name in the Excel file
- `dstSheetName`
    - Sheet name to be copied

##### `EXCEL_MCP_PAGING_CELLS_LIMIT`

The maximum number of cells to read in a single paging operation.
[default: 4000]

##### Tools Summary Table

| Tool Name                | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| **excel_describe_sheets**| List all sheets in a workbook.                                           |
| **excel_read_sheet**     | Read values/formulas from a specified range or sheet.                    |
| **excel_screen_capture** | (Windows only) Capture screenshot of a specified sheet/range.            |
| **excel_write_to_sheet** | Write values (including formulas) to a specified range/sheet.            |
| **excel_create_table**   | Create a table in the given sheet/range.                                 |
| **excel_copy_sheet**     | Copy an existing sheet to a new name/location.                           |

#### **Usage Examples**

- **Read a table:**
  “Extract all data from `Metadata` sheet in `archive2020.xlsx`, including formulas.”
- **Write a summary table:**
  “Create a new sheet ‘ProjectSummary’ and populate columns A1:D10 with results.”

#### **Best Practices & Project Guidance**

- Use paging for large sheets—extract in logical chunks to avoid overload.
- Always verify cell ranges and confirm operations, especially with `write_to_sheet`.
- Leverage `excel_screen_capture` for QA, documentation, or review processes on Windows.

#### **Official Documentation and Links**

- [Excel MCP Server GitHub](https://github.com/negokaz/excel-mcp-server)

---


### MCP Sequential Thinking Tools

**Source/Docs:**
- [GitHub](https://github.com/spences10/mcp-sequentialthinking-tools)

#### **Overview**

MCP Sequential Thinking Tools is an advanced adaptation of the core Sequential Thinking server. It not only supports reflective, stepwise problem-solving but also provides *intelligent recommendations for which MCP tools to use at each reasoning stage*. For each “thought,” it suggests relevant tools with confidence scores and rationale, optimizing tool use for the problem context.

**Core use cases:**
- Dynamic multi-stage workflows where each step may require a different tool (e.g., first search docs, then manipulate files, then commit to GitHub).
- Situations where LLMs or agents need both problem decomposition and actionable next steps with tool guidance.
- Project environments emphasizing reproducibility, modular thinking, and context-aware automation.


#### Features

- 🤔 Dynamic and reflective problem-solving through sequential
  thoughts
- 🔄 Flexible thinking process that adapts and evolves
- 🌳 Support for branching and revision of thoughts
- 🛠️ Intelligent tool recommendations for each step
- 📊 Confidence scoring for tool suggestions
- 🔍 Detailed rationale for tool recommendations
- 📝 Step tracking with expected outcomes
- 🔄 Progress monitoring with previous and remaining steps
- 🎯 Alternative tool suggestions for each step

##### How It Works

This server analyses each step of your thought process and recommends appropriate MCP tools to help accomplish the task. Each recommendation includes:
- A confidence score (0-1) indicating how well the tool matches the   current need
- A clear rationale explaining why the tool would be helpful
- A priority level to suggest tool execution order
- Alternative tools that could also be used

The server works with any MCP tools available in your environment. It provides recommendations based on the current step's requirements, but the actual tool execution is handled by the consumer (like Claude).

#### **Installation & Configuration**

Config snippet for `mcp_config.json`:
```json
{
  "mcp-sequentialthinking-tools": {
    "command": "npx",
    "args": ["-y", "mcp-sequentialthinking-tools"]
  }
}
```

#### **Available Tools & Methods**


`sequentialthinking_tools` -- A tool for dynamic and reflective problem-solving through thoughts,
with intelligent tool recommendations.

**Parameters:**
- `thought` (string, required): Your current thinking step
- `next_thought_needed` (boolean, required): Whether another thought
  step is needed
- `thought_number` (integer, required): Current thought number
- `total_thoughts` (integer, required): Estimated total thoughts
  needed
- `is_revision` (boolean, optional): Whether this revises previous
  thinking
- `revises_thought` (integer, optional): Which thought is being
  reconsidered
- `branch_from_thought` (integer, optional): Branching point thought
  number
- `branch_id` (string, optional): Branch identifier
- `needs_more_thoughts` (boolean, optional): If more thoughts are
  needed
- `current_step` (object, optional): Current step recommendation with:
  - `step_description`: What needs to be done
  - `recommended_tools`: Array of tool recommendations with confidence
    scores
  - `expected_outcome`: What to expect from this step
  - `next_step_conditions`: Conditions for next step
- `previous_steps` (array, optional): Steps already recommended
- `remaining_steps` (array, optional): High-level descriptions of
  upcoming steps

##### Tools Summary Table

| Tool Name                    | Description                                                    |
|------------------------------|----------------------------------------------------------------|
| **sequentialthinking_tools** | Orchestrates sequential thinking, branching, and tool recommendation. |
| **current_step** (object)    | For each thought, details step description, recommended tools (with confidence), expected outcomes, and next step conditions. |

##### **Key Parameters (for `sequentialthinking_tools`)**

- `thought` (string): The current thinking step.
- `next_thought_needed` (boolean): Whether another step is needed.
- `thought_number` (integer): Index of the current thought.
- `total_thoughts` (integer): Estimate of total required steps.
- `is_revision` (boolean): If revising previous reasoning.
- `revises_thought` (integer): Which prior thought is revised.
- `branch_from_thought` (integer): If branching, which thought is the root.
- `branch_id` (string): Identifier for this branch.
- `needs_more_thoughts` (boolean): If more steps are required.
- `current_step` (object): Describes the step, recommended tools, rationale, etc.
- `previous_steps`, `remaining_steps`: Track completed and future stages.

##### **Tool Recommendation Structure Example**
```json
"current_step": {
  "step_description": "Gather documentation for PostGIS vector transformation.",
  "expected_outcome": "LLM has exact usage for PostGIS ST_Transform.",
  "recommended_tools": [
    {
      "tool_name": "context7",
      "confidence": 0.95,
      "rationale": "Fetches up-to-date code samples and docs.",
      "priority": 1
    },
    {
      "tool_name": "brave-search",
      "confidence": 0.7,
      "rationale": "Web search for blog posts or bug reports.",
      "priority": 2
    }
  ],
  "next_step_conditions": [
    "Verify retrieved documentation matches current PostGIS version.",
    "Identify known pitfalls or version discrepancies."
  ]
}
```

#### **Usage Examples**

- **LLM workflow orchestration:**
  “Step 1: Research API. Step 2: Write integration script. Step 3: Commit to repo.”
  The server recommends `context7` for step 1, `filesystem` for step 2, and `github` for step 3—each with rationale and confidence score.
- **Dynamic project pipelines:**
  As project context changes, the recommended toolchain adapts to the best available resources.

Here's an example of how the server guides tool usage:

```json
{
	"thought": "Initial research step to understand what universal reactivity means in Svelte 5",
	"current_step": {
		"step_description": "Gather initial information about Svelte 5's universal reactivity",
		"expected_outcome": "Clear understanding of universal reactivity concept",
		"recommended_tools": [
			{
				"tool_name": "search_docs",
				"confidence": 0.9,
				"rationale": "Search Svelte documentation for official information",
				"priority": 1
			},
			{
				"tool_name": "tavily_search",
				"confidence": 0.8,
				"rationale": "Get additional context from reliable sources",
				"priority": 2
			}
		],
		"next_step_conditions": [
			"Verify information accuracy",
			"Look for implementation details"
		]
	},
	"thought_number": 1,
	"total_thoughts": 5,
	"next_thought_needed": true
}
```

The server tracks your progress and supports:

- Creating branches to explore different approaches
- Revising previous thoughts with new information
- Maintaining context across multiple steps
- Suggesting next steps based on current findings

```json
{
	"mcpServers": {
		"mcp-sequentialthinking-tools": {
			"command": "npx",
			"args": ["-y", "mcp-sequentialthinking-tools"]
		}
	}
}
```

#### **Best Practices & Project Guidance**

- Review tool recommendations and confidence scores; override if project-specific needs dictate.
- Track all revisions and branches to maintain auditability.
- Use the `remaining_steps` array to pre-plan or visualize pipeline stages.

#### **Official Documentation and Links**

- [GitHub – mcp-sequentialthinking-tools](https://github.com/spences10/mcp-sequentialthinking-tools)

---

### Code Reasoning MCP Server

**Source/Docs:**
- [GitHub](https://github.com/mikeysrecipes/code-reasoning)
- [Glama.ai Server](https://glama.ai/mcp/servers/@mettamatt/code-reasoning)

#### **Overview**

The Code Reasoning MCP server specializes in stepwise, hypothesis-driven, and branch-capable code problem solving. It is tuned for LLM-based agents solving complex programming tasks, debugging, or system design. Its “hybrid design” prompt outperforms other prompt architectures in code reasoning tasks and includes a rigorous, built-in prompt evaluation framework.

**Core use cases:**
- Multi-stage code generation, refactoring, and debugging workflows.
- Systematic exploration of alternate coding solutions via branching.
- Parameterized, testable prompt engineering for code-related tasks.

#### Key Features

-   **Programming Focus**: Optimized for coding tasks and problem-solving
-   **Structured Thinking**: Break down complex problems into manageable steps
-   **Thought Branching**: Explore multiple solution paths in parallel
-   **Thought Revision**: Refine earlier reasoning as understanding improves
-   **Safety Limits**: Automatically stops after 20 thought steps to prevent loops
-   **Ready-to-Use Prompts**: Pre-defined templates for common development tasks

#### Documentation

Detailed documentation available in the docs directory:

-   [Usage Examples](https://glama.ai/mcp/servers/@mettamatt/docs/examples.md): Examples of sequential thinking with the MCP server
-   [Configuration Guide](https://glama.ai/mcp/servers/@mettamatt/docs/configuration.md): All configuration options for the MCP server
-   [Prompts Guide](https://glama.ai/mcp/servers/@mettamatt/docs/prompts.md): Using and customizing prompts with the MCP server
-   [Testing Framework](https://glama.ai/mcp/servers/@mettamatt/docs/testing.md): Testing information


#### **Installation & Configuration**

Example config in `mcp_config.json`:
```json
{
  "code-reasoning": {
    "command": "npx",
    "args": ["-y", "@mettamatt/code-reasoning"]
  }
}
```

#### **Available Tools & Methods**

- `code-reasoning`
  - 🧠 A detailed tool for dynamic and reflective problem-solving through sequential thinking. This tool helps you analyze problems through a flexible thinking process that can adapt and evolve. Each thought can build on, question, or revise previous insights as understanding deepens. 📋 KEY PARAMETERS: - thought: Your current reasoning step (required) - thought_number: Current number in sequence (required) - total_thoughts: Estimated final count (required, can adjust as needed) - next_thought_needed: Set to FALSE ONLY when completely done (required) - branch_from_thought + branch_id: When exploring alternative approaches (🌿) - is_revision + revises_thought: When correcting earlier thinking (🔄) ✅ CRITICAL CHECKLIST (review every 3 thoughts): 1. Need to explore alternatives? → Use BRANCH (🌿) with branch_from_thought + branch_id 2. Need to correct earlier thinking? → Use REVISION (🔄) with is_revision + revises_thought 3. Scope changed? → Adjust total_thoughts up or down as needed 4. Only set next_thought_needed = false when you have a complete, verified solution 💡 BEST PRACTICES: - Start with an initial estimate of total_thoughts, but adjust as you go - Don't hesitate to revise earlier conclusions when new insights emerge - Use branching to explore multiple approaches to the same problem - Express uncertainty when present - Ignore information that is irrelevant to the current step - End with a clear, validated conclusion before setting next_thought_needed = false ✍️ End each thought by asking: "What am I missing or need to reconsider?"

##### Tools Summary Table

| Tool Name            | Description                                                                    |
|----------------------|--------------------------------------------------------------------------------|
| **code-reasoning**   | Central tool for iterative, branchable, and revision-aware code problem-solving. |

##### **Key Parameters**

- `thought`: The current reasoning step.
- `thought_number`: Step index.
- `total_thoughts`: Dynamic estimate of total required thoughts.
- `next_thought_needed`: False only when solution is fully validated.
- `branch_from_thought` + `branch_id`: Branch alternative approaches.
- `is_revision` + `revises_thought`: Mark and manage revisions.

##### **Prompt Engineering System**
- Built-in evaluation tests solution quality and a
dherence to prompt design.
- “Hybrid_Design” prompt delivers top performance and consistency across tasks (see documentation for detailed prompt benchmark tables and prompt source code).

The Code Reasoning MCP Server includes a prompt evaluation system that assesses Claude's ability to follow the code reasoning prompts. This system allows:

-   Testing different prompt variations against scenario problems
-   Verifying parameter format adherence
-   Scoring solution quality

Significant effort went into developing the optimal prompt for the Code Reasoning server. The current implementation uses the HYBRID\_DESIGN prompt, which emerged as the winner from our evaluation process.

We compared four different prompt designs:

| Prompt Design | Description |
| --- | --- |
| SEQUENTIAL | The original sequential thinking prompt design |
| DEFAULT | The baseline prompt previously used in the server |
| CODE\_REASONING\_0\_30 | An experimental variant focusing on code-specific reasoning |
| HYBRID\_DESIGN | A refined design incorporating the best elements of other approaches |

Our evaluation across seven diverse programming scenarios showed that HYBRID\_DESIGN outperformed other prompts:

| Scenario | HYBRID\_DESIGN | CODE\_REASONING\_0\_30 | DEFAULT | SEQUENTIAL |
| --- | --- | --- | --- | --- |
| Algorithm Selection | 87% | 82% | 88% | 82% |
| Bug Identification | 87% | 91% | 88% | 92% |
| Multi-Stage Implementation | 83% | 67% | 79% | 82% |
| System Design Analysis | 82% | 87% | 78% | 82% |
| Code Debugging Task | 92% | 87% | 92% | 92% |
| Compiler Optimization | 83% | 78% | 67% | 73% |
| Cache Strategy | 86% | 88% | 82% | 87% |
| **Average** | **86%** | **83%** | **82%** | **84%** |

The HYBRID\_DESIGN prompt marginally demonstrated both the highest average solution quality (86%) and the most consistent performance across all scenarios, with no scores below 80%. It also prodouced the most thoughts. The `src/server.ts` file has been updated to use this optimal prompt design.

Personally, I think the biggest improvement was adding this to the end of the prompt: "✍️ End each thought by asking: "What am I missing or need to reconsider?"

See [Testing Framework](https://glama.ai/mcp/servers/@mettamatt/docs/testing.md) for more details on the prompt evaluation system.


##### **Documentation Links**
- [Usage Examples](https://glama.ai/mcp/servers/@mettamatt/docs/examples.md)
- [Configuration Guide](https://glama.ai/mcp/servers/@mettamatt/docs/configuration.md)
- [Prompts Guide](https://glama.ai/mcp/servers/@mettamatt/docs/prompts.md)
- [Testing Framework](https://glama.ai/mcp/servers/@mettamatt/docs/testing.md)

#### **Usage Examples**

- **Debug complex code:**
  Prompt: “Identify why the georeferencing function throws an error on input EPSG:32614. Use stepwise reasoning and branch if alternative causes are plausible.”
- **Branch on solution hypotheses:**
  Explore two alternate approaches (e.g., different projection algorithms) in parallel, compare outcomes, then merge findings.

#### **Best Practices & Project Guidance**

- Always express uncertainty or need for further analysis at the end of each thought.
- Use branches and revisions liberally—do not force single-threaded reasoning for non-linear problems.
- Reference the testing framework for prompt optimization in new project modules.

#### **Official Documentation and Links**

- [Code Reasoning MCP GitHub](https://github.com/mikeysrecipes/code-reasoning)
- [Usage and Testing Frameworks](https://glama.ai/mcp/servers/@mettamatt/docs/testing.md)

---

### Docs Manager MCP Server

**Source/Docs:**
- [GitHub](https://github.com/alekspetrov/mcp-docs-service)
- [Glama.ai MCP UI](https://glama.ai/mcp/servers/@alekspetrov/mcp-docs-service)

#### **Overview**

Docs Manager is a full-featured markdown documentation management system built for AI-assisted curation, editing, metadata enforcement, navigation, health checking, and LLM optimization. It is engineered for projects that require high standards of documentation integrity, traceability, and query readiness.

**Core use cases:**
- Structured KB construction with YAML frontmatter.
- Line-based, diff-preview editing for versioned docs.
- Navigation, search, and health checks on all project markdown files.
- LLM-friendly documentation exports for RAG and retrieval tasks.

#### Features

-   **Read and Write Documents**: Easily read and write markdown documents with frontmatter metadata
-   **Edit Documents**: Make precise line-based edits to documents with diff previews
-   **List and Search**: Find documents by content or metadata
-   **Navigation Generation**: Create navigation structures from your documentation
-   **Health Checks**: Analyze documentation quality and identify issues like missing metadata or broken links
-   **LLM-Optimized Documentation**: Generate consolidated single-document output optimized for large language models
-   **MCP Integration**: Seamless integration with the Model Context Protocol
-   **Frontmatter Support**: Full support for YAML frontmatter in markdown documents
-   **Markdown Compatibility**: Works with standard markdown files

#### **Installation & Configuration**

Configured in `mcp_config.json`:
```json
{
  "docs-manager": {
    "command": "npx",
    "args": ["-y", "mcp-docs-service", "/Users/rcesa/ASU Dropbox/Rudolf Cesaretti/GitHubRepos/kb_setup_trial1"]
  }
}
```
- Directory argument must point to your documentation root.

#### **Available Tools & Methods**

| Tool Name           | Description                                                                |
|---------------------|----------------------------------------------------------------------------|
| **Read/Write Docs** | Read or write markdown docs, preserving frontmatter metadata.              |
| **Edit Docs**       | Line-based edits with dry-run diff previews.                               |
| **List/Search Docs**| By content, metadata, or structure.                                        |
| **Navigation Gen**  | Auto-generate navigation for KBs.                                          |
| **Health Checks**   | Analyze for missing metadata, broken links, and documentation issues.      |
| **LLM Export**      | Export optimized docs for LLM chunking or RAG workflows.                   |

#### **Usage Examples**

- **Fix missing metadata:**
  “Find all markdown docs in `/src/` missing a `project_phase` frontmatter entry.”
- **Consolidate and export:**
  “Export all finalized docs as a single file optimized for LLM chunking.”

#### **Best Practices & Project Guidance**

- Enforce structured YAML frontmatter for all docs—essential for downstream LLM pipelines.
- Use health check tools regularly to maintain documentation quality.
- Prefer navigation auto-generation to maintain cross-link consistency.

#### **Official Documentation and Links**

- [Docs Manager GitHub](https://github.com/alekspetrov/mcp-docs-service)

---

### Desktop Commander MCP Server

**Source/Docs:**
- [Desktop Commander Website](https://desktopcommander.app/)
- [GitHub](https://github.com/wonderwhy-er/desktop-commander)
- [Glama.ai MCP UI](https://glama.ai/mcp/servers/@wonderwhy-er/desktop-commander)

#### **Overview**

Work with code and text, run processes, and automate tasks, going far beyond other AI editors - without API token costs. All of your AI development tools in one place. Desktop Commander puts all dev tools in one chat. Execute long-running terminal commands on your computer and manage processes through Model Context Protocol (MCP). Built on top of MCP Filesystem Server to provide additional search and replace file editing capabilities.

#### Features

- Execute terminal commands with output streaming
- Command timeout and background execution support
- Process management (list and kill processes)
- Session management for long-running commands
- Server configuration management:
  - Get/set configuration values
  - Update multiple settings at once
  - Dynamic configuration changes without server restart
- Full filesystem operations:
  - Read/write files
  - Create/list directories
  - Move files/directories
  - Search files
  - Get file metadata
- Code editing capabilities:
  - Surgical text replacements for small changes
  - Full file rewrites for major changes
  - Multiple file support
  - Pattern-based replacements
  - vscode-ripgrep based recursive code or text search in folders
- Comprehensive audit logging:
  - All tool calls are automatically logged
  - Log rotation with 10MB size limit
  - Detailed timestamps and arguments

#### **Installation & Configuration**

Configured in `mcp_config.json`:

```json
{
  "desktop-commander": {
    "command": "npx",
    "args": [
      "-y",
      "@wonderwhy-er/desktop-commander"
    ]
  }
}
````

  - **`DESKTOP_COMMANDER_ALLOWED_DIRS`**: (Optional, Recommended for Security) A colon-separated list (like a PATH variable) of directories where `execute_command` is permitted to run. If not set, commands might run in a default directory or be blocked, depending on the server's implementation.
  - **`DESKTOP_COMMANDER_SCREENSHOT_DIR`**: (Optional) Specifies the directory where screenshots taken with `capture_screen` will be saved. Defaults to a system temporary directory if not set.

#### **Available Tools & Methods**

| Category | Tool | Description |
|----------|------|-------------|
| **Configuration** | `get_config` | Get the complete server configuration as JSON (includes blockedCommands, defaultShell, allowedDirectories, fileReadLineLimit, fileWriteLineLimit, telemetryEnabled) |
| | `set_config_value` | Set a specific configuration value by key. Available settings: <br>• `blockedCommands`: Array of shell commands that cannot be executed<br>• `defaultShell`: Shell to use for commands (e.g., bash, zsh, powershell)<br>• `allowedDirectories`: Array of filesystem paths the server can access for file operations (⚠️ terminal commands can still access files outside these directories)<br>• `fileReadLineLimit`: Maximum lines to read at once (default: 1000)<br>• `fileWriteLineLimit`: Maximum lines to write at once (default: 50)<br>• `telemetryEnabled`: Enable/disable telemetry (boolean) |
| **Terminal** | `execute_command` | Execute a terminal command with configurable timeout and shell selection |
| | `read_output` | Read new output from a running terminal session |
| | `force_terminate` | Force terminate a running terminal session |
| | `list_sessions` | List all active terminal sessions |
| | `list_processes` | List all running processes with detailed information |
| | `kill_process` | Terminate a running process by PID |
| **Filesystem** | `read_file` | Read contents from local filesystem or URLs with line-based pagination (supports offset and length parameters) |
| | `read_multiple_files` | Read multiple files simultaneously |
| | `write_file` | Write file contents with options for rewrite or append mode (uses configurable line limits) |
| | `create_directory` | Create a new directory or ensure it exists |
| | `list_directory` | Get detailed listing of files and directories |
| | `move_file` | Move or rename files and directories |
| | `search_files` | Find files by name using case-insensitive substring matching |
| | `search_code` | Search for text/code patterns within file contents using ripgrep |
| | `get_file_info` | Retrieve detailed metadata about a file or directory |
| **Text Editing** | `edit_block` | Apply targeted text replacements with enhanced prompting for smaller edits (includes character-level diff feedback) |

#### **Usage Examples**

Search/Replace Block Format:
```
filepath.ext
<<<<<<< SEARCH
content to find
=======
new content
>>>>>>> REPLACE
```

Example:
```
src/main.js
<<<<<<< SEARCH
console.log("old message");
=======
console.log("new message");
>>>>>>> REPLACE
```


##### Enhanced Edit Block Features

The `edit_block` tool includes several enhancements for better reliability:

1. **Improved Prompting**: Tool descriptions now emphasize making multiple small, focused edits rather than one large change
2. **Fuzzy Search Fallback**: When exact matches fail, it performs fuzzy search and provides detailed feedback
3. **Character-level Diffs**: Shows exactly what's different using `{-removed-}{+added+}` format
4. **Multiple Occurrence Support**: Can replace multiple instances with `expected_replacements` parameter
5. **Comprehensive Logging**: All fuzzy searches are logged for analysis and debugging

When a search fails, you'll see detailed information about the closest match found, including similarity percentage, execution time, and character differences. All these details are automatically logged for later analysis using the fuzzy search log tools.

##### URL Support
- `read_file` can now fetch content from both local files and URLs
- Example: `read_file` with `isUrl: true` parameter to read from web resources
- Handles both text and image content from remote sources
- Images (local or from URLs) are displayed visually in Claude's interface, not as text
- Claude can see and analyze the actual image content
- Default 30-second timeout for URL requests

##### Fuzzy Search Log Analysis (npm scripts)

The fuzzy search logging system includes convenient npm scripts for analyzing logs outside of the MCP environment:

```bash
# View recent fuzzy search logs
npm run logs:view -- --count 20

# Analyze patterns and performance
npm run logs:analyze -- --threshold 0.8

# Export logs to CSV or JSON
npm run logs:export -- --format json --output analysis.json

# Clear all logs (with confirmation)
npm run logs:clear
```

For detailed documentation on these scripts, see [scripts/README.md](scripts/README.md).

##### Fuzzy Search Logs

Desktop Commander includes comprehensive logging for fuzzy search operations in the `edit_block` tool. When an exact match isn't found, the system performs a fuzzy search and logs detailed information for analysis.

##### What Gets Logged

Every fuzzy search operation logs:
- **Search and found text**: The text you're looking for vs. what was found
- **Similarity score**: How close the match is (0-100%)
- **Execution time**: How long the search took
- **Character differences**: Detailed diff showing exactly what's different
- **File metadata**: Extension, search/found text lengths
- **Character codes**: Specific character codes causing differences

##### Log Location

Logs are automatically saved to:
- **Windows**: `%USERPROFILE%\.claude-server-commander-logs\fuzzy-search.log`


##### Configuration Tools

You can manage server configuration using the provided tools:

```javascript
// Get the entire config
get_config({})

// Set a specific config value
set_config_value({ "key": "defaultShell", "value": "/bin/zsh" })

// Set multiple config values using separate calls
set_config_value({ "key": "defaultShell", "value": "/bin/bash" })
set_config_value({ "key": "allowedDirectories", "value": ["/Users/username/projects"] })
```

The configuration is saved to `config.json` in the server's working directory and persists between server restarts.

#### **Best Practices & Project Guidance**

1. **Create a dedicated chat for configuration changes**: Make all your config changes in one chat, then start a new chat for your actual work.

2. **Be careful with empty `allowedDirectories`**: Setting this to an empty array (`[]`) grants access to your entire filesystem for file operations.

3. **Use specific paths**: Instead of using broad paths like `/`, specify exact directories you want to access.

4. **Always verify configuration after changes**: Use `get_config({})` to confirm your changes were applied correctly.

5. **NOTE: The `allowedDirectories` setting currently only restricts filesystem operations**, not terminal commands. Terminal commands can still access files outside allowed directories. Full terminal sandboxing is on the roadmap.

#### **Official Documentation and Links**

  - [Desktop Commander Website](https://desktopcommander.app/)
  - [Desktop Commander GitHub](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/wonderwhy-er/desktop-commander)
  - [Online Tool Documentation (Glama.ai)](https://www.google.com/url?sa=E&source=gmail&q=https://glama.ai/mcp/servers/@wonderwhy-er/desktop-commander)

-----

### Postgres MCP Server

**Source/Docs:**
- [GitHub](https://github.com/crystaldba/postgres-mcp)
- [Glama.ai MCP UI](https://glama.ai/mcp/servers/@crystaldba/postgres-mcp)
- [Crystal DBA Blog](https://www.crystaldba.ai/blog/post/announcing-postgres-mcp-server-pro)

#### **Overview**

Postgres MCP Pro (distributed as postgres-mcp) is a comprehensive Model Context Protocol server for PostgreSQL database management, optimization, and performance analysis. Unlike basic database connection wrappers, it provides enterprise-grade tools for database health monitoring, automated index tuning, query optimization, and safe SQL execution suitable for both development and production environments.

**Core use cases:**
- Database performance optimization through automated index analysis and recommendations.
- Comprehensive health monitoring including buffer cache, connections, vacuum status, and replication.
- Safe SQL execution with configurable access modes (unrestricted for development, restricted for production).
- Query plan analysis and slow query identification using PostgreSQL's built-in statistics.
- Schema intelligence for context-aware SQL generation and database exploration.

#### **Features**

- **🔍 Database Health Analysis**: Comprehensive health checks on indexes, connections, buffer cache, vacuum health, sequence limits, replication lag, and constraints
- **⚡ Index Tuning**: Industrial-strength algorithms for optimal index recommendations based on workload analysis or specific queries
- **📈 Query Plan Analysis**: EXPLAIN plan validation with hypothetical index simulation using `hypopg` extension
- **🧠 Schema Intelligence**: Context-aware SQL generation based on detailed database schema understanding
- **🛡️ Safe SQL Execution**: Configurable access control with read-only mode and safe SQL parsing for production use
- **🔄 Multiple Transport Support**: Both stdio and Server-Sent Events (SSE) transports for flexible deployment
- **🐳 Container Ready**: Docker deployment with automatic hostname remapping for cross-platform compatibility

#### **Installation & Configuration**

Postgres MCP Pro supports multiple installation methods. Docker is recommended for reliability across environments.

**Docker Configuration (Recommended):**
```json
{
  "postgres": {
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "-e",
      "DATABASE_URI",
      "crystaldba/postgres-mcp",
      "--access-mode=unrestricted"
    ],
    "env": {
      "DATABASE_URI": "postgresql://username:password@localhost:5432/dbname"
    }
  }
}
```

**Python Installation Configuration:**
```json
{
  "postgres": {
    "command": "postgres-mcp",
    "args": [
      "--access-mode=unrestricted"
    ],
    "env": {
      "DATABASE_URI": "postgresql://username:password@localhost:5432/dbname"
    }
  }
}
```

**Access Modes:**
- `--access-mode=unrestricted`: Full read/write access for development environments
- `--access-mode=restricted`: Read-only with execution time limits for production environments

**Required Extensions (Optional but Recommended):**
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- Query statistics
CREATE EXTENSION IF NOT EXISTS hypopg;             -- Hypothetical indexes
```

#### **Available Tools & Methods**

- **list_schemas**: Lists all database schemas available in the PostgreSQL instance
  - Returns comprehensive schema information for database exploration

- **list_objects**: Lists database objects (tables, views, sequences, extensions) within a specified schema
  - Inputs: `schema_name` (string): Target schema to explore
  - Returns detailed object inventory with types and metadata

- **get_object_details**: Provides detailed information about specific database objects
  - Inputs: `schema_name` (string), `object_name` (string), `object_type` (optional string)
  - Returns columns, constraints, indexes, and relationships for tables/views

- **execute_sql**: Executes SQL statements with configurable safety controls
  - Inputs: `query` (string): SQL statement to execute
  - Supports read-only limitations in restricted mode
  - Includes transaction management and error handling

- **explain_query**: Generates execution plans for SQL queries with cost analysis
  - Inputs: `query` (string): SQL to analyze, `hypothetical_indexes` (optional array)
  - Returns detailed PostgreSQL query planner output and cost estimates
  - Supports "what-if" analysis with hypothetical indexes

- **get_top_queries**: Reports slowest queries based on execution statistics
  - Inputs: `limit` (optional number), `sort_by` (optional: 'mean_time' or 'total_time')
  - Requires `pg_stat_statements` extension
  - Returns query text, execution counts, and performance metrics

- **analyze_workload_indexes**: Analyzes database workload for optimal index recommendations
  - Uses industrial-strength algorithms adapted from Microsoft's Anytime Algorithm
  - Performs cost-benefit analysis balancing performance gains vs. storage costs
  - Returns prioritized index recommendations with impact estimates

- **analyze_query_indexes**: Analyzes specific SQL queries for index optimization
  - Inputs: `queries` (array of strings, max 10): SQL statements to optimize
  - Returns targeted index recommendations for provided queries
  - Includes before/after performance projections

- **analyze_db_health**: Comprehensive database health assessment
  - Available checks: `index`, `connection`, `vacuum`, `sequence`, `replication`, `buffer`, `constraint`, `all`
  - Inputs: `checks` (optional string): Specific checks or 'all' (default)
  - Returns actionable health report with issue prioritization

##### Tools Summary Table

| Tool Name                  | Description                                                                     |
|----------------------------|---------------------------------------------------------------------------------|
| **list_schemas**           | List all database schemas available in the PostgreSQL instance                  |
| **list_objects**           | List database objects within a specified schema                                 |
| **get_object_details**     | Detailed information about specific database objects (tables, views, etc.)      |
| **execute_sql**            | Execute SQL with configurable safety controls and access modes                  |
| **explain_query**          | Generate execution plans with cost analysis and hypothetical index simulation   |
| **get_top_queries**        | Identify slowest queries using pg_stat_statements data                          |
| **analyze_workload_indexes**| Analyze entire database workload for optimal index recommendations             |
| **analyze_query_indexes**  | Analyze specific queries (up to 10) for targeted index optimization            |
| **analyze_db_health**      | Comprehensive health checks across all database subsystems                      |

#### **Usage Examples**

- **Database health assessment:**
  "Check the health of my database and identify any issues that need immediate attention."
  → Executes `analyze_db_health` with comprehensive reporting.

- **Performance optimization:**
  "Analyze my database workload and suggest indexes to improve performance."
  → Uses `analyze_workload_indexes` with industrial-strength optimization algorithms.

- **Query-specific optimization:**
  "Help me optimize this query: `SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id WHERE orders.created_at > '2023-01-01'`"
  → Calls `analyze_query_indexes` with targeted recommendations.

- **Slow query identification:**
  "What are the slowest queries in my database and how can I speed them up?"
  → Combines `get_top_queries` with `explain_query` for actionable insights.

#### **Best Practices & Project Guidance**

- **Access Mode Selection**: Use `unrestricted` mode only in development environments; always use `restricted` mode for production databases.
- **Extension Installation**: Install `pg_stat_statements` and `hypopg` extensions for full functionality—they're typically available on cloud providers (AWS RDS, Azure, GCP).
- **Index Recommendations**: Review cost-benefit analysis carefully; the server uses configurable thresholds (default: 100x performance improvement justifies 10x storage increase).
- **Health Monitoring**: Regular health checks can prevent critical issues; focus on vacuum health, connection utilization, and buffer cache hit rates.
- **Docker Deployment**: Preferred method for reliability; automatic hostname remapping handles localhost connections from containers across platforms.
- **Query Analysis**: Use hypothetical index simulation before implementing recommendations; the server provides before/after performance projections.

#### **Official Documentation and Links**

- [Postgres MCP Pro GitHub](https://github.com/crystaldba/postgres-mcp)
- [Glama.ai Server Documentation](https://glama.ai/mcp/servers/@crystaldba/postgres-mcp)
- [Crystal DBA Official Site](https://www.crystaldba.ai)
- [Launch Blog Post](https://www.crystaldba.ai/blog/post/announcing-postgres-mcp-server-pro)
- [Docker Hub Image](https://hub.docker.com/r/crystaldba/postgres-mcp)

-----

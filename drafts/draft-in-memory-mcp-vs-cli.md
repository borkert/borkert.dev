# Making Agent API Calls 10x Faster with Cached Definitions

*By Chris Borkert · Draft · August 2026*

When developers give an AI coding assistant (like Cursor, Claude Code, Antigravity, or Cline) access to web APIs, the default approach is almost always the same: give the agent a bash tool and let it run `curl` or a CLI.

I built a tool called `apicat` (invoked on the command line as `apic`) to simplify how APIs are managed and called. Instead of writing shell scripts or memorizing complex curl flags, you define endpoints once in a clean YAML file (`~/.apicat` or `apicat.yaml`), and `apic` handles headers, variable interpolation, and response formatting. While `apic` works well for human developers in a terminal, having an autonomous AI agent spawn shell processes to execute it revealed three deeper problems: slow execution, wasted context tokens, and lost socket reuse.

I ran a set of benchmarks on real API queries against Fireworks AI and OpenRouter to compare three execution models:

1. **Unassisted shell execution:** The agent reads documentation or local files and constructs `curl` commands.
2. **CLI subprocess wrappers:** The agent runs a local CLI command like `apic <service.endpoint>`.
3. **In-memory MCP server:** The agent sends structured calls to a compiled Rust Model Context Protocol (MCP) server that keeps connections open in memory.

The difference in speed and token efficiency was substantial. Shell-based tool execution required 10 times more reasoning turns, used 96.5% more tokens, and ran up to 6 times slower.

---

## Two bottlenecks of agent API execution

When an agent interacts with external APIs, it faces two separate challenges:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. The Knowledge Problem: "What are the endpoints & schemas?"│
└──────────────────────────────┬──────────────────────────────┘
                               │ Declarative apicat.yaml
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. The Execution Problem: "How do bytes reach the socket?"  │
└──────────────────────────────┬──────────────────────────────┘
                               │ In-Memory Rust MCP Server
                               ▼
                    [ Upstream Web APIs ]
```

### 1. The knowledge problem
Large models do not know your project's specific infrastructure:
* What is your custom account ID or quota path?
* Does this endpoint use `Authorization: Bearer <token>` or a custom header?
* Are timestamp filters formatted as ISO-8601 strings or Unix timestamps?

Without a defined schema, the agent enters an exploratory loop: searching the web, reading thousands of tokens of documentation, guessing parameters, and fixing 400 Bad Request responses.

### 2. The execution problem
Even when the agent knows the syntax, running through a shell adds overhead:
* **Subprocess startup:** Spawning a subshell, booting a runtime like Node.js or Python, and parsing configuration files from disk on every invocation.
* **No connection reuse:** Every `curl` command is an isolated process. It performs fresh DNS resolution and a fresh TLS 1.3 handshake on every request.
* **Shell escaping hazards:** Nested JSON payloads with single and double quotes inside terminal strings frequently cause escaping errors.

---

## Real-world autonomous agent benchmark

To measure this on an actual task, I gave an agent the following prompt:

> "Perform an AI infrastructure cost and quota audit: Check Fireworks AI monthly spend and RPM limit, check OpenRouter API key daily limit, usage, and lifetime spend, and summarize quota health."

I tested the agent under two setups:
1. **Unassisted CLI mode:** The agent located endpoint definitions in the workspace, constructed CLI commands, and parsed the output.
2. **In-memory MCP mode:** The agent used a compiled Rust MCP server with pre-loaded schemas.

### Results

| Metric | Unassisted Agent (CLI & Search) | In-Memory Rust MCP | Difference |
| :--- | :---: | :---: | :--- |
| **Total wall-clock latency** | 21.0 seconds | ~2.5 seconds | 6.0x faster |
| **LLM reasoning turns** | 10 turns | 1 turn | 10x fewer turns |
| **Context token footprint** | ~18,400 tokens | ~650 tokens | 96.5% reduction |
| **Exploratory probing steps** | 5 tool calls (`which`, `cat`, `--help`) | 0 tool calls | Zero trial and error |

The unassisted agent spent most of its time in multi-turn reasoning:

```
Unassisted trajectory (10 steps, 21.0s):
find_by_name -> which apic -> view_file apicat.yaml -> run apicat --help -> 
run apic fireworks.balance -> run apic openrouter.key -> run apic openrouter.balance -> 
which apic -> run apic fireworks.costs -> send_message report

In-memory MCP trajectory (1 step, 2.5s):
fireworks_balance() + openrouter_key() + fireworks_costs() in parallel -> send_message report
```

The main source of delay was not the network request itself. It was the LLM inference time across ten separate turns. Eliminating the exploration phase saved over 18 seconds on a single three-endpoint audit.

---

## Batch execution latency: raw curl vs. CLI vs. in-memory MCP

Next, I measured raw execution speed across four API calls without model inference in the loop:
1. `catfact.getFact` (Public GET endpoint)
2. `openrouter.key` (Authenticated GET endpoint)
3. `fireworks.costs` (Authenticated POST with JSON body)
4. `fireworks.balance` (Authenticated GET endpoint)

### Measured latency

| Endpoint | Raw `curl` (Subprocess) | `apic` CLI (Node.js) | In-Memory Rust MCP | MCP vs. Raw `curl` |
| :--- | :---: | :---: | :---: | :---: |
| **`catfact.getFact`** | 157.8 ms | 390.5 ms | 117.6 ms | 1.34x faster (+40 ms) |
| **`openrouter.key`** | 188.3 ms | 358.4 ms | 131.1 ms | 1.44x faster (+57 ms) |
| **`fireworks.costs`** | 1,198.7 ms | 1,242.4 ms | 783.1 ms | 1.53x faster (+416 ms) |
| **`fireworks.balance`** | 2,748.1 ms | 1,394.6 ms | 1,742.0 ms | 1.58x faster (+1,006 ms) |
| **Total batch (4 calls)** | 4,292.9 ms | 3,385.8 ms | 2,773.8 ms | 1.55x faster (+1.52s saved) |

---

## Why connection pooling matters

The main technical factor behind lower latency is HTTP connection reuse (Keep-Alive).

When an agent runs `curl` or a CLI command, the operating system creates a process that immediately terminates after printing stdout. Every subsequent request must create a new TCP connection, resolve DNS, and complete an SSL/TLS handshake.

With an in-memory MCP server, the process stays running. The HTTP client keeps an active connection pool across calls:

* **Cold socket (`openrouter.key`, new TLS handshake):** 4,066 ms
* **Warm socket (`openrouter.key`, reused socket):** 468 ms (8.7x speedup)

Repeated calls to the same provider reuse the existing encrypted connection.

---

## Runtime comparison: Rust vs. Bun vs. Python

I also compared three different implementations of the MCP server:
* **Native Rust:** Release binary using `ureq` and `serde_json`
* **Bun / TypeScript:** `Bun.spawn` with native streams
* **Python 3.14:** Standard library `json` and `subprocess`

| Metric | Rust (Native Release) | Bun (TypeScript) | Python 3.14 (Stdlib) |
| :--- | :---: | :---: | :---: |
| **Cold start and handshake** *(Spawn, Init, tools/list)* | 4.36 ms | 37.24 ms | 42.79 ms |
| **Raw JSON-RPC IPC latency** *(Stdio Ping)* | 0.018 ms (18 µs) | 0.058 ms (58 µs) | 0.028 ms (28 µs) |
| **Memory footprint (RSS)** | 1.77 MB | 22.83 MB | 17.45 MB |
| **Runtime dependencies** | None (Static binary) | Requires Bun or Node | Requires Python |

The compiled Rust binary starts in 4.3 milliseconds and uses 1.77 MB of memory, making it practical to leave running during an editing session.

---

## Architecture: apicat and native MCP

In [apicat](https://github.com/digplan/apicat), we combined declarative YAML definitions with an in-memory Rust MCP server.

### 1. Declarative YAML definitions (`apicat.yaml`)
Endpoints are defined in a structured YAML file:

```yaml
fireworks.costs:
  url: https://api.fireworks.ai/v1/accounts/chb1856-7irji5gdx5b0/usageCosts:query
  method: POST
  headers:
    Authorization: "Bearer $!FIREWORKS_API_KEY"
    Content-Type: application/json
  body: |
    {
      "start_time": "$START_TIME",
      "end_time": "$END_TIME",
      "scope": 1,
      "group_by": ["MODEL"]
    }
  help: Retrieve rated dollar costs and model spend breakdown.
```

### 2. Automatic JSON Schema generation
When the MCP server starts, it reads `~/.apicat` and `./apicat.yaml`, converting required (`$!VAR`) and optional (`$VAR`) variables into JSON Schema tool definitions:

```json
{
  "name": "fireworks_costs",
  "description": "Retrieve rated dollar costs and model spend breakdown.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "START_TIME": { "type": "string", "description": "ISO timestamp" },
      "END_TIME": { "type": "string", "description": "ISO timestamp" }
    },
    "required": ["START_TIME", "END_TIME"]
  }
}
```

The model receives exact parameter types upfront, preventing hallucinated flag names or shell escaping mistakes.

---

## Takeaways

1. **Avoid shell-based API calls in agents:** Running `curl` in a subshell creates escaping bugs, wastes context tokens, and loses connection pooling.
2. **Use declarative API catalogs:** Defining endpoints in YAML files like `apicat.yaml` removes the need for agents to search and scrape documentation.
3. **Keep tools in memory:** An in-memory MCP server with socket pooling turns multi-step terminal investigations into deterministic, single-turn tool calls.

The source code and benchmarks are available in the [apicat repository](https://github.com/digplan/apicat).

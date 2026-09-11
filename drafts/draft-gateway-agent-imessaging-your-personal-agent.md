# Gateway Agent: iMessaging Your Personal Agent
*By Chris Borkert · Draft · September 2026*

Most AI assistants live behind a web UI or an IDE plugin. That works fine at a desk, but not from a phone, not while driving, and not at 2 AM when an idea hits. The goal with `gateway-agent` was simple: make an AI assistant reachable through the messaging apps already on your phone — iMessage and Discord — and have it work directly on your machines.

Existing solutions like OpenClaw and other agent gateway frameworks looked promising on paper, but configuring them turned out to be more work than writing the integration from scratch. Heavy dependencies, opinionated architectures, and deployment assumptions.

The initial assumption was straightforward: a single Python script wrapping a few API calls. In practice, the project turned into an exercise in macOS system internals, undocumented SQLite schemas, AppleScript edge cases, and on-device ML inference.

The result is `gateway-agent` — a lightweight daemon that bridges Discord and iMessage to Antigravity CLI (`agy`). It runs as a macOS LaunchAgent, boots at login, recovers from crashes automatically, and operates continuously.

## The Discord Loop: 120 Lines of Bash

The assumption was that a Discord integration would require a heavy Node.js or Python framework. It didn't. The entire thing is written in bash.

Because `apic` handles the WebSocket connection, the integration reduces to a glorified `while read` loop. Unix pipes handle the rest. No framework. No runtime.

```bash
    (
      while true; do
        send_typing
        sleep 7
      done
    ) 2>/dev/null &
    typing_pid=$!

    reply="$(cd /Users/chris && agy -p "$prompt" --dangerously-skip-permissions --mode=accept-edits </dev/null)" || {
      kill "$typing_pid" 2>/dev/null || true
      wait "$typing_pid" 2>/dev/null || true
      echo "agy failed"
      continue
    }
```

When a message comes in, the loop kicks off a background subshell that sends a POST request to Discord's typing API every 7 seconds. It then blocks on `agy`. When `agy` finishes modifying files, the script kills the typing process and posts the output back to the channel.

Managing conversation context was another problem. I didn't want to spin up a database just to remember the last few messages. I used a flat text file.

```bash
    ## keep AGENTS.md under 50 lines whenever it grows past the cap
    [[ "$(wc -l < /Users/chris/gateway-agent/AGENTS.md)" -gt 50 ]] && tail -n 50 /Users/chris/gateway-agent/AGENTS.md > /tmp/AGENTS.md && cp /tmp/AGENTS.md /Users/chris/gateway-agent/AGENTS.md
```

This trick works exceptionally well. `AGENTS.md` acts as a rolling history. It is stateless, simple, and grep-able. The prompt construction just dumps this file into the input.

Since other bots share the Discord channel, cross-talk was an issue. Bare approval commands ("yes", "approve", "lgtm") intended for other integrations would wake up the agent. I added a hardcoded filter to ignore market mover commands to keep the signal clean.

## The iMessage Hack

iMessage was harder. There is no public API. You have to read the local SQLite database. 

macOS stores messages in `~/Library/Messages/chat.db`. Reading it programmatically requires Full Disk Access. I wrote a Python script to poll the database directly.

```python
def fetch_new_messages(last_rowid: int) -> list:
    conn = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    query = """
    SELECT 
        m.ROWID,
        m.text,
        m.is_from_me,
        h.id AS sender_handle,
        a.filename AS attachment_filename,
        a.mime_type AS attachment_mime,
        a.transfer_name AS attachment_name
    FROM message m
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    LEFT JOIN message_attachment_join maj ON m.ROWID = maj.message_id
    LEFT JOIN attachment a ON maj.attachment_id = a.ROWID
    WHERE m.ROWID > ?
    ORDER BY m.ROWID ASC;
    """
    cur.execute(query, (last_rowid,))
    rows = cur.fetchall()
    conn.close()
    return rows
```

This approach works, but it is fragile. Apple changes the schema between macOS versions without warning. Full Disk Access permissions frequently reset or fail silently. 

Replying to messages requires AppleScript (`osascript`). 

```python
script = f'''
tell application "Messages"
    set targetService to 1st service whose service type is iMessage and enabled is true
    set targetBuddy to buddy "{target}" of targetService
    send "{clean_text}" to targetBuddy
end tell
'''
```

AppleScript is terrible for sending messages at scale. If you send too many messages too fast, the Messages app locks up. 

I also needed strict anti-loop guards. To prevent the bot from reading its own outgoing messages and replying to them infinitely, bot replies are prefixed with the 🤖 emoji and tracked in a local set. Messages matching known bot outputs are silently dropped. When running on a separate Apple ID, I added a `DEDICATED_BOT` mode that just ignores all outgoing messages outright.

## Voice Memos via MLX Whisper

I wanted to send voice notes to the agent while driving. iMessage voice memos arrive as `.caf` attachments. 

I used `ffmpeg` to convert the `.caf` files to `.wav`, then ran them through MLX Whisper locally. 

```python
        import mlx_whisper
        t0 = time.time()
        result = mlx_whisper.transcribe(wav_path, path_or_hf_repo="mlx-community/whisper-tiny")
        text = result.get("text", "").strip()
```

Running the model locally on Apple Silicon means no cloud transcription service, no API latency, and no data leaving my machine. It transcribes audio clips in seconds.

## Scheduling and Synchronization

I needed the agent to act proactively, not just reactively. I wrote a cron-like daemon in Python (`scheduler.py`) to send recurring alerts to Discord or iMessage.

The scheduler is just a polling loop checking `HH:MM` against the current time. It drifts by up to 20 seconds. It is completely unsophisticated, and it works perfectly. It also monitors my Antigravity CLI quota usage, sending threshold alerts (50%, 30%, 20%, 10%) directly to my phone. Catching quota limits before you hit them matters when an agent has 24/7 write access to your machine.

The agent runs on an always-on machine, but development happens on a laptop. The two need to stay in sync. Git push/pull works, but it adds friction — you have to remember to commit and push before the agent can see your changes, and pull before you can see what the agent did. Mutagen eliminates that entirely. It mirrors repos bidirectionally in real-time. Edit a file on the laptop, and it appears on the server within seconds. The agent modifies code on the server, and it shows up on the laptop without touching git. Faster and requires less thinking about.

To keep everything running, the agent is packaged as a macOS LaunchAgent plist. The `KeepAlive` key ensures that if a script crashes — usually because of an SQLite database lock — `launchd` immediately restarts it.

## Tradeoffs and Surprises

The biggest surprise was the bash script. I wrote it as a temporary hack, but the 120 lines of code have been running for months without a single issue. The Unix pipeline model maps perfectly to a text-in, text-out API.

The iMessage integration requires more babysitting. The `chat.db` schema will inevitably break in a future macOS update.

If I were to do this again, I might try to build a unified queue instead of running separate bash and Python processes. But the separation of concerns keeps failures isolated. When AppleScript hangs the iMessage script, the Discord loop keeps running.

You can find the code here: [github.com/digplan/gateway-agent](https://github.com/digplan/gateway-agent). MIT licensed.

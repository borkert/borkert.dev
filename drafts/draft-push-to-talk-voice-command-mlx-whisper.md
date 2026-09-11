# Sub-100ms Push-to-Talk: Driving Local Agents with Apple Silicon and MLX Whisper
*By Chris Borkert · September 2026*

Typing prompts to autonomous agents creates an odd cognitive bottleneck. When reasoning about architectural diffs or test failures, speaking a prompt takes five seconds; typing it out with precise code references takes thirty. 

I wanted a frictionless push-to-talk (PTT) interface on macOS that worked across every application on my machine—terminal sessions, VS Code, web chats, or standalone agent CLIs. 

Existing solutions failed in two directions:
1. **Cloud-based speech APIs** (OpenAI Whisper API, Deepgram) introduce a 600ms to 1500ms network round-trip. Sending internal source code and token streams across public networks also violates basic security isolation.
2. **Built-in macOS dictation** requires multiple keystrokes to trigger, struggles with programming jargon, and doesn't auto-submit. You still have to reach back to the keyboard, wait for the animation, and hit Enter.

I built `voice_ptt.py`—a 330-line Python daemon that captures CoreAudio on key-press, transcribes on-device using Apple Silicon Metal via MLX Whisper, and injects the text with an automated Return key into whatever window has focus.

```
[Hold Right Option ⌥] ──► CoreAudio stream (16kHz)
           │
           ▼
     [Key Release] ──► MLX Whisper Metal Inference (47ms–165ms)
           │
           ▼
     pbcopy + ⌘V ──► delay 50ms ──► key code 36 (↵ Enter)
```

## The Mechanics: Dual-Key Routing

The interface requires no GUI window, no dock icon, and no menu bar interactions. It runs as a background process managed by `ptt start` in `~/.local/bin/ptt`.

I mapped the triggers to modifier keys on the right side of the keyboard that are rarely used during normal typing:

| Key Binding | Mode | Behavior | Use Case |
| :--- | :--- | :--- | :--- |
| **Right Option** (`⌥` / `alt_r`) | `enter` | Transcribe + Paste + `↵ Return` | Firing commands directly into terminal or agent chat |
| **Right Command** (`⌘` / `cmd_r`) | `no_enter` | Transcribe + Paste only | Inserting dictated text into an open editor for manual editing |
| **Right Control** (`ctrl_r`) | `no_enter` | Transcribe + Paste only | Alternative hand position for drafting |

On key-down, the daemon triggers an immediate audio cue (`afplay /System/Library/Sounds/Pop.aiff`) and begins appending raw PCM samples from a CoreAudio input stream into an in-memory buffer. On key-up, it plays `Tink.aiff`, stops the stream, and hands the buffer off to a dedicated worker thread.

```python
def audio_callback(self, indata, frames, time_info, status):
    if self.is_recording:
        with self.lock:
            self.audio_frames.append(indata.copy())
```

Decoupling recording from transcription via a worker thread prevents audio buffer overruns and ensures the key listener never drops release events if transcription takes longer than expected.

## Beating the Metal JIT Compilation Penalty

Apple's MLX framework compiles computation graphs lazily into Metal kernels on the first forward pass. 

In my initial prototype, the very first dictation after boot incurred a **1,840 ms stutter** while the GPU compiled the attention and convolution kernels. That initial delay destroyed the feeling of instant responsiveness.

The fix was a synthetic warm-up pass during daemon initialization:

```python
# Warmup Metal compilation graph upfront
print("Warming up MLX Whisper model...")
import mlx_whisper
mlx_whisper.transcribe(np.zeros(16000, dtype=np.float32), path_or_hf_repo=self.model_name)
print("Ready!")
```

Feeding a 1-second zero tensor forces MLX to compile and cache all Metal shader kernels at boot time. Subsequent runs bypass JIT compilation entirely.

## Injection: Why Clipboard Beats Keystroke Synthesis

Once transcription completes, the text must land in the active input field. 

The obvious approach was synthesizing individual key events via AppleScript's `tell application "System Events" to keystroke text`. In practice, this failed:
1. **Latency**: Emitting 40 words character-by-character takes ~600ms.
2. **Key Dropping**: If you press any physical key while System Events is firing virtual keystrokes, the modifier states conflict and produce garbled text.

The solution was atomic clipboard injection:

```python
def paste_text_and_enter(text: str, auto_enter: bool = True):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(text.encode("utf-8"))

    lines = ['tell application "System Events"', 'keystroke "v" using command down']
    if auto_enter:
        lines.append('delay 0.05')
        lines.append('key code 36')  # 36 is Return
    lines.append('end tell')

    subprocess.run(["osascript", "-e", "\n".join(lines)], stdout=subprocess.DEVNULL)
```

Piping UTF-8 bytes into `pbcopy` and emitting a single `⌘V` keystroke executes in under 15ms, regardless of prompt length. The 50ms delay before `key code 36` gives the host application time to process the clipboard paste event before submitting.

## Measured Latency on Apple Silicon

Using `mlx-community/whisper-tiny` on an M-series Mac, transcription latency scales with utterance length:

| Utterance Type | Spoken Words | Audio Duration | MLX Whisper Latency | End-to-End Delivery |
| :--- | :--- | :--- | :--- | :--- |
| Single command | 4 words | 1.1 s | **47 ms** | **~112 ms** |
| Short instruction | 8 words | 1.8 s | **59 ms** | **~124 ms** |
| Technical query | 11 words | 2.6 s | **72 ms** | **~137 ms** |
| Multi-clause prompt | 16 words | 3.9 s | **165 ms** | **~230 ms** |
| Complex prompt | 32 words | 7.4 s | **1,016 ms** | **~1,081 ms** |

For the vast majority of agent commands (under 15 words), transcription finishes in **under 100 milliseconds**. From the moment you release the Option key, the text appears and executes before your thumb has lifted off the keyboard.

## Negative Results & Edge Cases

Three operational bugs emerged during daily use:

### 1. The Zero-Duration Hallucination Loop
When releasing the Option key too quickly (<0.2s duration), or when recording background noise without speech, Whisper-tiny occasionally entered an autoregressive repetition loop, emitting hundreds of repeated tokens (e.g. `Ha ha ha ha...`). 

I added a minimum duration threshold before dispatching to the inference engine:

```python
audio_np = np.concatenate(frames, axis=0).flatten()
duration = len(audio_np) / self.sample_rate

if duration < 0.2:
    return
```

### 2. Domain Jargon Phonetics
Small quantized models (`whisper-tiny`) occasionally stumble on developer terminology. For instance, "Ollama" is consistently transcribed as "Olamah". 

Upgrading to `whisper-base` fixes most phonetic errors at the cost of increasing inference latency from ~60ms to ~180ms. For my workflow, sub-100ms response speed on `whisper-tiny` outweighs occasional spelling fixes.

### 3. macOS Accessibility Flakiness
macOS Sequoia and Sonoma require both Accessibility (`AXIsProcessTrusted`) and Input Monitoring permissions to capture global hotkeys via `pynput`. Rebuilding a virtual environment or moving binary paths invalidates the OS security token without warning, causing key events to be dropped silently.

I added an explicit diagnostic command (`ptt test` / `ptt open-settings`) that queries `AXIsProcessTrustedWithOptions` on startup and directs the user to the exact System Settings pane if permissions drop.

## Conclusion and Future Work

A 330-line script bridging CoreAudio, MLX Whisper, and macOS System Events outperforms cloud dictation in latency, privacy, and workflow ergonomics.

If I were refactoring this system, I would replace the Python runtime with a single compiled Swift binary using `CGEventTapCreate` and native MLX Swift bindings. That would drop memory usage from ~120MB to under 15MB and eliminate the Python virtualenv dependency.

The daemon runs locally on my workstation via `alias ptt="/Users/chris/.local/bin/ptt"`.

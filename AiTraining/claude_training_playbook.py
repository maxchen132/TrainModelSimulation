"""
claude_training_playbook.py
----------------------------
Automates the JMRI Training Playbook using the Anthropic Claude API.

Anthropic Files API notes (beta as of 2025):
  - PDFs can be uploaded and referenced by file_id as document blocks.
  - CSVs, TXT, DOCX, XLSX, and Markdown are NOT supported as document blocks —
    their content is read locally and sent inline as text.

Requirements:
    pip install anthropic

Usage:
    python claude_training_playbook.py \
        --csv data_traces.csv \
        --layout "Train Network Layout.txt" \
        [--model claude-sonnet-4-6] \
        [--output-dir ./outputs]
"""

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("[ERROR] anthropic package not found. Run: pip install anthropic")


# ---------------------------------------------------------------------------
# Constants / prompts
# ---------------------------------------------------------------------------

FILES_API_BETA = "files-api-2025-04-14"

# File types the Anthropic API accepts as uploaded document blocks (PDF only for now)
UPLOADABLE_EXTENSIONS = {".pdf"}

# File types we read locally and inline as text
INLINE_EXTENSIONS = {".csv", ".txt", ".md", ".docx", ".xlsx", ".json"}

INITIAL_PROMPT_TEMPLATE = """\
Here is the current Network Layout for a model train system using JMRI (provided below \
or as an attached document). I have also provided the raw data traces from data_traces.csv.

Generate 5-10 data invariants from data_traces.csv which are assumed constants.

Generate 5-10 independent events and data points that can violate the defined data \
invariants, using the sample output format below. For the synthetic violating events, \
please indicate how such an attack could occur based on the network configuration. \
Please generate what data traces for each attack would look like as well.

Generate the data invariants and independent events in the following format:

---
Inferred Invariants from Raw Traces
I-A: Invariant 1: (Explanation)
I-B: Invariant 2: (Explanation)
...

Synthetic Violating Events
I-1: X + Y + Z event -> Breaks A + B + C anomalies
  Attack vector: (how this could occur on the network)
  Simulated trace: (what the data would look like)
I-2: ...
---
"""

FOLLOW_UP_SUGGESTIONS = [
    "Give more anomalies that can break invariants with possible range values",
    "Generate a list of potential attack surfaces based on the given network configuration "
    "of the train model system (physical attacks, cyber threats, malformed JMRI messages, "
    "logic-level invariant violations, timing-based attacks)",
    "Generate additional quantitative or qualitative data points that can be recorded "
    "within the data traces",
    "Regenerate invariants and specify specific rows and ranges from the CSV to justify "
    "each invariant",
    "For each violating event, specify which rows/ranges in the CSV are most relevant "
    "and how the violation manifests",
    "[Enter your own prompt]",
    "[Done — save and exit]",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def wrap(text: str, width: int = 100) -> str:
    lines = []
    for paragraph in text.split("\n"):
        if len(paragraph) <= width:
            lines.append(paragraph)
        else:
            lines.extend(textwrap.wrap(paragraph, width=width))
    return "\n".join(lines)


def print_banner(title: str):
    bar = "=" * 70
    print(f"\n{bar}")
    print(f"  {title}")
    print(f"{bar}\n")


def print_response(label: str, content: str):
    print_banner(label)
    print(wrap(content))
    print()


def save_transcript(output_dir: Path, session_id: str, messages: list[dict]):
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"transcript_{session_id}.json"
    txt_path  = output_dir / f"transcript_{session_id}.txt"

    with open(json_path, "w") as f:
        json.dump(messages, f, indent=2)

    with open(txt_path, "w") as f:
        for msg in messages:
            role = msg["role"].upper()
            content = msg.get("content", "")
            if isinstance(content, list):
                # Flatten content blocks to readable text
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif block.get("type") == "document":
                            parts.append(f"[Document attached: {block.get('title', 'file')}]")
                content = "\n".join(parts)
            f.write(f"{'='*70}\n[{role}]\n{'='*70}\n{content}\n\n")

    print(f"[Saved] Transcript (JSON) → {json_path}")
    print(f"[Saved] Transcript (TXT)  → {txt_path}")
    return json_path, txt_path


def save_extracted_sections(output_dir: Path, session_id: str, messages: list[dict]):
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"invariants_and_events_{session_id}.txt"

    keywords = [
        "inferred invariant", "synthetic violating", "attack surface",
        "attack vector", "anomal", "i-a:", "i-b:", "i-1:", "i-2:",
    ]

    with open(out_path, "w") as f:
        for i, msg in enumerate(messages):
            if msg["role"] != "assistant":
                continue
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if any(k in content.lower() for k in keywords):
                f.write(f"--- Assistant message {i+1} ---\n{content}\n\n")

    print(f"[Saved] Invariants/Events  → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# File handling
# ---------------------------------------------------------------------------

def read_as_text(path: Path) -> str:
    """Read any text-like file and return its contents as a string."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def upload_pdf(client: anthropic.Anthropic, path: Path) -> str:
    """Upload a PDF to the Anthropic Files API and return the file_id."""
    print(f"[Upload] {path.name} (PDF via Files API) ...", end=" ", flush=True)
    with open(path, "rb") as f:
        response = client.beta.files.upload(
            file=(path.name, f, "application/pdf"),
            betas=[FILES_API_BETA],
        )
    print(f"OK  (id={response.id})")
    return response.id


def build_initial_message(
    csv_path: Path,
    layout_path: Path,
    layout_file_id: str | None,
) -> dict:
    """
    Build the first user message.
    - CSV is always inlined as text (Anthropic Files API doesn't support CSV as a document block).
    - Layout is either a referenced PDF document block or inlined text.
    """
    csv_text = read_as_text(csv_path)

    content_blocks = [
        {
            "type": "text",
            "text": INITIAL_PROMPT_TEMPLATE,
        },
        {
            "type": "text",
            "text": f"=== data_traces.csv ===\n{csv_text}\n=== end of data_traces.csv ===",
        },
    ]

    if layout_file_id:
        # PDF uploaded — reference by file_id as a document block
        content_blocks.append({
            "type": "document",
            "source": {
                "type": "file",
                "file_id": layout_file_id,
            },
            "title": "Train Network Layout",
        })
    else:
        # Text-based layout — inline directly
        layout_text = read_as_text(layout_path)
        content_blocks.append({
            "type": "text",
            "text": f"=== Train Network Layout ===\n{layout_text}\n=== end of layout ===",
        })

    return {"role": "user", "content": content_blocks}


# ---------------------------------------------------------------------------
# Claude API interaction
# ---------------------------------------------------------------------------

def chat(client: anthropic.Anthropic, model: str, messages: list[dict], max_tokens: int = 4096) -> str:
    """Send full message history to Claude and return the reply text."""
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )

    # Only include the Files API beta header if any message uses a file reference
    uses_files = any(
        isinstance(msg.get("content"), list) and
        any(
            isinstance(b, dict) and b.get("type") == "document" and
            isinstance(b.get("source"), dict) and b["source"].get("type") == "file"
            for b in msg["content"]
        )
        for msg in messages
    )

    if uses_files:
        response = client.beta.messages.create(betas=[FILES_API_BETA], **kwargs)
    else:
        response = client.messages.create(**kwargs)

    return response.content[0].text


# ---------------------------------------------------------------------------
# Interactive follow-up loop
# ---------------------------------------------------------------------------

def interactive_loop(client: anthropic.Anthropic, model: str, messages: list[dict]):
    while True:
        print_banner("Follow-up options")
        for i, suggestion in enumerate(FOLLOW_UP_SUGGESTIONS, 1):
            print(f"  [{i}] {suggestion}")

        choice = input("\nEnter option number (or type a custom prompt directly): ").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(FOLLOW_UP_SUGGESTIONS):
                selected = FOLLOW_UP_SUGGESTIONS[idx]
                if "[Done" in selected:
                    break
                if "[Enter your own" in selected:
                    prompt_text = input("Your prompt: ").strip()
                    if not prompt_text:
                        continue
                else:
                    prompt_text = selected
            else:
                print("[!] Invalid option.")
                continue
        else:
            prompt_text = choice
            if not prompt_text:
                continue

        print(f"\n[Sending] {prompt_text[:80]}{'...' if len(prompt_text) > 80 else ''}")
        messages.append({"role": "user", "content": prompt_text})

        try:
            reply = chat(client, model, messages)
        except anthropic.APIError as e:
            print(f"[ERROR] API call failed: {e}")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": reply})
        print_response("Claude", reply)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Automate the JMRI Training Playbook using the Anthropic Claude API"
    )
    parser.add_argument("--csv",    required=True, help="Path to data_traces.csv")
    parser.add_argument("--layout", required=True, help="Path to Train Network Layout document")
    parser.add_argument("--model",  default="claude-sonnet-4-6",
                        help="Claude model to use (default: claude-sonnet-4-6)")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="Max tokens per response (default: 4096)")
    parser.add_argument("--output-dir", default="./playbook_outputs",
                        help="Directory to save outputs (default: ./playbook_outputs)")
    parser.add_argument("--api-key",
                        help="Anthropic API key (default: reads ANTHROPIC_API_KEY env var)")
    return parser.parse_args()


def main():
    args = parse_args()

    csv_path    = Path(args.csv)
    layout_path = Path(args.layout)

    for p in (csv_path, layout_path):
        if not p.exists():
            sys.exit(f"[ERROR] File not found: {p}")

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit(
            "[ERROR] No API key found. Set ANTHROPIC_API_KEY environment variable "
            "or pass --api-key <key>"
        )

    client     = anthropic.Anthropic(api_key=api_key)
    session_id = timestamp()
    output_dir = Path(args.output_dir)

    print_banner(f"JMRI Claude Training Playbook  |  session {session_id}")
    print(f"  Model      : {args.model}")
    print(f"  CSV        : {csv_path}")
    print(f"  Layout     : {layout_path}")
    print(f"  Output dir : {output_dir}\n")

    # --- Upload layout PDF if applicable; otherwise read as text ---
    layout_file_id = None
    layout_ext = layout_path.suffix.lower()

    if layout_ext in UPLOADABLE_EXTENSIONS:
        print("[Step 1/3] Uploading layout PDF to Anthropic Files API...")
        try:
            layout_file_id = upload_pdf(client, layout_path)
        except Exception as e:
            sys.exit(f"[ERROR] File upload failed: {e}")
    else:
        print(f"[Step 1/3] Layout file ({layout_ext}) will be inlined as text.")
        if layout_ext not in INLINE_EXTENSIONS:
            print(f"  [WARN] Extension '{layout_ext}' is uncommon — will attempt to read as UTF-8 text.")

    # --- CSV is always inlined ---
    print(f"           CSV will be inlined as text (Files API does not support .csv as document blocks).")

    # --- Initial prompt ---
    print("\n[Step 2/3] Sending initial analysis prompt to Claude...")
    messages: list[dict] = []
    first_msg = build_initial_message(csv_path, layout_path, layout_file_id)
    messages.append(first_msg)

    try:
        initial_reply = chat(client, args.model, messages, max_tokens=args.max_tokens)
    except anthropic.APIError as e:
        sys.exit(f"[ERROR] Initial API call failed: {e}")

    messages.append({"role": "assistant", "content": initial_reply})
    print_response("Claude — Initial Analysis", initial_reply)

    # --- Interactive follow-ups ---
    print("[Step 3/3] Entering interactive follow-up loop...\n")
    print("  Choose a follow-up from the list, type your own, or pick '[Done]' to save and exit.\n")

    try:
        interactive_loop(client, args.model, messages)
    except KeyboardInterrupt:
        print("\n[Interrupted] Saving outputs before exit...")

    # --- Save outputs ---
    save_transcript(output_dir, session_id, messages)
    save_extracted_sections(output_dir, session_id, messages)

    # --- Optionally delete uploaded PDF ---
    if layout_file_id:
        cleanup = input("\nDelete uploaded PDF from Anthropic file storage? [y/N]: ").strip().lower()
        if cleanup == "y":
            try:
                client.beta.files.delete(layout_file_id, betas=[FILES_API_BETA])
                print(f"  Deleted file {layout_file_id}")
            except Exception as e:
                print(f"  [WARN] Could not delete {layout_file_id}: {e}")

    print_banner(f"Session complete — outputs saved to {output_dir}/")


if __name__ == "__main__":
    main()
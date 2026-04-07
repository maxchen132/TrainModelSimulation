"""
openai_training_playbook.py
----------------------------
Automates the OpenAI Training Playbook for JMRI model train system analysis.

Requirements:
    pip install openai

Usage:
    python openai_training_playbook.py \
        --csv data_traces.csv \
        --layout "Train Network Layout.txt" \
        [--model gpt-4o] \
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
    from openai import OpenAI
except ImportError:
    sys.exit("[ERROR] openai package not found. Run: pip install openai")


# ---------------------------------------------------------------------------
# Constants / prompts
# ---------------------------------------------------------------------------

INITIAL_PROMPT_TEMPLATE = """\
Here is the current Network Layout for a model train system using JMRI (provided as an \
attached file). I have also attached data_traces.csv containing raw sensor and turnout \
event traces.

Generate 5-10 data invariants from data_traces.csv which are assumed constants.

Generate 5-10 independent events and data points that can violate the defined data \
invariants, using the sample output format below. For the synthetic violating events, \
please indicate how such an attack could occur based on the network configuration file. \
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
    """Lightly wrap long lines for terminal display."""
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
    """Save full chat transcript as JSON and plain text."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"transcript_{session_id}.json"
    txt_path  = output_dir / f"transcript_{session_id}.txt"

    with open(json_path, "w") as f:
        json.dump(messages, f, indent=2)

    with open(txt_path, "w") as f:
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"] if isinstance(msg["content"], str) else "[file/structured content]"
            f.write(f"{'='*70}\n[{role}]\n{'='*70}\n{content}\n\n")

    print(f"[Saved] Transcript → {json_path}")
    print(f"[Saved] Transcript → {txt_path}")
    return json_path, txt_path


def save_extracted_sections(output_dir: Path, session_id: str, messages: list[dict]):
    """
    Best-effort extraction of invariants and violating events from assistant messages
    and save them to a dedicated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"invariants_and_events_{session_id}.txt"

    keywords = [
        "inferred invariant",
        "synthetic violating",
        "attack surface",
        "attack vector",
        "anomal",
        "i-a:",
        "i-b:",
        "i-1:",
        "i-2:",
    ]

    with open(out_path, "w") as f:
        for i, msg in enumerate(messages):
            if msg["role"] != "assistant":
                continue
            content = msg["content"] if isinstance(msg["content"], str) else ""
            lower = content.lower()
            if any(k in lower for k in keywords):
                f.write(f"--- Assistant message {i+1} ---\n")
                f.write(content)
                f.write("\n\n")

    print(f"[Saved] Invariants/Events → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# OpenAI interaction
# ---------------------------------------------------------------------------

def upload_file(client: OpenAI, path: Path, purpose: str = "assistants") -> str:
    """Upload a file to OpenAI and return its file ID."""
    print(f"[Upload] {path.name} ...", end=" ", flush=True)
    with open(path, "rb") as f:
        response = client.files.create(file=f, purpose=purpose)
    print(f"OK  (id={response.id})")
    return response.id


def build_initial_user_message(csv_file_id: str, layout_file_id: str) -> dict:
    """Build the first user message with both file attachments."""
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": INITIAL_PROMPT_TEMPLATE,
            },
            {
                "type": "file",
                "file": {"file_id": csv_file_id},
            },
            {
                "type": "file",
                "file": {"file_id": layout_file_id},
            },
        ],
    }


def chat(client: OpenAI, model: str, messages: list[dict]) -> str:
    """Send the full message history and return the assistant's reply text."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Interactive follow-up loop
# ---------------------------------------------------------------------------

def interactive_loop(client: OpenAI, model: str, messages: list[dict]):
    """Present suggested follow-up prompts and let the user iterate."""
    while True:
        print_banner("Follow-up options")
        for i, suggestion in enumerate(FOLLOW_UP_SUGGESTIONS, 1):
            print(f"  [{i}] {suggestion}")

        choice = input("\nEnter option number (or type a custom prompt directly): ").strip()

        # Numeric shortcut
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
            # Treat raw input as a custom prompt
            prompt_text = choice
            if not prompt_text:
                continue

        print(f"\n[Sending] {prompt_text[:80]}{'...' if len(prompt_text) > 80 else ''}")
        messages.append({"role": "user", "content": prompt_text})

        try:
            reply = chat(client, model, messages)
        except Exception as e:
            print(f"[ERROR] API call failed: {e}")
            messages.pop()  # remove the failed message
            continue

        messages.append({"role": "assistant", "content": reply})
        print_response("Assistant", reply)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Automate the OpenAI Training Playbook for JMRI analysis"
    )
    parser.add_argument(
        "--csv", required=True,
        help="Path to data_traces.csv"
    )
    parser.add_argument(
        "--layout", required=True,
        help="Path to Train Network Layout document (txt, pdf, docx, etc.)"
    )
    parser.add_argument(
        "--model", default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)"
    )
    parser.add_argument(
        "--output-dir", default="./playbook_outputs",
        help="Directory to save transcripts and extracted outputs (default: ./playbook_outputs)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (default: reads OPENAI_API_KEY env var)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # --- Validate files ---
    csv_path    = Path(args.csv)
    layout_path = Path(args.layout)

    for p in (csv_path, layout_path):
        if not p.exists():
            sys.exit(f"[ERROR] File not found: {p}")

    # --- API key ---
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "[ERROR] No API key found. Set OPENAI_API_KEY environment variable "
            "or pass --api-key <key>"
        )

    client     = OpenAI(api_key=api_key)
    session_id = timestamp()
    output_dir = Path(args.output_dir)

    print_banner(f"JMRI OpenAI Training Playbook  |  session {session_id}")
    print(f"  Model      : {args.model}")
    print(f"  CSV        : {csv_path}")
    print(f"  Layout     : {layout_path}")
    print(f"  Output dir : {output_dir}\n")

    # --- Upload files ---
    print("[Step 1/3] Uploading files to OpenAI...")
    try:
        csv_file_id    = upload_file(client, csv_path)
        layout_file_id = upload_file(client, layout_path)
    except Exception as e:
        sys.exit(f"[ERROR] File upload failed: {e}")

    # --- Initial prompt ---
    print("\n[Step 2/3] Sending initial analysis prompt...")
    messages: list[dict] = []
    first_user_msg = build_initial_user_message(csv_file_id, layout_file_id)
    messages.append(first_user_msg)

    try:
        initial_reply = chat(client, args.model, messages)
    except Exception as e:
        sys.exit(f"[ERROR] Initial API call failed: {e}")

    messages.append({"role": "assistant", "content": initial_reply})
    print_response("Initial Analysis", initial_reply)

    # --- Interactive follow-ups ---
    print("[Step 3/3] Entering interactive follow-up loop...\n")
    print("  You can now send additional prompts from the suggested list or type your own.")
    print("  Choose '[Done]' when finished to save all outputs.\n")

    try:
        interactive_loop(client, args.model, messages)
    except KeyboardInterrupt:
        print("\n[Interrupted] Saving outputs before exit...")

    # --- Save outputs ---
    # Flatten structured content in message history for saving
    saveable_messages = []
    for msg in messages:
        if isinstance(msg["content"], list):
            # Extract text portions only for the transcript
            text_parts = [
                block["text"] for block in msg["content"]
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            saveable_messages.append({"role": msg["role"], "content": "\n".join(text_parts)})
        else:
            saveable_messages.append(msg)

    save_transcript(output_dir, session_id, saveable_messages)
    save_extracted_sections(output_dir, session_id, saveable_messages)

    # --- Clean up uploaded files (optional) ---
    cleanup = input("\nDelete uploaded files from OpenAI storage? [y/N]: ").strip().lower()
    if cleanup == "y":  
        for fid in (csv_file_id, layout_file_id):
            try:
                client.files.delete(fid)
                print(f"  Deleted file {fid}")
            except Exception as e:
                print(f"  [WARN] Could not delete {fid}: {e}")

    print_banner(f"Session complete — outputs saved to {output_dir}/")


if __name__ == "__main__":
    main()
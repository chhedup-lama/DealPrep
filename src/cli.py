"""Terminal chat loop for the AE call-prep agent."""

from __future__ import annotations

import sys

from src.agent import build_client, final_text, run_turn


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    client = build_client()
    messages: list[dict] = []

    print("AE call-prep assistant. Ask about an account (e.g. 'Brightline Retail'). Ctrl+C to quit.\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            break

        messages.append({"role": "user", "content": user_input})
        assistant_message = run_turn(client, messages)
        messages.append(assistant_message)

        print(f"\nagent> {final_text(assistant_message)}\n")


if __name__ == "__main__":
    main()

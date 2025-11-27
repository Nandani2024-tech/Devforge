# scripts/run_full_pipeline.py
import time

from mocks.mock_asr import mock_asr_stream
from mocks.mock_cleaner import mock_cleaner_stage
from mocks.mock_grammar import mock_grammar_stage
from orchestrator.orchestrator import PipelineOrchestrator
from schemas.pipeline_message import PipelineMessage


def main():
    print("=== Full Mock Pipeline Demo ===")

    utt_id = "demo_utt"

    tone_mode = input("Enter tone mode (formal/casual/concise/neutral): ").strip().lower()
    if tone_mode not in {"formal", "casual", "concise", "neutral"}:
        print("Invalid mode, defaulting to neutral.")
        tone_mode = "neutral"

    orch = PipelineOrchestrator(tone_mode=tone_mode)

    # 1) ASR
    asr_msgs = mock_asr_stream(utt_id)
    eos_time = time.time()
    for m in asr_msgs:
        if m.event == "END_ASR":
            m.end_of_speech_time = eos_time

    print("\n[ASR OUTPUT]")
    for m in asr_msgs:
        if m.event == "PART":
            print(f"ASR PART[{m.chunk_index}]: {m.text}")

    # 2) Cleaner
    clean_msgs = mock_cleaner_stage(asr_msgs)
    print("\n[CLEANER OUTPUT]")
    for m in clean_msgs:
        if m.event == "PART":
            print(f"CLEAN PART[{m.chunk_index}]: {m.text}")

    # 3) Grammar
    grammar_msgs = mock_grammar_stage(clean_msgs)
    print("\n[GRAMMAR OUTPUT]")
    for m in grammar_msgs:
        if m.event == "PART":
            print(f"GRAMMAR PART[{m.chunk_index}]: {m.text}")

    # 4) Tone & Orchestrator
    print("\n[TONE ORCHESTRATOR OUTPUT]")
    final_msg: PipelineMessage | None = None

    for gm in grammar_msgs:
        out = orch.process_message(gm)
        if out is None:
            continue
        if out.event == "PREVIEW_TONE":
            print(f"PREVIEW_TONE[{out.chunk_index}]: {out.text}")
        elif out.event == "END_TONE":
            final_msg = out

    if final_msg:
        print("\n--- FINAL TONE OUTPUT ---")
        print(final_msg.text)
        print("-------------------------")
    else:
        print("\nNo END_TONE produced; check pipeline wiring.")


if __name__ == "__main__":
    main()

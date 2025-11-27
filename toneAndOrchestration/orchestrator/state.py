from typing import Dict, Optional


class UtteranceState:
    """
    Holds all intermediate data for a single utterance.
    Used by the orchestrator to store chunks until END_GRAMMAR.
    """

    def __init__(self):
        self.chunks: Dict[int, str] = {}          # chunk_index -> text
        self.end_of_speech_time: Optional[float] = None
        self.received_end_grammar: bool = False

    def add_chunk(self, index: int, text: str):
        self.chunks[index] = text

    def mark_end_grammar(self, eos_time: float):
        self.received_end_grammar = True
        self.end_of_speech_time = eos_time

    def assemble_full_text(self) -> str:
        ordered = [self.chunks[i] for i in sorted(self.chunks.keys())]
        return " ".join(ordered).strip()

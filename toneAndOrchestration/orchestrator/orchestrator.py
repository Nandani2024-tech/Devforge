from typing import Dict, Optional
from schemas.pipeline_message import PipelineMessage
from tone_module.transformer import ToneTransformer
from orchestrator.state import UtteranceState
from orchestrator.latency_logger import LatencyLogger


class PipelineOrchestrator:
    """
    Consumes grammar-corrected PipelineMessage chunks,
    buffers them per utterance, applies tone transformation,
    and emits partial + final outputs.
    """

    def __init__(self, tone_mode="neutral"):
        self.tone_mode = tone_mode
        self.tone_transformer = ToneTransformer(mode=tone_mode)
        self.state_by_id: Dict[str, UtteranceState] = {}

    def _get_state(self, utt_id: str) -> UtteranceState:
        if utt_id not in self.state_by_id:
            self.state_by_id[utt_id] = UtteranceState()
        return self.state_by_id[utt_id]

    # ----------------------------------------------------------
    # MAIN ENTRYPOINT — Process incoming grammar chunks
    # ----------------------------------------------------------
    def process_message(self, msg: PipelineMessage) -> Optional[PipelineMessage]:
        state = self._get_state(msg.id)

        # ----------------------
        # PART EVENT (streaming)
        # ----------------------
        if msg.event == "PART":
            state.add_chunk(msg.chunk_index, msg.text)

            # Apply CHUNK-LEVEL tone transformation for preview
            preview = self.tone_transformer._tone_transform(msg.text)

            return PipelineMessage(
                id=msg.id,
                chunk_index=msg.chunk_index,
                text=preview,
                event="PREVIEW_TONE",
                is_final=False,
                end_of_speech_time=None,
            )

        # ----------------------
        # END OF GRAMMAR
        # ----------------------
        if msg.event == "END_GRAMMAR":
            # Mark end state
            state.mark_end_grammar(msg.end_of_speech_time)

            # Assemble full text
            full_text = state.assemble_full_text()

            # Apply full tone transformation
            toned = self.tone_transformer._tone_transform(full_text)

            # Ensure final text ends with a period
            # (Safe UI formatting, not grammar correction)
            if not toned.endswith("."):
                toned += "."

            # Compute final latency
            latency_ms = LatencyLogger.compute_latency(msg.end_of_speech_time)
            LatencyLogger.log("Final Tone Stage", latency_ms)


            final_msg = PipelineMessage(
                id=msg.id,
                chunk_index=0,
                text=toned,
                event="END_TONE",
                is_final=True,
                end_of_speech_time=msg.end_of_speech_time,
            )

            # Cleanup: free memory for this utterance
            del self.state_by_id[msg.id]

            return final_msg

        # ----------------------
        # Any other event → ignore
        # ----------------------
        return None

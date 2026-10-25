from config import WINDOW_SEC, OVERLAP_SEC

   # Fixed time-window chunking: segments are grouped into windows of about
   # WINDOW_SEC seconds, each chunk tagged with its start/end timestamp.
   # With overlap_sec > 0, each new chunk also starts with the segments from
   # the last overlap_sec seconds of the previous one, so an idea that straddles
   # a boundary appears whole in at least one chunk.
def chunk_transcript(transcript, window_sec=WINDOW_SEC, overlap_sec=OVERLAP_SEC):
    if overlap_sec < 0 or overlap_sec >= window_sec:
        raise ValueError(f"overlap_sec must be >= 0 and smaller than window_sec ({window_sec}), got {overlap_sec}")
    if not transcript:
        return []
    chunks = []
    current, current_start = [], transcript[0]['start']
    for seg in transcript:
        if seg['start'] - current_start > window_sec and current:
            chunks.append({"text": " ".join(s['text'] for s in current), "start": current_start, "end": seg['start']})
            current = [s for s in current if s['start'] >= seg['start'] - overlap_sec] if overlap_sec > 0 else []
            current_start = current[0]['start'] if current else seg['start']
        current.append(seg)
    if current:
        last_end = transcript[-1]['start'] + transcript[-1].get('duration', 0.0)
        chunks.append({"text": " ".join(s['text'] for s in current), "start": current_start, "end": last_end})
    return chunks

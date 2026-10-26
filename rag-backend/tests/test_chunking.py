import pytest
from chunking import chunk_transcript


def seg(text, start):
    return {"text": text, "start": start, "duration": 2.0}


def test_short_transcript_makes_one_chunk():
    chunks = chunk_transcript([seg("a", 0), seg("b", 10), seg("c", 20)], window_sec=40)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "a b c"
    assert chunks[0]["start"] == 0


def test_splits_when_window_is_exceeded():
    t = [seg("a", 0), seg("b", 30), seg("c", 41), seg("d", 50)]
    chunks = chunk_transcript(t, window_sec=40)
    assert [c["text"] for c in chunks] == ["a b", "c d"]


def test_segment_exactly_at_boundary_stays_in_chunk():
    assert len(chunk_transcript([seg("a", 0), seg("b", 40)], window_sec=40)) == 1


def test_no_text_is_lost_across_chunks():
    t = [seg(str(i), i * 7) for i in range(50)]
    chunks = chunk_transcript(t, window_sec=40)
    assert " ".join(c["text"] for c in chunks).split() == [str(i) for i in range(50)]


def test_chunk_start_is_not_after_end():
    t = [seg(str(i), i * 7) for i in range(50)]
    for c in chunk_transcript(t, window_sec=40):
        assert c["start"] <= c["end"]


def test_empty_transcript_returns_no_chunks():
    assert chunk_transcript([]) == []


def test_single_segment_has_positive_duration_matching_duration():
    chunks = chunk_transcript([seg("hello", 10.0)], window_sec=40)
    assert len(chunks) == 1
    assert chunks[0]["start"] == 10.0
    assert chunks[0]["end"] == 12.0

def test_zero_overlap_matches_no_overlap():
    t = [seg(str(i), i * 7) for i in range(50)]
    assert chunk_transcript(t, window_sec=40, overlap_sec=0) == chunk_transcript(t, window_sec=40)


def test_overlap_repeats_boundary_segments_in_next_chunk():
    t = [seg("a", 0), seg("b", 30), seg("c", 35), seg("d", 41), seg("e", 50)]
    chunks = chunk_transcript(t, window_sec=40, overlap_sec=10)
    # the window closes at 41: "c" (35) is within the last 10s, "b" (30) is not
    assert [c["text"] for c in chunks] == ["a b c", "c d e"]
    assert chunks[1]["start"] == 35


def test_segment_exactly_overlap_sec_before_boundary_is_carried():
    t = [seg("a", 0), seg("b", 31), seg("c", 41)]
    chunks = chunk_transcript(t, window_sec=40, overlap_sec=10)
    assert [c["text"] for c in chunks] == ["a b", "b c"]


def test_overlap_keeps_every_segment_in_order():
    t = [seg(str(i), i * 7) for i in range(50)]
    chunks = chunk_transcript(t, window_sec=40, overlap_sec=10)
    assert len(chunks) > 1
    words = []
    for c in chunks:
        for w in c["text"].split():
            if not words or int(w) > int(words[-1]):
                words.append(w)
    assert words == [str(i) for i in range(50)]


def test_overlapping_chunks_start_before_previous_end():
    t = [seg(str(i), i * 7) for i in range(50)]
    chunks = chunk_transcript(t, window_sec=40, overlap_sec=10)
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt["start"] < prev["end"]
        assert nxt["start"] <= nxt["end"]


def test_gap_longer_than_overlap_carries_nothing():
    t = [seg("a", 0), seg("b", 5), seg("c", 100)]
    chunks = chunk_transcript(t, window_sec=40, overlap_sec=10)
    assert [c["text"] for c in chunks] == ["a b", "c"]


@pytest.mark.parametrize("overlap", [40, 55, -1])
def test_invalid_overlap_raises(overlap):
    with pytest.raises(ValueError):
        chunk_transcript([seg("a", 0)], window_sec=40, overlap_sec=overlap)

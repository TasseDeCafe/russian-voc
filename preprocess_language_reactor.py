#!/usr/bin/env python3
"""
Preprocess vocabulary CSV exports from YouTube subtitle extensions.

Supports:
- Language Reactor exports (old format with WORD| prefix)
- Simpler CSV exports (word, sentence, timestamp, videoTitle, videoId)

This script:
1. Parses the export and detects the format
2. Extracts the video ID and fetches the transcript
3. Outputs a preprocessed CSV ready for cleanup

Usage:
    python preprocess_language_reactor.py export.csv -o preprocessed.csv

Requirements:
    pip install youtube-transcript-api
"""

import argparse
import csv
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False


def detect_format(filepath: Path) -> str:
    """Detect the CSV format based on content."""
    with open(filepath, encoding="utf-8") as f:
        first_line = f.readline().strip()

        # Check for simple CSV header
        if first_line.startswith("word,"):
            return "simple"

        # Check for Language Reactor format
        if "WORD|" in first_line:
            return "language_reactor"

        # Try to detect by reading more
        f.seek(0)
        content = f.read(1000)
        if "WORD|" in content:
            return "language_reactor"

    # Default to simple if has comma-separated header
    return "simple"


def parse_simple_csv(filepath: Path) -> tuple[list[dict], str | None]:
    """Parse simple CSV format (word, sentence, timestamp, videoTitle, videoId).

    Returns:
        Tuple of (entries, video_id)
    """
    entries = []
    video_id = None

    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            word = row.get("word", "").strip()
            sentence = row.get("sentence", "").strip()
            vid = row.get("videoId", "").strip()

            if video_id is None and vid:
                video_id = vid

            if word:
                # Check if it's a multi-word chunk (collocation)
                is_chunk = " " in word

                entry = {
                    "lemma": word,
                    "word_form": word,
                    "pos": "",
                    "translation": "",  # Not provided in this format
                    "context_ru": sentence,
                    "context_en": "",  # Not provided in this format
                    "is_chunk": is_chunk,
                }
                entries.append(entry)

    return entries, video_id


def parse_language_reactor_export(filepath: Path) -> tuple[list[dict], str | None]:
    """Parse Language Reactor export file.

    Returns:
        Tuple of (entries, video_id)
    """
    entries = []
    video_id = None

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("WORD|"):
                continue

            fields = line.split("\t")
            if len(fields) < 9:
                continue

            # Parse the WORD|lemma|lang prefix
            prefix_parts = fields[0].split("|")
            if len(prefix_parts) < 2:
                continue

            lemma = prefix_parts[1]

            # Extract video ID (field 15, format: yt_VIDEOID)
            if video_id is None and len(fields) > 15:
                vid_field = fields[15]
                if vid_field.startswith("yt_"):
                    video_id = vid_field[3:]  # Remove "yt_" prefix

            entry = {
                "lemma": lemma,
                "word_form": fields[4] if len(fields) > 4 else lemma,
                "pos": fields[6] if len(fields) > 6 else "",
                "translation": fields[8].strip('"') if len(fields) > 8 else "",
                "context_ru": fields[2].strip('"') if len(fields) > 2 else "",
                "context_en": fields[3].strip('"') if len(fields) > 3 else "",
                "is_chunk": False,
            }

            if entry["lemma"] and (entry["translation"] or entry["context_ru"]):
                entries.append(entry)

    return entries, video_id


def fetch_transcript(video_id: str, lang: str = "ru") -> str | None:
    """Fetch YouTube transcript using youtube-transcript-api."""
    if not HAS_TRANSCRIPT_API:
        print("  Warning: youtube-transcript-api not installed.")
        print("  Install with: pip install youtube-transcript-api")
        return None

    try:
        api = YouTubeTranscriptApi()

        # List available transcripts
        transcript_list = api.list(video_id)

        # Try manual transcript first, then auto-generated
        transcript = None
        try:
            transcript = transcript_list.find_transcript([lang])
        except NoTranscriptFound:
            # Try auto-generated
            try:
                transcript = transcript_list.find_generated_transcript([lang])
            except NoTranscriptFound:
                pass

        if transcript:
            entries = transcript.fetch()
            # Join all text entries
            text = "\n".join(entry.text for entry in entries)
            return text

    except TranscriptsDisabled:
        print(f"  Warning: Transcripts are disabled for video {video_id}")
    except VideoUnavailable:
        print(f"  Warning: Video {video_id} is unavailable")
    except Exception as e:
        print(f"  Warning: Could not fetch transcript: {e}")

    return None


def write_preprocessed_csv(entries: list[dict], output_path: Path):
    """Write preprocessed entries to a CSV file."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Word", "Translation", "Context (RU)", "Context (EN)", "POS", "Is Chunk"])

        for entry in entries:
            writer.writerow([
                entry["lemma"],
                entry.get("translation", ""),
                entry.get("context_ru", ""),
                entry.get("context_en", ""),
                entry.get("pos", ""),
                "yes" if entry.get("is_chunk") else "",
            ])


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess vocabulary CSV exports from YouTube subtitle extensions."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Export CSV file",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("preprocessed.csv"),
        help="Output CSV file (default: preprocessed.csv)",
    )
    parser.add_argument(
        "--no-transcript",
        action="store_true",
        help="Skip fetching the transcript",
    )
    parser.add_argument(
        "--lang",
        default="ru",
        help="Subtitle language code (default: ru)",
    )

    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: {args.input_file} not found")
        return 1

    # Detect format
    fmt = detect_format(args.input_file)
    print(f"Detected format: {fmt}")

    # Parse based on format
    print(f"Parsing {args.input_file}...")
    if fmt == "simple":
        entries, video_id = parse_simple_csv(args.input_file)
    else:
        entries, video_id = parse_language_reactor_export(args.input_file)

    print(f"Found {len(entries)} word entries")

    # Count chunks
    chunks = sum(1 for e in entries if e.get("is_chunk"))
    if chunks:
        print(f"  Including {chunks} multi-word chunks (collocations)")

    if video_id:
        print(f"Video ID: {video_id}")
        print(f"Video URL: https://www.youtube.com/watch?v={video_id}")

    # Write preprocessed CSV
    write_preprocessed_csv(entries, args.output)
    print(f"Wrote preprocessed data to {args.output}")

    # Fetch transcript
    transcript_path = args.output.with_suffix(".transcript.txt")
    if not args.no_transcript and video_id:
        print(f"\nFetching transcript from YouTube...")
        transcript = fetch_transcript(video_id, args.lang)
        if transcript:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"Wrote transcript to {transcript_path}")
        else:
            print("  Could not fetch transcript")
    elif not video_id:
        print("\nNo video ID found in export, skipping transcript fetch")

    print("\n" + "=" * 60)
    print("Next step: Ask Claude to clean up the preprocessed file.")
    print("")
    print("Notes for cleanup:")
    print("  - Chunks marked 'Is Chunk=yes' should be kept as collocations")
    print("  - Convert chunks to nominative form if needed")
    print("  - Add translations (not provided in simple CSV format)")
    if transcript_path.exists():
        print(f"  - Transcript available at: {transcript_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())

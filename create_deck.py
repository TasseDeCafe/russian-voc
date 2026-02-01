#!/usr/bin/env python3
"""
Create an Anki deck from Russian vocabulary CSV files.

Usage:
    python create_deck.py *.csv -o russian.apkg
    python create_deck.py vocab1.csv vocab2.csv -o russian.apkg
    python create_deck.py --mode recognition passive_vocab.csv -o passive.apkg
"""

import argparse
import csv
import hashlib
from pathlib import Path

import genanki


# Fixed IDs ensure cards merge into the same deck on re-import
DECK_ID_PRODUCTION = 1635890001
DECK_ID_RECOGNITION = 1635890003
MODEL_ID_PRODUCTION = 1635890002
MODEL_ID_RECOGNITION = 1635890004

CSS = """
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
    .russian {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .translation {
        font-size: 22px;
        color: #333;
        margin: 15px 0;
    }
    .example {
        margin-top: 20px;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 5px;
    }
    .example-ru {
        font-size: 18px;
        color: #444;
        margin-bottom: 5px;
    }
    .example-trans {
        font-size: 16px;
        color: #666;
        font-style: italic;
    }
"""

# Production mode: English front, Russian back (harder active recall)
PRODUCTION_MODEL = genanki.Model(
    MODEL_ID_PRODUCTION,
    "Russian Vocabulary (Production)",
    fields=[
        {"name": "Russian"},
        {"name": "Translation"},
        {"name": "Example"},
        {"name": "ExampleTranslation"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": """
                <div class="translation">{{Translation}}</div>
                {{#ExampleTranslation}}
                <div class="example">
                    <div class="example-trans">{{ExampleTranslation}}</div>
                </div>
                {{/ExampleTranslation}}
            """,
            "afmt": """
                <div class="translation">{{Translation}}</div>
                <hr id="answer">
                <div class="russian">{{Russian}}</div>
                {{#Example}}
                <div class="example">
                    <div class="example-ru">{{Example}}</div>
                </div>
                {{/Example}}
            """,
        },
    ],
    css=CSS,
)

# Recognition mode: Russian front, English back (passive vocabulary)
RECOGNITION_MODEL = genanki.Model(
    MODEL_ID_RECOGNITION,
    "Russian Vocabulary (Recognition)",
    fields=[
        {"name": "Russian"},
        {"name": "Translation"},
        {"name": "Example"},
        {"name": "ExampleTranslation"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": """
                <div class="russian">{{Russian}}</div>
                {{#Example}}
                <div class="example">
                    <div class="example-ru">{{Example}}</div>
                </div>
                {{/Example}}
            """,
            "afmt": """
                <div class="russian">{{Russian}}</div>
                <hr id="answer">
                <div class="translation">{{Translation}}</div>
                {{#ExampleTranslation}}
                <div class="example">
                    <div class="example-trans">{{ExampleTranslation}}</div>
                </div>
                {{/ExampleTranslation}}
            """,
        },
    ],
    css=CSS,
)


def generate_guid(russian_word: str, mode: str) -> str:
    """Generate a stable GUID based on the Russian word and mode."""
    key = f"{mode}:{russian_word}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:10]


def read_csv(filepath: Path) -> list[dict]:
    """Read a vocabulary CSV file."""
    entries = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                entry = {
                    "russian": row[0].strip(),
                    "translation": row[1].strip() if len(row) > 1 else "",
                    "example": row[2].strip() if len(row) > 2 else "",
                    "example_translation": row[3].strip() if len(row) > 3 else "",
                    "tags": row[4].strip().split() if len(row) > 4 and row[4].strip() else [],
                }
                if entry["russian"]:
                    entries.append(entry)
    return entries


def create_deck(
    csv_files: list[Path],
    output_path: Path,
    deck_name: str,
    mode: str,
) -> int:
    """Create an Anki deck from CSV files."""
    if mode == "production":
        deck_id = DECK_ID_PRODUCTION
        model = PRODUCTION_MODEL
    else:
        deck_id = DECK_ID_RECOGNITION
        model = RECOGNITION_MODEL

    deck = genanki.Deck(deck_id, deck_name)

    all_entries = []
    for csv_file in csv_files:
        entries = read_csv(csv_file)
        all_entries.extend(entries)
        print(f"  {csv_file.name}: {len(entries)} entries")

    # Deduplicate by Russian word (keep last occurrence)
    seen = {}
    for entry in all_entries:
        seen[entry["russian"]] = entry
    unique_entries = list(seen.values())

    for entry in unique_entries:
        note = genanki.Note(
            model=model,
            fields=[
                entry["russian"],
                entry["translation"],
                entry["example"],
                entry["example_translation"],
            ],
            guid=generate_guid(entry["russian"], mode),
            tags=entry.get("tags", []),
        )
        deck.add_note(note)

    genanki.Package(deck).write_to_file(output_path)
    return len(unique_entries)


def main():
    parser = argparse.ArgumentParser(
        description="Create an Anki deck from Russian vocabulary CSV files."
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        type=Path,
        help="CSV files to process",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("russian.apkg"),
        help="Output .apkg file (default: russian.apkg)",
    )
    parser.add_argument(
        "-n", "--name",
        default=None,
        help="Deck name (default: 'Russian Vocabulary' for production, 'Russian Passive Vocabulary' for recognition)",
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["production", "recognition"],
        default="production",
        help="Card mode: 'production' (EN front, RU back) or 'recognition' (RU front, EN back). Default: production",
    )

    args = parser.parse_args()

    # Set default deck name based on mode
    if args.name is None:
        if args.mode == "production":
            args.name = "Russian Vocabulary"
        else:
            args.name = "Russian Passive Vocabulary"

    # Validate input files
    for csv_file in args.csv_files:
        if not csv_file.exists():
            print(f"Error: {csv_file} not found")
            return 1

    mode_desc = "EN→RU" if args.mode == "production" else "RU→EN"
    print(f"Creating deck '{args.name}' ({mode_desc})...")
    count = create_deck(args.csv_files, args.output, args.name, args.mode)
    print(f"Created {args.output} with {count} cards")
    return 0


if __name__ == "__main__":
    exit(main())

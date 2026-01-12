# Russian Vocabulary

A personal Russian vocabulary learning project for Anki flashcards, built from Google Sheets notes, language exchange sessions, and YouTube subtitle learning.

## Setup

```bash
pip install -r requirements.txt
```

## Creating Anki Decks

### Production Mode (Active Recall)

For words you've actively practiced (lessons, exchanges) — English front, Russian back:

```bash
python3 create_deck.py *.csv -o russian.apkg
```

Or specify files:

```bash
python3 create_deck.py "Russian vocab - Sheet1.csv" "Language Exchange with Genia - Russian.csv" -o russian.apkg
```

### Recognition Mode (Passive Vocabulary)

For words from YouTube/reading (Language Reactor) — Russian front, English back:

```bash
python3 create_deck.py --mode recognition language-reactor-shevtsov.csv -o passive.apkg
```

### Options

- `-o, --output`: Output file path (default: `russian.apkg`)
- `-n, --name`: Deck name in Anki (default: "Russian Vocabulary")
- `-m, --mode`: Card mode — `production` (EN→RU) or `recognition` (RU→EN)

Re-importing the same file updates existing cards without duplicates.

## Card Formats

| Mode | Front | Back | Use Case |
|------|-------|------|----------|
| `production` | English + example translation | Russian + example | Active recall (lessons, exchanges) |
| `recognition` | Russian + example | English + translation | Passive vocabulary (YouTube, reading) |

## CSV Structure

Each vocabulary CSV file has 4 columns:

| Column | Description |
|--------|-------------|
| 1 | Russian word/phrase (with stress marks on multisyllabic words) |
| 2 | Translation (English or French) |
| 3 | Example sentence in Russian |
| 4 | Translation of the example sentence |

**Important**: Wrap fields containing commas in double quotes.

## Examples

The `examples/` directory contains sample files for each workflow:

| Type | Raw/Input | Cleaned Output |
|------|-----------|----------------|
| Exchange | `exchange-raw.csv` | `exchange-cleaned.csv` |
| Lesson | `lesson-raw.csv` | `lesson-cleaned.csv` |
| Language Reactor | `language-reactor-preprocessed.csv` | `language-reactor-cleaned.csv` |

## Cleaning Up Language Exchange Notes

After a language exchange session, export your rough notes as CSV and clean them up:

1. **Create full sentences**: Turn fragments into complete example sentences
2. **Keep collocations together**: Phrases like `физи́ческое наси́лие` or `о́пыт вожде́ния` should stay as single entries
3. **Use verb pairs**: Format as `imperfective/perfective` (e.g., `ви́деть/уви́деть`)
4. **Add stress marks**: Only in column 1, on multisyllabic words
5. **Quote commas**: Any field with a comma needs double quotes

See `examples/exchange-raw.csv` → `examples/exchange-cleaned.csv`

## Cleaning Up Language Reactor Exports

For words saved from YouTube with Language Reactor:

### Step 1: Preprocess the raw export

```bash
python3 preprocess_language_reactor.py raw_export.csv -o preprocessed.csv
```

This will:
- Extract word, translation, context (RU/EN), and part of speech
- Automatically fetch the YouTube transcript via `youtube-transcript-api`
- Output both `preprocessed.csv` and `preprocessed.transcript.txt`

### Step 2: Clean up with Claude

Ask Claude to clean up the preprocessed file. Claude will:
- Read both the preprocessed CSV and the transcript
- Identify collocations from context
- Create simpler example sentences
- Add stress marks
- Output final 4-column format

### Step 3: Generate recognition deck

```bash
python3 create_deck.py --mode recognition cleaned.csv -o passive.apkg
```

### Collocation Examples

Language Reactor saves single words, but some should be studied together:
- `птичий` → `на пти́чьих права́х` (on precarious terms)
- `поразить` → `пораже́ны в права́х` (disenfranchised)
- `острый` → `о́стрые углы́` (sharp edges)

See `examples/` for sample preprocessed, transcript, and cleaned files.

## Stress Mark Tips

- Use the combining acute accent: `́` (U+0301) placed after the vowel
- On macOS: Option + E, then the vowel
- Common stressed vowels: `а́ е́ и́ о́ у́ ы́ э́ ю́ я́`
- Skip stress marks for:
  - Monosyllabic words (e.g., `да`, `нет`, `шерсть`)
  - Words containing `ё` (always stressed)

## Importing from Google Sheets

1. Export your Google Sheet as CSV (File > Download > CSV)
2. Add the CSV file to this directory
3. Clean up the data following the structure above
4. Regenerate the Anki deck

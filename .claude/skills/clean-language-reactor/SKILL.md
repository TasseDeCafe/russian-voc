---
name: clean-language-reactor
description: Clean up Russian vocabulary CSV exports from Language Reactor (YouTube subtitle learning extension). Use when the user asks to process or clean up a Language Reactor CSV file.
---

# Clean Language Reactor Exports

Transform Language Reactor CSV exports into vocabulary flashcards for recognition practice.

## Workflow

1. **Preprocess** the raw Language Reactor export:
   ```bash
   python preprocess_language_reactor.py export.csv -o preprocessed.csv
   ```
   This will:
   - Parse the export and extract word data
   - Automatically fetch the YouTube transcript
   - Output `preprocessed.csv` and `preprocessed.transcript.txt`

2. **Clean up** the preprocessed file (with Claude):
   - Read both the preprocessed CSV and the transcript
   - Identify collocations from context
   - Create simpler example sentences
   - Add stress marks
   - Output the final 4-column CSV

## Examples

See the `examples/` directory:
- **Preprocessed input**: `examples/language-reactor-preprocessed.csv`
- **Transcript**: `examples/language-reactor-preprocessed.transcript.txt`
- **Cleaned output**: `examples/language-reactor-cleaned.csv`

## Card Purpose

These cards are for **recognition** (passive vocabulary), not production:
- **Front**: Russian word + example sentence
- **Back**: English translation

Use `--mode recognition` when creating the deck:
```bash
python create_deck.py --mode recognition cleaned.csv -o passive.apkg
```

## CSV Output Format

4 columns, comma-separated:

| Column | Content |
|--------|---------|
| 1 | Russian word/phrase with stress marks |
| 2 | English translation |
| 3 | Example sentence in Russian |
| 4 | English translation of example |

## Processing Rules

### 1. Read Both Files

When cleaning up, read:
- The preprocessed CSV (word, translation, context, POS)
- The transcript file (full video text for understanding context)

### 2. Identify Collocations

Language Reactor only allows clicking single words, but some should be studied together. Use the transcript to identify:
- `птичий` → `на пти́чьих права́х` (on precarious terms)
- `поразить` → `пораже́ны в права́х` (disenfranchised)
- `острый` → `о́стрые углы́` (sharp edges)

### 3. Create Simpler Example Sentences

The subtitle context is often:
- Incomplete (cut off mid-sentence)
- Too long or complex for flashcards
- Contains multiple clauses

Create a **simpler, clearer sentence** that:
- Uses the word with the same meaning as in the video
- Is short enough for a flashcard (under 15 words ideally)
- Is grammatically complete

Use the full transcript to understand the meaning and context.

### 4. Stress Marks (Column 1 Only)

- Add stress mark (´) on the stressed vowel for multisyllabic words
- Skip monosyllables
- Skip words with ё (always stressed)

### 5. CSV Quoting

Wrap any field containing commas in double quotes.

## Example Transformation

**Preprocessed** (from `examples/language-reactor-preprocessed.csv`):
```csv
Word,Translation,Context (RU),Context (EN),POS
птичий,"bird's, avian",Пока у тебя нет гражданства ты всегда на птичьих правах,Until you have citizenship you're always on precarious terms,Adj
```

**Cleaned output** (see `examples/language-reactor-cleaned.csv`):
```
на пти́чьих права́х,on precarious terms (no legal rights),Без гражданства ты на птичьих правах.,Without citizenship you're on precarious terms.
```

Note: The single word `птичий` became the collocation `на пти́чьих права́х` because that's how it was used in context.

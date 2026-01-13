Configuration files

- `config/app_config.json` (single source of truth)

Schema (high level):

- `ocr`
  - `mode`: "local" | "ai" (controls OCR flow)
  - `confidence_threshold`: float (0-1) threshold for local OCR

- `models`
  - `selected`: string (name of the selected model)
  - `available`: array of {name, type, provider}

- `image`
  - `max_width`: integer (max pixel width for stored images)
  - `quality`: integer (0-100, used for JPEG fallback)

- `security`
  - `keys_path`: optional override for encrypted keys location (if empty, uses %APPDATA%/YourApp/keys.enc)

Notes:
- Do not duplicate model definitions in other files. The GUI reads and writes only to `config/app_config.json`.
- `config/symbols.json` contains symbol rules applied before any AI processing.
- `context/index.json` stores lightweight context (subjects/topics/links) used by the app.

Security:
- API keys are encrypted at rest. Do not commit keys to Git.

Autonomy & Determinism:
- The app avoids randomness. Same inputs produce same outputs when config is unchanged.

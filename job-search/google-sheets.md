# Job Search - Google Sheets Integration

## Sheet Configuration
- **Sheet ID:** `1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E`
- **Tab Name:** `AI Search Bot Result`
- **Columns:**
  1. LinkedIn URL
  2. Job Posted Date
  3. Job Title
  4. Company
  5. Job Category
  6. Location
  7. Interest
  8. Notes
  9. Days Ago

## API Access

### Option 1: Google Sheets API (Recommended)
1. Enable Google Sheets API:
   - Go to: https://console.developers.google.com/apis/api/sheets.googleapis.com
   - Select project: `292822285512`
   - Click "Enable"

2. Use with API key:
   ```
   GET https://sheets.googleapis.com/v4/spreadsheets/{sheetId}/values/{tabName}?key={API_KEY}
   ```

### Option 2: Share Publicly (Easiest)
1. Open the sheet in Google Sheets
2. Click "Share" → "Publish to web"
3. Select "Sheet: AI Search Bot Result"
4. Copy the publish URL and use web_fetch

### Option 3: gog CLI
- Ensure gog is authenticated: `gog auth list`
- Use: `gog sheets append <sheetId> "Tab!A:Z" --values-json '[[...]]'`

## Skill
- See: `../skills/google-sheets/SKILL.md`

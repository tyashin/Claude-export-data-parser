# Claude Export Parser

A Python tool that converts Claude's exported data files (conversations, projects, and users) into a well-organized, browseable markdown archive. The parser automatically detects file types and creates a comprehensive documentation structure with proper navigation and cross-references.

## Features

- **Smart File Detection**: Automatically identifies conversations, projects, and users files by filename
- **Flexible Input**: Works with any combination of the three file types
- **Rich Organization**: Creates a hierarchical structure with projects, conversations, and metadata
- **Full Content Preservation**: Maintains all conversations, project documents, and metadata
- **Easy Navigation**: Generates indexes, cross-references, and a central README
- **Clean Formatting**: Handles code blocks, formatting, and special characters properly

## How to Export Data from Claude

### Step 1: Access Claude Settings
1. Go to [claude.ai](https://claude.ai)
2. Click on your profile/Settings/Privacy
3. Look for "Export Data" option and click it

### Step 2: Export Your Data
1. Request the export
2. Check your email for a message from Claude with a "Download data" link
3. Click the download link to get the ZIP file containing your JSON exports

### Step 3: Extract Files
Extract the downloaded ZIP file. You should have files like:
- `conversations.json` - Your chat history
- `projects.json` - Project data and documents
- `users.json` - Account information

## Installation

No special installation required! The script uses only Python standard library modules.

**Requirements:**
- Python 3.6 or higher
- No additional packages needed

## Usage

### Basic Usage

The script automatically detects file types based on filenames:

```bash
# All three files (any order works)
python claude_complete_parser.py conversations.json projects.json users.json

# Files can be in any order
python claude_complete_parser.py users.json conversations.json projects.json

# Use wildcards
python claude_complete_parser.py *.json
```

### Partial Exports

You can run the script with any subset of files:

```bash
# Only conversations
python claude_complete_parser.py conversations.json

# Conversations + projects (no user info)
python claude_complete_parser.py conversations.json projects.json

# Conversations + users (no projects)
python claude_complete_parser.py conversations.json users.json
```

### Custom Output Directory

```bash
# Specify output directory
python claude_complete_parser.py *.json -o my_claude_archive

# With specific files
python claude_complete_parser.py conversations.json projects.json -o backup_2024
```

## Output Structure

The script creates a comprehensive archive:

```
claude_complete_export/
├── README.md                    # Main entry point with overview
├── projects/                    # Project folders
│   ├── project_name_1/
│   │   ├── project_info.md     # Project details and metadata
│   │   └── docs/               # Project documents
│   │       ├── document1.md
│   │       └── document2.md
│   └── project_name_2/
│       └── project_info.md
├── conversations/               # All conversations
│   ├── project_conversations/  # (Reserved for future use)
│   └── standalone_conversations/
│       ├── conversation1.md
│       ├── conversation2.md
│       └── ...
└── metadata/                   # Navigation and indexes
    ├── projects_index.md       # Complete projects list
    ├── conversations_index.md  # Complete conversations list
    └── user_info.md           # Account information
```

## File Type Detection

The script identifies files by checking if the filename contains:
- `conversation` → Conversations data
- `project` → Projects data  
- `user` → User data

Examples of supported filenames:
- `conversations.json` ✓
- `my_claude_conversations.json` ✓
- `exported_projects.json` ✓
- `user_data.json` ✓
- `claude_backup.json` ✗ (ambiguous - will be skipped)

## What's Generated

### Main README.md
- User information summary
- Statistics overview (total projects, conversations, messages)
- Date range of activity
- Quick access to recent conversations
- Navigation links to all sections

### Project Structure
Each project gets:
- Detailed project information (description, dates, settings)
- Creator information
- All uploaded documents converted to markdown
- Document index with creation dates

### Conversation Files
Each conversation includes:
- Full message history (human and assistant)
- Conversation metadata (creation/update dates, IDs)
- Proper formatting with timestamps
- Clean handling of code blocks and special content

### Metadata Indexes
- **Projects Index**: Complete list with descriptions and document counts
- **Conversations Index**: All conversations with summaries and dates
- **User Info**: Account details and contact information

## Example Output

Running the script will show progress:

```
Claude Complete Export Parser (Smart Detection)
==================================================
Loading conversations.json...
✓ Detected conversations file: 150 conversations
Loading projects.json...
✓ Detected projects file: 12 projects
Loading users.json...
✓ Detected users file: 1 users

Summary:
- Conversations: 150
- Projects: 12
- Users: 1

============================================================
CLAUDE EXPORT SUMMARY
============================================================
Users: 1
Projects: 12
  - Project documents: 45
Conversations: 150
  - Total messages: 3,247
============================================================

Exporting complete Claude archive to: claude_complete_export
============================================================
Created project: Web Scraper
Created project: Recommendation System
...
Created 150 conversation files
Created metadata files
Created main README: claude_complete_export/README.md
============================================================
Export complete! Archive created in: claude_complete_export
Start by opening: claude_complete_export/README.md
```

## Troubleshooting

### File Not Found Errors
```bash
Warning: File not found: projects.json - skipping
```
This is normal if you don't have all three file types. The script will continue with available files.

### Unknown File Type
```bash
? Unknown file type: my_data.json (filename doesn't contain 'conversation', 'project', or 'user') - skipping
```
Rename your file to include one of the keywords: `conversation`, `project`, or `user`.

### No Conversations Found
```bash
Error: No conversations file found!
Make sure at least one filename contains 'conversation' (e.g., conversations.json)
```
The script requires at least one conversations file to run. Projects and users are optional.

### JSON Parsing Errors
```bash
✗ JSON parsing error in conversations.json: Expecting ',' delimiter
```
The JSON file is corrupted or incomplete. Try re-exporting from Claude.

## Limitations

- **No Project-Conversation Links**: Claude's export format doesn't include explicit relationships between conversations and projects, so all conversations are placed in `standalone_conversations/`
- **File Size**: Very large exports (1000+ conversations) may take several minutes to process
- **Encoding**: Designed for UTF-8 text; binary content in documents may not display properly

## Tips

1. **Start with README.md**: Always begin browsing your archive from the main README.md file
2. **Use Search**: Most markdown viewers and editors support text search across files
3. **Regular Exports**: Export your data regularly to avoid losing conversations
4. **Backup**: Keep the original JSON files as backup alongside the generated markdown
5. **Version Control**: Consider using git to track changes between exports

## Contributing

The script is designed to be self-contained and easy to modify. Key areas for enhancement:
- Heuristic matching of conversations to projects
- Support for additional export formats
- Enhanced content analysis and tagging
- Custom formatting options

## License

This tool is provided as-is for personal use in organizing your Claude export data.

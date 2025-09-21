#!/usr/bin/env python3
"""
Claude Complete Export Parser - Refactored Version
Integrates conversations.json, projects.json, and users.json into a unified markdown structure
Uses filename analysis to automatically detect file types
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ClaudeCompleteParser:
    def __init__(self, file_paths: List[str]):
        self.file_paths = [Path(p) for p in file_paths]

        self.conversations = []
        self.projects = []
        self.users = []

        # Track which conversations are in projects
        self.conversation_to_project = {}
        self.project_conversations = set()

    def detect_file_type(self, file_path: Path) -> str:
        """Detect the type of Claude export file by analyzing filename"""
        filename = file_path.name.lower()

        if 'conversation' in filename:
            return "conversations"
        elif 'project' in filename:
            return "projects"
        elif 'user' in filename:
            return "users"
        else:
            return "unknown"

    def load_data(self):
        """Load and parse JSON files with automatic filename-based type detection"""
        conversations_found = False

        for file_path in self.file_paths:
            if not file_path.exists():
                print(f"Warning: File not found: {file_path} - skipping")
                continue

            file_type = self.detect_file_type(file_path)

            try:
                print(f"Loading {file_path}...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if file_type == "conversations":
                    self.conversations = data
                    conversations_found = True
                    print(f"✓ Detected conversations file: {len(data)} conversations")

                elif file_type == "projects":
                    self.projects = data
                    print(f"✓ Detected projects file: {len(data)} projects")

                elif file_type == "users":
                    self.users = data
                    print(f"✓ Detected users file: {len(data)} users")

                else:
                    print(
                        f"? Unknown file type: {file_path} (filename doesn't contain 'conversation', 'project', or 'user') - skipping")

            except json.JSONDecodeError as e:
                print(f"✗ JSON parsing error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"✗ Error loading {file_path}: {e}")
                continue

        # Conversations are required
        if not conversations_found:
            print("\nError: No conversations file found!")
            print("Make sure at least one filename contains 'conversation' (e.g., conversations.json)")
            sys.exit(1)

        print(f"\nSummary:")
        print(f"- Conversations: {len(self.conversations)}")
        print(f"- Projects: {len(self.projects)}")
        print(f"- Users: {len(self.users)}")

    def analyze_relationships(self):
        """Analyze relationships between conversations and projects"""
        # Note: Based on the data structure, there doesn't appear to be explicit 
        # conversation-to-project mappings in the JSON files.
        # This would need to be determined by other means (naming, timing, etc.)
        # For now, we'll organize by creation date and provide a clear structure

        # We can potentially match conversations to projects by:
        # 1. Timestamp proximity
        # 2. Similar names/topics
        # 3. Manual categorization

        pass

    def format_date(self, date_string: str) -> str:
        """Format ISO date string to readable format"""
        if not date_string:
            return "Unknown date"

        try:
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'

            dt = datetime.fromisoformat(date_string)
            return dt.strftime("%B %d, %Y at %I:%M %p %Z")
        except:
            return date_string

    def safe_filename(self, text: str, max_length: int = 100) -> str:
        """Convert text to safe filename"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', text)
        filename = re.sub(r'[^\w\s\-_.]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('_')

        if len(filename) > max_length:
            filename = filename[:max_length].rstrip('_')

        return filename or "untitled"

    def extract_message_text(self, content_array: List[Dict]) -> str:
        """Extract text from message content array"""
        text_parts = []

        for content_item in content_array:
            if content_item.get('type') == 'text':
                text = content_item.get('text', '')
                if text:
                    text_parts.append(text)

        return '\n'.join(text_parts)

    def format_message_content(self, message: Dict) -> str:
        """Format a single message's content"""
        # First try the direct 'text' field (which exists in the JSON)
        if 'text' in message and message['text']:
            return message['text'].strip()

        # Fallback to content array extraction
        content = message.get('content', [])
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, list):
            return self.extract_message_text(content).strip()

        return ""

    def get_conversation_summary(self, conversation: Dict) -> str:
        """Generate a brief summary of the conversation"""
        messages = conversation.get('chat_messages', [])
        if not messages:
            return "No messages"

        message_count = len(messages)
        first_message = None

        # Find first human message
        for msg in messages:
            if msg.get('sender') == 'human':
                first_message = self.format_message_content(msg)
                break

        if first_message:
            # Clean the message for summary display
            # Remove code blocks, excessive whitespace, and markdown formatting
            clean_message = re.sub(r'```[\s\S]*?```', '[code block]', first_message)  # Remove code blocks
            clean_message = re.sub(r'`[^`]*`', '[code]', clean_message)  # Remove inline code
            clean_message = re.sub(r'\n+', ' ', clean_message)  # Replace newlines with spaces
            clean_message = re.sub(r'\s+', ' ', clean_message)  # Normalize whitespace
            clean_message = clean_message.strip()

            # Truncate to first 80 characters (shorter for better display)
            if len(clean_message) > 80:
                summary = clean_message[:80].rstrip() + "..."
            else:
                summary = clean_message

            return f"{message_count} messages - {summary}"

        return f"{message_count} messages"

    def get_conversation_display_name(self, conversation: Dict) -> str:
        """Get a proper display name for a conversation, handling empty names"""
        name = conversation.get('name', '').strip()

        # If name is empty or just whitespace, generate one from first message
        if not name:
            messages = conversation.get('chat_messages', [])
            if messages:
                # Find first human message with actual content
                for msg in messages:
                    if msg.get('sender') == 'human':
                        first_message = self.format_message_content(msg)
                        if first_message:
                            # Clean and truncate for name
                            clean_message = re.sub(r'```[\s\S]*?```', '[code block]', first_message)
                            clean_message = re.sub(r'`[^`]*`', '[code]', clean_message)
                            clean_message = re.sub(r'\n+', ' ', clean_message)
                            clean_message = re.sub(r'\s+', ' ', clean_message)
                            clean_message = clean_message.strip()

                            # Use first 50 characters as name
                            if len(clean_message) > 50:
                                name = clean_message[:50].rstrip() + "..."
                            else:
                                name = clean_message
                            break

            # If still no name found, create unique name using conversation ID
            if not name:
                conv_id = conversation.get('uuid', 'unknown')
                # Use last 8 characters of UUID for uniqueness
                short_id = conv_id[-8:] if len(conv_id) >= 8 else conv_id
                name = f"Untitled Conversation {short_id}"

        return name

    def create_readme(self, output_dir: Path) -> None:
        """Create the main README.md file"""
        # Header
        header_content = f"""# Claude Export - Complete Archive

Export generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

"""

        # User information section
        user_info_section = ""
        if self.users:
            user = self.users[0]  # Assuming single user
            user_uuid = user.get('uuid', 'Unknown')
            user_info_section = f"""## User Information

**Name:** {user.get('full_name', 'Unknown')}
**Email:** {user.get('email_address', 'Unknown')}
**User ID:** `{user_uuid}`

"""

        # Statistics section
        total_messages = sum(len(conv.get('chat_messages', [])) for conv in self.conversations)

        overview_section = f"""## Overview

- **Total Projects:** {len(self.projects)}
- **Total Conversations:** {len(self.conversations)}
- **Total Messages:** {total_messages}

"""

        # Date range
        date_range_section = ""
        dates = [conv.get('created_at', '') for conv in self.conversations if conv.get('created_at')]
        if dates:
            dates.sort()
            first_date = self.format_date(dates[0])
            last_date = self.format_date(dates[-1])
            date_range_section = f"""**Date Range:** {first_date} to {last_date}

"""

        # Archive structure (refactored to use multi-line string)
        structure_section = f"""## Archive Structure

This archive is organized as follows:

```
{output_dir.name}/
├── README.md (this file)
├── projects/
│   ├── [project_name]/
│   │   ├── project_info.md
│   │   └── docs/
│   │       └── [document_files]
├── conversations/
│   ├── project_conversations/
│   │   └── [conversation_files]
│   └── standalone_conversations/
│       └── [conversation_files]
└── metadata/
    ├── projects_index.md
    ├── conversations_index.md
    └── user_info.md
```

"""

        # Projects section
        projects_section = self._create_projects_section()

        # Recent conversations section
        recent_conversations_section = self._create_recent_conversations_section()

        # Navigation section
        navigation_section = """## Navigation

- [All Projects](metadata/projects_index.md)
- [All Conversations](metadata/conversations_index.md)
- [User Information](metadata/user_info.md)

"""

        # Combine all sections
        readme_content = (
                header_content +
                user_info_section +
                overview_section +
                date_range_section +
                structure_section +
                projects_section +
                recent_conversations_section +
                navigation_section
        )

        # Write README
        readme_path = output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"Created main README: {readme_path}")

    def _create_projects_section(self) -> str:
        """Create the projects section for the README"""
        section_lines = ["## Projects\n"]

        if self.projects:
            # Sort projects by creation date
            sorted_projects = sorted(
                self.projects,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            for project in sorted_projects:
                name = project.get('name', 'Untitled Project')
                description = project.get('description', 'No description')
                created = self.format_date(project.get('created_at', ''))
                doc_count = len(project.get('docs', []))

                project_block = f"""### [{name}](projects/{self.safe_filename(name)}/project_info.md)
{f"*{description}*" if description else ""}

- **Created:** {created}
- **Documents:** {doc_count}
- **Private:** {'Yes' if project.get('is_private', False) else 'No'}

"""
                section_lines.append(project_block)
        else:
            section_lines.append("No projects found.\n")

        return "".join(section_lines)

    def _create_recent_conversations_section(self) -> str:
        """Create the recent conversations section for the README"""
        section_lines = ["## Recent Conversations\n"]

        # Show 10 most recent conversations
        recent_conversations = sorted(
            self.conversations,
            key=lambda x: x.get('updated_at', ''),
            reverse=True
        )[:10]

        for conv in recent_conversations:
            name = conv.get('name', 'Untitled Conversation')
            summary = self.get_conversation_summary(conv)
            updated = self.format_date(conv.get('updated_at', ''))
            filename = self.safe_filename(name) + '.md'

            conversation_line = f"- [{name}](conversations/standalone_conversations/{filename})\n  *{summary}* - {updated}\n"
            section_lines.append(conversation_line)

        section_lines.append("\n")
        return "".join(section_lines)

    def create_projects_structure(self, output_dir: Path) -> None:
        """Create project folders and documentation"""
        projects_dir = output_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)

        for project in self.projects:
            project_name = project.get('name', 'Untitled Project')
            safe_name = self.safe_filename(project_name)
            project_dir = projects_dir / safe_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # Create project info file
            self.create_project_info(project, project_dir)

            # Create docs folder and files
            if project.get('docs'):
                docs_dir = project_dir / "docs"
                docs_dir.mkdir(parents=True, exist_ok=True)

                for doc in project['docs']:
                    self.create_project_document(doc, docs_dir)

            print(f"Created project: {project_name}")

    def create_project_info(self, project: Dict, project_dir: Path) -> None:
        """Create project_info.md for a project"""
        name = project.get('name', 'Untitled Project')

        # Project header and basic info
        header_section = f"""# {name}

## Project Information

"""

        # Description and metadata
        description = project.get('description', '')
        metadata_section = f"""{"**Description:** " + description if description else "**Description:** No description provided"}
**Created:** {self.format_date(project.get('created_at', ''))}
**Last Updated:** {self.format_date(project.get('updated_at', ''))}
**Private:** {'Yes' if project.get('is_private', False) else 'No'}
**Starter Project:** {'Yes' if project.get('is_starter_project', False) else 'No'}

"""

        # Creator info
        creator_section = ""
        creator = project.get('creator', {})
        if creator:
            creator_uuid = creator.get('uuid', 'Unknown')
            creator_section = f"""**Creator:** {creator.get('full_name', 'Unknown')}
**Creator ID:** `{creator_uuid}`

"""

        # Project ID
        project_uuid = project.get('uuid', 'Unknown')
        project_id_section = f"""**Project ID:** `{project_uuid}`

"""

        # Prompt template
        prompt_section = ""
        prompt_template = project.get('prompt_template', '')
        if prompt_template:
            prompt_section = f"""## Prompt Template

> {prompt_template}

"""

        # Documents section
        docs_section = self._create_project_docs_section(project.get('docs', []))

        # Combine all sections
        content = (
                header_section +
                metadata_section +
                creator_section +
                project_id_section +
                prompt_section +
                docs_section
        )

        # Write project info file
        info_path = project_dir / "project_info.md"
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_project_docs_section(self, docs: List[Dict]) -> str:
        """Create the documents section for project info"""
        if not docs:
            return """## Documents

No documents in this project.

"""

        docs_lines = ["## Documents\n"]

        for doc in docs:
            filename = doc.get('filename', 'Untitled Document')
            doc_filename = self.safe_filename(filename)
            created = self.format_date(doc.get('created_at', ''))

            docs_lines.append(f"- [{filename}](docs/{doc_filename}.md) - Created {created}\n")

        docs_lines.append("\n")
        return "".join(docs_lines)

    def create_project_document(self, doc: Dict, docs_dir: Path) -> None:
        """Create a document file for a project"""
        filename = doc.get('filename', 'Untitled Document')
        safe_filename = self.safe_filename(filename) + '.md'

        doc_uuid = doc.get('uuid', 'Unknown')
        content = f"""# {filename}

**Created:** {self.format_date(doc.get('created_at', ''))}
**Document ID:** `{doc_uuid}`

---

{doc.get('content', '') or '*No content available*'}"""

        doc_path = docs_dir / safe_filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def has_meaningful_content(self, conversation: Dict) -> bool:
        """Check if a conversation has any meaningful content"""
        messages = conversation.get('chat_messages', [])
        if not messages:
            return False

        # Check if any message has actual content
        for msg in messages:
            content = self.format_message_content(msg)
            if content and content.strip():
                return True

        return False

    def create_conversations_structure(self, output_dir: Path) -> None:
        """Create conversations structure"""
        conversations_dir = output_dir / "conversations"
        conversations_dir.mkdir(parents=True, exist_ok=True)

        # For now, all conversations go to standalone since we don't have 
        # explicit project-conversation relationships
        standalone_dir = conversations_dir / "standalone_conversations"
        standalone_dir.mkdir(parents=True, exist_ok=True)

        # Create project conversations dir for future use
        project_conv_dir = conversations_dir / "project_conversations"
        project_conv_dir.mkdir(parents=True, exist_ok=True)

        # Filter out conversations with no meaningful content
        meaningful_conversations = [conv for conv in self.conversations if self.has_meaningful_content(conv)]
        skipped_count = len(self.conversations) - len(meaningful_conversations)

        for conversation in meaningful_conversations:
            self.create_conversation_file(conversation, standalone_dir)

        print(f"Created {len(meaningful_conversations)} conversation files")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} conversations with no meaningful content")

        # Update the conversations list to only include meaningful ones for other operations
        self.conversations = meaningful_conversations

    def create_conversation_file(self, conversation: Dict, output_dir: Path) -> None:
        """Create a conversation markdown file"""
        name = self.get_conversation_display_name(conversation)
        filename = self.safe_filename(name) + '.md'

        # Header and metadata
        header_section = f"""# {name}

## Conversation Details

"""

        # Summary and basic info
        summary = conversation.get('summary', '')
        conv_uuid = conversation.get('uuid', 'Unknown')
        summary_line = f"**Summary:** {summary}\n\n" if summary else ""
        created_line = f"**Created:** {self.format_date(conversation.get('created_at', ''))}"
        updated_line = f"**Last Updated:** {self.format_date(conversation.get('updated_at', ''))}"
        conv_id_line = f"**Conversation ID:** `{conv_uuid}`"

        summary_section = summary_line + created_line + "\n" + updated_line + "\n" + conv_id_line

        # Account info
        account_section = ""
        if conversation.get('account'):
            account_info = conversation['account']
            if account_info.get('uuid'):
                account_uuid = account_info['uuid']
                account_section = f"\n**Account ID:** `{account_uuid}`"

        metadata_section = summary_section + account_section + "\n\n---\n\n"

        # Messages section
        messages_section = self._create_messages_section(conversation.get('chat_messages', []))

        # Combine all sections
        content = header_section + metadata_section + messages_section

        # Write conversation file
        conv_path = output_dir / filename
        with open(conv_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_messages_section(self, messages: List[Dict]) -> str:
        """Create the messages section for a conversation"""
        if not messages:
            return "*No messages in this conversation.*"

        section_lines = [f"## Messages ({len(messages)})\n"]

        for i, message in enumerate(messages, 1):
            sender = message.get('sender', 'unknown')
            timestamp = self.format_date(message.get('created_at', ''))
            content = self.format_message_content(message)

            # Message header
            sender_name = {
                'human': 'Human',
                'assistant': 'Assistant'
            }.get(sender, sender.title())

            message_block = f"""### {i}. {sender_name}
*{timestamp}*

{content or '*[No content]*'}

"""

            section_lines.append(message_block)

            # Add separator between messages (except for the last one)
            if i < len(messages):
                section_lines.append("---\n")

        return "".join(section_lines)

    def create_metadata_files(self, output_dir: Path) -> None:
        """Create metadata index files"""
        metadata_dir = output_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        # Projects index
        self.create_projects_index(metadata_dir)

        # Conversations index
        self.create_conversations_index(metadata_dir)

        # User info
        self.create_user_info(metadata_dir)

        print("Created metadata files")

    def create_projects_index(self, metadata_dir: Path) -> None:
        """Create projects index file"""
        header_section = f"""# Projects Index

Total projects: **{len(self.projects)}**

"""

        if not self.projects:
            content = header_section + "No projects found.\n"
        else:
            # Sort by creation date (newest first)
            sorted_projects = sorted(
                self.projects,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            projects_section = "## All Projects\n\n"

            for project in sorted_projects:
                name = project.get('name', 'Untitled Project')
                description = project.get('description', 'No description')
                created = self.format_date(project.get('created_at', ''))
                doc_count = len(project.get('docs', []))
                safe_name = self.safe_filename(name)

                project_block = f"""### [{name}](../projects/{safe_name}/project_info.md)
{f"*{description}*" if description else ""}

- **Created:** {created}
- **Documents:** {doc_count}
- **Private:** {'Yes' if project.get('is_private', False) else 'No'}

"""
                projects_section += project_block

            content = header_section + projects_section

        index_path = metadata_dir / "projects_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def create_conversations_index(self, metadata_dir: Path) -> None:
        """Create conversations index file"""
        total_messages = sum(len(conv.get('chat_messages', [])) for conv in self.conversations)

        header_section = f"""# Conversations Index

Total conversations: **{len(self.conversations)}**
Total messages: **{total_messages}**

"""

        if not self.conversations:
            content = header_section + "No conversations found.\n"
        else:
            # Sort by last update (newest first)
            sorted_conversations = sorted(
                self.conversations,
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )

            conversations_section = "## All Conversations\n\n"

            for conversation in sorted_conversations:
                name = self.get_conversation_display_name(conversation)
                updated = self.format_date(conversation.get('updated_at', ''))
                summary = self.get_conversation_summary(conversation)
                filename = self.safe_filename(name) + '.md'

                conversation_line = f"- [{name}](../conversations/standalone_conversations/{filename})\n  *{summary}* - Updated {updated}\n\n"
                conversations_section += conversation_line

            content = header_section + conversations_section

        index_path = metadata_dir / "conversations_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def create_user_info(self, metadata_dir: Path) -> None:
        """Create user information file"""
        content = "# User Information\n\n"

        if not self.users:
            content += "No user information available."
        else:
            for user in self.users:
                phone = user.get('verified_phone_number')
                phone_line = f"**Verified Phone:** {phone}" if phone else "**Verified Phone:** Not provided"
                user_uuid = user.get('uuid', 'Unknown')

                user_block = f"""**Name:** {user.get('full_name', 'Unknown')}
**Email:** {user.get('email_address', 'Unknown')}
**User ID:** `{user_uuid}`
{phone_line}

"""
                content += user_block

        user_path = metadata_dir / "user_info.md"
        with open(user_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def export_to_markdown(self, output_dir: str) -> None:
        """Export all data to markdown structure"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nExporting complete Claude archive to: {output_path}")
        print("=" * 60)

        # Create main structure
        self.create_readme(output_path)
        self.create_projects_structure(output_path)
        self.create_conversations_structure(output_path)
        self.create_metadata_files(output_path)

        print("=" * 60)
        print(f"Export complete! Archive created in: {output_path}")
        print(f"Start by opening: {output_path / 'README.md'}")

    def print_summary(self) -> None:
        """Print a summary of the loaded data"""
        total_messages = sum(len(conv.get('chat_messages', [])) for conv in self.conversations)
        total_docs = sum(len(proj.get('docs', [])) for proj in self.projects)

        print("\n" + "=" * 60)
        print("CLAUDE EXPORT SUMMARY")
        print("=" * 60)
        print(f"Users: {len(self.users)}")
        print(f"Projects: {len(self.projects)}")
        print(f"  - Project documents: {total_docs}")
        print(f"Conversations: {len(self.conversations)}")
        print(f"  - Total messages: {total_messages}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Convert Claude export files to integrated markdown structure (auto-detects file types)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All three files in any order
  python claude_complete_parser.py conversations.json projects.json users.json
  python claude_complete_parser.py users.json conversations.json projects.json
  
  # Only conversations
  python claude_complete_parser.py conversations.json
  
  # Conversations + users only  
  python claude_complete_parser.py conversations.json users.json
  
  # Custom output directory
  python claude_complete_parser.py *.json -o my_archive
  
Note: Files are identified by filename (must contain 'conversation', 'project', or 'user')
        """
    )

    parser.add_argument('files', nargs='+', help='Claude export JSON files (auto-detected by filename)')
    parser.add_argument(
        '-o', '--output',
        default='claude_complete_export',
        help='Output directory for markdown files (default: claude_complete_export)'
    )

    args = parser.parse_args()

    print("Claude Complete Export Parser (Smart Detection)")
    print("=" * 50)

    # Create parser and process files
    parser_instance = ClaudeCompleteParser(args.files)

    parser_instance.load_data()
    parser_instance.analyze_relationships()
    parser_instance.print_summary()
    parser_instance.export_to_markdown(args.output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Claude Complete Export Parser - Clean Version
Integrates conversations.json, projects.json, and users.json into a unified markdown structure
Uses filename analysis to automatically detect file types
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


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

    def create_readme(self, output_dir: Path) -> None:
        """Create the main README.md file"""
        readme_lines = []

        # Header
        readme_lines.append("# Claude Export - Complete Archive")
        readme_lines.append("")
        readme_lines.append(f"Export generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        readme_lines.append("")

        # User information
        if self.users:
            user = self.users[0]  # Assuming single user
            readme_lines.append("## User Information")
            readme_lines.append("")
            readme_lines.append(f"**Name:** {user.get('full_name', 'Unknown')}")
            readme_lines.append(f"**Email:** {user.get('email_address', 'Unknown')}")
            readme_lines.append(f"**User ID:** `{user.get('uuid', 'Unknown')}`")
            readme_lines.append("")

        # Statistics
        total_messages = sum(len(conv.get('chat_messages', [])) for conv in self.conversations)

        readme_lines.append("## Overview")
        readme_lines.append("")
        readme_lines.append(f"- **Total Projects:** {len(self.projects)}")
        readme_lines.append(f"- **Total Conversations:** {len(self.conversations)}")
        readme_lines.append(f"- **Total Messages:** {total_messages}")
        readme_lines.append("")

        # Date range
        dates = [conv.get('created_at', '') for conv in self.conversations if conv.get('created_at')]
        if dates:
            dates.sort()
            first_date = self.format_date(dates[0])
            last_date = self.format_date(dates[-1])
            readme_lines.append(f"**Date Range:** {first_date} to {last_date}")
            readme_lines.append("")

        # Structure explanation
        readme_lines.append("## Archive Structure")
        readme_lines.append("")
        readme_lines.append("This archive is organized as follows:")
        readme_lines.append("")
        readme_lines.append("```")
        readme_lines.append("claude_export/")
        readme_lines.append("├── README.md (this file)")
        readme_lines.append("├── projects/")
        readme_lines.append("│   ├── [project_name]/")
        readme_lines.append("│   │   ├── project_info.md")
        readme_lines.append("│   │   └── docs/")
        readme_lines.append("│   │       └── [document_files]")
        readme_lines.append("├── conversations/")
        readme_lines.append("│   ├── project_conversations/")
        readme_lines.append("│   │   └── [conversation_files]")
        readme_lines.append("│   └── standalone_conversations/")
        readme_lines.append("│       └── [conversation_files]")
        readme_lines.append("└── metadata/")
        readme_lines.append("    ├── projects_index.md")
        readme_lines.append("    ├── conversations_index.md")
        readme_lines.append("    └── user_info.md")
        readme_lines.append("```")
        readme_lines.append("")

        # Projects section
        readme_lines.append("## Projects")
        readme_lines.append("")

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

                readme_lines.append(f"### [{name}](projects/{self.safe_filename(name)}/project_info.md)")
                if description:
                    readme_lines.append(f"*{description}*")
                readme_lines.append("")
                readme_lines.append(f"- **Created:** {created}")
                readme_lines.append(f"- **Documents:** {doc_count}")
                readme_lines.append(f"- **Private:** {'Yes' if project.get('is_private', False) else 'No'}")
                readme_lines.append("")
        else:
            readme_lines.append("No projects found.")
            readme_lines.append("")

        # Quick access to conversations
        readme_lines.append("## Recent Conversations")
        readme_lines.append("")

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

            readme_lines.append(f"- [{name}](conversations/standalone_conversations/{filename})")
            readme_lines.append(f"  *{summary}* - {updated}")
            readme_lines.append("")

        # Navigation links
        readme_lines.append("## Navigation")
        readme_lines.append("")
        readme_lines.append("- [All Projects](metadata/projects_index.md)")
        readme_lines.append("- [All Conversations](metadata/conversations_index.md)")
        readme_lines.append("- [User Information](metadata/user_info.md)")
        readme_lines.append("")

        # Write README
        readme_path = output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(readme_lines))

        print(f"Created main README: {readme_path}")

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
        lines = []

        name = project.get('name', 'Untitled Project')
        lines.append(f"# {name}")
        lines.append("")

        # Project metadata
        lines.append("## Project Information")
        lines.append("")

        description = project.get('description', '')
        if description:
            lines.append(f"**Description:** {description}")
        else:
            lines.append("**Description:** No description provided")

        lines.append(f"**Created:** {self.format_date(project.get('created_at', ''))}")
        lines.append(f"**Last Updated:** {self.format_date(project.get('updated_at', ''))}")
        lines.append(f"**Private:** {'Yes' if project.get('is_private', False) else 'No'}")
        lines.append(f"**Starter Project:** {'Yes' if project.get('is_starter_project', False) else 'No'}")
        lines.append("")

        # Creator info
        creator = project.get('creator', {})
        if creator:
            lines.append(f"**Creator:** {creator.get('full_name', 'Unknown')}")
            lines.append(f"**Creator ID:** `{creator.get('uuid', 'Unknown')}`")
            lines.append("")

        # Project UUID
        lines.append(f"**Project ID:** `{project.get('uuid', 'Unknown')}`")
        lines.append("")

        # Prompt template
        prompt_template = project.get('prompt_template', '')
        if prompt_template:
            lines.append("## Prompt Template")
            lines.append("")
            lines.append(f"> {prompt_template}")
            lines.append("")

        # Documents
        docs = project.get('docs', [])
        if docs:
            lines.append("## Documents")
            lines.append("")

            for doc in docs:
                filename = doc.get('filename', 'Untitled Document')
                doc_filename = self.safe_filename(filename)
                created = self.format_date(doc.get('created_at', ''))

                lines.append(f"- [{filename}](docs/{doc_filename}.md) - Created {created}")

            lines.append("")
        else:
            lines.append("## Documents")
            lines.append("")
            lines.append("No documents in this project.")
            lines.append("")

        # Write project info file
        info_path = project_dir / "project_info.md"
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def create_project_document(self, doc: Dict, docs_dir: Path) -> None:
        """Create a document file for a project"""
        filename = doc.get('filename', 'Untitled Document')
        safe_filename = self.safe_filename(filename) + '.md'

        lines = []
        lines.append(f"# {filename}")
        lines.append("")
        lines.append(f"**Created:** {self.format_date(doc.get('created_at', ''))}")
        lines.append(f"**Document ID:** `{doc.get('uuid', 'Unknown')}`")
        lines.append("")
        lines.append("---")
        lines.append("")

        content = doc.get('content', '')
        if content:
            lines.append(content)
        else:
            lines.append("*No content available*")

        doc_path = docs_dir / safe_filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

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

        for conversation in self.conversations:
            self.create_conversation_file(conversation, standalone_dir)

        print(f"Created {len(self.conversations)} conversation files")

    def create_conversation_file(self, conversation: Dict, output_dir: Path) -> None:
        """Create a conversation markdown file"""
        name = conversation.get('name', 'Untitled Conversation')
        filename = self.safe_filename(name) + '.md'

        lines = []
        lines.append(f"# {name}")
        lines.append("")

        # Conversation metadata
        lines.append("## Conversation Details")
        lines.append("")

        summary = conversation.get('summary', '')
        if summary:
            lines.append(f"**Summary:** {summary}")
            lines.append("")

        lines.append(f"**Created:** {self.format_date(conversation.get('created_at', ''))}")
        lines.append(f"**Last Updated:** {self.format_date(conversation.get('updated_at', ''))}")
        lines.append(f"**Conversation ID:** `{conversation.get('uuid', 'Unknown')}`")

        if conversation.get('account'):
            account_info = conversation['account']
            if account_info.get('uuid'):
                lines.append(f"**Account ID:** `{account_info['uuid']}`")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Messages
        messages = conversation.get('chat_messages', [])

        if not messages:
            lines.append("*No messages in this conversation.*")
        else:
            lines.append(f"## Messages ({len(messages)})")
            lines.append("")

            for i, message in enumerate(messages, 1):
                sender = message.get('sender', 'unknown')
                timestamp = self.format_date(message.get('created_at', ''))
                content = self.format_message_content(message)

                # Message header
                if sender == 'human':
                    lines.append(f"### {i}. Human")
                elif sender == 'assistant':
                    lines.append(f"### {i}. Assistant")
                else:
                    lines.append(f"### {i}. {sender.title()}")

                lines.append(f"*{timestamp}*")
                lines.append("")

                # Message content
                if content:
                    lines.append(content)
                else:
                    lines.append("*[No content]*")

                lines.append("")

                # Add separator between messages (except for the last one)
                if i < len(messages):
                    lines.append("---")
                    lines.append("")

        # Write conversation file
        conv_path = output_dir / filename
        with open(conv_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

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
        lines = []
        lines.append("# Projects Index")
        lines.append("")
        lines.append(f"Total projects: **{len(self.projects)}**")
        lines.append("")

        if not self.projects:
            lines.append("No projects found.")
            lines.append("")
        else:
            # Sort by creation date (newest first)
            sorted_projects = sorted(
                self.projects,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            lines.append("## All Projects")
            lines.append("")

            for project in sorted_projects:
                name = project.get('name', 'Untitled Project')
                description = project.get('description', 'No description')
                created = self.format_date(project.get('created_at', ''))
                doc_count = len(project.get('docs', []))
                safe_name = self.safe_filename(name)

                lines.append(f"### [{name}](../projects/{safe_name}/project_info.md)")

                if description:
                    lines.append(f"*{description}*")

                lines.append("")
                lines.append(f"- **Created:** {created}")
                lines.append(f"- **Documents:** {doc_count}")
                lines.append(f"- **Private:** {'Yes' if project.get('is_private', False) else 'No'}")
                lines.append("")

        index_path = metadata_dir / "projects_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def create_conversations_index(self, metadata_dir: Path) -> None:
        """Create conversations index file"""
        lines = []
        lines.append("# Conversations Index")
        lines.append("")

        total_messages = sum(len(conv.get('chat_messages', [])) for conv in self.conversations)
        lines.append(f"Total conversations: **{len(self.conversations)}**")
        lines.append(f"Total messages: **{total_messages}**")
        lines.append("")

        if not self.conversations:
            lines.append("No conversations found.")
            lines.append("")
        else:
            # Sort by last update (newest first)
            sorted_conversations = sorted(
                self.conversations,
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )

            lines.append("## All Conversations")
            lines.append("")

            for conversation in sorted_conversations:
                name = conversation.get('name', 'Untitled Conversation')
                updated = self.format_date(conversation.get('updated_at', ''))
                message_count = len(conversation.get('chat_messages', []))
                summary = self.get_conversation_summary(conversation)
                filename = self.safe_filename(name) + '.md'

                lines.append(f"- [{name}](../conversations/standalone_conversations/{filename})")
                lines.append(f"  *{summary}* - Updated {updated}")
                lines.append("")

        index_path = metadata_dir / "conversations_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def create_user_info(self, metadata_dir: Path) -> None:
        """Create user information file"""
        lines = []
        lines.append("# User Information")
        lines.append("")

        if not self.users:
            lines.append("No user information available.")
        else:
            for user in self.users:
                lines.append(f"**Name:** {user.get('full_name', 'Unknown')}")
                lines.append(f"**Email:** {user.get('email_address', 'Unknown')}")
                lines.append(f"**User ID:** `{user.get('uuid', 'Unknown')}`")

                phone = user.get('verified_phone_number')
                if phone:
                    lines.append(f"**Verified Phone:** {phone}")
                else:
                    lines.append("**Verified Phone:** Not provided")

                lines.append("")

        user_path = metadata_dir / "user_info.md"
        with open(user_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

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

#!/usr/bin/env python3
"""
Update internal links from .html to .md in converted Markdown files.
This script finds all links to .html files within the markdown files and updates them to .md
"""

import os
import re
import glob

def update_html_links_in_file(file_path):
    """
    Update HTML links to MD links in a single file.
    Returns True if file was modified, False otherwise.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match markdown links that point to .html files
    # This matches [text](path.html) and [text](path.html#anchor)
    # But excludes external links (http/https)
    pattern = r'\[([^\]]+)\]\(([^)]*?)\.html(#[^)]*?)?\)'
    
    def replace_html_link(match):
        text = match.group(1)
        path = match.group(2)
        anchor = match.group(3) or ''
        
        # Don't replace external links
        if path.startswith('http://') or path.startswith('https://'):
            return match.group(0)  # Return original match
        
        # Replace .html with .md
        return f'[{text}]({path}.md{anchor})'
    
    content = re.sub(pattern, replace_html_link, content)
    
    # Check if content was modified
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    """
    Main function to update all markdown files.
    """
    print("Updating HTML links to MD links in converted files")
    print("=" * 50)
    
    # Find all markdown files (excluding ones we don't want to modify)
    md_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        skip_dirs = ['.git', '.venv', '__pycache__']
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    print(f"Found {len(md_files)} markdown files to check")
    
    modified_files = []
    
    for file_path in md_files:
        print(f"Checking: {file_path}")
        try:
            if update_html_links_in_file(file_path):
                modified_files.append(file_path)
                print(f"  -> Updated links in {file_path}")
        except Exception as e:
            print(f"  -> Error processing {file_path}: {e}")
    
    print(f"\nUpdate completed:")
    print(f"  Files checked: {len(md_files)}")
    print(f"  Files modified: {len(modified_files)}")
    
    if modified_files:
        print(f"\nModified files:")
        for file_path in modified_files:
            print(f"  {file_path}")
    
    # Save summary
    with open('link_update_summary.txt', 'w') as f:
        f.write("Link Update Summary\n")
        f.write("=" * 20 + "\n\n")
        f.write(f"Files checked: {len(md_files)}\n")
        f.write(f"Files modified: {len(modified_files)}\n\n")
        
        if modified_files:
            f.write("Modified files:\n")
            for file_path in modified_files:
                f.write(f"  {file_path}\n")

if __name__ == "__main__":
    main()
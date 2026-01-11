#!/usr/bin/env python3
# Copyright Vespa.ai. All rights reserved.
"""
Extract all Jekyll redirect_from entries and generate a redirects.yml file.

This script scans the repository for Jekyll pages (HTML and Markdown files) that use
the jekyll-redirect-from plugin with 'redirect_from' in their front matter, and
generates a consolidated redirects.yml file with all redirects in the format:
  /old-path: /new-path

Usage:
  python3 extract_redirects.py

Output:
  redirects.yml - Contains all redirect mappings sorted alphabetically by old path
"""

import os
import re
from pathlib import Path


def extract_redirect_from(file_path):
    """Extract redirect_from entries from YAML front matter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match YAML front matter between --- delimiters
    match = re.match(r'^---\s*\n(.*?\n)---\s*\n', content, re.DOTALL)
    if not match:
        return None

    front_matter = match.group(1)

    # Look for redirect_from entries
    # Can be single line: redirect_from: /path
    # Or multi-line list:
    # redirect_from:
    # - /path1
    # - /path2
    redirects = []

    # Try to find redirect_from block
    redirect_match = re.search(r'redirect_from:\s*\n((?:\s*-\s*.+\n)+)', front_matter)
    if redirect_match:
        # Multi-line format
        redirect_lines = redirect_match.group(1)
        for line in redirect_lines.strip().split('\n'):
            path = line.strip().lstrip('-').strip()
            if path:
                redirects.append(path)
    else:
        # Try single line format
        single_match = re.search(r'redirect_from:\s*(.+?)(?:\n|$)', front_matter)
        if single_match:
            path = single_match.group(1).strip()
            if path:
                redirects.append(path)

    return redirects if redirects else None


def find_redirects(root_dir='.'):
    """Find all files with redirect_from in their front matter."""
    redirects = {}

    # Common extensions for Jekyll pages
    extensions = ['.html', '.md', '.markdown']

    # Directories to exclude from scanning
    excluded_dirs = ['vendor/', 'node_modules/', '.git/']

    for ext in extensions:
        # Use glob to find all files with these extensions
        for file_path in Path(root_dir).rglob(f'*{ext}'):
            # Skip files in excluded directories
            str_path = str(file_path)
            if any(excluded in str_path for excluded in excluded_dirs):
                continue
            if any(part.startswith('_') or part.startswith('.') for part in file_path.parts):
                if not str_path.startswith('_'):  # Allow files in root starting with _
                    continue

            try:
                redirect_from_list = extract_redirect_from(file_path)
                if redirect_from_list:
                    # Get the relative path from root
                    relative_path = file_path.relative_to(root_dir)
                    # Convert to URL path (use forward slashes)
                    new_path = str(relative_path).replace('\\', '/')

                    # Store each old path -> new path mapping
                    for old_path in redirect_from_list:
                        # Ensure paths start with /
                        if not old_path.startswith('/'):
                            old_path = '/' + old_path
                        if not new_path.startswith('/'):
                            new_path = '/' + new_path

                        redirects[old_path] = new_path

            except Exception as e:
                print(f"Warning: Error processing {file_path}: {e}")
                continue

    return redirects


def write_redirects_yaml(redirects, output_file='redirects.yml'):
    """Write redirects to YAML file in the format /old-path: /new-path."""
    # Sort by old path for consistency
    sorted_redirects = dict(sorted(redirects.items()))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Copyright Vespa.ai. All rights reserved.\n")
        f.write("# Generated redirect mappings from Jekyll redirect_from plugin\n")
        f.write("# Format: /old-path: /new-path\n\n")

        for old_path, new_path in sorted_redirects.items():
            # Quote paths if they contain special characters
            old_quoted = f'"{old_path}"' if ':' in old_path or '#' in old_path else old_path
            new_quoted = f'"{new_path}"' if ':' in new_path or '#' in new_path else new_path
            f.write(f"{old_quoted}: {new_quoted}\n")


def main():
    """Main function."""
    print("Scanning for Jekyll redirect_from entries...")
    redirects = find_redirects()

    print(f"Found {len(redirects)} redirects")

    if redirects:
        write_redirects_yaml(redirects)
        print(f"Redirects written to redirects.yml")
    else:
        print("No redirects found")


if __name__ == '__main__':
    main()

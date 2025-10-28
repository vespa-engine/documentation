#!/usr/bin/env python3
"""
Convert HTML files to Markdown while preserving Jekyll front matter.
This script converts HTML content files to Markdown format, maintaining
the YAML front matter and converting HTML elements to equivalent Markdown.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple
import subprocess

try:
    from bs4 import BeautifulSoup, NavigableString
    import markdownify
except ImportError:
    print("Required packages not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "markdownify", "lxml"])
    from bs4 import BeautifulSoup, NavigableString
    import markdownify

def extract_front_matter_and_content(file_path: str) -> Tuple[str, str]:
    """
    Extract YAML front matter and HTML content from a Jekyll file.
    
    Returns:
        Tuple of (front_matter, html_content)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file starts with front matter
    if not content.startswith('---'):
        return "", content
    
    # Split on the second occurrence of ---
    parts = content.split('---', 2)
    if len(parts) < 3:
        return "", content
    
    front_matter = f"---{parts[1]}---"
    html_content = parts[2].strip()
    
    return front_matter, html_content

def convert_html_to_markdown(html_content: str) -> str:
    """
    Convert HTML content to Markdown format.
    """
    # Custom conversion for better handling of code blocks and specific elements
    h = markdownify.MarkdownConverter(
        heading_style='atx',  # Use # style headers
        code_language='',     # Don't assume language for code blocks
        wrap=False,           # Don't wrap long lines
        escape_asterisks=False,
        escape_underscores=False,
        strip=['script', 'style'],  # Remove script and style tags
    )
    
    # Convert HTML to markdown
    markdown_content = h.convert(html_content)
    
    # Clean up common issues
    markdown_content = clean_markdown(markdown_content)
    
    return markdown_content

def clean_markdown(markdown_content: str) -> str:
    """
    Clean up common markdown conversion issues.
    """
    # Remove excessive newlines (more than 2 consecutive)
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    
    # Fix code blocks that might have been mangled
    markdown_content = re.sub(r'```\s*\n\s*```', '```\n```', markdown_content)
    
    # Clean up list formatting
    markdown_content = re.sub(r'\n\s*\n(\s*[-\*\+])', r'\n\1', markdown_content)
    
    # Remove trailing whitespace from lines
    lines = markdown_content.split('\n')
    lines = [line.rstrip() for line in lines]
    markdown_content = '\n'.join(lines)
    
    # Ensure file ends with single newline
    markdown_content = markdown_content.rstrip() + '\n'
    
    return markdown_content

def get_html_files_to_convert() -> List[str]:
    """
    Get list of HTML files to convert (excluding template files).
    """
    html_files = []
    
    # Find all HTML files excluding _layouts and _includes directories
    for root, dirs, files in os.walk('.'):
        # Skip template directories
        dirs[:] = [d for d in dirs if d not in ['_layouts', '_includes']]
        
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    return html_files

def convert_file(input_path: str) -> str:
    """
    Convert a single HTML file to Markdown.
    
    Returns:
        Path to the output Markdown file
    """
    print(f"Converting: {input_path}")
    
    # Extract front matter and content
    front_matter, html_content = extract_front_matter_and_content(input_path)
    
    # Convert HTML to Markdown
    markdown_content = convert_html_to_markdown(html_content)
    
    # Combine front matter with markdown content
    if front_matter:
        full_content = front_matter + '\n\n' + markdown_content
    else:
        full_content = markdown_content
    
    # Create output path (change .html to .md)
    output_path = input_path.replace('.html', '.md')
    
    # Write the converted content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"  -> {output_path}")
    return output_path

def main():
    """
    Main function to convert all HTML files to Markdown.
    """
    print("HTML to Markdown Converter")
    print("=" * 40)
    
    # Get list of HTML files to convert
    html_files = get_html_files_to_convert()
    
    print(f"Found {len(html_files)} HTML files to convert")
    
    if not html_files:
        print("No HTML files found to convert.")
        return
    
    # Ask for confirmation
    response = input(f"Convert {len(html_files)} files? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Conversion cancelled.")
        return
    
    converted_files = []
    failed_files = []
    
    # Convert each file
    for html_file in html_files:
        try:
            output_file = convert_file(html_file)
            converted_files.append((html_file, output_file))
        except Exception as e:
            print(f"Error converting {html_file}: {e}")
            failed_files.append((html_file, str(e)))
    
    # Print summary
    print("\n" + "=" * 40)
    print(f"Conversion completed:")
    print(f"  Successfully converted: {len(converted_files)}")
    print(f"  Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for file_path, error in failed_files:
            print(f"  {file_path}: {error}")
    
    # Create a summary file
    with open('conversion_summary.txt', 'w') as f:
        f.write("HTML to Markdown Conversion Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Successfully converted: {len(converted_files)}\n")
        f.write(f"Failed: {len(failed_files)}\n\n")
        
        if converted_files:
            f.write("Converted files:\n")
            for html_file, md_file in converted_files:
                f.write(f"  {html_file} -> {md_file}\n")
        
        if failed_files:
            f.write("\nFailed files:\n")
            for file_path, error in failed_files:
                f.write(f"  {file_path}: {error}\n")
    
    print(f"\nConversion summary saved to: conversion_summary.txt")

if __name__ == "__main__":
    main()
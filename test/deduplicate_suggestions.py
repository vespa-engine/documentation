#!/usr/bin/env python3
"""
Script to deduplicate suggestions_index.json based on the 'term' field (case-insensitive).
"""

import json
import sys
from pathlib import Path


def deduplicate_suggestions(input_file, output_file):
    """
    Read JSON objects from input file (one per line), deduplicate based on
    lowercased 'term' field, and write to output file.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    """
    seen_terms = {}  # Dictionary to track lowercased terms
    deduplicated_items = []
    duplicate_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check if the file starts with an array bracket
    if lines and lines[0].strip() == '[':
        # Skip the opening bracket
        start_idx = 1
    else:
        start_idx = 0
    
    for line_num, line in enumerate(lines[start_idx:], start=start_idx + 1):
        line = line.strip()
        
        # Skip empty lines and closing bracket
        if not line or line == ']':
            continue
        
        # Remove trailing comma if present
        if line.endswith(','):
            line = line[:-1]
        
        try:
            item = json.loads(line)
            
            # Extract the term field
            if 'fields' in item and 'term' in item['fields']:
                term = item['fields']['term']
                term_lower = term.lower()
                
                # Check if we've seen this term before
                if term_lower not in seen_terms:
                    seen_terms[term_lower] = term
                    deduplicated_items.append(item)
                else:
                    duplicate_count += 1
                    print(f"Skipping duplicate term: '{term}' (original: '{seen_terms[term_lower]}')")
            else:
                # If no term field, keep the item anyway
                deduplicated_items.append(item)
                print(f"Warning: Item at line {line_num} has no 'term' field")
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON at line {line_num}: {e}")
            continue
    
    # Write deduplicated items to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n')
        for i, item in enumerate(deduplicated_items):
            json_line = json.dumps(item, ensure_ascii=False)
            if i < len(deduplicated_items) - 1:
                f.write(json_line + ', \n')
            else:
                f.write(json_line + '\n')
        f.write(']\n')
    
    print(f"\nDeduplication complete!")
    print(f"Original items: {len(lines) - 1}")  # Minus 1 for opening bracket
    print(f"Unique items: {len(deduplicated_items)}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Output written to: {output_file}")


if __name__ == "__main__":
    # Get the script directory and go up one level to find the file
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    input_file = project_dir / "suggestions_index.json"
    output_file = project_dir / "suggestions_index_deduplicated.json"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    deduplicate_suggestions(input_file, output_file)


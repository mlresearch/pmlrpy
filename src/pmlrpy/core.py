import re
import bibtexparser
import logging
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import unicodedata
import os
import shutil

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Base level for file logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pmlrpy.log'),
    ]
)

# Add console handler with higher level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Only show INFO and above in console
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

REQUIRED_PROCEEDINGS_FIELDS = {
    'booktitle', 'name', 'shortname', 'year', 'editor', 
    'volume', 'start', 'end', 'published', 'address', 'conference_url'
}

def get_unique_normalized_id(original_id, normalized_id, existing_ids):
    """Generate a unique normalized ID by adding a suffix if needed."""
    base_id = normalized_id
    counter = 1
    while normalized_id in existing_ids:
        normalized_id = f"{base_id}_{counter}"
        counter += 1
    return normalized_id

def check_and_fix_bibtex(input_file, output_file):
    # Log start of processing
    logging.info(f"Starting to process {input_file}")
    
    # Custom parser settings
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    
    # Read the BibTeX file
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser)
    logging.info(f"Loaded {len(bib_database.entries)} entries from BibTeX file")

    proceedings_entries = []
    issues = []

    # Unicode replacements (for all fields)
    unicode_replacements = {
        # German/Swedish/Finnish umlauts
        'ä': '{\\"{a}}',
        'ë': '{\\"{e}}',
        'ï': '{\\"{i}}',
        'ö': '{\\"{o}}',
        'ü': '{\\"{u}}',
        'ÿ': '{\\"{y}}',
        'Ä': '{\\"{A}}',
        'Ë': '{\\"{E}}',
        'Ï': '{\\"{I}}',
        'Ö': '{\\"{O}}',
        'Ü': '{\\"{U}}',
        'Ÿ': '{\\"{Y}}',
        'ß': '{\\ss}',
        
        # Acute accents
        'á': '{\\\'{a}}',
        'é': '{\\\'{e}}',
        'í': '{\\\'{i}}',
        'ó': '{\\\'{o}}',
        'ú': '{\\\'{u}}',
        'ý': '{\\\'{y}}',
        'Á': '{\\\'{A}}',
        'É': '{\\\'{E}}',
        'Í': '{\\\'{I}}',
        'Ó': '{\\\'{O}}',
        'Ú': '{\\\'{U}}',
        'Ý': '{\\\'{Y}}',
        
        # Grave accents
        'à': '{\\`{a}}',
        'è': '{\\`{e}}',
        'ì': '{\\`{i}}',
        'ò': '{\\`{o}}',
        'ù': '{\\`{u}}',
        'À': '{\\`{A}}',
        'È': '{\\`{E}}',
        'Ì': '{\\`{I}}',
        'Ò': '{\\`{O}}',
        'Ù': '{\\`{U}}',
        
        # Circumflex
        'â': '{\\^{a}}',
        'ê': '{\\^{e}}',
        'î': '{\\^{i}}',
        'ô': '{\\^{o}}',
        'û': '{\\^{u}}',
        'Â': '{\\^{A}}',
        'Ê': '{\\^{E}}',
        'Î': '{\\^{I}}',
        'Ô': '{\\^{O}}',
        'Û': '{\\^{U}}',
        
        # Tilde
        'ã': '{\\~{a}}',
        'ñ': '{\\~{n}}',
        'õ': '{\\~{o}}',
        'Ã': '{\\~{A}}',
        'Ñ': '{\\~{N}}',
        'Õ': '{\\~{O}}',
        
        # Polish specific
        'ą': '\\k{a}',
        'ę': '\\k{e}',
        'ć': "\\'c",
        'ł': '\\l{}',
        'ń': "\\'n",
        'ś': "\\'s",
        'ź': "\\'z",
        'ż': '\\.z',
        'Ą': '\\k{A}',
        'Ę': '\\k{E}',
        'Ć': "\\'C",
        'Ł': '\\L{}',
        'Ń': "\\'N",
        'Ś': "\\'S",
        'Ź': "\\'Z",
        'Ż': '\\.Z',
        
        # Czech/Slovak specific
        'ř': '\\v{r}',
        'š': '\\v{s}',
        'ť': '\\v{t}',
        'ď': '\\v{d}',
        'Ř': '\\v{R}',
        'Š': '\\v{S}',
        'Ť': '\\v{T}',
        'Ď': '\\v{D}',
        
        # Danish/Norwegian specific
        'ø': '\\o{}',
        'å': '\\aa{}',
        'Ø': '\\O{}',
        'Å': '\\AA{}',
        
        # Various quotation marks and dashes
        '"': "``",    # left double quote
        '"': "''",    # right double quote
        "'": "`",     # left single quote
        "'": "'",     # right single quote
        '‚': ",",     # low single quote
        '„': ",,",    # low double quote
        '–': '--',    # en-dash
        '—': '---',   # em-dash
        
        # Other special characters
        'æ': '\\ae{}',
        'Æ': '\\AE{}',
        'œ': '\\oe{}',
        'Œ': '\\OE{}',
        'ß': '\\ss{}',
        '¡': '!`',
        '¿': '?`',
        
        # Greek letters
        'λ': '\\lambda',
        
        # Additional characters found in corl24.bib
        '\xa0': ' ',        # non-breaking space
        'ç': '\\c{c}',      # c-cedilla
        'ğ': '\\u{g}',      # g with breve
        'ś': "\\'s",        # s-acute
        'ć': "\\'c",        # c-acute
        '≥': '$\\geq$',     # greater than or equal
        'å': '\\aa{}',      # a with ring
        'ø': '\\o{}',       # slashed o
        '–': '--',          # en-dash
        '—': '---',         # em-dash
        '’': "'",           # right single quote
        '\u201c': '``',          # left double quote (U+201C)
        '\u201d': "''",          # right double quote (U+201D) 
        
        # Dashes - specify exact Unicode values
        '\u2013': '--',    # en-dash (–)
        '\u2014': '---',   # em-dash (—)
        '\u2212': '-',     # minus sign (−)
    }

    # Special LaTeX characters that need escaping in abstracts
    abstract_latex_escapes = {
        '%': '\\%',
        '&': '\\&',
    }

    # PDF ligature replacements (common combinations that get merged in PDFs)
    pdf_ligature_replacements = {
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        'ﬀ': 'ff',
        'ﬃ': 'ffi',
        'ﬄ': 'ffl',
        'ﬅ': 'ft',
        'ﬆ': 'st',
        'Ꜳ': 'AA',
        'ꜳ': 'aa',
        'Ꜵ': 'AO',
        'ꜵ': 'ao',
        'Ꜷ': 'AU',
        'ꜷ': 'au',
        'Ꜹ': 'AV',
        'ꜹ': 'av',
        'Ꜻ': 'AY',
        'ꜻ': 'ay',
        'Ꜽ': 'OO',
        'ꜽ': 'oo'
    }
    
    # Check proceedings entry
    logging.debug("Starting proceedings entry check")
    proceedings_entries = []
    
    for entry in bib_database.entries:
        # Normalize entry type to title case (Proceedings, InProceedings)
        entry['ENTRYTYPE'] = entry['ENTRYTYPE'].title()
        logging.debug(f"Checking entry type: {entry.get('ENTRYTYPE')} with ID: {entry.get('ID')}")
        
        if entry['ENTRYTYPE'] == 'Proceedings':
            logging.info(f"Found proceedings entry with ID: {entry.get('ID')}")
            proceedings_entries.append(entry)
            # Check required fields immediately for each proceedings entry
            missing_fields = REQUIRED_PROCEEDINGS_FIELDS - set(entry.keys())
            if missing_fields:
                msg = f"Missing required field(s) in Proceedings: {', '.join(missing_fields)}"
                logging.error(msg)
                raise ValueError(msg)

    # Move this check after the field validation
    if len(proceedings_entries) != 1:
        msg = f"Found {len(proceedings_entries)} Proceedings entries, expected 1"
        logging.error(msg)
        raise ValueError(msg)

    # Check and fix InProceedings entries
    existing_ids = set()  # Track all IDs we've seen
    id_changes = {}  # Store original -> normalized ID mappings

    for entry in bib_database.entries:
        if entry['ENTRYTYPE'].lower() == 'inproceedings':  # Make case-insensitive
            # Check required fields
            required_fields = ['title', 'author', 'pages', 'abstract']
            for field in required_fields:
                if field not in entry or not entry[field]:
                    issues.append(f"Missing or empty required field '{field}' in entry {entry.get('ID', 'unknown')}")

            # Normalize ID if it contains Unicode characters
            if any(ord(c) > 127 for c in entry['ID']):
                original_id = entry['ID']
                # First replace ß with ss
                normalized_id = entry['ID'].replace('ß', 'ss')
                # Then convert remaining Unicode to closest ASCII representation
                normalized_id = unicodedata.normalize('NFKD', normalized_id)
                normalized_id = ''.join(c for c in normalized_id if ord(c) < 128)
                
                if normalized_id != original_id:
                    # Check for clashes and get unique ID
                    if normalized_id in existing_ids:
                        normalized_id = get_unique_normalized_id(original_id, normalized_id, existing_ids)
                        logging.warning(f"ID clash detected. '{original_id}' normalized to '{normalized_id}' to avoid duplicate")
                    
                    id_changes[original_id] = normalized_id
                    logging.warning(f"Normalized ID from '{original_id}' to '{normalized_id}'")
                    entry['ID'] = normalized_id
            
            existing_ids.add(entry['ID'])

            # Check ID format - only exclude characters that would break BibTeX
            if not re.match(r'^[^,{}\(\)="\#%~\\\s]+$', entry.get('ID', '')):
                issues.append(f"Invalid ID format (contains illegal characters): {entry.get('ID', 'unknown')}")

            # Check software field format if present
            if 'software' in entry and entry['software']:
                # URL pattern matching https:// or http:// followed by valid URL characters
                if not re.match(r'^https?://[^\s,]+$', entry['software'].strip()):
                    issues.append(f"Software field should contain a single valid URL in entry {entry.get('ID', 'unknown')}")

            # Fix PDF ligatures and Unicode in all text fields
            text_fields = ['title', 'abstract', 'author', 'editor']
            for field in text_fields:
                if field in entry:
                    # Handle author/editor fields which might be lists or strings
                    if field in ['author', 'editor'] and entry[field]:
                        # Split authors/editors if they're in a string format
                        if isinstance(entry[field], str):
                            # Normalize whitespace first - collapse multiple spaces and newlines into single space
                            normalized_text = ' '.join(entry[field].split())
                            authors = [name.strip() for name in normalized_text.split(' and ')]
                        else:
                            authors = entry[field]
                        
                        # Process each author/editor name
                        processed_authors = []
                        for author in authors:
                            # First handle Unicode replacements
                            for char, replacement in unicode_replacements.items():
                                if char not in ['"', '"', ''', ''']:  # Skip quote replacements
                                    author = author.replace(char, replacement)
                            
                            # Then handle PDF ligatures
                            for ligature, replacement in pdf_ligature_replacements.items():
                                author = author.replace(ligature, replacement)
                            
                            # Finally handle quotes, but not within LaTeX commands
                            for char, replacement in {'"': "``", '"': "''", ''': "`", ''': "'"}.items():
                                # Don't replace quotes that are part of LaTeX commands (after backslash)
                                parts = author.split('\\')
                                new_parts = [parts[0]]  # First part (no backslash)
                                for part in parts[1:]:  # Parts after backslashes
                                    new_parts.append('\\' + part)  # Keep original backslash and part
                                author = ''.join(new_parts)
                                
                            processed_authors.append(author)
                        
                        # Rejoin the authors/editors
                        entry[field] = ' and '.join(processed_authors)
                    else:
                        # For other fields (title, abstract), process in the same way
                        text = entry[field]
                        
                        # Normalize whitespace - collapse multiple spaces and newlines into single space
                        text = ' '.join(text.split())
                        
                        # First handle Unicode replacements (excluding quotes)
                        for char, replacement in unicode_replacements.items():
                            if char not in ['"', '"', ''', ''']:  # Skip quote replacements
                                text = text.replace(char, replacement)
                        
                        # Then handle PDF ligatures
                        for ligature, replacement in pdf_ligature_replacements.items():
                            text = text.replace(ligature, replacement)
                        
                        # Handle quotes with more sophisticated logic
                        text = replace_quotes(text)
                        
                        entry[field] = text

                    # Handle special LaTeX escapes for abstract only
                    if field == 'abstract':
                        for char, replacement in abstract_latex_escapes.items():
                            entry[field] = re.sub(
                                r'(?<!\\)' + re.escape(char),
                                replacement,
                                entry[field]
                            )

    # Define field ordering priority
    proceedings_order = [
        'booktitle',
        'name',
        'shortname',
        'year',
        'editor',
        'volume',
        'start',
        'end',
        'published',
        'address',
        'conference_url',
        'conference_number'
    ]

    inproceedings_order = [
        'title',
        'author',
        'pages',
        'abstract',
        'section',      # optional fields
        'openreview',
        'software',
        'video'
    ]

    # Set up writer with custom ordering
    writer = BibTexWriter()
    writer.indent = '    '
    writer.order_entries_by = None  # Disable entry ordering
    writer.display_order = ['ENTRYTYPE', 'ID'] + proceedings_order + inproceedings_order  # Set field display order
    writer._entry_separator = '\n\n'  # Add blank line between entries

    def custom_entry_sort(entry):
        if entry['ENTRYTYPE'] == 'Proceedings':
            field_order = proceedings_order
        else:  # InProceedings
            field_order = inproceedings_order
        
        # Create ordered dict with fields in specified order
        ordered_entry = {}
        # First add ENTRYTYPE and ID
        ordered_entry['ENTRYTYPE'] = entry['ENTRYTYPE']
        ordered_entry['ID'] = entry['ID']
        # Then add other fields in specified order
        for field in field_order:
            if field in entry:
                ordered_entry[field] = entry[field]
        # Add any remaining fields
        for key, value in entry.items():
            if key not in ordered_entry:
                ordered_entry[key] = value
        
        return ordered_entry

    # Apply ordering to entries
    for entry in bib_database.entries:
        # Store the entry data before clearing
        entry_data = dict(entry)
        # Clear and update with ordered data
        entry.clear()
        entry.update(custom_entry_sort(entry_data))

    # Write fixed BibTeX
    with open(output_file, 'w', encoding='utf-8') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file, writer)

    # Print issues
    if issues:
        logging.warning("\nIssues found:")
        for issue in issues:
            logging.warning(f"- {issue}")
    else:
        logging.info("\nNo issues found!")

    logging.info(f"\nFixed BibTeX written to {output_file}")

    if id_changes:
        logging.info("\nChecking for associated files to rename...")
        directory = os.path.dirname(input_file) if os.path.dirname(input_file) else '.'
        
        for original_id, new_id in id_changes.items():
            # Find all files matching the original ID pattern
            files_to_rename = []
            for filename in os.listdir(directory):
                # Match both direct files and supplementary files
                if (filename.startswith(original_id + '.') or 
                    filename.startswith(original_id + '-supp.')):
                    old_path = os.path.join(directory, filename)
                    # Replace only the ID portion of the filename
                    new_filename = filename.replace(original_id, new_id, 1)
                    new_path = os.path.join(directory, new_filename)
                    files_to_rename.append((old_path, new_path))
            
            if files_to_rename:
                # Check for any destination conflicts
                conflicts = [new_path for _, new_path in files_to_rename if os.path.exists(new_path)]
                if conflicts:
                    logging.warning(f"Cannot rename files for '{original_id}' -> '{new_id}': "
                                  f"destination files already exist: {', '.join(conflicts)}")
                    continue
                
                # List all files that will be renamed
                print(f"\nFound the following files for '{original_id}':")
                for old_path, new_path in files_to_rename:
                    print(f"  {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                
                while True:
                    response = input(f"Rename these files? [y/n]: ").lower()
                    if response in ['y', 'n']:
                        break
                    print("Please answer 'y' or 'n'")
                
                if response == 'y':
                    try:
                        # Perform all renames
                        for old_path, new_path in files_to_rename:
                            shutil.move(old_path, new_path)
                            logging.info(f"Renamed: {old_path} -> {new_path}")
                    except Exception as e:
                        logging.error(f"Error renaming files for {original_id}: {str(e)}")
                else:
                    logging.info(f"Skipped renaming files for {original_id}")
            else:
                logging.info(f"No files found matching '{original_id}.*' or '{original_id}-supp.*'")

def replace_quotes(text):
    """Process quotes in text, handling various edge cases."""
    # First handle quotes within LaTeX commands
    parts = []
    current = 0
    in_command = False
    command_start = 0
    
    for i, char in enumerate(text):
        if char == '\\' and not in_command:
            # Add text before command
            if current < i:
                parts.append(process_quotes_in_text(text[current:i]))
            command_start = i
            in_command = True
        elif in_command and char == '{':
            # Find matching closing brace
            brace_count = 1
            j = i + 1
            while j < len(text) and brace_count > 0:
                if text[j] == '{':
                    brace_count += 1
                elif text[j] == '}':
                    brace_count -= 1
                j += 1
            if brace_count == 0:
                # Add the entire command unchanged
                parts.append(text[command_start:j])
                current = j
                in_command = False
            else:
                # No matching brace found, treat as normal text
                in_command = False
                
    # Add remaining text
    if current < len(text):
        parts.append(process_quotes_in_text(text[current:]))
    
    return ''.join(parts)

def process_quotes_in_text(text):
    """Process quotes in regular text (not in LaTeX commands)."""
    # First handle double quotes
    parts = []
    current = 0
    
    # Pattern for finding quotes, considering context
    quote_pattern = r'(?:^|[(\[{]|\s)"([^"]*)"(?:$|[)\]}]|\s)'
    
    for match in re.finditer(quote_pattern, text):
        # Add text before the quote
        start = match.start()
        if current < start:
            parts.append(text[current:start])
        
        # Get the context and quoted content
        before = match.group(0)[0]
        content = match.group(1)
        after = match.group(0)[-1]
        
        # Add the quote with proper formatting
        if before in '([{':
            parts.append(before)
        elif before.isspace():
            parts.append(before)
        parts.append(f"``{content}''")
        if after in ')]}':
            parts.append(after)
        elif after.isspace():
            parts.append(after)
        
        current = match.end()
    
    # Add remaining text
    if current < len(text):
        parts.append(text[current:])
    
    # Handle single quotes - using plain single quote for closing
    result = ''.join(parts)
    result = re.sub(r"(?<!\w)'([^']+)'(?!\w)", r"`\1'", result)
    
    return result

if __name__ == "__main__":
    check_and_fix_bibtex('corl24.bib', 'corl24_fixed.bib')

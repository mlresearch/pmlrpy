# PMLR BibTeX Validator and Fixer

[![Tests](https://github.com/mlresearch/pmlrpy/actions/workflows/tests.yml/badge.svg)](https://github.com/mlresearch/pmlrpy/actions/workflows/tests.yml)

A Python script to validate and fix BibTeX files according to the [PMLR Proceedings Specification](https://proceedings.mlr.press/spec.html).

## Overview

This script helps conference organizers prepare their BibTeX files for submission to PMLR by:
1. Validating required fields
2. Fixing common Unicode issues
3. Escaping special characters
4. Reporting problems that need manual attention

## Requirements

- Python 3.11+
- bibtexparser (`pip install bibtexparser`)

## Usage

1. Save your BibTeX file as `input.bib`
2. Run: `python pmlrpy.py input.bib output.bib`
3. Check the console for validation messages
4. Review `output.bib` for the fixed version

## What's Implemented

### Validation
- Checks for single @Proceedings entry with required fields:
  - booktitle
  - name  
  - shortname
  - year
  - editor
  - volume
  - start
  - end
  - address
  - conference_url

- Validates @InProceedings entries have:
  - title
  - author
  - pages
  - abstract


### Fixes
- Replaces common Unicode characters with LaTeX equivalents:
  - ö → \"o
  - ü → \"u
  - é → \'e
  - è → \`e
  - á → \'a
  - ñ → \~n
  - — → ---
  - " → ``
  - " → ''
- Escapes % characters in abstracts and titles

## Not Yet Implemented

1. Author name format validation ("Lastname, Firstname")
2. Complex name prefix handling (von, van der, etc.)
3. Section definition validation
4. Math formula validation in abstracts
5. File presence checking for PDFs and supplementary materials
6. HTML tag validation in abstracts (<em>, <b>, etc.)

## Known Limitations

- The script may not catch all Unicode characters
- Complex LaTeX commands in abstracts are not validated
- Author name formatting is not fully validated
- Supplementary material naming conventions are not checked

## References

- [PMLR Specification](https://proceedings.mlr.press/spec.html)
- [PMLR FAQ](https://proceedings.mlr.press/faq.html)

## Contributing

Feel free to submit issues and enhancement requests!

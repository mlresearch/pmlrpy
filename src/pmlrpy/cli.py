from .core import check_and_fix_bibtex

def main():
    import argparse
    parser = argparse.ArgumentParser(description='PMLR BibTeX validator and fixer')
    parser.add_argument('input', help='Input BibTeX file')
    parser.add_argument('output', help='Output BibTeX file')
    args = parser.parse_args()
    
    check_and_fix_bibtex(args.input, args.output)

if __name__ == '__main__':
    main() 
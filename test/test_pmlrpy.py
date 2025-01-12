import pytest
from pmlrpy import check_and_fix_bibtex
import bibtexparser
from bibtexparser.bparser import BibTexParser
import os

@pytest.fixture
def test_bib_file(tmp_path):
    # Create a temporary test file
    test_content = """
@InProceedings{test24,
  title = {Testing λ-Repformer with ﬁ and ﬂ ligatures},
  author = {Müller, José and Łukasz},
  abstract = {This is a test with "smart quotes" and em—dash},
  pages = {1-10},
}
"""
    input_file = tmp_path / "test.bib"
    input_file.write_text(test_content, encoding='utf-8')
    return str(input_file)

@pytest.fixture
def base_proceedings():
    """Returns a standard proceedings entry required for all tests"""
    return """@Proceedings{corl2024,
  booktitle = {Conference on Robot Learning},
  name = {Conference on Robot Learning},
  shortname = {CoRL},
  year = {2024},
  editor = {Some Editor},
  volume = {1},
  start = {2024-01-01},
  end = {2024-01-05},
  published = {2024-03-01},
  address = {Virtual Conference},
  conference_url = {https://corl2024.org}
}

"""

def test_unicode_replacement(test_bib_file, tmp_path, base_proceedings):
    output_file = str(tmp_path / "test_fixed.bib")
    
    # Combine proceedings with test content
    with open(test_bib_file, 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    combined_content = base_proceedings + test_content
    input_file = tmp_path / "combined.bib"
    input_file.write_text(combined_content, encoding='utf-8')
    
    check_and_fix_bibtex(str(input_file), output_file)
    
    # Read the output file
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check specific replacements
    assert '\\lambda' in content     # λ should be replaced
    assert 'fi' in content          # ﬁ ligature should be replaced
    assert 'fl' in content          # ﬂ ligature should be replaced
    assert '\\"{u}' in content      # ü should be replaced with properly escaped and braced version

def test_real_corl_file(tmp_path):
    output_file = str(tmp_path / "corl24_fixed.bib")
    
    # Process the input file
    check_and_fix_bibtex('test/corl24.bib', output_file)
    
    # Read the processed output file
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find any remaining unicode characters
    unicode_chars = set()
    for char in content:
        if ord(char) > 127:  # Non-ASCII characters
            unicode_chars.add(char)
    
    if unicode_chars:
        print("\nFound unicode characters in processed output file:")
        for char in sorted(unicode_chars):
            print(f"Character: {char}, Unicode: U+{ord(char):04X}")
    
    assert not unicode_chars, "Found unexpected unicode characters in processed output"

def test_specific_entries():
    # Test specific entries we know have issues
    parser = bibtexparser.bparser.BibTexParser()
    
    with open('test/corl24.bib', 'r', encoding='utf-8') as f:
        db = bibtexparser.load(f, parser)
    
    # Check specific entries we saw in the snippets
    entries_to_check = ['goko24', 'murray24', 'ko24a']
    
    issues_found = []
    for entry_id in entries_to_check:
        entry = next((e for e in db.entries if e['ID'] == entry_id), None)
        if entry:
            for field, value in entry.items():
                if isinstance(value, str):
                    unicode_chars = [c for c in value if ord(c) > 127]
                    if unicode_chars:
                        issues_found.append(f"Entry {entry_id}, field {field} contains unicode: {''.join(unicode_chars)}")
    
    if issues_found:
        print("\nSpecific entry issues found:")
        for issue in issues_found:
            print(issue)
        
    assert not issues_found, "Found unicode characters in specific entries" 

@pytest.fixture
def complex_test_bib(tmp_path):
    test_content = '''@Inproceedings{el-agroudi24,
    title = {In-Flight Attitude Control of a Quadruped using Deep
Reinforcement Learning},
    author = {El-Agroudi, Tarek and Maurer, Finn Gross and Olsen,
Jørgen Anker and Alexis, Kostas},
    pages = {5014-5029},
    abstract = {We present the development and real world
demonstration of an in-flight attitude control law
for a small low-cost quadruped with a
five-bar-linkage leg design using only its legs as
reaction masses. The control law is trained using
deep reinforcement learning (DRL) and specifically
through Proximal Policy Optimization (PPO) in the
NVIDIA Omniverse Isaac Sim simulator with a
GPU-accelerated DRL pipeline. To demonstrate the
policy, a small quadruped is designed, constructed,
and evaluated both on a rotating pole test setup and
in free fall. During a free fall of 0.7 seconds, the
quadruped follows commanded attitude steps of 45
degrees in all principal axes, and achieves an
average base angular velocity of 110 degrees per
second during large attitude reference steps.},
    section = {Poster},
    openreview = {67tTQeO4HQ},
    software = {https://github.com/ntnu-arl/Eurepus-RL and
https://github.com/ntnu-arl/Eurepus-design},
    video = {https://www.youtube.com/watch?v=5qNPCH34M2M&t=1s}
}'''
    input_file = tmp_path / "complex_test.bib"
    input_file.write_text(test_content, encoding='utf-8')
    return str(input_file)

def test_complex_entry(tmp_path, caplog, base_proceedings):
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    # Write test entry to file with proceedings
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{el-agroudi24,
  title =	 {In-Flight Attitude Control of a Quadruped using Deep
                   Reinforcement Learning},
  section =	 {Poster},
  author =	 {El-Agroudi, Tarek and Maurer, Finn Gross and Olsen,
                   Jørgen Anker and Alexis, Kostas},
  pages =	 {5014-5029},
  openreview =	 {67tTQeO4HQ},
  abstract =	 {We present the development and real world
                   demonstration of an in-flight attitude control law
                   for a small low-cost quadruped with a
                   five-bar-linkage leg design using only its legs as
                   reaction masses.},
  software =	 {https://github.com/ntnu-arl/Eurepus-RL and
                   https://github.com/ntnu-arl/Eurepus-design},
  video =	 {https://www.youtube.com/watch?v=5qNPCH34M2M&t=1s},
}""")

    # Process the file
    check_and_fix_bibtex(input_file, output_file)

    # Read and parse the output file
    with open(output_file) as f:
        parser = BibTexParser()
        bib_database = bibtexparser.load(f, parser)

    # Check that we got exactly one entry
    assert len(bib_database.entries) == 2
    entry = bib_database.entries[1]

    # Verify the warning was logged
    assert any("Software field should contain a single valid URL" in record.message 
              for record in caplog.records)

    # Verify other fields are correct
    assert entry['ENTRYTYPE'] == 'inproceedings'
    assert entry['ID'] == 'el-agroudi24'
    assert entry['pages'] == '5014-5029'
    assert 'J\\o{}rgen' in entry['author']  # Check that special character was preserved 

def test_issues():
    # Process the file
    check_and_fix_bibtex('test/corl24.bib', 'test/corl24_fixed.bib')

    # Read and parse the output file
    with open('test/corl24_fixed.bib') as f:
        parser = BibTexParser()
        bib_database = bibtexparser.load(f, parser)

    # Find the specific entry
    entry = next(e for e in bib_database.entries if e['ID'] == 'el-agroudi24')
    
    # Verify fields
    assert entry['ENTRYTYPE'] == 'inproceedings'
    assert entry['pages'] == '5014-5029'
    assert 'J\\o{}rgen' in entry['author']
    
    # Clean up
    os.remove('test/corl24_fixed.bib') 

def test_proceedings_entry(tmp_path):
    """Test validation of Proceedings entry fields"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    # Create a proceedings entry missing some required fields
    with open(input_file, "w") as f:
        f.write("""@Proceedings{corl2024,
  booktitle = {Conference on Robot Learning},
  name = {Conference on Robot Learning},
  year = {2024},
  editor = {Some Editor},
  volume = {1}
}""")

    # Process the file and capture logs
    with pytest.raises(ValueError) as exc_info:
        check_and_fix_bibtex(str(input_file), str(output_file))
    
    # Verify that the error message mentions missing fields
    assert "Missing required field(s) in Proceedings" in str(exc_info.value)

def test_id_normalization(tmp_path, base_proceedings):
    """Test normalization of entry IDs containing Unicode characters"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    # Create entries with Unicode IDs
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{müller24,
  title = {Test Title},
  author = {Test Author},
  pages = {1-10},
  abstract = {Test abstract}
}

@InProceedings{größe24,
  title = {Another Test},
  author = {Another Author},
  pages = {11-20},
  abstract = {Another abstract}
}""")

    check_and_fix_bibtex(str(input_file), str(output_file))
    
    # Read the output and verify ID normalization
    with open(output_file) as f:
        parser = BibTexParser()
        bib_database = bibtexparser.load(f, parser)
    
    ids = [entry['ID'] for entry in bib_database.entries]
    assert 'muller24' in ids
    assert 'grosse24' in ids

def test_quote_handling(tmp_path, base_proceedings):
    """Test proper handling of different types of quotes"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{test24,
  title = {Test with "smart quotes" and 'single quotes'},
  author = {Test Author},
  pages = {1-10},
  abstract = {Testing "quotes" within text and within \\command{"quoted"}. Also 'single' quotes.}
}""")

    check_and_fix_bibtex(str(input_file), str(output_file))
    
    with open(output_file) as f:
        content = f.read()
    
    # Check quote replacements
    assert '``smart quotes\'\'' in content
    assert '\\command{"quoted"}' in content  # Quotes in LaTeX commands should be preserved
    assert '`single\'' in content

def test_field_ordering(tmp_path, base_proceedings):
    """Test that fields are ordered correctly in the output"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    # Create entry with fields in random order
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{test24,
  video = {http://example.com},
  abstract = {Test abstract},
  author = {Test Author},
  title = {Test Title},
  pages = {1-10},
  software = {http://example.com},
  section = {Poster}
}""")

    check_and_fix_bibtex(str(input_file), str(output_file))
    
    with open(output_file) as f:
        content = f.read()
    
    # Check field order (title should come before author, etc.)
    title_pos = content.find('title')
    author_pos = content.find('author')
    pages_pos = content.find('pages')
    abstract_pos = content.find('abstract')
    
    assert title_pos < author_pos < pages_pos < abstract_pos

def test_latex_escapes_in_abstract(tmp_path, base_proceedings):
    """Test that special LaTeX characters are properly escaped in abstracts"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{test24,
  title = {Test Title},
  author = {Test Author},
  pages = {1-10},
  abstract = {Testing special characters: 100% accuracy & more}
}""")

    check_and_fix_bibtex(str(input_file), str(output_file))
    
    with open(output_file) as f:
        content = f.read()
    
    assert '100\\%' in content
    assert '\\&' in content 

def test_quote_handling_with_brackets(tmp_path, base_proceedings):
    """Test proper handling of quotes around brackets and at string boundaries"""
    input_file = tmp_path / "test.bib"
    output_file = tmp_path / "test_fixed.bib"
    
    with open(input_file, "w") as f:
        f.write(base_proceedings + """@InProceedings{test24,
  title = {"[Bracketed] Title"},
  author = {Test Author},
  pages = {1-10},
  abstract = {Testing "[quoted] brackets" and "(quoted) parens" and "{quoted} braces".
             Also testing "string start" and "string end".
             Multiple "quoted" words in "one string".
             Nested [("quoted")] elements.}
}""")

    check_and_fix_bibtex(str(input_file), str(output_file))
    
    with open(output_file) as f:
        content = f.read()
    # Display the content to the test console here for debugging
    print(content)
    # Check quote replacements in various contexts
    assert '``[Bracketed] Title\'\'' in content  # Quotes around entire bracketed title
    assert '``[quoted] brackets\'\'' in content    # Quotes around word with brackets after
    assert '``(quoted) parens\'\'' in content     # Quotes around word with parens after
    assert '``{quoted} braces\'\'' in content     # Quotes around word with braces after
    assert '``string start\'\'' in content      # Quotes at start of string
    assert '``string end\'\'' in content        # Quotes at end of string
    assert '``quoted\'\' words in ``one string\'\'' in content  # Multiple quotes in one string
    assert '[(``quoted\'\')]' in content            # Nested quotes within brackets 
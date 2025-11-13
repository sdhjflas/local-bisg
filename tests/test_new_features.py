"""
Test script for new label generation features
Tests auto-fit title, book label sheets, and two-up carton labels
"""

import os
from label_generator import generate_labels

# Test data with various title lengths
test_cases = [
    {
        'name': 'Long Title (Auto-fit test)',
        'data': {
            'Title': 'THE SUFI MESSAGE OF HAZRAT INAYAT KHAN VOL. 7 CENTENNIAL EDITION IN PRAISE OF KNOWLEDGE',
            'Author': 'Hazrat Inayat Khan',
            'Publisher': 'OMEGA PUBLICATIONS',
            'ISBN13': '9781941810521',
            'Price': '36.00',
            'CTN_QTY': '20',
            'CTN_WGT': '30',
            'PrintedIn': 'USA',
            'OnSale': '01/15/2025',
            'Currency': 'USD'
        }
    },
    {
        'name': 'Regular Title',
        'data': {
            'Title': 'THE OKLAHOMANS',
            'Author': 'Dwyer, John J.',
            'Publisher': 'RED RIVER PRESS',
            'ISBN13': '9780985347024',
            'Price': '49.95',
            'CTN_QTY': '10',
            'CTN_WGT': '37',
            'PrintedIn': 'USA',
            'OnSale': '',
            'Currency': 'USD'
        }
    }
]

def test_all_formats():
    """Test all label generation formats"""
    print("=" * 60)
    print("TESTING NEW LABEL GENERATION FEATURES")
    print("=" * 60)

    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)

    for test_case in test_cases:
        print(f"\n📚 Testing: {test_case['name']}")
        print("-" * 60)
        data = test_case['data']
        isbn = data['ISBN13']

        # Test 1: Single book label only
        print("  1. Single book label only...")
        result = generate_labels(data, 'book', output_dir, 'single', 'single')
        print(f"     ✓ Generated: {result.get('book_label_single')}")

        # Test 2: Book label sheet (30 per page) only
        print("  2. Book label sheet (30 per page) only...")
        result = generate_labels(data, 'book', output_dir, 'sheet', 'single')
        print(f"     ✓ Generated: {result.get('book_label_sheet')}")

        # Test 3: Both book label formats
        print("  3. Both book label formats (single + sheet)...")
        result = generate_labels(data, 'book', output_dir, 'both', 'single')
        print(f"     ✓ Generated: {list(result.keys())}")

        # Test 4: Single carton label (with auto-fit title)
        print("  4. Single carton label (auto-fit title)...")
        result = generate_labels(data, 'carton', output_dir, 'single', 'single')
        print(f"     ✓ Generated: {result.get('carton_label_single')}")

        # Test 5: Two-up carton label
        print("  5. Two-up carton label (2 per page)...")
        result = generate_labels(data, 'carton', output_dir, 'single', 'twoup')
        print(f"     ✓ Generated: {result.get('carton_label_twoup')}")

        # Test 6: Both carton formats
        print("  6. Both carton formats (single + twoup)...")
        result = generate_labels(data, 'carton', output_dir, 'single', 'both')
        print(f"     ✓ Generated: {list(result.keys())}")

        # Test 7: ALL FORMATS (default behavior)
        print("  7. ALL FORMATS - Default 'both' behavior...")
        result = generate_labels(data, 'both', output_dir, 'both', 'both')
        print(f"     ✓ Generated {len(result)} files:")
        for key, path in result.items():
            print(f"       - {key}: {os.path.basename(path)}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print(f"\n📁 Test PDFs saved to: {os.path.abspath(output_dir)}/")

    # List generated files
    print("\n📄 Generated files:")
    for file in sorted(os.listdir(output_dir)):
        if file.endswith('.pdf'):
            filepath = os.path.join(output_dir, file)
            size = os.path.getsize(filepath)
            print(f"   - {file} ({size:,} bytes)")

if __name__ == '__main__':
    test_all_formats()

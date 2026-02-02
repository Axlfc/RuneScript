import sys
import os

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup4 not installed. Basic check only.")
    BeautifulSoup = None

def verify_html(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if BeautifulSoup:
            soup = BeautifulSoup(content, 'html.parser')
            # Basic validation: check for <html>, <head>, <body>
            missing = []
            if not soup.find('html'): missing.append('<html>')
            if not soup.find('body'): missing.append('<body>')

            if missing:
                print(f"❌ HTML is missing core tags: {', '.join(missing)}")
                sys.exit(1)
            else:
                print(f"✅ HTML structure in {file_path} looks valid.")
        else:
            if "<html" in content.lower() and "<body" in content.lower():
                print(f"✅ Basic HTML check passed for {file_path}")
            else:
                print(f"❌ HTML check failed for {file_path}")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error verifying HTML: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_html.py <file_path>")
        sys.exit(1)

    verify_html(sys.argv[1])

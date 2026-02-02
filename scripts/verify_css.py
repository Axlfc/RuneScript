import sys
import os
import re

def verify_css(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple regex check for CSS blocks: selector { property: value; }
        if re.search(r"[^{]+\s*\{[^}]+\}", content):
            print(f"✅ CSS in {file_path} contains valid-looking rules.")
            sys.exit(0)
        else:
            print(f"❌ No valid CSS rules found in {file_path}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error verifying CSS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_css.py <file_path>")
        sys.exit(1)

    verify_css(sys.argv[1])

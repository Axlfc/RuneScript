import os
import sys

def verify_structure(required_paths):
    """Verify that all required paths exist."""
    missing = []
    for path in required_paths:
        if not os.path.exists(path):
            missing.append(path)

    if missing:
        print(f"❌ Missing paths: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("✅ All required paths exist.")
        sys.exit(0)

if __name__ == "__main__":
    # Expecting paths as command line arguments
    if len(sys.argv) < 2:
        print("Usage: python verify_structure.py <path1> <path2> ...")
        sys.exit(1)

    verify_structure(sys.argv[1:])

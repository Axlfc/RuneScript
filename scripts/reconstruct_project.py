#!/usr/bin/env python3
import sys
import os
import argparse

# Add current directory to path to allow importing from lib
sys.path.append(os.getcwd())

from lib.nia_reconstructor import ProjectReconstructor

def main():
    parser = argparse.ArgumentParser(description="Rebuild a nIA project from its patch history.")
    parser.add_argument("project_path", help="Path to the existing project containing .nia directory")
    parser.add_argument("output_path", help="Path where the rebuilt project will be created")
    parser.add_argument("--report", action="store_true", help="Generate HTML history report before rebuilding")
    parser.add_argument("--export", help="Export .nia history to a tar.gz file")

    args = parser.parse_args()

    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist.")
        sys.exit(1)

    reconstructor = ProjectReconstructor(args.project_path)

    if args.report:
        print("📊 Generating HTML history report...")
        report_path = reconstructor.generate_html_report()
        print(f"✅ Report generated at: {report_path}")

    if args.export:
        print(f"📦 Exporting history to {args.export}...")
        export_path = reconstructor.export_history(args.export)
        print(f"✅ History exported to: {export_path}")

    success = reconstructor.rebuild_from_patches(args.output_path)

    if success:
        print("\n✨ Reconstruction completed successfully!")
    else:
        print("\n❌ Reconstruction failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

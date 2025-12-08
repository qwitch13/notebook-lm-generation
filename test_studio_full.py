#!/usr/bin/env python3
"""
NotebookLM Studio Full Automation Test

Commands:
    python test_studio_full.py                         # Generate all materials
    python test_studio_full.py --download              # Download all completed materials
    python test_studio_full.py --create "My Notebook"  # Create new notebook
    python test_studio_full.py --list-sources          # List sources
    python test_studio_full.py --list-materials        # List generated materials

Examples:
    # Generate audio for sources matching "audiobook"
    python test_studio_full.py --single audiobook --materials audio
    
    # Download all videos and mindmaps
    python test_studio_full.py --download
    
    # Create notebook and add PDF sources
    python test_studio_full.py --create "Study Guide" --files ~/Documents/*.pdf
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.auth.google_auth import GoogleAuthenticator
from src.generators.notebooklm import NotebookLMClient
from src.generators.studio_automator import (
    StudioAutomator, 
    MaterialType,
    quick_download_all,
    quick_generate_all
)
from src.utils.logger import setup_logger

TEST_NOTEBOOK = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM Studio Full Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-sources          # List all sources
  %(prog)s --list-materials        # List generated materials  
  %(prog)s                         # Generate all materials for all sources
  %(prog)s --materials audio video # Generate only audio and video
  %(prog)s --download              # Download all completed materials
  %(prog)s --create "My Notes"     # Create new notebook
        """
    )
    
    # Notebook selection
    parser.add_argument("--notebook", "-n", default=TEST_NOTEBOOK,
                        help="Notebook URL")
    
    # Actions
    parser.add_argument("--list-sources", "-l", action="store_true",
                        help="List sources and exit")
    parser.add_argument("--list-materials", action="store_true",
                        help="List generated materials and exit")
    parser.add_argument("--download", "-d", action="store_true",
                        help="Download all completed materials")
    parser.add_argument("--create", metavar="NAME",
                        help="Create new notebook with given name")
    
    # Source filtering
    parser.add_argument("--sources", "-s", nargs="+",
                        help="Source name patterns to process")
    parser.add_argument("--single", help="Process sources matching pattern")
    
    # Material selection
    parser.add_argument("--materials", "-m", nargs="+",
                        choices=["audio", "video", "mindmap", "quiz", "flashcards", "infographic"],
                        help="Materials to generate (default: all)")
    
    # Source addition
    parser.add_argument("--files", "-f", nargs="+",
                        help="Files to add as sources")
    parser.add_argument("--text", help="Text file to add as source")
    
    # Options
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode")
    parser.add_argument("--wait", type=int, default=0,
                        help="Wait N seconds before starting")
    
    args = parser.parse_args()
    
    # Setup
    logger = setup_logger()
    print("=" * 60)
    print("NotebookLM Studio Full Automation")
    print("=" * 60)
    
    # Initialize browser
    print("\n🌐 Initializing browser...")
    auth = GoogleAuthenticator(headless=args.headless)
    driver = auth.get_driver()
    
    if not driver:
        print("❌ Failed to initialize browser")
        return 1
    
    try:
        # Create new notebook if requested
        if args.create:
            print(f"\n📓 Creating new notebook: {args.create}")
            studio = StudioAutomator(driver)
            notebook_url = studio.create_new_notebook(args.create)
            
            if notebook_url:
                print(f"   ✅ Created: {notebook_url}")
                args.notebook = notebook_url
            else:
                print("   ❌ Failed to create notebook")
                return 1
        else:
            # Navigate to existing notebook
            print(f"\n📓 Opening notebook...")
            client = NotebookLMClient(auth)
            if not client.navigate_to_notebook(args.notebook):
                print("❌ Failed to navigate to notebook")
                return 1
            print("   ✅ Notebook loaded")
        
        time.sleep(3 + args.wait)
        
        # Create automation instance
        studio = StudioAutomator(driver)
        
        # Add sources if provided
        if args.files:
            print(f"\n📁 Adding {len(args.files)} file sources...")
            for f in args.files:
                if studio.add_source_file(f):
                    print(f"   ✅ Added: {f}")
                else:
                    print(f"   ❌ Failed: {f}")
        
        if args.text:
            print(f"\n📝 Adding text source...")
            with open(args.text, 'r') as f:
                text_content = f.read()
            if studio.add_source_text(text_content, Path(args.text).stem):
                print("   ✅ Text source added")
            else:
                print("   ❌ Failed to add text source")
        
        # List sources
        if args.list_sources:
            print("\n📋 Sources in notebook:")
            sources = studio.list_sources()
            if sources:
                for i, s in enumerate(sources, 1):
                    print(f"  {i}. {s.name}")
            else:
                print("  (No sources found)")
            return 0
        
        # List materials
        if args.list_materials:
            print("\n📋 Generated materials:")
            materials = studio.list_generated_materials()
            if materials:
                for i, m in enumerate(materials, 1):
                    status = "⏳" if m['status'] == 'generating' else "✅"
                    dl = "📥" if m['downloadable'] else "🔗"
                    print(f"  {status} {dl} [{m['type']}] {m['name'][:50]}")
            else:
                print("  (No materials found)")
            return 0
        
        # Download materials
        if args.download:
            print("\n📥 Downloading all materials...")
            results = studio.download_all_materials()
            
            print(f"\n📊 Download Results:")
            print(f"   Total: {results['total']}")
            print(f"   Downloaded: {results['downloaded']}")
            print(f"   Skipped: {results['skipped']}")
            print(f"   Failed: {results['failed']}")
            
            if results['downloaded'] > 0:
                print("\n   Files saved to your Downloads folder")
            return 0
        
        # Generate materials (default action)
        materials = None
        if args.materials:
            material_map = {
                "audio": MaterialType.AUDIO,
                "video": MaterialType.VIDEO,
                "mindmap": MaterialType.MINDMAP,
                "quiz": MaterialType.QUIZ,
                "flashcards": MaterialType.FLASHCARDS,
                "infographic": MaterialType.INFOGRAPHIC,
            }
            materials = [material_map[m] for m in args.materials]
            print(f"\n📦 Selected materials: {', '.join(args.materials)}")
        else:
            print("\n📦 Generating all 6 material types")
        
        # Source patterns
        source_patterns = args.sources
        if args.single:
            source_patterns = [args.single]
        
        # List sources
        sources = studio.list_sources()
        if not sources:
            print("⚠️ No sources found in notebook")
            return 1
        
        print(f"\n📁 Found {len(sources)} sources")
        
        # Calculate work
        if source_patterns:
            matching = [s for s in sources 
                       if any(p.lower() in s.name.lower() for p in source_patterns)]
            sources = matching
            print(f"   Matching pattern: {len(matching)}")
        
        num_materials = len(materials) if materials else 6
        print(f"   Materials per source: {num_materials}")
        print(f"   Total operations: {len(sources) * num_materials}")
        
        input("\nPress Enter to start (Ctrl+C to cancel)...")
        
        # Run generation
        results = studio.process_all_sources(
            source_patterns=source_patterns,
            materials=materials
        )
        
        # Print report
        print(studio.get_summary_report())
        
        print("\n✅ Generation complete!")
        print("   Materials are processing in the background.")
        print("\n   Generation times:")
        print("   • Audio/Video: 3-15 minutes")
        print("   • Mindmap/Quiz/Flashcards: 1-5 minutes")
        print("   • Infographic: 3-8 minutes")
        print("\n   Run with --download later to download completed files.")
        
        input("\nPress Enter to close browser...")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

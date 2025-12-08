#!/usr/bin/env python3
"""
NotebookLM Studio Full Automation with Batch Processing

Commands:
    python test_studio_full.py --batch ~/Documents/study/  # Process all PDFs in folder
    python test_studio_full.py --file document.pdf         # Process single file
    python test_studio_full.py --download                  # Download completed materials
    python test_studio_full.py --list-sources              # List sources in notebook

Batch Mode:
    For each PDF in folder:
    1. Create notebook (name = filename or custom)
    2. Add PDF as source
    3. Generate all materials
    4. Move to next file
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from src.auth.google_auth import GoogleAuthenticator
from src.generators.notebooklm import NotebookLMClient
from src.generators.studio_automator import (
    StudioAutomator, 
    MaterialType,
)
from src.utils.logger import setup_logger

TEST_NOTEBOOK = "https://notebooklm.google.com/notebook/a39ed9e3-62be-43ca-96b7-6d97d7dd4009"


def get_files_from_folder(folder_path: str, extensions: List[str] = None) -> List[Path]:
    """Get all matching files from a folder."""
    if extensions is None:
        extensions = ['.pdf', '.txt', '.md', '.docx']
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    files = []
    for ext in extensions:
        files.extend(folder.glob(f"*{ext}"))
        files.extend(folder.glob(f"**/*{ext}"))  # Recursive
    
    # Sort by name
    files = sorted(set(files))
    return files


def prompt_notebook_name(default_name: str) -> str:
    """Prompt user for notebook name with default."""
    print(f"\n📓 Notebook name (Enter for '{default_name}'): ", end="")
    user_input = input().strip()
    return user_input if user_input else default_name


def process_single_file(
    studio: StudioAutomator,
    file_path: Path,
    materials: List[MaterialType] = None,
    auto_name: bool = False,
    custom_name: str = None
) -> dict:
    """
    Process a single file: create notebook, add source, generate materials.
    
    Args:
        studio: StudioAutomator instance
        file_path: Path to the file
        materials: Materials to generate (default: all)
        auto_name: Use filename as notebook name without prompting
        custom_name: Override name (skips prompt)
    
    Returns:
        dict with results
    """
    result = {
        'file': str(file_path),
        'notebook_url': None,
        'notebook_name': None,
        'source_added': False,
        'materials_started': 0,
        'errors': []
    }
    
    # Determine notebook name
    default_name = file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    if custom_name:
        notebook_name = custom_name
    elif auto_name:
        notebook_name = default_name
    else:
        notebook_name = prompt_notebook_name(default_name)
    
    result['notebook_name'] = notebook_name
    
    print(f"\n{'='*60}")
    print(f"📄 Processing: {file_path.name}")
    print(f"📓 Notebook: {notebook_name}")
    print(f"{'='*60}")
    
    # Step 1: Create notebook
    print("\n1️⃣ Creating notebook...")
    notebook_url = studio.create_new_notebook(notebook_name)
    
    if not notebook_url:
        result['errors'].append("Failed to create notebook")
        print("   ❌ Failed to create notebook")
        return result
    
    result['notebook_url'] = notebook_url
    print(f"   ✅ Created: {notebook_url}")
    
    # Step 2: Add file as source
    print("\n2️⃣ Adding source file...")
    time.sleep(2)  # Wait for notebook to fully load
    
    if studio.add_source_file(str(file_path)):
        result['source_added'] = True
        print(f"   ✅ Added: {file_path.name}")
    else:
        result['errors'].append("Failed to add source file")
        print(f"   ❌ Failed to add source")
        return result
    
    # Wait for source to be processed
    print("   ⏳ Waiting for source processing...")
    time.sleep(10)
    
    # Step 3: Generate materials
    print("\n3️⃣ Generating materials...")
    
    # Get sources (should be just the one we added)
    sources = studio.list_sources()
    
    if not sources:
        print("   ⚠️ No sources found, waiting more...")
        time.sleep(5)
        sources = studio.list_sources()
    
    if sources:
        # Generate for the source
        gen_results = studio.process_all_sources(materials=materials)
        
        # Count successes
        for source_name, statuses in gen_results.items():
            for status in statuses:
                if status.started:
                    result['materials_started'] += 1
        
        print(f"   ✅ Started {result['materials_started']} material generations")
    else:
        result['errors'].append("No sources available for generation")
        print("   ❌ No sources found")
    
    return result


def batch_process(
    studio: StudioAutomator,
    files: List[Path],
    materials: List[MaterialType] = None,
    auto_name: bool = False,
    delay_between: int = 5
) -> List[dict]:
    """
    Process multiple files in batch.
    
    Args:
        studio: StudioAutomator instance
        files: List of file paths
        materials: Materials to generate
        auto_name: Auto-name notebooks from filenames
        delay_between: Seconds to wait between files
    
    Returns:
        List of result dicts
    """
    results = []
    total = len(files)
    
    print("\n" + "#" * 60)
    print(f"# BATCH PROCESSING: {total} files")
    print("#" * 60)
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{total}] Processing {file_path.name}...")
        
        result = process_single_file(
            studio=studio,
            file_path=file_path,
            materials=materials,
            auto_name=auto_name
        )
        results.append(result)
        
        # Summary for this file
        if result['errors']:
            print(f"   ⚠️ Completed with errors: {result['errors']}")
        else:
            print(f"   ✅ Completed: {result['materials_started']} materials started")
        
        # Delay between files (except last)
        if i < total:
            print(f"\n   ⏳ Waiting {delay_between}s before next file...")
            time.sleep(delay_between)
    
    # Final summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 60)
    
    success = sum(1 for r in results if not r['errors'])
    failed = sum(1 for r in results if r['errors'])
    total_materials = sum(r['materials_started'] for r in results)
    
    print(f"  Files processed: {len(results)}")
    print(f"  Successful: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total materials started: {total_materials}")
    
    print("\n📓 Created notebooks:")
    for r in results:
        status = "✅" if not r['errors'] else "❌"
        print(f"  {status} {r['notebook_name']}: {r['notebook_url'] or 'N/A'}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM Studio Full Automation with Batch Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in a folder (prompts for each notebook name)
  %(prog)s --batch ~/Documents/study/
  
  # Process folder with auto-naming (uses filenames)
  %(prog)s --batch ~/Documents/study/ --auto-name
  
  # Process single file
  %(prog)s --file lecture.pdf
  
  # Process file with custom notebook name
  %(prog)s --file lecture.pdf --name "Networking Lecture 1"
  
  # Generate only audio and mindmap
  %(prog)s --batch ~/study/ --materials audio mindmap --auto-name
  
  # Use existing notebook
  %(prog)s --notebook URL --list-sources
  %(prog)s --notebook URL --download
        """
    )
    
    # Input modes
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--batch", "-b", metavar="FOLDER",
                             help="Process all files in folder")
    input_group.add_argument("--file", "-f", metavar="FILE",
                             help="Process single file")
    input_group.add_argument("--notebook", "-n", metavar="URL",
                             help="Use existing notebook")
    
    # Naming
    parser.add_argument("--name", metavar="NAME",
                        help="Custom notebook name (for --file)")
    parser.add_argument("--auto-name", "-a", action="store_true",
                        help="Auto-name notebooks from filenames (no prompts)")
    
    # Actions for existing notebook
    parser.add_argument("--list-sources", "-l", action="store_true",
                        help="List sources and exit")
    parser.add_argument("--list-materials", action="store_true",
                        help="List generated materials")
    parser.add_argument("--download", "-d", action="store_true",
                        help="Download all completed materials")
    
    # Material selection
    parser.add_argument("--materials", "-m", nargs="+",
                        choices=["audio", "video", "mindmap", "quiz", "flashcards", "infographic"],
                        help="Materials to generate (default: all)")
    
    # Options
    parser.add_argument("--extensions", "-e", nargs="+", default=[".pdf"],
                        help="File extensions for batch mode (default: .pdf)")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay between files in batch mode (default: 5s)")
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.batch and not args.file and not args.notebook:
        parser.print_help()
        print("\n❌ Please specify --batch, --file, or --notebook")
        return 1
    
    # Setup
    logger = setup_logger()
    print("=" * 60)
    print("NotebookLM Studio Full Automation")
    print("=" * 60)
    
    # Parse materials
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
        print(f"📦 Materials: {', '.join(args.materials)}")
    else:
        print("📦 Materials: all (audio, video, mindmap, quiz, flashcards, infographic)")
    
    # Initialize browser
    print("\n🌐 Initializing browser...")
    auth = GoogleAuthenticator(headless=args.headless)
    driver = auth.get_driver()
    
    if not driver:
        print("❌ Failed to initialize browser")
        return 1
    
    try:
        studio = StudioAutomator(driver)
        
        # === BATCH MODE ===
        if args.batch:
            print(f"\n📁 Scanning folder: {args.batch}")
            files = get_files_from_folder(args.batch, args.extensions)
            
            if not files:
                print(f"❌ No files found with extensions: {args.extensions}")
                return 1
            
            print(f"   Found {len(files)} files:")
            for f in files[:10]:
                print(f"   • {f.name}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more")
            
            if not args.auto_name:
                print("\n💡 Tip: Use --auto-name to skip name prompts")
            
            input(f"\nPress Enter to process {len(files)} files (Ctrl+C to cancel)...")
            
            results = batch_process(
                studio=studio,
                files=files,
                materials=materials,
                auto_name=args.auto_name,
                delay_between=args.delay
            )
            
            print("\n✅ Batch processing complete!")
            print("   Materials are generating in the background.")
            print("   Use --notebook URL --download to download later.")
            
        # === SINGLE FILE MODE ===
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {args.file}")
                return 1
            
            result = process_single_file(
                studio=studio,
                file_path=file_path,
                materials=materials,
                auto_name=args.auto_name,
                custom_name=args.name
            )
            
            if result['errors']:
                print(f"\n⚠️ Completed with errors: {result['errors']}")
            else:
                print(f"\n✅ Processing complete!")
                print(f"   Notebook: {result['notebook_url']}")
                print(f"   Materials started: {result['materials_started']}")
        
        # === EXISTING NOTEBOOK MODE ===
        elif args.notebook:
            print(f"\n📓 Opening notebook: {args.notebook[:50]}...")
            client = NotebookLMClient(auth)
            
            if not client.navigate_to_notebook(args.notebook):
                print("❌ Failed to navigate to notebook")
                return 1
            
            print("   ✅ Notebook loaded")
            time.sleep(3)
            
            # List sources
            if args.list_sources:
                print("\n📋 Sources:")
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
                mats = studio.list_generated_materials()
                if mats:
                    for m in mats:
                        status = "⏳" if m['status'] == 'generating' else "✅"
                        dl = "📥" if m['downloadable'] else "🔗"
                        print(f"  {status} {dl} [{m['type']}] {m['name'][:50]}")
                else:
                    print("  (No materials found)")
                return 0
            
            # Download
            if args.download:
                print("\n📥 Downloading materials...")
                results = studio.download_all_materials()
                print(f"\n   Downloaded: {results['downloaded']}")
                print(f"   Skipped: {results['skipped']}")
                print(f"   Failed: {results['failed']}")
                return 0
            
            # Default: generate materials
            print("\n🎬 Generating materials...")
            sources = studio.list_sources()
            if sources:
                studio.process_all_sources(materials=materials)
                print(studio.get_summary_report())
            else:
                print("⚠️ No sources found")
        
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

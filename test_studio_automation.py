#!/usr/bin/env python3
"""
Full Studio Automation Test Script

Usage:
    python3 test_studio_automation.py --notebook-url "https://notebooklm.google.com/notebook/..."
    python3 test_studio_automation.py --notebook-url "..." --test sources  # Just list sources
    python3 test_studio_automation.py --notebook-url "..." --test single   # One material per source
    python3 test_studio_automation.py --notebook-url "..." --test all      # All materials all sources
    python3 test_studio_automation.py --notebook-url "..." --pattern "audiobook" --test all
"""

import sys
import os
import argparse
import time

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.auth.google_auth import GoogleAuthenticator
from src.generators.notebooklm import NotebookLMClient
from src.generators.studio_automator import StudioAutomator, MaterialType


def test_sources(automator: StudioAutomator):
    """List all sources in the notebook."""
    print("\n" + "=" * 60)
    print("TEST: List Sources")
    print("=" * 60)
    
    sources = automator.list_sources()
    
    if not sources:
        print("❌ No sources found!")
        return False
        
    print(f"\n✅ Found {len(sources)} sources:\n")
    for i, source in enumerate(sources):
        print(f"  [{i+1}] {source.name}")
        
    return True


def test_select_source(automator: StudioAutomator, pattern: str = None):
    """Test source selection."""
    print("\n" + "=" * 60)
    print("TEST: Source Selection")
    print("=" * 60)
    
    sources = automator.list_sources()
    if not sources:
        print("❌ No sources found!")
        return False
    
    # Pick first source or matching pattern
    target = sources[0]
    if pattern:
        for s in sources:
            if pattern.lower() in s.name.lower():
                target = s
                break
    
    print(f"\nSelecting: {target.truncated_name}")
    
    # Deselect all first
    automator.deselect_all_sources()
    time.sleep(1)
    
    # Select target
    if automator.select_source(target):
        print(f"✅ Selected source successfully")
        count = automator.get_sources_count_display()
        print(f"   Display shows: {count}")
        return True
    else:
        print("❌ Failed to select source")
        return False


def test_single_material(automator: StudioAutomator, material: MaterialType = MaterialType.MINDMAP):
    """Test generating a single material type."""
    print("\n" + "=" * 60)
    print(f"TEST: Generate Single Material ({material.value})")
    print("=" * 60)
    
    sources = automator.list_sources()
    if not sources:
        print("❌ No sources!")
        return False
    
    target = sources[0]
    print(f"\nUsing source: {target.truncated_name}")
    
    # Select source
    automator.deselect_all_sources()
    time.sleep(1)
    automator.select_source(target)
    time.sleep(1)
    
    # Open Studio
    automator._open_studio_panel()
    time.sleep(2)
    
    # Generate
    if material == MaterialType.AUDIO:
        status = automator.generate_audio(target.name)
    elif material == MaterialType.VIDEO:
        status = automator.generate_video(target.name)
    elif material == MaterialType.MINDMAP:
        status = automator.generate_mindmap(target.name)
    elif material == MaterialType.QUIZ:
        status = automator.generate_quiz(target.name)
    elif material == MaterialType.FLASHCARDS:
        status = automator.generate_flashcards(target.name)
    elif material == MaterialType.INFOGRAPHIC:
        status = automator.generate_infographic(target.name)
    else:
        print(f"Unknown material type: {material}")
        return False
    
    if status.started:
        print(f"✅ {material.value} generation started!")
        return True
    else:
        print(f"❌ Failed: {status.error}")
        return False


def test_all_materials_one_source(automator: StudioAutomator, pattern: str = None):
    """Test generating all materials for one source."""
    print("\n" + "=" * 60)
    print("TEST: All Materials for One Source")
    print("=" * 60)
    
    sources = automator.list_sources()
    if not sources:
        print("❌ No sources!")
        return False
    
    # Pick source
    target = sources[0]
    if pattern:
        for s in sources:
            if pattern.lower() in s.name.lower():
                target = s
                break
    
    print(f"\nProcessing: {target.truncated_name}")
    
    # Select and generate
    automator.deselect_all_sources()
    time.sleep(1)
    automator.select_source(target)
    time.sleep(1)
    
    results = automator.generate_all_materials_for_source(target)
    
    # Report
    success = sum(1 for r in results if r.started)
    print(f"\n✅ Generated {success}/{len(results)} materials")
    
    for r in results:
        icon = "✅" if r.started else "❌"
        print(f"  {icon} {r.material_type.value}: {'Started' if r.started else r.error}")
    
    return success > 0


def test_all_sources(automator: StudioAutomator, patterns: list = None, materials: list = None):
    """Test processing all sources with all materials."""
    print("\n" + "=" * 60)
    print("TEST: Full Automation - All Sources")
    print("=" * 60)
    
    results = automator.process_all_sources(
        source_patterns=patterns,
        materials=materials
    )
    
    # Summary
    print("\n" + automator.get_summary_report())
    
    return len(results) > 0


def main():
    parser = argparse.ArgumentParser(description="Test Studio Automation")
    parser.add_argument(
        "--notebook-url",
        required=True,
        help="NotebookLM notebook URL"
    )
    parser.add_argument(
        "--test",
        choices=["sources", "select", "single", "one-source", "all"],
        default="sources",
        help="Test to run"
    )
    parser.add_argument(
        "--pattern",
        help="Source name pattern to filter"
    )
    parser.add_argument(
        "--material",
        choices=["audio", "video", "mindmap", "quiz", "flashcards", "infographic"],
        default="mindmap",
        help="Material type for single test"
    )
    args = parser.parse_args()
    
    print("\n🚀 Studio Automation Test")
    print("=" * 60)
    print(f"Notebook: {args.notebook_url}")
    print(f"Test: {args.test}")
    if args.pattern:
        print(f"Pattern: {args.pattern}")
    print("=" * 60)
    
    # Initialize
    print("\n1️⃣ Initializing browser...")
    auth = GoogleAuthenticator()
    client = NotebookLMClient(auth)
    
    # Navigate
    print(f"\n2️⃣ Navigating to notebook...")
    if not client.navigate_to_notebook(args.notebook_url):
        print("❌ Failed to navigate!")
        return 1
    print("✅ Navigated successfully")
    time.sleep(3)
    
    # Create automator
    automator = StudioAutomator(client.driver)
    
    # Run test
    success = False
    
    if args.test == "sources":
        success = test_sources(automator)
        
    elif args.test == "select":
        success = test_select_source(automator, args.pattern)
        
    elif args.test == "single":
        material_map = {
            "audio": MaterialType.AUDIO,
            "video": MaterialType.VIDEO,
            "mindmap": MaterialType.MINDMAP,
            "quiz": MaterialType.QUIZ,
            "flashcards": MaterialType.FLASHCARDS,
            "infographic": MaterialType.INFOGRAPHIC,
        }
        success = test_single_material(automator, material_map[args.material])
        
    elif args.test == "one-source":
        success = test_all_materials_one_source(automator, args.pattern)
        
    elif args.test == "all":
        patterns = [args.pattern] if args.pattern else None
        success = test_all_sources(automator, patterns)
    
    # Done
    print("\n" + "=" * 60)
    print("✅ Test completed!" if success else "❌ Test failed!")
    print("=" * 60)
    
    # Keep browser open for inspection
    print("\nBrowser kept open for inspection. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

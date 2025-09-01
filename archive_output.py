#!/usr/bin/env python3
# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive_output.py
# Version: v2.3.4
# Build: 2025-09-01T08:25:00
# Commit: n/a
# Stamped: 2025-09-01T08:36:03
# === CUBIST STAMP END ===
"""
Archive Output Script

This script archives the contents of the output/ folder to prevent accumulation
of test files and ensures clean separation between test runs.

Usage:
    python archive_output.py [--dry-run]

Features:
- Archives all contents of output/ to Archived Output/output_archive_YYYYMMDD_HHMMSS/
- Creates archive directory structure if it doesn't exist
- Logs all operations using the shared logger
- Supports dry-run mode to preview operations without executing them
- Ensures output/ folder is empty and ready for next test run

Author: Corey Prator
Date: 2025-08-01
"""

import shutil
import argparse
import datetime
from pathlib import Path

# Import shared logger
from cubist_logger import logger


def archive_output_folder(dry_run=False):
    """
    Archive all contents of the output/ folder to a timestamped archive directory.

    Args:
        dry_run (bool): If True, simulate the operation without actually moving files

    Returns:
        str: Path to the archive directory, or None if no archiving was needed
    """
    logger.info(f"archive_output_folder() ENTRY: dry_run={dry_run}")

    # Define paths
    project_root = Path(__file__).parent
    output_dir = project_root / "output"
    archived_output_dir = project_root / "Archived Output"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Archive base directory: {archived_output_dir}")

    # Check if output directory exists
    if not output_dir.exists():
        logger.info("Output directory does not exist - nothing to archive")
        print("📁 Output directory does not exist - nothing to archive")
        return None

    # Check if output directory has any contents
    output_contents = list(output_dir.iterdir())
    if not output_contents:
        logger.info("Output directory is empty - nothing to archive")
        print("📁 Output directory is empty - nothing to archive")
        return None

    # Generate timestamp for archive folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder_name = f"output_archive_{timestamp}"
    archive_path = archived_output_dir / archive_folder_name

    logger.info(f"Archive destination: {archive_path}")
    logger.info(
        f"Found {len(output_contents)} items to archive: {[item.name for item in output_contents]}"
    )

    if dry_run:
        print("🔍 DRY RUN MODE - Simulating operations:")
        print(f"📁 Would create archive directory: {archive_path}")
        print(f"📦 Would move {len(output_contents)} items:")
        for item in output_contents:
            item_type = "folder" if item.is_dir() else "file"
            print(f"   • {item.name} ({item_type})")
        print(f"🎯 Archive destination: {archive_path}")
        logger.info(
            f"DRY RUN: Would archive {len(output_contents)} items to {archive_path}"
        )
        return str(archive_path)

    try:
        # Create the archived output directory if it doesn't exist
        archived_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified archive base directory: {archived_output_dir}")

        # Create the specific archive folder
        archive_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created archive directory: {archive_path}")

        # Move all contents from output/ to the archive folder
        moved_count = 0
        failed_moves = []

        for item in output_contents:
            try:
                destination = archive_path / item.name
                logger.debug(f"Moving {item} to {destination}")

                # Use shutil.move for cross-platform compatibility
                shutil.move(str(item), str(destination))
                moved_count += 1

                item_type = "folder" if destination.is_dir() else "file"
                logger.info(f"Successfully moved {item_type}: {item.name}")

            except Exception as e:
                error_msg = f"Failed to move {item.name}: {str(e)}"
                failed_moves.append(error_msg)
                logger.error(error_msg)

        # Report results
        if failed_moves:
            logger.warning(f"Archive completed with {len(failed_moves)} failures")
            print(f"⚠️  Archive completed with {len(failed_moves)} failures:")
            for failure in failed_moves:
                print(f"   • {failure}")
        else:
            logger.info(f"Archive completed successfully: moved {moved_count} items")

        # Verify output directory is now empty
        remaining_items = list(output_dir.iterdir())
        if remaining_items:
            logger.warning(
                f"Output directory not fully cleaned - {len(remaining_items)} items remain"
            )
            print(f"⚠️  Warning: {len(remaining_items)} items still in output directory")
        else:
            logger.info("Output directory is now empty and ready for next test run")
            print("✅ Output directory is now empty and ready for next test run")

        # Print success message with archive location
        print(f"📦 Successfully archived {moved_count} items")
        print(f"🎯 Archive location: {archive_path}")
        logger.info(
            f"archive_output_folder() EXIT: Successfully archived to {archive_path}"
        )

        return str(archive_path)

    except Exception as e:
        error_msg = f"Failed to create archive directory {archive_path}: {str(e)}"
        logger.error(error_msg)
        print(f"❌ Error: {error_msg}")
        return None


def main():
    """Main entry point for the archive script."""
    parser = argparse.ArgumentParser(
        description="Archive output folder contents to prevent accumulation between test runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python archive_output.py                  # Archive output folder contents
  python archive_output.py --dry-run        # Preview what would be archived

The archive will be created at:
  Archived Output/output_archive_YYYYMMDD_HHMMSS/
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the archiving process without actually moving files",
    )

    args = parser.parse_args()

    # Log script start
    logger.info("=" * 60)
    logger.info("archive_output.py started")
    logger.info(f"Arguments: dry_run={args.dry_run}")

    print("🗂️  Cubist Art Generator - Output Archiver")
    print("=" * 50)

    if args.dry_run:
        print("🔍 Running in DRY RUN mode - no files will be moved")
        print()

    try:
        # Perform the archiving
        archive_path = archive_output_folder(dry_run=args.dry_run)

        if archive_path:
            print()
            print("🎉 Archiving completed successfully!")
            print(f"📂 Archive location: {archive_path}")
        else:
            print()
            print("ℹ️  No archiving was needed")

        logger.info("archive_output.py completed successfully")

    except KeyboardInterrupt:
        logger.info("archive_output.py interrupted by user")
        print("\n⏹️  Operation cancelled by user")

    except Exception as e:
        error_msg = f"Unexpected error in archive_output.py: {str(e)}"
        logger.error(error_msg)
        print(f"\n❌ Unexpected error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
# === CUBIST FOOTER STAMP BEGIN ===
# End of file — v2.3.4 — stamped 2025-09-01T08:36:03
# === CUBIST FOOTER STAMP END ===

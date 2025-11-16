#!/usr/bin/env python3
"""
Plutus Data Warehouse - Command Line Interface

Main CLI for running microservices manually.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def run_tofu_ingestion(args):
    """Run TOFU leads ingestion"""
    from microservices.tofu_ingestion.main import main
    
    exit_code = main(
        dry_run=args.dry_run,
        verbose=args.verbose,
        sheet=args.sheet
    )
    return exit_code


def run_bofu_ingestion(args):
    """Run BOFU transactions ingestion"""
    from microservices.bofu_ingestion.main import main

    exit_code = main(
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    return exit_code


def run_mofu_ingestion(args):
    """Run MOFU lead assignments ingestion"""
    from microservices.mofu_ingestion.main import main

    exit_code = main(
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    return exit_code


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Plutus Data Warehouse CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run TOFU ingestion (dry-run first to test)
  python cli.py tofu-ingestion --dry-run
  
  # Run TOFU ingestion for real
  python cli.py tofu-ingestion
  
  # Run with verbose logging
  python cli.py tofu-ingestion --verbose
  
  # Process only one specific sheet
  python cli.py tofu-ingestion --sheet Sheet1
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # TOFU Ingestion command
    tofu_parser = subparsers.add_parser(
        "tofu-ingestion",
        help="Run TOFU leads ingestion from Google Sheets"
    )
    tofu_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database (test mode)"
    )
    tofu_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    tofu_parser.add_argument(
        "--sheet",
        type=str,
        help="Process only this specific sheet (by name or tab)"
    )
    tofu_parser.set_defaults(func=run_tofu_ingestion)

    # BOFU ingestion command
    bofu_parser = subparsers.add_parser(
        "bofu-ingestion",
        help="Run BOFU transactions ingestion from API"
    )
    bofu_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database (test mode)"
    )
    bofu_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    bofu_parser.set_defaults(func=run_bofu_ingestion)

    # MOFU ingestion command
    mofu_parser = subparsers.add_parser(
        "mofu-ingestion",
        help="Run MOFU lead assignments ingestion from API"
    )
    mofu_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database (test mode)"
    )
    mofu_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    mofu_parser.set_defaults(func=run_mofu_ingestion)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Quinn Social Media Bot - Main Entry Point
Organized project structure for better maintainability
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the main bot functionality
from core.main import main, clear_memory_files, show_memory_status, run_specific_accounts

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clear":
            clear_memory_files()
        elif command == "status":
            show_memory_status()
        elif command == "help":
            print("""
🔧 Quinn Social Media Bot - Command Line Options:

Usage:
  python main.py                    # Run the full bot (all 6 accounts)
  python main.py technews           # Run only TechNews
  python main.py reddit             # Run only Reddit
  python main.py product            # Run only ProductHunt
  python main.py crypto             # Run only Crypto
  python main.py books              # Run only Books
  python main.py quotes             # Run only Quotes
  python main.py clear              # Clear all memory files
  python main.py status             # Show memory status
  python main.py help               # Show this help

Account Types:
  - technews: High-signal tech news with educational content
  - reddit: Top Reddit posts summary
  - product: ProductHunt product showcase
  - crypto: High-signal crypto news with educational content
  - books: 6-tweet book recommendation thread
  - quotes: 4-tweet inspirational quotes thread

Memory Management:
  - clear: Removes all memory files to start fresh
  - status: Shows current memory usage for all content types
  - help: Displays this help message

Examples:
  python main.py technews           # Run only TechNews
  python main.py reddit product     # Run Reddit and ProductHunt
  python main.py clear              # Start fresh with no memory
  python main.py status             # Check what's been used recently
            """)
        elif command in ["technews", "reddit", "product", "books", "quotes", "crypto"]:
            # Run specific account type(s) - support multiple accounts
            accounts_to_run = [command]
            
            # Check if additional account types were provided
            if len(sys.argv) > 2:
                for arg in sys.argv[2:]:
                    if arg.lower() in ["technews", "reddit", "product", "books", "quotes"]:
                        accounts_to_run.append(arg.lower())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_accounts = []
            for acc in accounts_to_run:
                if acc not in seen:
                    seen.add(acc)
                    unique_accounts.append(acc)
            
            run_specific_accounts(unique_accounts)
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python main.py help' for available commands")
    else:
        main()

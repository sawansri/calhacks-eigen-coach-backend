#!/usr/bin/env python3
"""
Script to view all current memory entries in the database.
Shows the content of the student_memory table.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db import DatabaseManager


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def get_memory_entries():
    """Fetch all memory entries from the database."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, memory_entry, created_at 
            FROM student_memory 
            ORDER BY created_at DESC
        """)
        
        entries = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return entries
        
    except Exception as e:
        print(f"❌ Error fetching memory entries: {e}")
        return None


def get_memory_count():
    """Get the total count of memory entries."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM student_memory")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"❌ Error getting memory count: {e}")
        return None


def display_memory_entries(entries):
    """Display memory entries in a formatted way."""
    if not entries:
        print("\n📋 No memory entries found in the database.\n")
        return
    
    print(f"\n📝 Total Entries: {len(entries)}\n")
    
    for idx, entry in enumerate(entries, 1):
        entry_id = entry.get('id', 'N/A')
        memory_text = entry.get('memory_entry', 'N/A')
        created_at = entry.get('created_at', 'N/A')
        
        # Format the timestamp nicely
        if created_at and created_at != 'N/A':
            timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created_at, 'strftime') else str(created_at)
        else:
            timestamp = "N/A"
        
        # Print entry with nice formatting
        print(f"┌─ Entry #{idx} (ID: {entry_id}) ─────────────────────────────────────")
        print(f"│ Created: {timestamp}")
        print(f"│")
        
        # Word wrap the memory text for better readability
        max_width = 66
        words = memory_text.split()
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += word + " "
            else:
                if current_line:
                    print(f"│ {current_line}")
                current_line = word + " "
        
        if current_line:
            print(f"│ {current_line}")
        
        print(f"└" + "─" * 68)


def display_stats(entries):
    """Display statistics about the memory entries."""
    if not entries:
        return
    
    print("\n📊 Statistics:")
    print(f"  • Total entries: {len(entries)}")
    
    # Calculate average length
    avg_length = sum(len(entry.get('memory_entry', '')) for entry in entries) / len(entries)
    print(f"  • Average entry length: {avg_length:.0f} characters")
    
    # Find longest entry
    longest = max(len(entry.get('memory_entry', '')) for entry in entries)
    print(f"  • Longest entry: {longest} characters")
    
    # Find shortest entry
    shortest = min(len(entry.get('memory_entry', '')) for entry in entries)
    print(f"  • Shortest entry: {shortest} characters")


def main():
    """Main function to display memory entries."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " DATABASE MEMORY ENTRIES VIEWER ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Initialize database connection
        print("\n🔗 Connecting to database...")
        DatabaseManager.initialize()
        print("✅ Connected successfully\n")
        
        # Get count
        count = get_memory_count()
        if count is not None:
            print(f"📊 Database contains {count} memory entry/entries")
        
        # Fetch and display entries
        print_header("MEMORY ENTRIES")
        entries = get_memory_entries()
        
        if entries is not None:
            display_memory_entries(entries)
            display_stats(entries)
        
        print("\n✅ Memory entries retrieved successfully\n")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  Operation cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)

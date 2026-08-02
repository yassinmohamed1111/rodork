#!/usr/bin/env python3
import argparse
import cmd
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from modules.shodan_client import ShodanClient
from modules.dork_manager import DorkManager
from modules.filter_engine import apply_filters, calculate_risk
from modules.output_formatter import (
    results_to_table, results_to_json, results_to_csv
)

BANNER = r"""
  ____       ____            __  
 / __ \____ / __ \____  ____/ /__
/ /_/ / __ / / / / __ \/ __  / _ \
/ _, _/ /_/ / /_/ / /_/ / /_/ /  __/
/_/ |_|\____/_____/\____/\__,_/\___/

 Robotics Threat Intelligence Tool
"""

class RoDorkShell(cmd.Cmd):
    intro = "\nType 'help' for commands. 'exit' to quit.\n"
    prompt = "rodork> "

    def __init__(self):
        super().__init__()
        try:
            self.client = ShodanClient()
            # Test the API key
            self.client.api.info()
            print("✓ Shodan API connection successful")
        except Exception as e:
            print(f"\n⚠️  Shodan API Error: {str(e)}")
            print("Please check your API key in the .env file")
            print("You can still browse dorks locally, but searches won't work.\n")
            self.client = None
        
        self.dork_mgr = DorkManager()
        self.current_results = []
        
    def do_search(self, arg):
        """Search Shodan with a dork ID, category, or raw query.
Usage: search <dork_id|category:<cat>|raw:"query"|all>
Examples:
  search d001
  search category:manufacturer
  search raw:"ABB robot"
  search all
"""
        if not self.client:
            print("❌ Shodan API not configured. Set SHODAN_API_KEY in .env file.")
            return

        args = arg.strip()
        if not args:
            print("Usage: search <id|category:...|raw:...|all>")
            return

        queries = []
        if args == 'all':
            print("⚠️  Warning: 'all' will run multiple queries. This may hit rate limits.")
            confirm = input("Continue? (y/n): ")
            if confirm.lower() != 'y':
                return
            for d in self.dork_mgr.get_all():
                queries.append(d['query'])
        elif args.startswith('category:'):
            cat = args.split(':', 1)[1].strip()
            dorks = self.dork_mgr.get_by_category(cat)
            if not dorks:
                print(f"No dorks found in category '{cat}'")
                print(f"Available categories: {', '.join(self.dork_mgr.list_categories())}")
                return
            queries = [d['query'] for d in dorks]
            print(f"Found {len(queries)} dorks in category '{cat}'")
        elif args.startswith('raw:'):
            raw_q = args.split(':', 1)[1].strip()
            queries = [raw_q]
        else:
            dork = self.dork_mgr.get_by_id(args)
            if dork:
                queries = [dork['query']]
                print(f"Dork: {dork['description']}")
                print(f"Query: {dork['query']}")
            else:
                print(f"No dork found with ID '{args}'")
                print("Use 'list_dorks' to see available dorks")
                return

        print(f"\n🔍 Searching {len(queries)} query(ies)...")
        all_matches = []
        for i, q in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {q[:80]}...")
            try:
                res = self.client.search(q, limit=50)
                matches = res.get('matches', [])
                print(f"    ✓ {len(matches)} results")
                all_matches.extend(matches)
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print(f"    ❌ API key invalid. Check your .env file.")
                elif "403" in error_msg or "Forbidden" in error_msg:
                    print(f"    ❌ Access denied. Your API key may not have search permissions.")
                    print(f"    Get a free API key at: https://account.shodan.io/register")
                elif "429" in error_msg or "rate limit" in error_msg.lower():
                    print(f"    ⏳ Rate limited. Waiting 10 seconds...")
                    import time
                    time.sleep(10)
                    try:
                        res = self.client.search(q, limit=50)
                        matches = res.get('matches', [])
                        print(f"    ✓ {len(matches)} results (after retry)")
                        all_matches.extend(matches)
                    except:
                        print(f"    ❌ Still failed. Skipping this query.")
                else:
                    print(f"    ❌ Error: {error_msg[:100]}")

        self.current_results = all_matches
        print(f"\n✅ Total collected: {len(self.current_results)} results")

    def do_filter(self, arg):
        """Apply filters to the current results.
Filter options: country=<ISO>, risk=<level>, robot_type=<mfr>, technology=<ros/modbus/rtsp/...>, port=<num>, logic=AND|OR
Example: filter country=US risk=high
         filter robot_type=ABB logic=OR port=502
         filter clear  (remove all filters)
"""
        if not self.current_results:
            print("No search results to filter. Run 'search' first.")
            return

        if arg.strip() == 'clear':
            print("Filters cleared (showing all results).")
            return

        filters = {}
        for part in arg.split():
            if '=' in part:
                key, val = part.split('=', 1)
                filters[key] = val
        logic = filters.pop('logic', 'AND')
        filters['logic'] = logic

        original_count = len(self.current_results)
        filtered = apply_filters(self.current_results, filters)
        self.current_results = filtered
        print(f"Filters applied: {original_count} → {len(self.current_results)} results")

    def do_show(self, arg):
        """Show current results in a table (default) or export format.
Usage: show [format=table|json|csv] [columns=ip,port,org,risk,...] [limit=N]
"""
        if not self.current_results:
            print("No results to show. Run 'search' first.")
            return

        limit = None
        fmt = 'table'
        cols = None

        for part in arg.split():
            if part.startswith('format='):
                fmt = part.split('=')[1]
            elif part.startswith('columns='):
                cols = part.split('=')[1].split(',')
            elif part.startswith('limit='):
                try:
                    limit = int(part.split('=')[1])
                except:
                    print("Invalid limit value")
                    return

        results = self.current_results[:limit] if limit else self.current_results

        if fmt == 'table':
            print(results_to_table(results, columns=cols))
        elif fmt == 'json':
            print(results_to_json(results))
        elif fmt == 'csv':
            path = Path("rodork_export.csv")
            msg = results_to_csv(results, path)
            print(msg)
        else:
            print("Unknown format. Use table, json, or csv.")

    def do_export(self, arg):
        """Export current results to JSON or CSV.
Usage: export json [filename]  or  export csv [filename]
Default filenames: rodork_export.json / rodork_export.csv
"""
        if not self.current_results:
            print("No results to export. Run 'search' first.")
            return

        parts = arg.split()
        if not parts:
            print("Specify json or csv.")
            return
        fmt = parts[0]
        filename = parts[1] if len(parts) > 1 else None

        if fmt == 'json':
            if not filename:
                filename = 'rodork_export.json'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(results_to_json(self.current_results))
            print(f"✅ Exported {len(self.current_results)} results to {filename}")
        elif fmt == 'csv':
            if not filename:
                filename = 'rodork_export.csv'
            print(results_to_csv(self.current_results, filename))
        else:
            print("Format must be 'json' or 'csv'.")

    def do_list_dorks(self, arg):
        """List all dorks, optionally filtered by category.
Usage: list_dorks [category=<cat>]
"""
        if arg.startswith('category='):
            cat = arg.split('=')[1]
            dorks = self.dork_mgr.get_by_category(cat)
            if not dorks:
                print(f"No dorks found in category '{cat}'")
                print(f"Available categories: {', '.join(self.dork_mgr.list_categories())}")
                return
        else:
            dorks = self.dork_mgr.get_all()

        print(f"\nTotal dorks: {len(dorks)}\n")
        print(f"{'ID':6} {'Category':15} {'Query':60} {'Risk':10}")
        print("-" * 95)
        for d in dorks:
            print(f"{d['id']:6} {d['category']:15} {d['query'][:60]:60} {d['risk_level']:10}")

    def do_stats(self, arg):
        """Show statistics about the dork library.
Usage: stats
"""
        dorks = self.dork_mgr.get_all()
        categories = {}
        risk_levels = {}
        
        for d in dorks:
            cat = d['category']
            risk = d['risk_level']
            categories[cat] = categories.get(cat, 0) + 1
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        print(f"\n📊 Dork Library Statistics")
        print(f"Total dorks: {len(dorks)}")
        print(f"\nBy Category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat:20} {count}")
        print(f"\nBy Risk Level:")
        for risk, count in sorted(risk_levels.items()):
            print(f"  {risk:10} {count}")
        print(f"\nAPI Status: {'✅ Connected' if self.client else '❌ Not configured'}")

    def do_add_dork(self, arg):
        """Add a custom user dork. Prompts for details.
Usage: add_dork
"""
        print("\n📝 Add New Dork")
        print("-" * 30)
        query = input("Shodan query: ").strip()
        if not query:
            print("Query cannot be empty")
            return
        
        print("\nCategories: " + ", ".join(self.dork_mgr.list_categories()))
        category = input("Category: ").strip().lower()
        
        description = input("Short description: ").strip()
        
        risk = input("Risk level (critical/high/medium/low): ").strip().lower()
        if risk not in ['critical', 'high', 'medium', 'low']:
            print("Invalid risk level, defaulting to 'medium'")
            risk = 'medium'
        
        dork = self.dork_mgr.add_dork(query, category, description, risk)
        print(f"✅ Added dork with ID {dork['id']}")

    def do_exit(self, arg):
        """Exit RoDork."""
        print("Goodbye!")
        return True

    def emptyline(self):
        pass  # Don't repeat last command on empty line

    def default(self, line):
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands.")


def check_api_key():
    """Check if the API key is properly configured."""
    api_key = os.getenv("SHODAN_API_KEY")
    
    if not api_key:
        print("\n⚠️  SHODAN_API_KEY not found!")
        print("\nTo fix this:")
        print("1. Go to https://account.shodan.io/register")
        print("2. Create a free account")
        print("3. Copy your API key from https://account.shodan.io/")
        print("4. Create a .env file with: SHODAN_API_KEY=your_key_here")
        print("   or run: echo 'SHODAN_API_KEY=your_key_here' > .env")
        return False
    
    if api_key == "your_shodan_api_key_here":
        print("\n⚠️  You need to replace the example API key with your real one!")
        print("Edit the .env file and set your actual Shodan API key.")
        print("Get one at: https://account.shodan.io/register")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="RoDork - Robotics Threat Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python rodork.py
  
  Quick search:
    python rodork.py -s category:manufacturer
    python rodork.py -s d001 --country US
    python rodork.py -s raw:"KUKA robot" --risk high -o json
  
  List available dorks:
    python rodork.py --list-dorks
  
  Check API status:
    python rodork.py --check-api
        """
    )
    parser.add_argument('--search', '-s', 
                       help="Dork ID, category:<cat>, raw:<query>, or 'all'")
    parser.add_argument('--country', help="Filter by country code (e.g. US)")
    parser.add_argument('--risk', help="Filter by risk level")
    parser.add_argument('--robot-type', help="Filter by robot manufacturer")
    parser.add_argument('--technology', help="Filter by technology (ros, modbus, rtsp)")
    parser.add_argument('--port', type=int, help="Filter by port number")
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'], 
                       default='table', help="Output format")
    parser.add_argument('--export', help="Export file (for json/csv)")
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help="Suppress banner and extra output")
    parser.add_argument('--list-dorks', action='store_true',
                       help="List all available dorks")
    parser.add_argument('--check-api', action='store_true',
                       help="Check Shodan API configuration")

    args = parser.parse_args()

    # Handle utility commands first
    if args.list_dorks:
        dm = DorkManager()
        print(f"\nAvailable Dorks ({len(dm.get_all())} total):\n")
        for d in dm.get_all():
            print(f"  {d['id']:6} [{d['category']:12}] {d['description']}")
        return

    if args.check_api:
        if check_api_key():
            try:
                client = ShodanClient()
                info = client.api.info()
                print(f"\n✅ API connection successful!")
                print(f"   Plan: {info.get('plan', 'Unknown')}")
                print(f"   Query credits: {info.get('query_credits', 'Unknown')}")
                print(f"   Scan credits: {info.get('scan_credits', 'Unknown')}")
            except Exception as e:
                print(f"\n❌ API connection failed: {str(e)}")
        return

    # Print banner only in interactive mode or when not quiet
    if not args.quiet and not args.search:
        print(BANNER)

    # Check API key
    api_ok = check_api_key()
    if not api_ok and (args.search or not args.quiet):
        print("\n⚠️  You can browse dorks offline, but searches require a valid API key.\n")

    if args.search:
        if not api_ok:
            print("❌ Cannot search without a valid API key.")
            print("   Get one at: https://account.shodan.io/register")
            sys.exit(1)

        # Non-interactive mode
        client = ShodanClient()
        dm = DorkManager()
        queries = []
        
        if args.search == 'all':
            for d in dm.get_all():
                queries.append(d['query'])
        elif args.search.startswith('category:'):
            cat = args.search.split(':', 1)[1]
            dorks = dm.get_by_category(cat)
            if not dorks:
                print(f"No dorks in category '{cat}'")
                sys.exit(1)
            queries = [d['query'] for d in dorks]
        elif args.search.startswith('raw:'):
            queries = [args.search.split(':', 1)[1]]
        else:
            dork = dm.get_by_id(args.search)
            if dork:
                queries = [dork['query']]
            else:
                print(f"Unknown dork ID: {args.search}")
                sys.exit(1)

        results = []
        for q in queries:
            try:
                print(f"Searching: {q}")
                res = client.search(q, limit=50)
                results.extend(res.get('matches', []))
            except Exception as e:
                print(f"Error: {str(e)[:200]}")

        # Apply filters
        filters = {}
        if args.country:
            filters['country'] = args.country
        if args.risk:
            filters['risk'] = args.risk
        if args.robot_type:
            filters['robot_type'] = args.robot_type
        if args.technology:
            filters['technology'] = args.technology
        if args.port:
            filters['port'] = args.port
        if filters:
            results = apply_filters(results, filters)

        if args.output == 'table':
            print(results_to_table(results))
        elif args.output == 'json':
            out = results_to_json(results)
            if args.export:
                with open(args.export, 'w') as f:
                    f.write(out)
                print(f"Exported to {args.export}")
            else:
                print(out)
        elif args.output == 'csv':
            if not args.export:
                args.export = 'rodork_export.csv'
            print(results_to_csv(results, args.export))
    else:
        # Interactive mode
        try:
            RoDorkShell().cmdloop()
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

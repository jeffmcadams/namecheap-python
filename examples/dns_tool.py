#!/usr/bin/env python3
"""
DNS management tool for Namecheap domains

A command-line tool to manage DNS records for domains hosted on Namecheap's nameservers.
Allows listing, adding, deleting, importing, and exporting DNS records.

Examples:
    # List all DNS records for a domain
    python dns_tool.py list example.com

    # Add an A record
    python dns_tool.py add example.com --name www --type A --value 192.168.1.1

    # Delete a record
    python dns_tool.py delete example.com --name www --type A

    # Export records to JSON
    python dns_tool.py export example.com records.json

    # Import records from JSON
    python dns_tool.py import example.com records.json
"""

import argparse
import json
from typing import Any, Dict, List, Optional, Union

from examples.utils.print_table import print_table
from namecheap import NamecheapClient, NamecheapException


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask for user confirmation before proceeding with an action.

    Args:
        message: The message to display to the user
        default: Default action if user just presses Enter (True=yes, False=no)

    Returns:
        Boolean indicating whether to proceed (True) or abort (False)
    """
    default_str = "yes" if default else "no"
    choices = "(Y/n)" if default else "(y/N)"

    response = input(f"\n{message} {choices}: ").strip().lower()

    if not response:
        # User pressed Enter, use default
        return default

    return response.startswith("y")


def display_record(record: Dict[str, Any], index: Optional[int] = None) -> None:
    """Display record details in a consistent format"""
    prefix = f"\nRecord {index}:" if index is not None else ""
    print(f"{prefix}")
    print(f"  Name: {record['Name']}")
    print(f"  Type: {record['Type']}")
    print(f"  Value: {record['Address']}")
    print(f"  TTL: {record['TTL']}")
    if record["Type"] == "MX" and "MXPref" in record:
        print(f"  Priority: {record['MXPref']}")


def list_records(
    client: NamecheapClient, domain: str, show_raw: bool = False
) -> List[Dict[str, Any]]:
    """List all DNS records for a domain"""
    records: List[Dict[str, Any]] = []
    try:
        if client.debug:
            print(f"\nAttempting to retrieve DNS records for {domain}...")

        # Get records now returns a clean list of normalized records
        records = client.domains.dns.get_hosts(domain)
        return records

        if client.debug:
            print(f"\nFound {len(records)} DNS records")

        # Display raw record data if requested
        if show_raw:
            print("\nRaw record data:")
            for i, record in enumerate(records):
                print(f"\nRecord {i+1}:")
                print(json.dumps(record, indent=2))
            print("\n")

        # Prepare data for table
        headers = ["Name", "Type", "TTL", "Priority", "Address/Value"]
        rows: List[List[Union[str, int, float]]] = []

        for record in records:
            # Use the original API field names
            name = record["Name"]
            record_type = record["Type"]
            ttl = record["TTL"]
            mx_pref = record["MXPref"] if record_type == "MX" else ""
            address = record["Address"]

            rows.append(
                [str(name), str(record_type), str(ttl), str(mx_pref), str(address)]
            )

        # Print table
        print(f"\nDNS Records for {domain}:")
        print_table(headers, rows)

    except NamecheapException as e:
        print(e)
        return []


def add_record(
    client: NamecheapClient,
    domain: str,
    record_data: Dict[str, Any],
    args: Optional[argparse.Namespace] = None,
) -> None:
    """Add a new DNS record to a domain"""
    try:
        # Get current records first
        current_records = client.domains.dns.get_hosts(domain)

        if client.debug:
            print(f"\nCurrent records: {len(current_records)}")

        # Create record in Namecheap API format
        new_record = {
            "Name": record_data["name"],
            "Type": record_data["type"],
            "Address": record_data["value"],
            "TTL": record_data["ttl"],
        }

        # Add MXPref for MX records
        if new_record["Type"].upper() == "MX":
            new_record["MXPref"] = record_data["priority"]

        # Combine with existing records
        updated_records = current_records + [new_record]

        # Confirm if not forced
        if args and not args.force:
            display_record(new_record)

            if not confirm_action("Add this record?"):
                print("Operation cancelled.")
                return

        # Update the records
        result = client.domains.dns.set_hosts(domain, updated_records)

        if result["success"]:
            print(f"\nSuccess! Record added to {domain}")
        else:
            print(
                f"\nWarning: Operation completed but with warnings: {result['warnings']}"
            )

    except NamecheapException as e:
        print(e)


def delete_record(
    client: NamecheapClient,
    domain: str,
    record_data: Dict[str, Any],
    args: Optional[argparse.Namespace] = None,
) -> None:
    """Delete a DNS record from a domain"""
    try:
        # Get current records
        current_records = client.domains.dns.get_hosts(domain)

        if client.debug:
            print(f"\nFetched {len(current_records)} records")

        # Find matching records
        records_to_keep: List[Dict[str, str]] = []
        records_to_delete: List[Dict[str, Any]] = []

        for record in current_records:
            # Check if this record matches the criteria to delete
            if (
                record["Name"] == record_data["name"]
                and record["Type"] == record_data["type"]
            ):
                # If value is specified, it must match too
                if record_data["value"] and record["Address"] != record_data["value"]:
                    records_to_keep.append({k: str(v) for k, v in record.items()})
                else:
                    records_to_delete.append(record)
            else:
                records_to_keep.append({k: str(v) for k, v in record.items()})

        # Check if any records were found to delete
        if not records_to_delete:
            print(
                f"No matching records found with name={record_data['name']} and type={record_data['type']}"
            )
            return

        # Confirm deletion unless force flag is used
        if args and not args.force:
            print(f"\nFound {len(records_to_delete)} records to delete:")
            for i, record in enumerate(records_to_delete):
                display_record(record, i + 1)

            if not confirm_action(
                f"Delete {len(records_to_delete)} record(s)?", default=False
            ):
                print("Operation cancelled.")
                return

        # Update records (removing the ones to delete)
        result = client.domains.dns.set_hosts(domain, records_to_keep)

        if result["success"]:
            print(
                f"\nSuccess! {len(records_to_delete)} record(s) deleted from {domain}"
            )
        else:
            print(
                f"\nWarning: Operation completed but with warnings: {result['warnings']}"
            )

    except NamecheapException as e:
        print(e)


def import_records(
    client: NamecheapClient,
    domain: str,
    json_file: str,
    args: Optional[argparse.Namespace] = None,
) -> None:
    """Import DNS records from a JSON file"""
    try:
        # Load records from JSON file
        with open(json_file) as f:
            records = json.load(f)

        if not isinstance(records, list):
            raise ValueError("JSON file must contain a list of DNS records")

        # Normalize records to ensure they have required fields
        host_records: List[Dict[str, str]] = []
        for record in records:
            # Ensure the record uses the Namecheap API field names
            host_record = {
                "Name": record.get("Name", "@"),
                "Type": record.get("Type", "A"),
                "Address": record.get("Address", ""),
                "TTL": record.get("TTL", "1800"),
            }

            # Add MXPref for MX records
            if host_record["Type"] == "MX":
                host_record["MXPref"] = record.get("MXPref", "10")

            host_records.append(host_record)

        # Display records that will be imported
        print(f"\nImporting {len(host_records)} DNS records to {domain}:")
        for idx, record in enumerate(host_records, 1):
            display_record(record, idx)

        # Ask for confirmation before making changes (unless force flag is used)
        if args and args.force:
            proceed = True
        else:
            proceed = confirm_action(
                "This will replace ALL existing DNS records. Continue?", default=False
            )

        if not proceed:
            print("Operation aborted.")
            return

        # Update records
        result = client.domains.dns.set_hosts(domain, host_records)

        print(f"\n{len(host_records)} records imported successfully to {domain}")

    except NamecheapException as e:
        print(e)
    except Exception as e:
        print(f"Error: {e}")


def export_records(client: NamecheapClient, domain: str, json_file: str) -> None:
    """Export DNS records to a JSON file"""
    try:
        # Get existing records (already normalized)
        records = client.domains.dns.get_hosts(domain)

        # Write to JSON file
        with open(json_file, "w") as f:
            json.dump(records, f, indent=2)

        print(f"\n{len(records)} DNS records exported to {json_file}")

    except NamecheapException as e:
        print(e)
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    """Main entry point"""
    # Initialize main parser
    parser = argparse.ArgumentParser(description="Namecheap DNS Management Tool")

    # Add global arguments
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug mode for API calls"
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True

    # List command
    list_parser = subparsers.add_parser("list", help="List DNS records for a domain")
    list_parser.add_argument("domain", help="Domain name")
    list_parser.add_argument(
        "--show-raw",
        action="store_true",
        help="Show raw record data including metadata fields",
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a DNS record to a domain")
    add_parser.add_argument("domain", help="Domain name")
    add_parser.add_argument("--name", default="@", help="Record name (@ for root)")
    add_parser.add_argument(
        "--type", default="A", help="Record type (A, CNAME, MX, TXT, etc.)"
    )
    add_parser.add_argument("--value", required=True, help="Record value/address")
    add_parser.add_argument("--ttl", default="1800", help="Time to live")
    add_parser.add_argument(
        "--priority", default="10", help="MX priority (only for MX records)"
    )
    add_parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )

    # Delete command
    delete_parser = subparsers.add_parser(
        "delete", help="Delete a DNS record from a domain"
    )
    delete_parser.add_argument("domain", help="Domain name")
    delete_parser.add_argument("--name", required=True, help="Record name to delete")
    delete_parser.add_argument(
        "--type", required=True, help="Record type to delete (A, CNAME, MX, TXT, etc.)"
    )
    delete_parser.add_argument(
        "--value",
        help="Specific record value to delete (optional, will delete all matching name/type if not specified)",
    )
    delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )

    # Import command
    import_parser = subparsers.add_parser(
        "import", help="Import DNS records from a JSON file"
    )
    import_parser.add_argument("domain", help="Domain name")
    import_parser.add_argument("json_file", help="JSON file to import records from")
    import_parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )

    # Export command
    export_parser = subparsers.add_parser(
        "export", help="Export DNS records to a JSON file"
    )
    export_parser.add_argument("domain", help="Domain name")
    export_parser.add_argument("json_file", help="JSON file to export records to")

    args = parser.parse_args()

    # Initialize client with debug mode using the args object
    client = NamecheapClient(
        api_user="default",
        api_key="default",
        username="default",
        client_ip="default",
        debug=args.debug,
    )

    # Execute the appropriate command
    if args.command == "list":
        list_records(client, args.domain, getattr(args, "show_raw", False))
    elif args.command == "add":
        record_data = {
            "name": args.name,
            "type": args.type,
            "value": args.value,
            "ttl": args.ttl,
            "priority": args.priority,
        }
        add_record(client, args.domain, record_data, args)
    elif args.command == "delete":
        record_data = {
            "name": args.name,
            "type": args.type,
            "value": args.value,
        }
        delete_record(client, args.domain, record_data, args)
    elif args.command == "import":
        import_records(client, args.domain, args.json_file, args)
    elif args.command == "export":
        export_records(client, args.domain, args.json_file)


if __name__ == "__main__":
    main()

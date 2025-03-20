#!/usr/bin/env python3
"""
DNS management tool for Namecheap domains
"""

import argparse
import json

from examples.utils.print_table import print_table
from namecheap import NamecheapClient, NamecheapException


# Helper functions
def confirm_action(message, default=False):
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


def init_client():
    """Initialize the Namecheap API client"""
    # The client will automatically load credentials from environment variables
    return NamecheapClient()


def list_records(client, domain):
    """List all DNS records for a domain"""
    try:
        result = client.domains_dns_get_hosts(domain)

        # Extract host records
        host_records = result.get("DomainDNSGetHostsResult", {}).get("host", [])
        if not isinstance(host_records, list):
            host_records = [host_records]

        # Prepare data for table
        headers = ["Name", "Type", "TTL", "Priority", "Address/Value"]
        rows = []

        for record in host_records:
            name = record.get("Name", "")
            record_type = record.get("Type", "")
            ttl = record.get("TTL", "")
            mx_pref = record.get("MXPref", "") if record_type == "MX" else ""
            address = record.get("Address", "")

            rows.append([name, record_type, ttl, mx_pref, address])

        # Print table
        print(f"\nDNS Records for {domain}:")
        print_table(headers, rows)

    except NamecheapException as e:
        print(f"API Error ({e.code}): {e.message}")
    except Exception as e:
        print(f"Error: {e}")


def add_record(client, domain, record_data, args=None):
    """Add a new DNS record to a domain"""
    try:
        # First, get existing records
        result = client.domains_dns_get_hosts(domain)

        # Extract host records
        host_records = result.get("DomainDNSGetHostsResult", {}).get("host", [])
        if not isinstance(host_records, list):
            host_records = [host_records]

        # Create new record
        new_record = {
            "HostName": record_data.get("name", "@"),
            "RecordType": record_data.get("type", "A"),
            "Address": record_data.get("value", ""),
            "TTL": record_data.get("ttl", "1800"),
        }

        # Add MXPref for MX records
        if new_record["RecordType"] == "MX":
            new_record["MXPref"] = record_data.get("priority", "10")

        # Ask for confirmation before making changes (unless force flag is used)
        print("\nYou are about to add a new DNS record:")
        print(f"  Type: {new_record['RecordType']}")
        print(f"  Host: {new_record['HostName']}.{domain}")
        print(f"  Value: {new_record['Address']}")
        print(f"  TTL: {new_record['TTL']}")
        if new_record["RecordType"] == "MX":
            print(f"  Priority: {new_record['MXPref']}")

        if not getattr(args, "force", False) and not confirm_action(
            "Do you want to proceed?"
        ):
            print("Operation cancelled.")
            return

        # Add new record to existing records
        host_records.append(new_record)

        # Update the DNS records
        result = client.domains_dns_set_hosts(domain, host_records)

        if result.get("DomainDNSSetHostsResult", {}).get("IsSuccess"):
            print(
                f"Successfully added {new_record['RecordType']} record for {new_record['HostName']}.{domain}"
            )
        else:
            print("Failed to add DNS record")

    except NamecheapException as e:
        print(f"API Error ({e.code}): {e.message}")
    except Exception as e:
        print(f"Error: {e}")


def delete_record(client, domain, record_data, args=None):
    """Delete a DNS record from a domain"""
    try:
        # First, get existing records
        result = client.domains_dns_get_hosts(domain)

        # Extract host records
        host_records = result.get("DomainDNSGetHostsResult", {}).get("host", [])
        if not isinstance(host_records, list):
            host_records = [host_records]

        # Find the record to delete
        name = record_data.get("name", "")
        record_type = record_data.get("type", "")
        value = record_data.get("value", "")

        filtered_records = []
        records_to_delete = []

        for record in host_records:
            # If this record matches our criteria, add to delete list
            if (
                record.get("Name") == name
                and record.get("Type") == record_type
                and (not value or record.get("Address") == value)
            ):
                records_to_delete.append(record)
            else:
                filtered_records.append(record)

        if not records_to_delete:
            print(f"No matching {record_type} record found for {name}.{domain}")
            return

        # Ask for confirmation before deleting
        print("\nYou are about to delete the following DNS record(s):")
        for i, record in enumerate(records_to_delete, 1):
            print(f"\n  Record #{i}:")
            print(f"    Type: {record.get('Type')}")
            print(f"    Host: {record.get('Name')}.{domain}")
            print(f"    Value: {record.get('Address')}")
            print(f"    TTL: {record.get('TTL')}")
            if record.get("Type") == "MX":
                print(f"    Priority: {record.get('MXPref')}")

        if not getattr(args, "force", False) and not confirm_action(
            f"Do you want to delete {len(records_to_delete)} record(s)?"
        ):
            print("Operation cancelled.")
            return

        # Update the DNS records
        result = client.domains_dns_set_hosts(domain, filtered_records)

        if result.get("DomainDNSSetHostsResult", {}).get("IsSuccess"):
            print(
                f"Successfully deleted {len(records_to_delete)} {record_type} record(s) for {name}.{domain}"
            )
        else:
            print("Failed to delete DNS record(s)")

    except NamecheapException as e:
        print(f"API Error ({e.code}): {e.message}")
    except Exception as e:
        print(f"Error: {e}")


def import_records(client, domain, json_file, args=None):
    """Import DNS records from a JSON file"""
    try:
        # Read the JSON file
        with open(json_file) as f:
            records = json.load(f)

        if not isinstance(records, list):
            print("Error: JSON file must contain an array of DNS records")
            return

        # Convert to Namecheap format
        host_records = []
        for record in records:
            new_record = {
                "HostName": record.get("name", "@"),
                "RecordType": record.get("type", "A"),
                "Address": record.get("value", ""),
                "TTL": str(record.get("ttl", 1800)),
            }

            # Add MXPref for MX records
            if new_record["RecordType"] == "MX":
                new_record["MXPref"] = str(record.get("priority", 10))

            host_records.append(new_record)

        # Display summary of records to be imported
        print(f"\nReady to import {len(host_records)} DNS records for {domain}:")
        record_types = {}
        for record in host_records:
            record_type = record["RecordType"]
            record_types[record_type] = record_types.get(record_type, 0) + 1

        for record_type, count in record_types.items():
            print(f"  {count} {record_type} record(s)")

        # Ask for confirmation before proceeding (unless force flag is used)
        if not getattr(args, "force", False) and not confirm_action(
            "Do you want to proceed with the import?"
        ):
            print("Import operation cancelled.")
            return

        # Update the DNS records
        result = client.domains_dns_set_hosts(domain, host_records)

        if result.get("DomainDNSSetHostsResult", {}).get("IsSuccess"):
            print(f"Successfully imported {len(host_records)} DNS records for {domain}")
        else:
            print("Failed to import DNS records")

    except json.JSONDecodeError:
        print(f"Error: {json_file} is not a valid JSON file")
    except NamecheapException as e:
        print(f"API Error ({e.code}): {e.message}")
    except Exception as e:
        print(f"Error: {e}")


def export_records(client, domain, json_file):
    """Export DNS records to a JSON file"""
    try:
        # Get the DNS records
        result = client.domains_dns_get_hosts(domain)

        # Extract host records
        host_records = result.get("DomainDNSGetHostsResult", {}).get("host", [])
        if not isinstance(host_records, list):
            host_records = [host_records]

        # Convert to a simpler format
        records = []
        for record in host_records:
            new_record = {
                "name": record.get("Name", ""),
                "type": record.get("Type", ""),
                "value": record.get("Address", ""),
                "ttl": int(record.get("TTL", 1800)),
            }

            # Add priority for MX records
            if record.get("Type") == "MX":
                new_record["priority"] = int(record.get("MXPref", 10))

            records.append(new_record)

        # Write to the JSON file
        with open(json_file, "w") as f:
            json.dump(records, f, indent=2)

        print(f"Successfully exported {len(records)} DNS records to {json_file}")

    except NamecheapException as e:
        print(f"API Error ({e.code}): {e.message}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point for the DNS tool"""
    parser = argparse.ArgumentParser(description="Namecheap DNS Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List records command
    list_parser = subparsers.add_parser("list", help="List DNS records for a domain")
    list_parser.add_argument("domain", help="Domain name")

    # Add record command
    add_parser = subparsers.add_parser("add", help="Add a DNS record to a domain")
    add_parser.add_argument("domain", help="Domain name")
    add_parser.add_argument("--name", default="@", help="Host name (@ for root)")
    add_parser.add_argument(
        "--type",
        choices=["A", "AAAA", "CNAME", "MX", "TXT", "URL", "URL301", "FRAME"],
        required=True,
        help="Record type",
    )
    add_parser.add_argument("--value", required=True, help="Record value/address")
    add_parser.add_argument(
        "--ttl", default=1800, type=int, help="Time to live in seconds"
    )
    add_parser.add_argument(
        "--priority", default=10, type=int, help="Priority (for MX records)"
    )
    add_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )

    # Delete record command
    delete_parser = subparsers.add_parser(
        "delete", help="Delete a DNS record from a domain"
    )
    delete_parser.add_argument("domain", help="Domain name")
    delete_parser.add_argument("--name", required=True, help="Host name to delete")
    delete_parser.add_argument(
        "--type",
        required=True,
        choices=["A", "AAAA", "CNAME", "MX", "TXT", "URL", "URL301", "FRAME"],
        help="Record type to delete",
    )
    delete_parser.add_argument(
        "--value",
        help="Record value/address (if specified, only deletes records with this value)",
    )
    delete_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )

    # Import records command
    import_parser = subparsers.add_parser(
        "import", help="Import DNS records from a JSON file"
    )
    import_parser.add_argument("domain", help="Domain name")
    import_parser.add_argument("json_file", help="JSON file containing DNS records")
    import_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )

    # Export records command
    export_parser = subparsers.add_parser(
        "export", help="Export DNS records to a JSON file"
    )
    export_parser.add_argument("domain", help="Domain name")
    export_parser.add_argument("json_file", help="JSON file to export DNS records to")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize the client
    client = init_client()

    # Execute the command
    if args.command == "list":
        list_records(client, args.domain)
    elif args.command == "add":
        record_data = {
            "name": args.name,
            "type": args.type,
            "value": args.value,
            "ttl": str(args.ttl),
            "priority": str(args.priority),
        }
        add_record(client, args.domain, record_data, args)
    elif args.command == "delete":
        record_data = {"name": args.name, "type": args.type, "value": args.value}
        delete_record(client, args.domain, record_data, args)
    elif args.command == "import":
        import_records(client, args.domain, args.json_file, args)
    elif args.command == "export":
        export_records(client, args.domain, args.json_file)


if __name__ == "__main__":
    main()

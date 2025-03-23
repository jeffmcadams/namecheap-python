"""
Enhanced DNS operations
"""
from typing import Any, Dict, List, Optional


class EnhancedDnsAPI:
    """
    Enhanced DNS operations that combine multiple API calls
    """

    def __init__(self, client):
        """
        Initialize enhanced DNS operations

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def update_record(
        self,
        domain_name: str,
        host: str,
        record_type: str,
        value: str,
        ttl: int = 1800,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add or update a single DNS record while preserving all other records

        Args:
            domain_name: The domain to update
            host: Host name (e.g., "@", "www")
            record_type: Type of record (A, AAAA, CNAME, MX, TXT, etc.)
            value: Value for the record
            ttl: Time to live in seconds (default: 1800)
            priority: Priority for MX records

        Returns:
            Result of the operation

        Raises:
            ValueError: If parameters are invalid
            NamecheapException: If the API returns an error
        """
        # Get current hosts
        result = self.client.domains.dns.get_hosts(domain_name)

        # Extract existing records
        host_records = []
        if "DomainDNSGetHostsResult" in result and "host" in result["DomainDNSGetHostsResult"]:
            host_records = result["DomainDNSGetHostsResult"]["host"]
            if not isinstance(host_records, list):
                host_records = [host_records]

        # Find if record exists
        found = False
        new_hosts = []

        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type_existing = host_record.get("Type", "")

            if record_name == host and record_type_existing == record_type:
                # Update existing record
                new_record = {
                    "Name": host,
                    "Type": record_type,
                    "Address": value,
                    "TTL": str(ttl)
                }

                if record_type == "MX" and priority is not None:
                    new_record["MXPref"] = str(priority)
                elif "MXPref" in host_record and host_record["MXPref"]:
                    new_record["MXPref"] = host_record["MXPref"]

                new_hosts.append(new_record)
                found = True
            else:
                # Keep existing record
                new_hosts.append({
                    "Name": record_name,
                    "Type": record_type_existing,
                    "Address": host_record.get("Address", ""),
                    "MXPref": host_record.get("MXPref", "10"),
                    "TTL": host_record.get("TTL", "1800")
                })

        # Add new record if not found
        if not found:
            new_record = {
                "Name": host,
                "Type": record_type,
                "Address": value,
                "TTL": str(ttl)
            }

            if record_type == "MX":
                new_record["MXPref"] = str(
                    priority if priority is not None else 10)

            new_hosts.append(new_record)

        # Set the updated host records
        return self.client.domains.dns.set_hosts(domain_name, new_hosts)

    def delete_record(
        self,
        domain_name: str,
        host: str,
        record_type: str,
        value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a DNS record

        Args:
            domain_name: The domain to update
            host: Host name (e.g., "@", "www")
            record_type: Type of record (A, AAAA, CNAME, MX, TXT, etc.)
            value: Optional value for the record (if specified, will only delete records with matching value)

        Returns:
            Result of the operation

        Raises:
            NamecheapException: If the API returns an error
        """
        # Get current hosts
        result = self.client.domains.dns.get_hosts(domain_name)

        # Extract existing records
        host_records = []
        if "DomainDNSGetHostsResult" in result and "host" in result["DomainDNSGetHostsResult"]:
            host_records = result["DomainDNSGetHostsResult"]["host"]
            if not isinstance(host_records, list):
                host_records = [host_records]

        # Filter out the records to delete
        new_hosts = []
        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type_existing = host_record.get("Type", "")

            # Skip records that match the deletion criteria
            if record_name == host and record_type_existing == record_type:
                if value is None or host_record.get("Address", "") == value:
                    continue

            # Keep this record
            new_hosts.append({
                "Name": record_name,
                "Type": record_type_existing,
                "Address": host_record.get("Address", ""),
                "MXPref": host_record.get("MXPref", "10"),
                "TTL": host_record.get("TTL", "1800")
            })

        # Set the updated host records
        return self.client.domains.dns.set_hosts(domain_name, new_hosts)

    def set_a_records(self, domain_name: str, ip_address: str) -> Dict[str, Any]:
        """
        Set A records for @ and www to point to the same IP address

        Args:
            domain_name: The domain to update
            ip_address: IP address to set

        Returns:
            Result of the operation

        Raises:
            NamecheapException: If the API returns an error
        """
        # Get current hosts to preserve other records
        result = self.client.domains.dns.get_hosts(domain_name)

        # Extract existing records
        host_records = []
        if "DomainDNSGetHostsResult" in result and "host" in result["DomainDNSGetHostsResult"]:
            host_records = result["DomainDNSGetHostsResult"]["host"]
            if not isinstance(host_records, list):
                host_records = [host_records]

        # Keep only non-A records for @ and www
        new_hosts = []
        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type = host_record.get("Type", "")

            if record_name in ["@", "www"] and record_type == "A":
                continue

            new_hosts.append({
                "Name": record_name,
                "Type": record_type,
                "Address": host_record.get("Address", ""),
                "MXPref": host_record.get("MXPref", "10"),
                "TTL": host_record.get("TTL", "1800")
            })

        # Add new A records
        new_hosts.append({
            "Name": "@",
            "Type": "A",
            "Address": ip_address,
            "TTL": "1800"
        })

        new_hosts.append({
            "Name": "www",
            "Type": "A",
            "Address": ip_address,
            "TTL": "1800"
        })

        # Set the updated host records
        return self.client.domains.dns.set_hosts(domain_name, new_hosts)

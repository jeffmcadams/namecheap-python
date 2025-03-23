"""
Enhanced DNS operations
"""
from typing import Dict, List, Optional, TYPE_CHECKING, TypedDict, Union, cast

from ..base import ResponseDict

# Import needed for type hints
if TYPE_CHECKING:
    from ..client import NamecheapClient


class DnsHostRecord(TypedDict, total=False):
    """Type for a DNS host record"""
    Name: str
    Type: str
    Address: str
    MXPref: str
    TTL: str


class DnsDomainResult(TypedDict):
    """Type for DNS domain result"""
    Domain: str
    IsUsingOurDNS: bool
    Hosts: List[DnsHostRecord]
    EmailType: str


class UpdateRecordResult(TypedDict):
    """Result type for update_record operation"""
    domain: str
    host: str
    type: str
    value: str
    ttl: int
    success: bool


class DeleteRecordResult(TypedDict):
    """Result type for delete_record operation"""
    domain: str
    host: str
    type: str
    success: bool
    deleted_count: int


class SetARecordsResult(TypedDict):
    """Result type for set_a_records operation"""
    domain: str
    ip_address: str
    success: bool


def _convert_host_record_to_dict(record: DnsHostRecord) -> Dict[str, str]:
    """Convert a DnsHostRecord to a compatible Dict[str, str]"""
    result: Dict[str, str] = {}
    for key, value in record.items():
        if value is not None:
            result[key] = str(value)
    return result


class EnhancedDnsAPI:
    """
    Enhanced DNS operations that combine multiple API calls
    """

    def __init__(self, client: "NamecheapClient") -> None:
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
    ) -> UpdateRecordResult:
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
            Result of the operation including domain, host, type, value, ttl, and success

        Raises:
            ValueError: If parameters are invalid
            NamecheapException: If the API returns an error
        """
        # Import utility functions
        from ..utils import safe_get, ensure_list
        
        # Get current hosts
        result = self.client.domains.dns.get_hosts(domain_name)
        
        # Extract existing records safely
        dns_hosts_result: Dict[str, object] = {}
        if isinstance(result, dict):
            hosts_result = result.get("DomainDNSGetHostsResult")
            if isinstance(hosts_result, dict):
                dns_hosts_result = hosts_result
        
        host_entries: List[object] = []
        if isinstance(dns_hosts_result, dict):
            entries = dns_hosts_result.get("host")
            if isinstance(entries, list):
                host_entries = entries
            elif entries is not None:
                host_entries = [entries]
            
        host_records = ensure_list(host_entries)
        
        # Find if record exists
        found = False
        new_hosts: List[DnsHostRecord] = []

        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type_existing = host_record.get("Type", "")

            if record_name == host and record_type_existing == record_type:
                # Update existing record
                updated_record: DnsHostRecord = {
                    "Name": host,
                    "Type": record_type,
                    "Address": value,
                    "TTL": str(ttl)
                }

                if record_type == "MX" and priority is not None:
                    updated_record["MXPref"] = str(priority)
                elif host_record.get("MXPref"):
                    updated_record["MXPref"] = host_record.get("MXPref", "")

                new_hosts.append(updated_record)
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
            new_rec: DnsHostRecord = {
                "Name": host,
                "Type": record_type,
                "Address": value,
                "TTL": str(ttl)
            }

            if record_type == "MX":
                new_rec["MXPref"] = str(
                    priority if priority is not None else 10)

            new_hosts.append(new_rec)

        # Convert host records to dict and set the updated host records
        host_records_dict = [_convert_host_record_to_dict(record) for record in new_hosts]
        response = self.client.domains.dns.set_hosts(domain_name, host_records_dict)

        # Create properly typed result
        update_result: UpdateRecordResult = {
            "domain": domain_name,
            "host": host,
            "type": record_type,
            "value": value,
            "ttl": ttl,
            "success": bool(response.get("IsSuccess", False))
        }
        return update_result

    def delete_record(
        self,
        domain_name: str,
        host: str,
        record_type: str,
        value: Optional[str] = None
    ) -> DeleteRecordResult:
        """
        Delete a DNS record

        Args:
            domain_name: The domain to update
            host: Host name (e.g., "@", "www")
            record_type: Type of record (A, AAAA, CNAME, MX, TXT, etc.)
            value: Optional value for the record (if specified, will only delete records with matching value)

        Returns:
            Result of the operation including domain, host, type, success, and deleted_count

        Raises:
            NamecheapException: If the API returns an error
        """
        # Import utility functions
        from ..utils import ensure_list
        
        # Get current hosts
        result = self.client.domains.dns.get_hosts(domain_name)

        # Extract existing records safely
        dns_hosts_result: Dict[str, object] = {}
        if isinstance(result, dict):
            hosts_result = result.get("DomainDNSGetHostsResult")
            if isinstance(hosts_result, dict):
                dns_hosts_result = hosts_result
        
        host_entries: List[object] = []
        if isinstance(dns_hosts_result, dict):
            entries = dns_hosts_result.get("host")
            if isinstance(entries, list):
                host_entries = entries
            elif entries is not None:
                host_entries = [entries]
            
        host_records = ensure_list(host_entries)
        
        # Filter out the records to delete
        new_hosts: List[DnsHostRecord] = []
        deleted_count = 0

        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type_existing = host_record.get("Type", "")

            # Skip records that match the deletion criteria
            if record_name == host and record_type_existing == record_type:
                if value is None or host_record.get("Address", "") == value:
                    deleted_count += 1
                    continue

            # Keep this record
            new_hosts.append({
                "Name": record_name,
                "Type": record_type_existing,
                "Address": host_record.get("Address", ""),
                "MXPref": host_record.get("MXPref", "10"),
                "TTL": host_record.get("TTL", "1800")
            })

        # Convert host records to dict and set the updated host records
        host_records_dict = [_convert_host_record_to_dict(record) for record in new_hosts]
        response = self.client.domains.dns.set_hosts(domain_name, host_records_dict)

        # Create properly typed result
        delete_result: DeleteRecordResult = {
            "domain": domain_name,
            "host": host,
            "type": record_type,
            "success": bool(response.get("IsSuccess", False)),
            "deleted_count": deleted_count
        }
        return delete_result

    def set_a_records(self, domain_name: str, ip_address: str) -> SetARecordsResult:
        """
        Set A records for @ and www to point to the same IP address

        Args:
            domain_name: The domain to update
            ip_address: IP address to set

        Returns:
            Result of the operation including domain, ip_address, and success

        Raises:
            NamecheapException: If the API returns an error
        """
        # Import utility functions
        from ..utils import ensure_list
        
        # Get current hosts to preserve other records
        result = self.client.domains.dns.get_hosts(domain_name)

        # Extract existing records safely
        dns_hosts_result: Dict[str, object] = {}
        if isinstance(result, dict):
            hosts_result = result.get("DomainDNSGetHostsResult")
            if isinstance(hosts_result, dict):
                dns_hosts_result = hosts_result
        
        host_entries: List[object] = []
        if isinstance(dns_hosts_result, dict):
            entries = dns_hosts_result.get("host")
            if isinstance(entries, list):
                host_entries = entries
            elif entries is not None:
                host_entries = [entries]
            
        host_records = ensure_list(host_entries)

        # Keep only non-A records for @ and www
        new_hosts: List[DnsHostRecord] = []

        for host_record in host_records:
            if not isinstance(host_record, dict):
                continue

            record_name = host_record.get("Name", "")
            record_type = host_record.get("Type", "")

            # Skip A records for @ and www
            if record_name in ["@", "www"] and record_type == "A":
                continue

            # Add record with correct typing
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

        # Convert host records to dict and set the updated host records
        host_records_dict = [_convert_host_record_to_dict(record) for record in new_hosts]
        response = self.client.domains.dns.set_hosts(domain_name, host_records_dict)

        # Create properly typed result
        a_records_result: SetARecordsResult = {
            "domain": domain_name,
            "ip_address": ip_address,
            "success": bool(response.get("IsSuccess", False))
        }
        return a_records_result

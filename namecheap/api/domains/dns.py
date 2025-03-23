"""
DNS-related operations for domains API
"""
from typing import Any, Dict, List, Optional


class DnsAPI:
    """DNS API methods for domains namespace"""

    def __init__(self, client):
        """
        Initialize the DNS API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def _split_domain_name(self, domain_name: str):
        """Split domain name into SLD and TLD parts"""
        parts = domain_name.split(".")
        sld = parts[0]
        tld = ".".join(parts[1:])
        return sld, tld

    def get_hosts(self, domain_name: str) -> Dict[str, Any]:
        """
        Get DNS host records for a domain

        Args:
            domain_name: The domain name to get host records for

        Returns:
            Dictionary with host record information in a standardized format:
            {
                "DomainDNSGetHostsResult": {
                    "Domain": "example.com",
                    "IsUsingOurDNS": True,
                    "EmailType": "NONE",
                    "host": [
                        {
                            "Name": "@",
                            "Type": "A",
                            "Address": "192.0.2.1",
                            "MXPref": "10",
                            "TTL": "1800",
                            "HostId": "12345",
                            "IsActive": True
                        },
                        ...
                    ]
                }
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}

        result = self.client._make_request(
            "namecheap.domains.dns.getHosts", params)

        # Normalize the response to ensure host is always a list
        if "DomainDNSGetHostsResult" in result:
            hosts_result = result["DomainDNSGetHostsResult"]

            if "host" in hosts_result:
                host_records = hosts_result["host"]
                # Convert single host record to a list for consistency
                if not isinstance(host_records, list):
                    hosts_result["host"] = [host_records]
            else:
                # No host records found, initialize with empty list
                hosts_result["host"] = []

        return result

    def set_hosts(self, domain_name: str, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Set DNS host records for a domain

        Args:
            domain_name: The domain name to set host records for
            hosts: List of host record dictionaries with keys:
                  - HostName: Name of the host record (e.g., "@", "www")
                  - RecordType: Type of record (A, AAAA, CNAME, MX, TXT, URL, URL301, FRAME)
                  - Address: Value of the record
                  - MXPref: MX preference (required for MX records)
                  - TTL: Time to live in seconds (min 60, max 86400, default 1800)

        Returns:
            Dictionary with status information in a standardized format:
            {
                "DomainDNSSetHostsResult": {
                    "Domain": "example.com",
                    "IsSuccess": True
                }
            }

        Raises:
            ValueError: If any required host record fields are missing
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}

        valid_record_types = [
            "A",
            "AAAA",
            "CNAME",
            "MX",
            "TXT",
            "URL",
            "URL301",
            "FRAME",
        ]

        # Handle the case when hosts parameter is empty
        if not hosts:
            if hasattr(self.client, 'debug') and self.client.debug:
                print("Warning: No host records provided for DNS update")

        # Normalize host record field names
        normalized_hosts = []
        for host in hosts:
            # Convert between the API format (HostName) and a more user-friendly format (Name)
            normalized_host = {}

            # Handle Name/HostName field
            if "Name" in host:
                normalized_host["HostName"] = host["Name"]
            elif "HostName" in host:
                normalized_host["HostName"] = host["HostName"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Name' or 'HostName'")

            # Handle Type/RecordType field
            if "Type" in host:
                normalized_host["RecordType"] = host["Type"]
            elif "RecordType" in host:
                normalized_host["RecordType"] = host["RecordType"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Type' or 'RecordType'")

            # Handle Address/Value field
            if "Value" in host:
                normalized_host["Address"] = host["Value"]
            elif "Address" in host:
                normalized_host["Address"] = host["Address"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Value' or 'Address'")

            # Handle MXPref/Priority field
            if normalized_host["RecordType"] == "MX":
                if "Priority" in host:
                    normalized_host["MXPref"] = host["Priority"]
                elif "MXPref" in host:
                    normalized_host["MXPref"] = host["MXPref"]
                else:
                    # Use default value for MX priority
                    normalized_host["MXPref"] = "10"

            # Handle TTL field
            if "TTL" in host:
                ttl = host["TTL"]
                # Convert to string if it's an integer
                if isinstance(ttl, int):
                    ttl = str(ttl)
                normalized_host["TTL"] = ttl
            else:
                # Use default TTL
                normalized_host["TTL"] = "1800"

            normalized_hosts.append(normalized_host)

        # Add host records to API parameters
        for i, host in enumerate(normalized_hosts):
            record_type = host["RecordType"]
            if record_type not in valid_record_types:
                raise ValueError(
                    f"Invalid record type '{record_type}'. Must be one of {valid_record_types}"
                )

            # If TTL is provided, validate it
            if "TTL" in host:
                try:
                    ttl = int(host["TTL"])
                    if ttl < 60 or ttl > 86400:
                        raise ValueError(
                            "TTL must be between 60 and 86400 seconds")
                except ValueError:
                    raise ValueError(
                        f"Invalid TTL value: {host['TTL']}. Must be an integer between 60 and 86400."
                    )

            params[f"HostName{i+1}"] = host["HostName"]
            params[f"RecordType{i+1}"] = host["RecordType"]
            params[f"Address{i+1}"] = host["Address"]

            if "MXPref" in host:
                params[f"MXPref{i+1}"] = host["MXPref"]
            if "TTL" in host:
                params[f"TTL{i+1}"] = host["TTL"]

        if hasattr(self.client, 'debug') and self.client.debug:
            print(
                f"Setting {len(normalized_hosts)} host records for {domain_name}")

        return self.client._make_request("namecheap.domains.dns.setHosts", params)

    def set_default(self, domain_name: str) -> Dict[str, Any]:
        """
        Set default nameservers for a domain

        Args:
            domain_name: The domain name to set nameservers for

        Returns:
            Dictionary with status information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld}
        return self.client._make_request("namecheap.domains.dns.setDefault", params)

    def set_custom(self, domain_name: str, nameservers: List[str]) -> Dict[str, Any]:
        """
        Set custom nameservers for a domain

        Args:
            domain_name: The domain name to set nameservers for
            nameservers: List of nameservers to use (max 12)

        Returns:
            Dictionary with status information

        Raises:
            ValueError: If more than 12 nameservers are provided
            NamecheapException: If the API returns an error
        """
        if len(nameservers) > 12:
            raise ValueError("Maximum of 12 nameservers can be set")

        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld,
                  "Nameservers": ",".join(nameservers)}
        return self.client._make_request("namecheap.domains.dns.setCustom", params)

    def get_list(self, domain_name: str) -> Dict[str, Any]:
        """
        Gets a list of DNS servers associated with the requested domain

        Args:
            domain_name: The domain name to get DNS servers for

        Returns:
            Dictionary with DNS server information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}
        return self.client._make_request("namecheap.domains.dns.getList", params)

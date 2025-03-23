#!/usr/bin/env python3
"""
Test suite for the Namecheap Python SDK
"""

import unittest
from unittest.mock import Mock, patch

from namecheap import NamecheapClient, NamecheapException


class TestNamecheapClient(unittest.TestCase):
    """Test cases for the Namecheap API client"""

    def setUp(self):
        """Set up test environment"""
        self.client = NamecheapClient(
            api_user="test_user",
            api_key="test_key",
            username="test_user",
            client_ip="127.0.0.1",
            sandbox=True,
            debug=False,
        )

    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.api_user, "test_user")
        self.assertEqual(self.client.api_key, "test_key")
        self.assertEqual(self.client.username, "test_user")
        self.assertEqual(self.client.client_ip, "127.0.0.1")
        self.assertEqual(
            self.client.base_url, "https://api.sandbox.namecheap.com/xml.response"
        )
        self.assertEqual(self.client.debug, False)

    @patch("requests.get")
    def test_make_request(self, mock_get):
        """Test making a request to the API"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
            <Errors />
            <Warnings />
            <RequestedCommand>namecheap.domains.check</RequestedCommand>
            <CommandResponse Type="namecheap.domains.check">
                <DomainCheckResult Domain="example.com" Available="false" />
            </CommandResponse>
            <Server>SERVER-NAME</Server>
            <GMTTimeDifference>+5</GMTTimeDifference>
            <ExecutionTime>0.32</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the method
        result = self.client._make_request(
            "namecheap.domains.check", {"DomainList": "example.com"}
        )

        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(
            args[0], "https://api.sandbox.namecheap.com/xml.response")
        self.assertEqual(kwargs["params"]["ApiUser"], "test_user")
        self.assertEqual(kwargs["params"]["ApiKey"], "test_key")
        self.assertEqual(kwargs["params"]["UserName"], "test_user")
        self.assertEqual(kwargs["params"]["ClientIp"], "127.0.0.1")
        self.assertEqual(kwargs["params"]["Command"],
                         "namecheap.domains.check")
        self.assertEqual(kwargs["params"]["DomainList"], "example.com")

        # Verify result is parsed correctly
        domain_check_result = result["DomainCheckResult"]
        # Check if the result is a list or a single item
        if isinstance(domain_check_result, list):
            # If it's a list, get the first item
            self.assertEqual(domain_check_result[0]["Domain"], "example.com")
            self.assertEqual(
                domain_check_result[0]["Available"], False
            )  # Should be converted to a bool
        else:
            # If it's a single item
            self.assertEqual(domain_check_result["Domain"], "example.com")
            self.assertEqual(
                domain_check_result["Available"], False
            )  # Should be converted to a bool

    @patch("requests.get")
    def test_error_response(self, mock_get):
        """Test handling API error responses"""
        # Mock error response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <ApiResponse Status="ERROR" xmlns="http://api.namecheap.com/xml.response">
            <Errors>
                <Error Number="1011102">API Key is invalid or API access has not been enabled</e>
            </Errors>
            <Warnings />
            <RequestedCommand>namecheap.domains.check</RequestedCommand>
            <Server>SERVER-NAME</Server>
            <GMTTimeDifference>+5</GMTTimeDifference>
            <ExecutionTime>0.001</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the method and verify exception
        with self.assertRaises(NamecheapException) as context:
            self.client._make_request(
                "namecheap.domains.check", {"DomainList": "example.com"}
            )

        # Verify exception details
        self.assertEqual(context.exception.code, "1011102")
        self.assertEqual(
            context.exception.message,
            "API Key is invalid or API access has not been enabled - Please verify your API key and ensure API access is enabled at https://ap.www.namecheap.com/settings/tools/apiaccess/",
        )

    @patch("requests.get")
    def test_domains_check(self, mock_get):
        """Test domains_check method"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
            <Errors />
            <Warnings />
            <RequestedCommand>namecheap.domains.check</RequestedCommand>
            <CommandResponse Type="namecheap.domains.check">
                <DomainCheckResult Domain="example.com" Available="false" IsPremiumName="false" />
                <DomainCheckResult Domain="example.net" Available="true" IsPremiumName="false" />
            </CommandResponse>
            <Server>SERVER-NAME</Server>
            <GMTTimeDifference>+5</GMTTimeDifference>
            <ExecutionTime>0.32</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Test with multiple domains
        domains = ["example.com", "example.net"]
        result = self.client.domains_check(domains)

        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["Command"],
                         "namecheap.domains.check")
        self.assertEqual(kwargs["params"]["DomainList"],
                         "example.com,example.net")

        # Verify results
        self.assertEqual(len(result["DomainCheckResult"]), 2)
        self.assertEqual(result["DomainCheckResult"]
                         [0]["Domain"], "example.com")
        self.assertEqual(result["DomainCheckResult"][0]["Available"], False)
        self.assertEqual(result["DomainCheckResult"]
                         [1]["Domain"], "example.net")
        self.assertEqual(result["DomainCheckResult"][1]["Available"], True)

        # Test with too many domains
        with self.assertRaises(ValueError) as context:
            self.client.domains_check(
                ["domain" + str(i) + ".com" for i in range(51)])
        self.assertIn("Maximum of 50 domains", str(context.exception))

    @patch("namecheap.client.NamecheapClient._make_request")
    def test_domains_get_list(self, mock_make_request):
        """Test domains_get_list method"""
        # Mock successful response
        mock_make_request.return_value = {
            "DomainGetListResult": {
                "Domain": [
                    {
                        "ID": "1",
                        "Name": "example.com",
                        "Created": "2023-01-01",
                        "Expires": "2024-01-01",
                    },
                    {
                        "ID": "2",
                        "Name": "example.net",
                        "Created": "2023-01-01",
                        "Expires": "2024-01-01",
                    },
                ]
            },
            "Paging": {"TotalItems": "2", "CurrentPage": "1", "PageSize": "20"},
        }

        # Test with default parameters
        result = self.client.domains_get_list()

        # Verify request
        mock_make_request.assert_called_once_with(
            "namecheap.domains.getList",
            {"Page": 1, "PageSize": 20, "SortBy": "NAME", "ListType": "ALL"},
        )

        # Verify results
        self.assertEqual(len(result["DomainGetListResult"]["Domain"]), 2)
        self.assertEqual(
            result["DomainGetListResult"]["Domain"][0]["Name"], "example.com"
        )
        self.assertEqual(
            result["DomainGetListResult"]["Domain"][1]["Name"], "example.net"
        )

        # Test with custom parameters
        mock_make_request.reset_mock()
        result = self.client.domains_get_list(
            page=2,
            page_size=50,
            sort_by="EXPIREDATE",
            list_type="EXPIRING",
            search_term="example",
        )

        # Verify request
        mock_make_request.assert_called_once_with(
            "namecheap.domains.getList",
            {
                "Page": 2,
                "PageSize": 50,
                "SortBy": "EXPIREDATE",
                "ListType": "EXPIRING",
                "SearchTerm": "example",
            },
        )

        # Test with invalid sort_by
        with self.assertRaises(ValueError):
            self.client.domains_get_list(sort_by="INVALID")

        # Test with invalid list_type
        with self.assertRaises(ValueError):
            self.client.domains_get_list(list_type="INVALID")

        # Test with page_size too large
        with self.assertRaises(ValueError):
            self.client.domains_get_list(page_size=101)

    @patch("namecheap.client.NamecheapClient._make_request")
    def test_domains_dns_set_hosts(self, mock_make_request):
        """Test domains_dns_set_hosts method"""
        # Mock successful response
        mock_make_request.return_value = {
            "DomainDNSSetHostsResult": {"Domain": "example.com", "IsSuccess": True}
        }

        # Test with valid hosts
        hosts = [
            {"HostName": "@", "RecordType": "A",
                "Address": "192.0.2.1", "TTL": "1800"},
            {"HostName": "www", "RecordType": "CNAME",
                "Address": "@", "TTL": "1800"},
            {
                "HostName": "mail",
                "RecordType": "MX",
                "Address": "mail.example.com",
                "MXPref": "10",
                "TTL": "1800",
            },
        ]

        result = self.client.domains_dns_set_hosts("example.com", hosts)

        # Verify request
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        self.assertEqual(args[0], "namecheap.domains.dns.setHosts")
        params = args[1] if len(args) > 1 else kwargs
        self.assertEqual(params["SLD"], "example")
        self.assertEqual(params["TLD"], "com")

        # Verify host parameters
        self.assertEqual(params["HostName1"], "@")
        self.assertEqual(params["RecordType1"], "A")
        self.assertEqual(params["Address1"], "192.0.2.1")
        self.assertEqual(params["HostName3"], "mail")
        self.assertEqual(params["MXPref3"], "10")

        # Test with missing required fields
        with self.assertRaises(ValueError):
            self.client.domains_dns_set_hosts(
                "example.com", [{"RecordType": "A", "Address": "192.0.2.1"}]
            )

        with self.assertRaises(ValueError):
            self.client.domains_dns_set_hosts(
                "example.com", [{"HostName": "@", "Address": "192.0.2.1"}]
            )

        with self.assertRaises(ValueError):
            self.client.domains_dns_set_hosts(
                "example.com", [{"HostName": "@", "RecordType": "A"}]
            )

        # Test with invalid record type
        with self.assertRaises(ValueError):
            self.client.domains_dns_set_hosts(
                "example.com",
                [{"HostName": "@", "RecordType": "INVALID", "Address": "192.0.2.1"}],
            )

        # In the current implementation, MXPref defaults to "10" if not provided
        # So this wouldn't raise an error anymore
        mx_host = {
            "HostName": "mail",
            "RecordType": "MX",
            "Address": "mail.example.com",
        }
        self.client.domains_dns_set_hosts("example.com", [mx_host])

        # Test with invalid TTL
        with self.assertRaises(ValueError):
            self.client.domains_dns_set_hosts(
                "example.com",
                [
                    {
                        "HostName": "@",
                        "RecordType": "A",
                        "Address": "192.0.2.1",
                        "TTL": "30",
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Unit tests for the Namecheap API client
"""

import unittest
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET
from namecheap import NamecheapClient, NamecheapException


class TestNamecheapClient(unittest.TestCase):
    """Test cases for the Namecheap API client"""

    def setUp(self):
        """Set up the test environment"""
        self.client = NamecheapClient(
            api_user="test_user",
            api_key="test_key",
            username="test_user",
            client_ip="127.0.0.1",
            sandbox=True
        )

    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.api_user, "test_user")
        self.assertEqual(self.client.api_key, "test_key")
        self.assertEqual(self.client.username, "test_user")
        self.assertEqual(self.client.client_ip, "127.0.0.1")
        self.assertEqual(self.client.base_url, "https://api.sandbox.namecheap.com/xml.response")

    def test_get_base_params(self):
        """Test _get_base_params method"""
        base_params = self.client._get_base_params()
        expected_params = {
            "ApiUser": "test_user",
            "ApiKey": "test_key",
            "UserName": "test_user",
            "ClientIp": "127.0.0.1"
        }
        self.assertEqual(base_params, expected_params)

    @patch('requests.get')
    def test_make_request(self, mock_get):
        """Test _make_request method"""
        # Mock the response
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
            <ExecutionTime>32.76</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the method
        result = self.client._make_request("namecheap.domains.check", {"DomainList": "example.com"})

        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://api.sandbox.namecheap.com/xml.response")
        self.assertEqual(kwargs["params"]["ApiUser"], "test_user")
        self.assertEqual(kwargs["params"]["ApiKey"], "test_key")
        self.assertEqual(kwargs["params"]["UserName"], "test_user")
        self.assertEqual(kwargs["params"]["ClientIp"], "127.0.0.1")
        self.assertEqual(kwargs["params"]["Command"], "namecheap.domains.check")
        self.assertEqual(kwargs["params"]["DomainList"], "example.com")

    @patch('requests.get')
    def test_domains_check(self, mock_get):
        """Test domains_check method"""
        # Mock the response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
            <Errors />
            <Warnings />
            <RequestedCommand>namecheap.domains.check</RequestedCommand>
            <CommandResponse Type="namecheap.domains.check">
                <DomainCheckResult Domain="example.com" Available="false" />
                <DomainCheckResult Domain="example.net" Available="true" />
            </CommandResponse>
            <Server>SERVER-NAME</Server>
            <GMTTimeDifference>+5</GMTTimeDifference>
            <ExecutionTime>32.76</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.domains_check(["example.com", "example.net"])

        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["Command"], "namecheap.domains.check")
        self.assertEqual(kwargs["params"]["DomainList"], "example.com,example.net")

        # Verify the result is parsed correctly
        domain_results = result["DomainCheckResult"]
        self.assertEqual(len(domain_results), 2)
        for domain in domain_results:
            if domain["Domain"] == "example.com":
                self.assertFalse(domain["Available"])
            elif domain["Domain"] == "example.net":
                self.assertTrue(domain["Available"])

    @patch('requests.get')
    def test_dns_record_operations(self, mock_get):
        """Test DNS record operations"""
        # Mock the get hosts response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
            <Errors />
            <Warnings />
            <RequestedCommand>namecheap.domains.dns.getHosts</RequestedCommand>
            <CommandResponse Type="namecheap.domains.dns.getHosts">
                <DomainDNSGetHostsResult Domain="example.com" EmailType="MX" IsUsingOurDNS="true">
                    <host HostId="12345" Name="@" Type="A" Address="192.0.2.1" MXPref="10" TTL="1800" />
                    <host HostId="12346" Name="www" Type="CNAME" Address="example.com." MXPref="10" TTL="1800" />
                </DomainDNSGetHostsResult>
            </CommandResponse>
            <Server>SERVER-NAME</Server>
            <GMTTimeDifference>+5</GMTTimeDifference>
            <ExecutionTime>32.76</ExecutionTime>
        </ApiResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.domains_dns_get_hosts("example.com")

        # Check the result contains normalized host records
        hosts_result = result["DomainDNSGetHostsResult"]
        self.assertEqual(hosts_result["Domain"], "example.com")
        self.assertTrue(hosts_result["IsUsingOurDNS"])
        
        host_records = hosts_result["host"]
        self.assertEqual(len(host_records), 2)
        self.assertEqual(host_records[0]["Name"], "@")
        self.assertEqual(host_records[0]["Type"], "A")
        self.assertEqual(host_records[1]["Name"], "www")
        self.assertEqual(host_records[1]["Type"], "CNAME")

    @patch('requests.get')
    def test_parse_error_response(self, mock_get):
        """Test error handling in _parse_response method"""
        # Mock the error response
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

        # Call the method and verify exception is raised
        with self.assertRaises(NamecheapException) as context:
            self.client._make_request("namecheap.domains.check", {"DomainList": "example.com"})
        
        self.assertEqual(context.exception.code, "1011102")
        self.assertIn("API Key is invalid or API access has not been enabled", context.exception.message)


if __name__ == "__main__":
    unittest.main()
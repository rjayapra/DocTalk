"""Tests for blob_utils SAS token generation."""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.api.blob_utils import add_sas_to_url


class TestAddSasToUrl(unittest.TestCase):
    """Tests for add_sas_to_url helper."""

    def test_empty_url_returns_empty(self):
        self.assertEqual(add_sas_to_url("", "myaccount"), "")

    def test_none_url_returns_empty(self):
        self.assertEqual(add_sas_to_url(None, "myaccount"), "")

    def test_non_blob_url_returned_unchanged(self):
        url = "https://example.com/audio.mp3"
        self.assertEqual(add_sas_to_url(url, "myaccount"), url)

    def test_non_azure_url_returned_unchanged(self):
        url = "https://cdn.example.com/file.mp3"
        self.assertEqual(add_sas_to_url(url, "myaccount"), url)

    @patch("src.api.blob_utils.generate_blob_sas")
    @patch("src.api.blob_utils.BlobServiceClient")
    @patch("src.api.blob_utils.DefaultAzureCredential")
    def test_blob_url_gets_sas_appended(self, mock_cred, mock_bsc, mock_gen_sas):
        mock_bsc_instance = MagicMock()
        mock_bsc.return_value = mock_bsc_instance
        mock_udk = MagicMock()
        mock_bsc_instance.get_user_delegation_key.return_value = mock_udk
        mock_gen_sas.return_value = "sv=2024-01-01&se=2025-01-01&sr=b&sig=test123"

        url = "https://myaccount.blob.core.windows.net/podcasts/abc123.mp3"
        result = add_sas_to_url(url, "myaccount")

        self.assertEqual(result, f"{url}?sv=2024-01-01&se=2025-01-01&sr=b&sig=test123")
        mock_gen_sas.assert_called_once()
        call_kwargs = mock_gen_sas.call_args
        self.assertEqual(call_kwargs.kwargs["container_name"], "podcasts")
        self.assertEqual(call_kwargs.kwargs["blob_name"], "abc123.mp3")
        self.assertEqual(call_kwargs.kwargs["account_name"], "myaccount")

    @patch("src.api.blob_utils.BlobServiceClient")
    @patch("src.api.blob_utils.DefaultAzureCredential")
    def test_sas_failure_returns_original_url(self, mock_cred, mock_bsc):
        mock_bsc.side_effect = Exception("Auth failed")

        url = "https://myaccount.blob.core.windows.net/podcasts/abc123.mp3"
        result = add_sas_to_url(url, "myaccount")

        self.assertEqual(result, url)

    def test_blob_url_missing_blob_name_returned_unchanged(self):
        url = "https://myaccount.blob.core.windows.net/podcasts"
        result = add_sas_to_url(url, "myaccount")
        self.assertEqual(result, url)


if __name__ == "__main__":
    unittest.main()

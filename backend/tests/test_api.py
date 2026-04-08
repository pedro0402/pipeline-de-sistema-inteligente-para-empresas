import os
from unittest.mock import Mock, patch

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


def fetch_sources(supabase_url: str, supabase_key: str, timeout: int = 10) -> requests.Response:
    return requests.get(
        f"{supabase_url}/rest/v1/sources",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        },
        timeout=timeout,
    )


def test_fetch_sources_builds_expected_request():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.text = "[]"

    with patch("requests.get", return_value=fake_response) as mocked_get:
        response = fetch_sources("https://example.supabase.co", "fake-key")

    assert response.status_code == 200
    mocked_get.assert_called_once_with(
        "https://example.supabase.co/rest/v1/sources",
        headers={
            "apikey": "fake-key",
            "Authorization": "Bearer fake-key",
        },
        timeout=10,
    )


@pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"),
    reason="SUPABASE_URL/SUPABASE_KEY nao configurados para teste de integracao",
)
def test_fetch_sources_live_returns_success():
    response = fetch_sources(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    assert response.status_code == 200
    assert isinstance(response.text, str)
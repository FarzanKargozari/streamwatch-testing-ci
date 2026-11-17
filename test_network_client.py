
import pytest
from unittest.mock import Mock
from network_client import check_network, send_with_retry


def test_network_timeout():
    network = Mock()
    network.send.side_effect = TimeoutError("Network timeout")

    with pytest.raises(TimeoutError):
        network.send()


def test_check_network_handles_timeout():
    network = Mock()
    network.send.side_effect = TimeoutError("Network timeout")

    result = check_network(network)

    assert result == "NETWORK_ERROR"


def test_check_network_success():
    network = Mock()
    network.send.return_value = "SUCCESS"

    result = check_network(network)

    assert result == "SUCCESS"
    network.send.assert_called_once()



def test_mock_retries():
    network = Mock()

    network.send.side_effect = [
        TimeoutError("Temporary failure"),
        "SUCCESS"
    ]

    with pytest.raises(TimeoutError):
        network.send()

    result = network.send()

    assert result == "SUCCESS"
    assert network.send.call_count == 2


def test_automatic_retry():
    network = Mock()

    network.send.side_effect = [
        TimeoutError("Temporary failure"),
        "SUCCESS"
    ]

    result = send_with_retry(network)

    assert result == "SUCCESS"
    assert network.send.call_count == 2


def test_retry_both_attempts_fail():
    network = Mock()

    network.send.side_effect = TimeoutError("Network unavailable")

    with pytest.raises(TimeoutError):
        send_with_retry(network)

    assert network.send.call_count == 2



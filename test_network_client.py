
import pytest
from unittest.mock import Mock
from network_client import check_network


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

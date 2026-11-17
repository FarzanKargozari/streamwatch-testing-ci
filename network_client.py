
def check_network(network):
    try:
        return network.send()
    except TimeoutError:
        return "NETWORK_ERROR"

def send_with_retry(network):
    try:
        return network.send()
    except TimeoutError:
        return network.send()

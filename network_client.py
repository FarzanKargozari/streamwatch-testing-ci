
def check_network(network):
    try:
        return network.send()
    except TimeoutError:
        return "NETWORK_ERROR"

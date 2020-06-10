from configparser import ConfigParser
from typing import Optional, List

from src.utils.config_parsers.user import NodeConfig
from src.utils.data_wrapper.oasis_api import OasisApiWrapper
from src.utils.logging import DUMMY_LOGGER
from src.utils.user_input import yn_prompt


def get_node(nodes_so_far: List[NodeConfig],
             oasis_api_data_wrapper: OasisApiWrapper) -> Optional[NodeConfig]:
    # Get node's name
    node_names_so_far = [n.node_name for n in nodes_so_far]
    while True:
        node_name = input('Unique node name that is identical to the node name'
                          'specified in the API server configuration'
                          ':\n')
        if node_name in node_names_so_far:
            print('Node name must be unique.')
        elif len(node_name) == 0:
            print('Node name cannot be empty.')
        else:
            break
    
    # Get the current chain ID
    while True:
        chain_name = input('Node\'s chain ID this can be found at '
                           'https://oasis.smartstake.io/:\n')
        if len(chain_name) == 0:
            print('Node\'s Chain ID cannot be empty.')
        else:
            break

    # Get node's API Url
    while True:
        api_url = input('Node\'s API url (typically http://API_IP:8686):\n')
        print('Trying to connect to endpoint {}/api/ping'.format(api_url))
        try:
            oasis_api_data_wrapper.ping_api(api_url)
            print('Success.')
            break
        except Exception:
            if not yn_prompt('Failed to connect to endpoint. Do '
                             'you want to try again? (Y/n)\n'):
                if not yn_prompt(
                        'Do you still want to add the node? (Y/n)\n'):
                    return None
                else:
                    break


    # Ask if node is a validator
    node_is_validator = yn_prompt('Is this node a validator? (Y/n)\n')
    node_has_exporter = yn_prompt('Does this node have Node Exporter installed?'
                                  ' (Y/n)\n')

    # Ask if node is an archive node.
    # Note: if the node is a validator, it must also be an archive node.
    # However, it was done this way in case of changes in future updates.
    node_is_archive_node = yn_prompt('Is this node an archive node? (Y/n)\n')

    monitor_node = yn_prompt('Would you like to monitor this node? (Y/n) \n')

    # Get validator's node public key
    if node_is_validator:
        while True:
            node_public_key = input('Node\'s public identifier, found inside '
                            'the file entity.json within the key-value pair '
                            '"nodes":"NODE_PUBLIC_KEY", found on the machine '
                            'running the node. The format shown below : '
                            'J4i/ADAze7jYjcmPZvTFHD/tMa3wt9AMeaQALPXZebs=')

            if not node_public_key.strip():
                if not yn_prompt('You cannot leave the node_public_key '
                                 'field empty for a validator. Do you want to '
                                 'try again? (Y/n)\n'):
                    return None
            else:
                break
    else:
        node_public_key = ''

    # Return node
    return NodeConfig(node_name, chain_name, api_url, node_public_key, \
                    node_is_validator, node_has_exporter, monitor_node, \
                    node_is_archive_node, True)


def setup_nodes(cp: ConfigParser) -> None:
    print('==== Nodes')
    print('To produce alerts, the alerter needs something to monitor! The list '
          'of nodes to be included in the monitoring will now be set up. This '
          'includes validators, sentries, and any full nodes that can be used '
          'as data sources to monitor from the network\'s perspective, together'
          ' with whether they have Node Exporter enabled. You '
          'may include nodes from multiple networks in any order; PANIC '
          'will figure out which network they belong to when you run it. Node '
          'names must be set identical to the ones previously set in the API '
          'Server/s!')

    # Check if list already set up
    if len(cp.sections()) > 0 and \
            not yn_prompt('The list of nodes is already set up. Do you wish to '
                          'clear this list? You will then be asked to set up a '
                          'new list of nodes, if you wish to do so (Y/n)\n'):
        return

    # Clear config and initialise new list
    cp.clear()
    nodes = []

    # Ask if they want to set it up
    if not yn_prompt('Do you wish to set up the list of nodes? (Y/n)\n'):
        return

    # Get node details and append them to the list of nodes
    while True:
        # Check that API is running by retrieving some data which will be used.
        oasis_api_data_wrapper = OasisApiWrapper(DUMMY_LOGGER)
        node = get_node(nodes, oasis_api_data_wrapper)

        if node is not None:
            nodes.append(node)
            if node.node_is_validator:
                print('Successfully added validator node.')
            else:
                print('Successfully added full node.')

        if not yn_prompt('Do you want to add another node? (Y/n)\n'):
            break

    # Add nodes to config
    for i, node in enumerate(nodes):
        section = 'node_' + str(i)
        cp.add_section(section)
        cp[section]['node_name'] = node.node_name
        cp[section]['chain_name'] = node.chain_name
        cp[section]['node_api_url'] = node.node_api_url
        cp[section]['node_public_key'] = node.node_public_key
        cp[section]['node_is_validator'] = \
            'true' if node.node_is_validator else 'false'
        cp[section]['node_has_exporter'] = \
            'true' if node.node_has_exporter else 'false'
        cp[section]['monitor_node'] = \
            'true' if node.monitor_node else 'false'
        cp[section]['is_archive_node'] = \
            'true' if node.is_archive_node else 'false'
        cp[section]['use_as_data_source'] = \
            'true' if node.use_as_data_source else 'false'

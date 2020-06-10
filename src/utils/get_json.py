import json
import logging
from typing import Dict

import requests

from src.utils.exceptions import ApiCallFailedException, \
    UnexpectedApiCallErrorException, NodeWasNotConnectedToApiServerException, \
    UnexpectedApiErrorWhenReadingDataException, \
    ConnectionWithNodeApiLostException, InvalidConsensusPublicKeyException, \
    NodeIsNotAnArchiveNodeException


def get_json(endpoint: str, logger: logging.Logger, params=None):
    if params is None:
        params = {}
    # The timeout must be slightly greater than the API timeout so that errors
    # could be received from the API.
    get_ret = requests.get(url=endpoint, params=params, timeout=15)
    logger.debug('get_json: get_ret: %s', get_ret)
    return json.loads(get_ret.content.decode('UTF-8'))


def get_oasis_json(endpoint: str, params: Dict, logger: logging.Logger,
                      api_call: str = ''):
    data = get_json(endpoint, logger, params)
    if 'result' in data:
        return data['result']
    elif 'error' in data:
        # Error means that the Node is not connected to the API.
        if 'API call {} failed.'.format(api_call) in data['error']:
            raise ApiCallFailedException(data['error'])
        elif 'Node name requested doesn\'t exist'  in data['error']:
            raise NodeWasNotConnectedToApiServerException(data['error'])
        elif 'Error: API call {} failed.'.format(api_call) in data['error']:
            raise ApiCallFailedException(data['error'])
        elif 'An API for ' + params['name'] + \
                ' needs to be setup before it can be queried' in data['error']:
            raise NodeWasNotConnectedToApiServerException(data['error'])
        elif 'Failed to ping node by retrieving highest block height!' in data['error']:
            raise ConnectionWithNodeApiLostException(data['error'])
        elif 'Failed to Unmarshal Public Key' in data['error']:
            raise InvalidConsensusPublicKeyException(
                "Failed to parse Consensus public key.")
        else:
            raise UnexpectedApiCallErrorException(data['error'])
    else:
        raise UnexpectedApiErrorWhenReadingDataException(data)

import json
import logging

import requests
from prometheus_client.parser import text_string_to_metric_families

from src.utils.exceptions import NoParametersGivenException, \
    MetricNotFoundException, RequestCallFailedException


def get_prometheus(endpoint: str, logger: logging.Logger):
    try:
        metrics = requests.get(endpoint).content
        logger.debug('retrieved prometheus data from endpoint: ' + endpoint)
        return metrics.decode("utf-8")
    except requests.exceptions.RequestException as e:
        raise RequestCallFailedException('Failed to retrieve data from: ' + \
                                         endpoint)


def get_oasis_prometheus(endpoint: str, params: list, logger: logging.Logger) \
        -> dict:
    response = {}
    if len(params) == 0:
        raise NoParametersGivenException('no parameters given for ' + endpoint)

    metrics = get_prometheus(endpoint, logger)
    for family in text_string_to_metric_families(metrics):
        for sample in family.samples:
            if sample.name in params:
                if sample.name not in response:
                    if sample.labels != {}:
                        response[sample.name] = {}
                        response[sample.name][json.dumps(sample.labels)] = \
                            sample.value
                    else:
                        response[sample.name] = sample.value
                else:
                    if sample.labels != {}:
                        response[sample.name][json.dumps(sample.labels)] = \
                            sample.value
                    else:
                        response[sample.name] = sample.value + \
                                                response[sample.name]

    # Alert on the metrics that had not been retrieved from prometheus
    difference = set(params).difference(set(response))
    for i in difference:
        raise MetricNotFoundException('metric ' + i + ' not found at endpoint' \
                                                      ' ' + endpoint)

    return response


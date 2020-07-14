import React from 'react';
import Form from 'react-bootstrap/Form';
import { forbidExtraProps } from 'airbnb-prop-types';
import PropTypes from 'prop-types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle } from '@fortawesome/free-solid-svg-icons/faInfoCircle';
import { toBool } from '../../utils/string';
import { fieldEmpty } from '../../utils/configs';
import { NODE_CONFIG_TYPE } from '../../utils/constants';
import {
  createColumnFormContentWithSubmit,
  createColumnWithContent,
  createFormLabel,
} from '../../utils/forms';
import TooltipOverlay from '../overlays';
import { PingNodeButton } from '../buttons';
import { CollapsibleForm, Trigger } from './collapsible_form';
import '../../style/style.css';

function AddNodeForm({
  handleAddNode, handleChangeInNonBooleanField, handleChangeInBooleanField,
  currentNodeConfig, currentNodeIndex, validated, nodeNameValid, chainNameValid,
  nodeAPIUrlValid, nodePubKeyValid, nodeExporterUrlValid,
}) {
  const labels = [
    createFormLabel(true, '3', 'Name'),
    createFormLabel(true, '3', 'Chain'),
    createFormLabel(true, '3', 'Node API URL'),
    createFormLabel(true, '3', 'Is a validator'),
    createFormLabel(true, '3', 'Node Public Key'),
    createFormLabel(true, '3', 'Monitor node'),
    createFormLabel(true, '3', 'Use as data source'),
    createFormLabel(true, '3', 'Is archive'),
    createFormLabel(true, '3', 'Node Exporter URL'),
  ];
  const inputFields = [
    [
      createColumnWithContent(
        '5',
        <div>
          <Form.Control
            type="text"
            onChange={
              event => handleChangeInNonBooleanField(event, 'node_name')
            }
            placeholder={`node_${currentNodeIndex}`}
            value={currentNodeConfig.node_name}
            isInvalid={validated && !nodeNameValid()}
            isValid={validated && nodeNameValid()}
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          {fieldEmpty(currentNodeConfig.node_name)
            ? (
              <Form.Control.Feedback type="invalid">
                Node name cannot be empty!
              </Form.Control.Feedback>
            )
            : (
              <Form.Control.Feedback type="invalid">
                Node names must be unique
              </Form.Control.Feedback>
            )}
        </div>,
        1,
      ),
      createColumnWithContent(
        '1',
        <div className="info-tooltip-div-style">
          <TooltipOverlay
            identifier="node-name"
            placement="right"
            tooltipText="Node names must be unique"
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>,
        2,
      ),
    ],
    [
      createColumnWithContent(
        '5',
        <div>
          <Form.Control
            type="text"
            onChange={
              event => handleChangeInNonBooleanField(event, 'chain_name')
            }
            placeholder="questnet-2020-05-11-1589212800"
            value={currentNodeConfig.chain_name}
            isInvalid={validated && !chainNameValid()}
            isValid={validated && chainNameValid()}
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          <Form.Control.Feedback type="invalid">
            Chain name cannot be empty!
          </Form.Control.Feedback>
        </div>,
        3,
      ),
      createColumnWithContent(
        '1',
        <div className="info-tooltip-div-style">
          <TooltipOverlay
            identifier="chain-name"
            placement="right"
            tooltipText="Chain that the node runs on"
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>,
        4,
      ),
    ],
    [
      createColumnWithContent(
        '5',
        <div>
          <Form.Control
            type="text"
            onChange={
              event => handleChangeInNonBooleanField(event, 'node_api_url')
            }
            placeholder="http://NODE_IP:8686"
            isInvalid={validated && !nodeAPIUrlValid()}
            isValid={validated && nodeAPIUrlValid()}
            value={currentNodeConfig.node_api_url}
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          <Form.Control.Feedback type="invalid">
            Node API URL cannot be empty!
          </Form.Control.Feedback>
        </div>,
        5,
      ),
      createColumnWithContent(
        '4',
        <div>
          <PingNodeButton
            disabled={!nodeAPIUrlValid()}
            apiUrl={currentNodeConfig.node_api_url}
            nodeName={currentNodeConfig.node_name}
          />
        </div>,
        6,
      ),
    ],
    createColumnWithContent(
      '2',
      <div>
        <div style={{ display: 'inline-block' }}>
          <Form.Check
            type="checkbox"
            id="is-validator-check-box"
            aria-label="checkbox"
            className="checkbox-style"
            onChange={
              event => handleChangeInBooleanField(event, 'node_is_validator')
            }
            checked={toBool(currentNodeConfig.node_is_validator)}
          />
        </div>
        <div
          className="info-tooltip-div-style2"
          style={{ display: 'inline-block' }}
        >
          <TooltipOverlay
            identifier="is-validator"
            placement="right"
            tooltipText="Tick box if your node is a validator."
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>
      </div>,
      7,
    ),
    [
      createColumnWithContent(
        '5',
        <div>
          <Form.Control
            type="text"
            disabled={!toBool(currentNodeConfig.node_is_validator)}
            onChange={
              event => handleChangeInNonBooleanField(
                event, 'node_public_key',
              )
            }
            placeholder="wmWxzHKDJWJi0QkYqoZfRqFby+duWYUjh0CFWdj2Q40="
            value={currentNodeConfig.node_public_key}
            // Only show feedback in the case of validators
            isInvalid={validated && !nodePubKeyValid()
            && toBool(currentNodeConfig.node_is_validator)}
            isValid={validated && nodePubKeyValid()
            && toBool(currentNodeConfig.node_is_validator)}
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          <Form.Control.Feedback type="invalid">
            Node Public Key must be non-empty for validators!
          </Form.Control.Feedback>
        </div>,
        8,
      ),
      createColumnWithContent(
        '1',
        <div className="info-tooltip-div-style">
          <TooltipOverlay
            identifier="node_public_key"
            placement="right"
            tooltipText="Only for validators."
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>,
        9,
      ),
    ],
    createColumnWithContent(
      '2',
      <div>
        <div style={{ display: 'inline-block' }}>
          <Form.Check
            type="checkbox"
            id="monitor-node-check-box"
            aria-label="checkbox"
            className="checkbox-style"
            onChange={
              event => handleChangeInBooleanField(event, 'monitor_node')
            }
            checked={toBool(currentNodeConfig.monitor_node)}
          />
        </div>
        <div
          className="info-tooltip-div-style2"
          style={{ display: 'inline-block' }}
        >
          <TooltipOverlay
            identifier="monitor-node"
            placement="right"
            tooltipText="Tick if you would like your node to be node monitored."
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>
      </div>,
      10,
    ),
    createColumnWithContent(
      '2',
      <div>
        <div style={{ display: 'inline-block' }}>
          <Form.Check
            type="checkbox"
            id="data-source-check-box"
            aria-label="checkbox"
            className="checkbox-style"
            onChange={
              event => handleChangeInBooleanField(event, 'use_as_data_source')
            }
            checked={toBool(currentNodeConfig.use_as_data_source)}
          />
        </div>
        <div
          className="info-tooltip-div-style2"
          style={{ display: 'inline-block' }}
        >
          <TooltipOverlay
            identifier="data-source"
            placement="right"
            tooltipText={'Tick if you would like your node to be used as data '
          + 'source for indirect monitoring.'}
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>
      </div>,
      11,
    ),
    createColumnWithContent(
      '2',
      <div>
        <div style={{ display: 'inline-block' }}>
          <Form.Check
            type="checkbox"
            id="is-archive-check-box"
            aria-label="checkbox"
            className="checkbox-style"
            disabled={!toBool(currentNodeConfig.use_as_data_source)}
            onChange={
              event => handleChangeInBooleanField(event, 'is_archive_node')
            }
            checked={toBool(currentNodeConfig.is_archive_node)}
          />
        </div>
        <div
          className="info-tooltip-div-style2"
          style={{ display: 'inline-block' }}
        >
          <TooltipOverlay
            identifier="is-archive"
            placement="right"
            tooltipText={'Tick if your node is an archive node and you would '
            + 'like it to be used as a data source for archive monitoring. '
            + 'Available only if the \'Use as data source\' field is ticked. '}
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>
      </div>,
      12,
    ),
    [
      createColumnWithContent(
        '5',
        <div>
          <Form.Control
            type="text"
            onChange={
              event => handleChangeInNonBooleanField(event, 'node_exporter_url')
            }
            placeholder="http://111.02.32.132:9100/metrics"
            value={currentNodeConfig.node_exporter_url}
            isInvalid={validated && !nodeExporterUrlValid()}
            isValid={validated && nodeExporterUrlValid()}
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
        </div>,
        13,
      ),
      createColumnWithContent(
        '1',
        <div className="info-tooltip-div-style">
          <TooltipOverlay
            identifier="node_exporter_url"
            placement="right"
            tooltipText="This will be used to monitor the system metrics."
            component={<FontAwesomeIcon icon={faInfoCircle} />}
          />
        </div>,
        14,
      ),
    ],
  ];
  return (
    <div className="div-style">
      <CollapsibleForm
        trigger={(<Trigger name="Node" />)}
        triggerClassName="collapsible-style"
        triggerOpenedClassName="collapsible-style"
        open
        content={(
          <div>
            <Form.Text className="text-muted info-div-style">
              You may include nodes from multiple Oasis chains in any order,
              PANIC will group them automatically. Please make sure that the API
              Server is setup and running at the provided IP with
              <strong> ALL</strong>
              {' '}
              desired nodes before proceeding further. Also, please first set-up
              PANIC using the Settings-&gt;Main page before proceeding any
              further, otherwise, this setup page would not know where the API
              is running.
            </Form.Text>
            {createColumnFormContentWithSubmit(
              labels, inputFields, handleAddNode, 'Add Node',
            )}
          </div>
        )}
      />
    </div>
  );
}

AddNodeForm.propTypes = forbidExtraProps({
  currentNodeConfig: NODE_CONFIG_TYPE.isRequired,
  handleChangeInNonBooleanField: PropTypes.func.isRequired,
  handleChangeInBooleanField: PropTypes.func.isRequired,
  handleAddNode: PropTypes.func.isRequired,
  currentNodeIndex: PropTypes.number.isRequired,
  validated: PropTypes.bool.isRequired,
  nodeNameValid: PropTypes.func.isRequired,
  chainNameValid: PropTypes.func.isRequired,
  nodeAPIUrlValid: PropTypes.func.isRequired,
  nodePubKeyValid: PropTypes.func.isRequired,
  nodeExporterUrlValid: PropTypes.func.isRequired,
});

export default AddNodeForm;

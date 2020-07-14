# Change Log

## Unreleased

### Improvements
* (UI)
    * (Authentication) Session based authentication is now used to secure access to the UI. The user must define a username and password by running the `run_ui_setup.py` script.
    * (Dashboard) The data cards now have a fixed height and are placed on the dashboard using `react-bootstrap`'s grid system. This avoids having messy data cards, and adds more structure to the layout of the dashboard.
    * (System Monitoring) A System overview section which contains system badges that signifying the state of the system running your node with 3 colours Green(Safe)|Yellow(Warning)|Red(Danger). A More details section is also added to show users extra details about the monitored systems such as : ( Process CPU Seconds Total, Process Memory Usage, Virtual Memory Usage, Open File Descriptors, System CPU Usage, System RAM Usage, System Storage Usage). The system overview section is shown per node if the node has `node_exporter_url` not blank but with a working Node Exporter Url.
    * (HTTPS) The UI back-end server is now an HTTPS server. The user must put his own SSL certificate signed by a certificate authority in the `panic_oasis/src/web/ui/certificates` folder for maximum security. For convenience, a dummy certificate and key are provided. Note, the UI server does not start without these files.
* (alerter) Whenever a validator node monitor loses connection with the API server for 15 seconds, a critical alert is sent to the operator, informing them that the monitor cannot retrieve validator data for monitoring.
* (System Monitoring Alerter) System Monitoring has been added to the alerter that will monitor the systems which are running the nodes through the `node_exporter_url` field inside the `user_config_nodes.ini` file. The alerter will alert each metric based on two types of thresholds depending if the node running on the system is a full node or a validator. The metrics which will be alerted on are: Process Memory Usage, Open File Descriptors, System CPU Usage, System RAM Usage and System Storage Usage. The metrics which will be retrieved but not alerted on are: Process CPU Seconds Total and Virtual Memory Usage. The metrics as well as thresholds are percentaged based to make it easier for the user to configure e.g If a System CPU Usage has gone up to 60% and the safe boundary threshold is 40% a user will receive a warning alert.
* (setup) The CLI setup no longer forces nodes and repos to be accessible for them to be added to the configs. Setup has also been modified to cater for the `node_exporter_url` field.

### Bug Fixes

* (UI Dashboard) The columns of the `Monitors Status` table were fixed to a minimum of `200px` in width. This allows for better visualisation on mobile devices.
* (UI Settings Pages) The `Save Config` button in the `Nodes` and `Settings` pages no longer disappears when the respective configs are empty.
* (alerter)
    * A monitor no longer fails if a function from the Oasis API Server fails.
    * A node that is removed from the API server is no longer declared as down. Now, the user is specifically informed about this scenario via a critical/warning alert if the node is a validator/full-node respectively. The user is then informed via an info alert whenever the operator adds the node back to the API server.
    * PANIC no longer crashes if one of the nodes/repos is inaccessible during start-up. In this version, the monitor belonging to the inaccessible node/repo only does not start.
* (UI twilio) Fixed Twilio error not being reported when making a test call with an incorrectly formatted AccountSID or Auth Token.

### Other

* (Security Vulnerabilities)
    * Updated `package-lock.json` to resolve the `Denial of Service` vulnerability issue in `react-scripts`.
    * Updated `package-lock.json` to resolve the `Prototype pollution` vulnerability issue in `react-scripts`.
* Better file/folder layout and decomposition of components.
* The `run_setup.py` file was renamed to `run_alerter_setup.py`, as a new setup script named `run_ui_setup.py` was added for the UI.
* A new config file was added for the UI named `user_config_ui.ini`, and can be located in the `panic_oasis/config` folder.
* The `run_util_validate_configs.py` now also validates the `user_config_ui.ini` config.
* Added util `run_util_change_ui_auth_pass.py` to change the UI authentication password.

## 1.0.1

Released on 19th June 2020

Small updates to fix breaking changes with Oasis v20.8 release

## 1.0.0

Released on 13th May 2020

This release of PANIC for Oasis satisfies Milestone 1 of the Oasis Labs grant.

Apart from the tool itself, it includes an API server for Oasis nodes (now found [here](https://github.com/simplyvc/oasis_api_server)) and testing reports are also included.

### Added

* First version of PANIC for Oasis by Simply VC

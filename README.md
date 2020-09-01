# PANIC for Oasis

<img src="doc/images/IMG_PANIC.png" alt="PANIC Oasis logo" />

PANIC for [Oasis](https://oasisprotocol.org/) is a lightweight yet powerful open source monitoring and alerting solution for Oasis nodes by [Simply VC](https://simply-vc.com.mt/). The tool was built with user friendliness in mind, without excluding cool and useful features like phone calls for critical alerts and Telegram commands for increased control over your alerter.

The alerter's focus on a modular design means that it is beginner friendly but also developer friendly. It allows the user to decide which components of the alerter to set up while making it easy for developers to add new features. PANIC also offers two levels of configurability, _user_ and _internal_, allowing more experienced users to fine-tune the alerter to their preference.

We are sure that PANIC will be beneficial for node operators in the Oasis community and we look forward for [feedback](https://forms.gle/6HDfpmxRmpSVca7HA). Feel free to read on if you are interested in the design of the alerter, if you wish to try it out, or if you would like to support and contribute to this open source project.

## Design and Features

To be able to monitor and alert, PANIC was designed to retrieve data from Oasis nodes using a custom-built [Oasis API Server](https://github.com/SimplyVC/oasis_api_server). The API Server is an intermediate component which interacts with the Oasis nodes via the [oasis-core](https://github.com/oasislabs/oasis-core). For more details on the API Server please refer to the [Oasis API Server repository](https://github.com/SimplyVC/oasis_api_server). If you want to dive into the design and feature set of PANIC [click here](doc/DESIGN_AND_FEATURES.md).

## Installation Guide

We will guide you through the steps required to get PANIC up and running. We recommend that PANIC is installed on a Linux system. This installation guide will use Docker. If you do not want to install PANIC using docker then then follow [this guide](doc/INSTALL_AND_RUN.md).

### Requirements

- **Required**: The [Oasis API Server](https://github.com/SimplyVC/oasis_api_server) installed and running on each machine that you will monitor.
- **Optional**: [Node Exporter](doc/INSTALL_NODE_EXPORTER.md), this will be used to monitor the systems on which nodes the are running. It should be installed on each machine that you want to monitor.
- **Optional**: Telegram account and bots, for Telegram alerts and commands. [Click here](INSTALL_TELEGRAM.md) if you want to set it up.
- **Optional**: Twilio account, for highly effective phone call alerts. [Click here](INSTALL_TWILIO.md) if you want to set it up.
- **Required**: This installation guide uses Docker and Docker Compose to run PANIC, these will need to be installed.

### Installation

#### Docker and Docker Compose Installation

First, install Docker and Docker Compose by running these commands on your terminal.

```bash
# Install docker and docker-compose
curl -sSL https://get.docker.com/ | sh
sudo apt install docker-compose -y

# Confirm that installation successful
docker --version
docker-compose --version
```
These should give you the current versions of the softwares that have been installed.

#### Python Installation


```bash
# Install Python and Pipenv
sudo apt-get update
sudo apt-get install python3.6 -y
sudo apt-get install python3-pip -y
sudo pip3 install pipenv

# Confirm that installation successful
python --version
```

This should give you the current version of python installed, if the installation was successful.

#### Configuration Setup

```bash
# Clone the panic repositry and navigate into it
git clone https://github.com/SimplyVC/panic_oasis
cd panic_oasis
```

You can use the programmatic setup process which is started up by running the following in the project directory:

```bash
pipenv sync                            
pipenv run python run_alerter_setup.py
```

Once the PANIC configuration is completed, the user will need to configure the UI, by running the command below.

```bash
pipenv run python run_ui_setup.py
```

**Authentication Note:** If you are running PANIC through Docker and authentication is not set for Mongo and Redis then it will default to the authentication details found in the `.env` file.

#### Running PANIC

Once you have everything setup, you can start PANIC by running the below command:

```bash
docker-compose up -d --build
```

Congratulations you should have PANIC up and running!

## Support and Contribution

On top of the additional work that we will put in ourselves to improve and maintain the tool, any support from the community through development will be greatly appreciated. 

## Who We Are

Simply VC runs highly reliable and secure infrastructure in our own datacentre in Malta, built with the aim of supporting the growth of the blockchain ecosystem. Read more about us on our website and Twitter:

- Simply VC website: <https://simply-vc.com.mt/>
- Simply VC Twitter: <https://twitter.com/Simply_VC>

---

# PANIC for Oasis

<img src="doc/images/IMG_PANIC.png" alt="PANIC Oasis logo" />

PANIC for [Oasis](https://oasisprotocol.org/) is a lightweight yet powerful open source monitoring and alerting solution for Oasis nodes by [Simply VC](https://simply-vc.com.mt/). The tool was built with user friendliness in mind, without excluding cool and useful features like phone calls for critical alerts and Telegram commands for increased control over your alerter.

The alerter's focus on a modular design means that it is beginner friendly but also developer friendly. It allows the user to decide which components of the alerter to set up while making it easy for developers to add new features. PANIC also offers two levels of configurability, _user_ and _internal_, allowing more experienced users to fine-tune the alerter to their preference.

We are sure that PANIC will be beneficial for node operators in the Oasis community and we look forward for [feedback](https://forms.gle/6HDfpmxRmpSVca7HA). Feel free to read on if you are interested in the design of the alerter, if you wish to try it out, or if you would like to support and contribute to this open source project.

## Design and Features

To be able to monitor and alert, PANIC was designed to retrieve data from Oasis nodes using a custom-built [Oasis API Server](https://github.com/SimplyVC/oasis_api_server). The API Server is an intermediate component which interacts with the Oasis nodes via the [oasis-core](https://github.com/oasislabs/oasis-core). For more details on the API Server please refer to the [Oasis API Server repository](https://github.com/SimplyVC/oasis_api_server). If you want to dive into the design and feature set of PANIC [click here](doc/DESIGN_AND_FEATURES.md).

## Ready, Set, Alert!

PANIC is highly dependent on the [Oasis API Server](https://github.com/SimplyVC/oasis_api_server) for correct execution. Therefore, if you are ready to try out PANIC on your Oasis nodes, you should first setup and run the API Server on each of your machines that are running the nodes, using the guides found inside the [Oasis API Server repository](https://github.com/SimplyVC/oasis_api_server). After the API Server is successfully running, you should set up and run the alerter using [this guide](doc/INSTALL_AND_RUN.md).

## Support and Contribution

On top of the additional work that we will put in ourselves to improve and maintain the tool, any support from the community through development will be greatly appreciated. 

## Who We Are

Simply VC runs highly reliable and secure infrastructure in our own datacentre in Malta, built with the aim of supporting the growth of the blockchain ecosystem. Read more about us on our website and Twitter:

- Simply VC website: <https://simply-vc.com.mt/>
- Simply VC Twitter: <https://twitter.com/Simply_VC>

---

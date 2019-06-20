<!-- PROJECT SHIELDS -->

<h2 align="center">
  <br/>
  <a href='https://raidex.io/'><img 
      width='600px' 
      alt='' 
      src="https://user-images.githubusercontent.com/35398162/59664605-a7aecb00-91b1-11e9-9d61-44adaf4db0a2.jpeg" /></a>
  <br/>
   raidEX Proof of Concept
  <br/>
</h2>

<h4 align="center">
   POC for a decentralized exchange built on Raiden state channel technology
</h4>

<p align="center">
  <a href="#getting-started">Getting Started</a> ∙
  <a href='#contact'>Contact</a>
</p>

<p align="center">
  <a href="https://gitter.im/raiden-network/raiden">
    <img src="https://badges.gitter.im/gitterHQ/gitter.png" alt="Gitter Raiden Badge">
  </a>
</p>

> **INFO** The current raidEX version is a work in progress proof-of-concept to show how a DEX could be built on top of Raiden. 

## Fixing the custodian issue

While there are already decentralized exchanges, they are built on the blockchain and inherit the performance restrictions of the global consensus systems, i.e. especially latency and limited transaction throughput. This results in a low liquidity for these exchanges. 

## High throughput & low latency

The mentioned performance restrictions are overcome by off-chain state technology, i.e. the Raiden Network for Ethereum. As raidEX is based on the Ethereum platform and the Raiden Network, it is fully interoperable and leverages synergies with tokens and apps in the Ethereum ecosystem.

## Table of Contents


## Architecture

// TODO: Adapt

### [Raiden Light Client SDK](./raiden/README.md)

This is a standalone Typescript library which contains all the low level machinery to interact with the Ethereum blockchain and the Raiden Network.

Its target audience is blockchain and dApp developers looking into interacting with and performing payments through the Raiden Network from their apps. Targeting browsers and Node.js as initial platforms allows it to reach the majority of current and in-development dApps, as well as to work as a common language reference implementation for ports and re-implementations in other future languages and environments.

Look at the [Raiden Light Client SDK folder of this repository](./raiden/README.md) for more information.

### Raiden dApp

The Raiden dApp is the demo and first dApp user of the SDK. It's a single page application (SPA) built on top of [Vue.js](https://vuejs.org/), [vuex](https://vuex.vuejs.org) and [vuetify](https://vuetifyjs.com) as UI framework which uses Material Design as the design guideline.

### Architecture diagram

```
            +-------------------+
            |                   |
            |   Raiden dApp   |
            |                   |
            |  vue/vuex/vuetify |
            |                   |
            +---------+---------+
            |                   |
            |    Raiden SDK     |
            |                   |
            +----+----+----+----+
            |         |         |      +------------+
         +--+  redux  +  epics  +------+ Matrix.org |
         |  |         |         |      +-----+------+
         |  +---------+-----+---+            |
         |                  |          +-----+------+
+--------+-------+   +------+------+   |   Raiden   |
|  localStorage  |   |  ethers.js  |   |   Network  |
+----------------+   +------+------+   +------------+
                            |
                     +------+------+
                     |  ethereum   |
                     +-------------+
```

## Getting Started

### Learn about Raiden

If you didn't use Raiden before, you can

* Checkout the [developer portal](http://developer.raiden.network)
* Look at the [documentation](https://raiden-network.readthedocs.io/en/stable/index.html)
* Learn more by watching explanatory [videos](https://www.youtube.com/channel/UCoUP_hnjUddEvbxmtNCcApg)
* Read the blog posts on [Medium](https://medium.com/@raiden_network)

### Prerequisites

To run the code in this repository, you must
* [Install Raiden](https://raiden-network.readthedocs.io/en/stable/overview_and_guide.html)
* [Create an account, get some testnet ETH and tokens](https://github.com/raiden-network/workshop/)

## Installation

1) `git clone https://github.com/brainbot-com/raidex.git`
2) `cd raidex`
3) Install with `python setup.py develop`.

### Run

The easiest way to test the functionality of raidex is achieved with a special command that mocks all 
the networking activity as well as the commitment-service in one process.
Additionally, different types of bots can be started, to introduce some trading activity.

```
raidex --mock-networking --api --bots liquidity random manipulator
```

After installing all dependecies (see `./webui/README.md`), the WebUI can than be started
with:
 
```
cd webui
ng serve
```


## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Also have a look at the [raidEX Development Guide](./CONTRIBUTING.md) for more info.

## License

Distributed under the [MIT License](./LICENSE).

## Contact

Dev Chat: [Gitter](https://gitter.im/raiden-network/raiden)

Twitter: [@raiden_network](https://twitter.com/raiden_network)

Website: [Raiden Network](https://raiden.network/)

Mail: contact@raiden.network 

*The Raiden project is led by brainbot labs Est.*

> Disclaimer: Please note, that even though we do our best to ensure the quality and accuracy of the information provided, this publication may contain views and opinions, errors and omissions for which the content creator(s) and any represented organization cannot be held liable. The wording and concepts regarding financial terminology (e.g. “payments”, “checks”, “currency”, “transfer” [of value]) are exclusively used in an exemplary way to describe technological principles and do not necessarily conform to the real world or legal equivalents of these terms and concepts.

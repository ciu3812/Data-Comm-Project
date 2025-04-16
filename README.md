# Data Communication and Networking - Project

P2P File Sharing Software

## Authors

- Damon Gonzalez
- Caleb Underkoffler

### Description

- Up to 10 peers are searched for when the client is first started
- The user can refresh the peers which will grab another randomly selected batch up to 10
- Peer discovery has a timeout
- When a peer successfully creates a connection to a random it sends "PEER" string and expects "PEER" string back

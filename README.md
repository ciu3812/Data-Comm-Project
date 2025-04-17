# Data Communication and Networking - Project

P2P File Sharing Software

## Authors

- Damon Gonzalez
- Caleb Underkoffler

### Details

- When the client searches up to 5 peers are registered
- The user can refresh the peers which will grab another randomly selected batch up to 5
- Peer discovery has a timeout of 10 seconds
- When a peer successfully creates a connection to a random it sends "PEER" string and expects "PEER" string back
- File chunks are 4 KBs
- There is no restriction on total file size

### How To Run

Note: no packages outside of standard python modules are required to run this program

1. Run 'python3 client.py [dir]'
2. Run 'help' to see a list of valid commands
    - 'help' prints list of helpful commands to the user
    - 'exit' closes the program
    - 'discover' searches for running peers on your machine
    - 'peers' shows already discovered peers
    - 'index' gets information from a peer about what files they can transfer
    - 'request' requests a file from a peer
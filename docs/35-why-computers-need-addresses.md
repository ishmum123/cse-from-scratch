# Names That Route

## The Problem

You want to send a message to your colleague's laptop. Both machines are on the same office network. You know her name is "Alice" and her laptop is "Alice's MacBook Pro." But the network switch doesn't understand names. It only understands hardware identifiers. And when your company acquires another company and merges their network, suddenly there are two "Alice's MacBook Pro" machines. Names collide. Routing breaks.

More fundamentally: the internet connects a billion machines. If every machine broadcast to every other machine to find a destination by name, the network would be flooded with lookup traffic before any data moved. Routing requires a structured, hierarchical addressing scheme that lets intermediate devices make forwarding decisions without knowing about every machine everywhere.

Any addressing scheme must:

- Uniquely identify any machine reachable on a network
- Allow routing decisions without global knowledge (each router knows only its neighborhood)
- Scale to billions of devices
- Support hierarchical aggregation (knowing a range of addresses belongs to a region)

## What Would You Try?

Before reading on:

- If every machine had a unique random 64-bit name, how would a router decide where to forward a packet? What information would it need?
- Phone numbers are hierarchical: country code + area code + local number. What does this hierarchy enable for routing?
- What's the difference between a name (human-readable) and an address (machine-routing-friendly)?

## Failed Attempts

### Attempt 1: Broadcast to Find Destinations

When Machine A wants to reach Machine B, broadcast a "who is Machine B?" message to all machines on the network. Machine B replies. A now knows B's hardware location and sends data directly. This is how ARP (Address Resolution Protocol) works at the local network level.

ARP works fine on a local network of 50 machines — the broadcast reaches all 50, one replies. But on a network of 50,000 machines, 50,000 machines process every ARP request. At 1,000 lookups per second, the entire network bandwidth is consumed by ARP traffic before any actual data is sent. On the early ARPAnet (the internet's predecessor), broadcast-based lookup collapsed under load as the network grew past a few hundred machines. This is why internet routing is not broadcast-based: broadcasts don't scale.

### Attempt 2: Central Directory of Name→Location Mappings

A central server holds a table of all machines and their locations. Any machine that wants to send data first queries the directory: "where is Alice's MacBook Pro?" Directory replies with a location. Sender routes to that location.

This is how early networks tried to work (the HOSTS.TXT file on ARPAnet, maintained centrally at SRI). With 100 machines, the file was updated weekly and distributed manually. With 10,000 machines (early 1980s), it was updated daily and distributed automatically. With 100,000 machines, daily updates were too slow and the file too large. The central directory creates a single point of failure, a performance bottleneck (every connection requires a directory lookup), and a scaling wall (the directory grows linearly with the network). DNS replaced HOSTS.TXT by distributing the directory into a hierarchy — but the core naming problem remains.

### Attempt 3: Hardware MAC Addresses for All Routing

Every network interface card has a unique 48-bit MAC address burned in at manufacture (e.g., `AA:BB:CC:DD:EE:FF`). MAC addresses are globally unique. Route everything by MAC address.

MAC addresses are flat — there's no hierarchy. `AA:BB:CC:DD:EE:FF` gives no information about which country, network, or building the device is in. A router would need a table entry for every device on the internet — billions of entries — to route by MAC. Routing tables would require petabytes of memory. More importantly, when a laptop moves from one network to another (hotel WiFi to office WiFi), its MAC address doesn't change, but its location in the network topology does. The flat MAC address can't encode topology changes; every router on the internet would need to be updated.

## The Discovery

Broadcasts don't scale. Central directories are single points of failure and bottlenecks. Flat hardware addresses can't encode hierarchical topology.

The answer separates two things: **identity** (what a machine is) from **location** (where it is in the network). Location must be hierarchical to enable routing without global knowledge.

**IP addressing**: an IPv4 address is 32 bits, written as four decimal octets (`192.168.1.42`). The key structure: the address is split into a **network prefix** (identifies which network) and a **host part** (identifies which machine within that network). The split point is specified by a **subnet mask** or CIDR notation (`/24` means the first 24 bits are the network prefix, the last 8 bits are the host).

Why this enables routing: a router at a large ISP doesn't need to know about every machine inside a corporate network. It only needs to know "`192.168.0.0/16` is delivered to this ISP's edge router." The ISP's edge router handles internal delivery. This is **hierarchical routing**: each level of the hierarchy handles its portion of the address space, delegating the rest to the next level down. A full internet backbone router (Tier 1 ISP) holds ~900,000 prefixes — not billions of individual host addresses.

**Dynamic assignment (DHCP)**: when a laptop connects to a network, a DHCP server assigns it an IP address from the network's pool. The IP address is a *location* identifier, not a permanent identity — the same laptop gets a different IP on different networks. DNS (chapter 35's complement) maps human-readable names to current IP addresses, bridging identity and location.

## Try It

<iframe src="../assets/browser/chapter35/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter35/index.html)

Before changing anything, predict:

- In the simulation, change the subnet mask from /24 to /16. How does the range of addresses in the same network change?
- When the router receives a packet for `10.0.0.42` and its routing table has entries for `10.0.0.0/24` and `10.0.0.0/16`, which entry does it use?
- Add a new machine to the network without an IP address (no DHCP). What happens when it tries to send a packet?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter35/index.html` (shared helpers in `browser/common/sim.js`). Both panels use `nodePositions()` to place nodes in a ring and `drawNet()` to animate packet delivery. On the left (broadcast), every node lights up on each send; on the right (addressed), only the `destNode` is highlighted. The `bcastTotal` and `routeTotal` counters accumulate wasted transmissions vs. efficient direct delivery, and the "Dest node" and "Nodes" sliders update both panels live.

## When It Breaks

**IPv4 exhaustion.** 32-bit addresses allow 4.3 billion unique addresses. The internet has more than 4.3 billion connected devices. IPv4 exhaustion was declared in 2011; IANA allocated the last /8 blocks. The stopgap: NAT (Network Address Translation), where an entire private network (`192.168.0.0/16`, 65,536 addresses) shares one public IP. Behind NAT, outbound connections work (the NAT device tracks connection state and rewrites addresses); inbound connections to specific machines require explicit port forwarding. NAT breaks the end-to-end principle: every device should be directly addressable. Peer-to-peer protocols, VoIP, and gaming are harder with NAT. IPv6 (128-bit addresses, 3.4 × 10³⁸ possible addresses) was designed to fix this; adoption has reached ~40% of internet traffic as of 2024.

**BGP routing instability.** The internet's inter-domain routing protocol (BGP) propagates reachability information for ~900,000 IP prefixes. A misconfigured router can announce that it can reach everyone's prefixes (a "BGP hijack"). In 2008, Pakistan Telecom accidentally hijacked YouTube's IP block for 2 hours. BGP has no cryptographic authentication by default — anyone who can establish a BGP session can announce any prefix. RPKI (Resource Public Key Infrastructure) provides cryptographic prefix ownership verification, but adoption is incomplete.

## Transfer

- **Subnetting in cloud networking.** AWS VPCs use CIDR blocks (`10.0.0.0/16`) subdivided into subnets (`10.0.1.0/24` for the public tier, `10.0.2.0/24` for the private tier). Security groups and route tables operate on these CIDR blocks. Understanding subnetting is a prerequisite for cloud network architecture.
- **CIDR aggregation.** If an ISP owns `10.1.0.0/16` through `10.4.0.0/16`, it can announce a single aggregate prefix `10.0.0.0/14` to upstream routers instead of four separate /16 prefixes. This is called "route aggregation" or "supernetting" and is why routing tables are ~900,000 entries rather than 4 billion.
- **Link-local addresses (`169.254.x.x`).** When DHCP fails, an OS assigns itself a link-local address from `169.254.0.0/16` using APIPA. These addresses are valid only on the local link — routers don't forward them. If you've seen a `169.254.x.x` address in network diagnostics, DHCP failed.

Try these:

1. Given the IP address `172.16.5.130` and subnet mask `255.255.255.192` (`/26`), what is the network address? The broadcast address? How many host addresses are available?
2. Why does `0.0.0.0/0` (the "default route") always lose in a longest-prefix-match tie? What does it represent?
3. A /24 network has 254 usable host addresses. A /23 network has 510. A /22 has 1022. Why isn't the pattern `2^(32-prefix) - 2` explained by "minus 2"? What are those two addresses?

---

**Continue → [Why Packets Exist](36-why-packets-exist.md)**

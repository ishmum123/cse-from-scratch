# Traffic Control at Scale

## The Problem

A single web server handles 1,000 requests/second at peak load. The Black Friday traffic spike brings 10,000 requests/second. The server falls over. You add a second server, but clients' browsers have the old IP address bookmarked — they only know about server 1. Server 2 sits idle. Clients get errors.

Even without the scale problem: server 1 crashes due to a memory bug. Every user's request fails until a human notices, SSHes in, restarts the server, and updates DNS to point to the backup. That takes 10 minutes. DNS TTL means browsers cached the old address for another hour. The service is down for customers who have the stale DNS entry.

Any solution must:

- Route traffic across multiple backend servers
- Hide individual server failures from clients (automatic failover)
- Not require clients to know about backend topology
- Distribute load reasonably — not send all traffic to one server while others are idle

## What Would You Try?

Before reading on:

- If you publish two IP addresses for the same domain name, what decides which server a client connects to?
- A backend server becomes slow (not failed — just slow). How does a load balancer detect "slow" vs. "failed"?
- Client A starts a shopping session on server 1 and adds items to a cart stored in server 1's memory. Client A's next request routes to server 2. What happens to the cart?

## Failed Attempts

### Attempt 1: DNS Round-Robin

Publish multiple A records for the same domain. DNS rotates which IP is returned per query. Traffic is roughly split among the backend servers.

DNS round-robin is genuinely used but has two fundamental problems. First, DNS TTLs cache addresses for minutes to hours. When server 1 fails, clients with its cached IP continue sending requests to it for the TTL duration. The DNS update removing server 1 propagates slowly. During that window — up to hours — half of clients hit a dead server. Second, DNS has no idea how loaded each server is. If server 1 takes twice as long per request as server 2, round-robin still sends equal traffic, and server 1 becomes a bottleneck while server 2 is underutilized. DNS round-robin distributes connections, not load.

### Attempt 2: Client-Side Load Balancing

Give each client a list of all backend server addresses. The client picks one (round-robin, random, or by measuring latency). Libraries like Netflix Ribbon and gRPC's built-in load balancing use this approach.

Client-side balancing works well for service-to-service communication where both sides are controlled software. It fails for public-facing services: you don't control user browsers or mobile apps, can't push an updated server list when you add capacity, and exposing all backend IPs to clients creates security exposure. When a server is added, clients must receive the updated list — requiring either polling or a push mechanism, which is its own distributed systems problem. Client-side load balancing is the right choice *inside* a system; it's the wrong choice at the system's external boundary.

### Attempt 3: Sticky Sessions via Cookies

Add one load balancer in front of multiple backends. Assign each client to one backend server based on a cookie or the client's IP hash. The same client always hits the same server (session affinity). This solves the cart problem: the cart is on server 1 and the client always reaches server 1.

Sticky sessions concentrate traffic on servers whose assigned clients are active and leave other servers underutilized. A client on a slow server is stuck on that slow server even if others are idle. Worse: when server 1 crashes, all clients affined to server 1 lose their session state — which was the whole point of the cookie. Stickiness trades stateless scalability for stateful coupling. The real fix is to make backends stateless: store session data externally (Redis, a database), not on the server itself. Sticky sessions are a workaround for a stateful backend design, not a solution.

## The Discovery

DNS round-robin can't detect failures or account for load. Client-side balancing can't control external clients. Sticky sessions couple clients to specific backends, defeating fault tolerance.

The correct abstraction is a **load balancer** sitting between clients and backends, acting as a single logical endpoint while distributing work:

**Layer 4 (transport) load balancing**: the load balancer sees TCP connections and distributes them across backends using source IP, port, and protocol. It doesn't inspect HTTP content. Fast — operates at kernel speed using techniques like IPVS (IP Virtual Server). Used for high-throughput raw TCP traffic.

**Layer 7 (application) load balancing**: the load balancer terminates the HTTP connection, reads the request, and makes routing decisions based on URL path, headers, or content. A request to `/api/orders` routes to the orders service; `/api/users` routes to the users service. This is what nginx, HAProxy, and AWS ALB do.

**Health checks**: the load balancer probes each backend continuously (HTTP GET `/health` every 5 seconds). If a backend fails to respond within a timeout, it's marked "unhealthy" and removed from the rotation — in seconds, not hours. Health checks are what distinguish a load balancer from DNS round-robin.

**Load distribution algorithms**: round-robin (simple, fair for equal-cost requests), least connections (route to the backend with fewest active connections, good for variable-cost requests), random-two-choices (pick two backends at random, route to the less loaded — provably approaches least-connections performance with much less coordination).

The result: one IP, many backends, automatic failure detection, even load distribution. Adding a new backend: register it with the load balancer. Remove it: deregister or let health checks detect its failure.

## Try It

<iframe src="../assets/browser/chapter39/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter39/index.html)

Before changing anything, predict:

- With 3 backends and round-robin, kill one backend. How long before the load balancer stops sending traffic to it?
- Switch to "least connections" and make one backend 3× slower. Does the load balancer compensate by sending it fewer requests?
- What happens to in-flight requests on a backend that fails mid-request? Can the load balancer retry them?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter39/index.html` (shared helpers in `browser/common/sim.js`). The right panel maintains `lbServers`, an array of `{id, alive, queue}` objects. Each tick, arriving requests are spread evenly: `perServer = ceil(arrivals / aliveServers.length)`. The "Kill LB server" button marks a server's `alive` flag false; traffic redistributes automatically. `drawSingle()` shows the single server overflowing under load, while `drawLB()` shows queue depth per server — kill a server to watch the others absorb the load.

## When It Breaks

**Thundering herd on recovery.** When a backend recovers from a crash, the load balancer marks it healthy and immediately routes traffic to it at full rate. The server's caches are cold, its connection pools are empty, and it's handling full load on cold start. It immediately becomes slow, fails health checks, gets removed, recovers, and the cycle repeats. Fix: gradual traffic ramping ("slow start" for backends) — after marking healthy, send 1% of traffic, then 5%, then 25%, then 100%, allowing the backend to warm up.

**Session state and statefulness.** Once you have multiple backends, any request might hit any backend. Session state (user login, shopping cart, partial form data) stored in one backend's memory is invisible to others. This forces either sticky sessions (and the tradeoffs above), external session storage (Redis cluster, database), or stateless session tokens (JWT, signed cookies). The load balancer exposes this design constraint: it's a forcing function toward stateless backends, which are easier to scale and replace.

**SSL termination and certificate management.** Layer 7 load balancers typically terminate TLS — they hold the private key and decrypt HTTPS connections. This centralizes certificate management (one cert at the load balancer instead of N certs at N backends) but means traffic between the load balancer and backends is unencrypted inside the datacenter unless re-encryption is configured. mTLS (mutual TLS, where both sides authenticate) between load balancer and backends adds security at the cost of per-backend certificate management.

## Transfer

- **Anycast routing.** Content delivery networks (Cloudflare, AWS CloudFront) assign the same IP address to servers in dozens of cities. BGP anycast routes each client to the nearest server based on network topology. The client sends to one IP; the network routes to the closest data center. No explicit load balancer — routing itself distributes load geographically. Used for DNS (1.1.1.1, 8.8.8.8), DDoS mitigation, and CDN edge nodes.
- **Service meshes (Istio, Linkerd).** In microservice architectures, every service calls many other services. A service mesh adds a sidecar proxy (Envoy) to each service instance that handles load balancing, retries, circuit breaking, and observability. The mesh provides layer 7 load balancing between services without requiring changes to the service code.
- **Circuit breakers.** When a backend is consistently slow or failing, a circuit breaker "trips" and immediately returns errors (without attempting the backend) for a configurable period. This prevents cascading failures: a slow payments service doesn't cause the entire order service to queue up slow requests until timeouts expire. Netflix's Hystrix popularized this pattern; most service mesh implementations include it.

Try these:

1. Describe the "power of two choices" load balancing algorithm. Why does choosing the better of two random backends give near-optimal load distribution with O(1) coordination?
2. A load balancer health check polls `/health` every 10 seconds with a 3-second timeout and requires 2 consecutive failures before marking a backend unhealthy. What's the maximum time between a backend failing and traffic being redirected away from it?
3. What is a "connection draining" (or "deregistration delay") period, and why is it needed when removing a backend from rotation?

---

**Continue → [Why One Computer Isn't Enough](40-why-one-computer-isnt-enough.md)**

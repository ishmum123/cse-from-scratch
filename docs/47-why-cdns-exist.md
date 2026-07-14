# The Speed of Light Is the Bottleneck

## The Problem

Your servers are in Virginia. A user in Jakarta loads your homepage. The TCP handshake alone takes ~180ms (speed of light across the Pacific and back). HTTPS adds another round trip for TLS negotiation: ~360ms total before you've sent a byte of content. The HTML arrives, references a 500KB image — another ~180ms. Then JavaScript files, CSS. For a typical page, a user in Jakarta waits 2–3 seconds just on network round trips, before any server processing or slow connection overhead.

You can't compress the speed of light. You can move the content.

Any geographic content distribution must handle:

- Static assets (images, JS, CSS, video) that are the same for all users
- Cache consistency: when you update a file, users shouldn't see the old version
- Picking the geographically closest server for each user's request
- Distributing load across hundreds of edge locations without a central bottleneck

## What Would You Try?

Before reading on:

- Light travels roughly 200,000 km/s in fiber. Virginia to Jakarta is ~17,000 km. What's the minimum possible round-trip time — ignoring routing overhead, server processing, and congestion?
- If you cache a JavaScript file at an edge server, and you deploy a new version, how does the edge know to serve the new version?
- Your site has 500 edge servers. A user in Istanbul makes a request. How does the DNS system route them to the closest one?

## Failed Attempts

### Attempt 1: Increase Origin Server Bandwidth and Compute

Throw more capacity at the origin. More bandwidth, faster servers, more RAM.

The bottleneck isn't compute — it's propagation delay. A 10Gbps pipe to Virginia is still 180ms away from Jakarta. You can serve Jakarta's entire country simultaneously with perfect compute, and a Jakarta user still waits 180ms for the TCP handshake response. Bandwidth helps throughput (how much data per second). It does not help latency (how long the first byte takes). For interactive web pages, latency dominates user experience. This is why a CDN delivering from Singapore is a qualitative improvement even if the edge server has a slower connection than the origin.

### Attempt 2: Geographically Distributed Origin Servers

Run full application servers in each region: Virginia for the Americas, Singapore for Asia-Pacific, Frankfurt for Europe. Replicate the database to all regions. Each user hits their regional origin.

This works for dynamic content but is extremely expensive for static assets. You now maintain full infrastructure globally, and database replication adds consistency challenges (chapter 44). The replication lag means users in different regions might see different dynamic content. Most importantly, static assets — which are 80–90% of page bytes — don't *need* origin logic; they're the same bytes for everyone. Running full application servers in every region to serve files that never change is massive overengineering.

### Attempt 3: A Single Cache Server per Region, Self-Managed

Put one server in each region. Pre-populate it with all your static assets. When you deploy new assets, update all regional servers.

Deployment becomes an O(regions) operation. Miss one region and it serves stale files. The regional servers have no automatic invalidation — they're manually managed. As the asset catalog grows, keeping all edge servers in sync requires complex orchestration. And one server per region is still a single point of failure for that region. If your Singapore server goes down, all of Asia-Pacific goes back to the origin. Pre-population also means you're paying for storage and bandwidth in every region for assets that users in that region may never request.

## The Discovery

More origin capacity doesn't fix propagation delay. Full regional origins are overengineered for static content. Manually managed regional servers are brittle and don't scale.

The insight: static assets don't *need* to be pulled from origin until someone in that region actually requests them. Cache on demand, close to users, with automatic invalidation tied to the asset URL.

A **CDN** (Content Delivery Network) is a globally distributed network of edge servers that cache content close to users. The mechanism: your DNS returns the IP of the nearest edge server (using Anycast or GeoDNS). The edge checks its cache. Miss → fetches from origin, caches for the asset's TTL. Subsequent requests from the same region hit the edge — no origin round trip. Cache invalidation is URL-based: to update a file, change its URL (add a version hash like `app-v2.3.min.js`). Old URLs expire naturally; new URLs are fresh.

URL versioning is the key correctness insight: you never invalidate, you never corrupt, and you never have stale-vs-new confusion. The old URL serves the old file until its TTL expires (or you purge it). The new URL is always a cache miss until the first request in each region — after which it's cached correctly. Deploys become safe: you push new assets with new names, then update HTML to reference them. Roll back is trivial (reference old names again).

## Try It

<iframe src="../assets/browser/chapter47/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter47/index.html)

Before changing anything, predict:

- A user in Sydney requests a file for the first time. The Sydney edge fetches from Virginia origin: what's the total latency? What's the latency for the second user in Sydney?
- Increase the number of unique assets. At what point does the edge cache fill up? What gets evicted?
- Change the TTL from 1 hour to 1 second. How does edge hit rate change? What happens to origin load?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter47/index.html` (shared helpers in `browser/common/sim.js`). Look for the `edgeRequest()` function: cache lookup, origin fetch on miss, TTL management. The geographic routing logic (which edge server a request reaches) and the hit rate tracker show the latency savings numerically.

## When It Breaks

**Cache poisoning.** If an edge server caches a malicious or corrupted response, it serves that corruption to every user in its region until TTL expiry. An attacker who can influence what the edge caches (e.g., via a poisoned DNS response or a cache-key confusion attack) serves malicious content at CDN scale. CDNs must validate origin responses and use strict cache-key normalization.

**CDN misconfigurations serve private data publicly.** When a CDN caches a page that includes user-specific content (because Cache-Control headers were set incorrectly or vary headers were missing), every user who requests that URL gets the first user's private data. Optus in 2023 had this failure: cached API responses included PII for the wrong users. CDNs require careful Vary header configuration and often explicit "private" or "no-store" directives on authenticated content.

## Transfer

- **Netflix Open Connect** is a private CDN: Netflix places its own appliances in ISP data centers to cache video content. A video stored in a local cache skips the entire public internet — dramatically reducing both latency and Netflix's transit costs.
- **Browser caches** are a CDN with one edge node per user device. HTTP Cache-Control, ETag, and If-None-Match implement the same TTL and conditional validation patterns at the browser level.
- **Game patch distribution** (Steam, PlayStation Network) uses CDN-like regional caches to distribute large game updates. Without geographic distribution, peak concurrent downloads (a major game update) would saturate a central origin's bandwidth.

Try these:

1. You have 200 assets totaling 1GB. A CDN edge has 500MB of cache. Your 20 most popular assets are 300MB total. What cache size is "enough" to serve 95% of requests from edge? How does this relate to the 80/20 rule?
2. A CDN has 150 edge locations. You deploy a new version of your homepage JavaScript. In the worst case, how many origin requests will occur as the new file propagates? How does URL versioning change this?
3. Compare CDN TTL of 1 hour vs 1 year for a CSS file. For each: what's the worst-case user sees a stale version after a deploy? What's the trade-off?

---

**Continue → [Why Queues Exist](48-why-queues-exist.md)**

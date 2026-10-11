# Joshua Isika

Backend engineer based in Nairobi, Kenya. I build C#/.NET services on PostgreSQL. Professionally, I have worked on ERP systems, business process automation, and industrial IoT and embedded systems, including MQTT telemetry.

My focus is correctness under concurrency: what happens when two requests, workers or retries hit the same data at the same time.

Portfolio: [joshuaisikah.github.io](https://joshuaisikah.github.io)

## Practice projects: concurrency and reliability in .NET

Alongside my professional work, I build focused projects that target the hard parts of backend systems. Each has written acceptance criteria and automated tests, plus a README explaining the design decisions and trade-offs.

| Project | Focus |
|---|---|
| [JobRunner](https://github.com/Joshuaisikah/JobRunner) | Multi-worker job queue on PostgreSQL: `FOR UPDATE SKIP LOCKED` claiming, fencing tokens, stale-claim recovery, retries with backoff. Verified with 3 workers × 200 jobs, each executed exactly once, 20/20 runs |
| [Notifications](https://github.com/Joshuaisikah/Notifications) | Transactional outbox with at-least-once delivery, retries and capped exponential backoff |
| [TicketInventory](https://github.com/Joshuaisikah/TicketInventory) | Preventing overselling under concurrent purchases: optimistic concurrency and atomic updates |
| [Image-Processing](https://github.com/Joshuaisikah/Image-Processing) | Background processing with `BackgroundService` and `Channel<T>`, `202 Accepted` and startup recovery |
| [Expense Tracker](https://github.com/Joshuaisikah/02-expense-tracker) | REST API with relationships, DTOs, filtering and pagination |
| [URL Shortener](https://github.com/Joshuaisikah/url-shortener-dotnet) | REST API with EF Core, migrations, unique constraints and exact click counting |

## Open source

- **[MQTTnet](https://github.com/dotnet/MQTTnet)** (C#): fix for server subscriber-session tracking ([#2279](https://github.com/dotnet/MQTTnet/pull/2279))
- **[rustls](https://github.com/rustls/rustls)** (Rust): removed stale `std` feature references ([#3180](https://github.com/rustls/rustls/pull/3180), merged)
- **[rust-analyzer](https://github.com/rust-lang/rust-analyzer)** (Rust): config error reporting for item-scoped postfix snippets ([#22937](https://github.com/rust-lang/rust-analyzer/pull/22937), merged)

## Skills

- **Backend:** C#, ASP.NET Core, EF Core, PostgreSQL, Docker, xUnit
- **Systems and IoT:** Rust, C/C++, MQTT, embedded systems
- **Also:** Python, TypeScript/JavaScript, Java, PHP

## Contact

Open to backend engineering roles, in Nairobi or remote: [joshuaiska@gmail.com](mailto:joshuaiska@gmail.com)

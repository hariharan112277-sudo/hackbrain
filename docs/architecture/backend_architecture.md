# Clean Architecture & Enterprise SOLID Specification

## 1. Architectural Style: Clean Layered Microservice-Ready Architecture
We enforce a strict dependency rule: **Inner circles contain business policies, outer circles contain mechanisms.** Dependencies point only inward.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Outer Layer: Infrastructure, FastAPI Routes, Middleware, Databases     │
│   ┌────────────────────────────────────────────────────────────────────┐
│   │ Interface Adapters: Controllers, Repositories, Presenters          │
│   │   ┌────────────────────────────────────────────────────────────────┐
│   │   │ Application Business Rules: Use Cases / Service Components     │
│   │   │   ┌────────────────────────────────────────────────────────────┐
│   │   │   │ Core Domain: Entities, Invariant Business Models           │
│   │   │   └────────────────────────────────────────────────────────────┘
│   │   └────────────────────────────────────────────────────────────────┘
│   └────────────────────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────────┘
```

## 2. SOLID Design Blueprint
- **Single Responsibility Principle (SRP):** Routers only extract inputs; Services execute orchestration workflows; Repositories perform I/O operations.
- **Open/Closed Principle (OCP):** New operational metrics extend Abstract Base Classes without altering foundational evaluation code blocks.
- **Liskov Substitution Principle (LSP):** Mock repositories mirror actual production PostgreSQL instances via rigorous static type conformance checking.
- **Interface Segregation Principle (ISP):** Client-specific API consumers only see structural interfaces dedicated strictly to their scopes.
- **Dependency Inversion Principle (DIP):** Top-level components access low-level frameworks strictly through abstract interfaces resolved at runtime via FastAPI's Dependency Injection.

## 3. Microservice Extraction Roadmap
To ensure future modular extraction to standalone microservices, bounded contexts are explicitly split by module directories inside app/core/modules/. Communication passes through abstract service boundaries, enabling simple replacement with gRPC or HTTP network interfaces if scaled horizontally into dedicated containers.
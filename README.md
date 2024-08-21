# void_forms

## Overview

A simple micro service that handles form submissions. Built in rust.

## Reasoning

1. **Performant**: Building in Rust allows for great performance, scalability, and reliability.
2. **Simple**: The service is simple and easy to use.
3. **Modular**: This service can be used as a standalone drop in place solution for handling form submissions, on any platform.

## Usage

### Dependencies

- Rust
- Cargo
- Docker
- Docker Compose

### Running

Spin up the database

```bash
docker-compose up -d
```

Run the service

```bash
cargo run
```
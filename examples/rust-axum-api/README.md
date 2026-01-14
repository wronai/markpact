# Rust Axum API Example

Minimalne REST API w Rust (Axum) uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/rust-axum-api/README.md
```

---

```markpact:file toml path=Cargo.toml
[package]
name = "markpact_axum_example"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```markpact:file rust path=src/main.rs
use axum::{
    extract::Json,
    http::StatusCode,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

#[derive(Serialize)]
struct Health {
    status: &'static str,
}

#[derive(Deserialize)]
struct EchoReq {
    message: String,
}

#[derive(Serialize)]
struct EchoRes {
    message: String,
}

async fn health() -> Json<Health> {
    Json(Health { status: "ok" })
}

async fn echo(Json(payload): Json<EchoReq>) -> (StatusCode, Json<EchoRes>) {
    (StatusCode::OK, Json(EchoRes { message: payload.message }))
}

#[tokio::main]
async fn main() {
    let port: u16 = std::env::var("MARKPACT_PORT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8081);

    let app = Router::new()
        .route("/health", get(health))
        .route("/echo", post(echo));

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

```markpact:run shell
cargo run
```

```markpact:test http
GET /health EXPECT 200
POST /echo BODY {"message":"hello"} EXPECT 200
```

use dotenv::dotenv;
use axum::{
    extract::State,
    routing::get,
    Router,
};
mod router;
mod form;
mod db;
use std::env;
use std::sync::Arc;

struct AppState {
    db_client: Arc<tokio_postgres::Client>,
}

#[tokio::main]
async fn main() {
    dotenv().ok();

    // Load the database client
    let db_client = db::connect().await.unwrap();

    let port = env::var("PORT").expect("PORT must be set");
    let port = port.parse::<u16>().expect("PORT must be a number");

    // Create the app state and then the app routes
    let shared_state = Arc::new(AppState {
        db_client: Arc::new(db_client),
    });   
    let app = router::init(shared_state); 

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port)).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

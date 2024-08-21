mod db;
mod routes;
mod logic;

use dotenv::dotenv;
use std::env;
use std::sync::Arc;
use std::panic;

use crate::routes::init_routes;

struct AppState {
    db_client: Arc<tokio_postgres::Client>,
}


#[tokio::main]
async fn main() {
    dotenv().ok();

     // Set up global panic hook to handle panics and return 500 responses
    panic::set_hook(Box::new(|panic_info| {
        eprintln!("Unhandled panic: {:?}", panic_info);
    }));

    // Load the database client
    let db_client = db::connect().await.unwrap();

    let port = env::var("PORT").expect("PORT must be set");
    let port = port.parse::<u16>().expect("PORT must be a number");

    // Create the app state and then the app routes
    let shared_state = Arc::new(AppState {
        db_client: Arc::new(db_client),
    });   
    // let app = router::init(shared_state); 
    let app = init_routes(shared_state);

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port)).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

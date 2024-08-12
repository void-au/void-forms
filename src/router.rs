use axum::{
    extract::State,
    routing::get,
    Router,
};
use crate::form::{
    get_forms,
    get_form_by_id,
};
use crate::AppState;
use std::sync::Arc;


// Creates all the routes
pub fn init(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/", get(|| async { "Hello, World!" }))
        .route("/forms/:id", get(get_form_by_id))
        .route("/forms", get(get_forms))
        .with_state(state);
}
pub mod form;
pub mod user;
pub mod auth;

use std::sync::Arc;
use crate::AppState;
use axum::Router;
// use crate::routes::auth;
// use crate::routes::form;
// use crate::routes::user;

pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .nest("/auth", auth::init_routes(state.clone()))
        .nest("/forms", form::init_routes(state.clone()))
        .nest("/users", user::init_routes(state.clone()));
}
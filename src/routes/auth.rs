use std::sync::Arc;
use axum::{
    Router,
    routing::post,
};

use crate::AppState;
use crate::logic::user;

// Create routes for auth
pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/login", 
            post(user::login_user_handler))
        // .route("/register", 
        //     post(register_handler))
        .with_state(state);
}
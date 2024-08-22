pub mod form;
pub mod user;

use std::sync::Arc;

use crate::AppState;
use crate::routes::form::init_form_routes;
use crate::routes::user::init_user_routes;
use axum::{
    Router,
};

pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .nest("/forms", init_form_routes(state.clone()))
        .nest("/users", init_user_routes(state.clone()));
}
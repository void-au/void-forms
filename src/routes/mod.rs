pub mod form;
pub mod user;

use std::sync::Arc;

use crate::AppState;
use crate::routes::form::init_form_routes;
use crate::routes::user::init_user_routes;
use axum::{
    body::Body,
    http::{Request, Response},
    middleware::Next,
    response::IntoResponse,
    Router,
};
use std::convert::Infallible;
use std::future::Future;




pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .nest("/forms", init_form_routes(state.clone()))
        .nest("/users", init_user_routes(state.clone()));
}
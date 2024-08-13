pub mod form;

use axum::Router;
use std::sync::Arc;

use crate::AppState;
use crate::routes::form::init_form_routes;

pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .nest("/forms", init_form_routes(state));
}
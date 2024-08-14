use std::sync::Arc;
use axum::{
    routing::get,
    Router,
};

use crate::AppState;
use crate::logic::form::{
    get_form_by_id,
    get_forms,
    create_new_form,
    update_form,
    remove_form
};

// Creates all the routes
pub fn init_form_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/:id", get(get_form_by_id).put(update_form).delete(remove_form))
        .route("/", get(get_forms).post(create_new_form))
        .with_state(state);
}
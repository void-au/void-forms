use std::sync::Arc;
use axum::{
    routing::get,
    Router,
};

use crate::AppState;
use crate::logic::form;

// Creates all the routes
pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/:id", 
            get(form::get_form_via_id_handler)
            .put(form::update_form_handler)
            .delete(form::delete_form_handler))
        .route("/", 
            get(form::get_all_forms_handler)
            .post(form::insert_form_handler))
        .with_state(state);
}
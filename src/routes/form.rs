use std::sync::Arc;
use axum::{
    routing::get,
    Router,
};

use crate::AppState;
use crate::logic::form::{
    get_all_forms_handler,
    get_form_via_id_handler,
    insert_form_handler,
    update_form_handler,
    delete_form_handler
};

// Creates all the routes
pub fn init_form_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/:id", 
            get(get_form_via_id_handler)
            .put(update_form_handler)
            .delete(delete_form_handler))
        .route("/", 
            get(get_all_forms_handler)
            .post(insert_form_handler))
        .with_state(state);
}
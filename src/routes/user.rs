use std::sync::Arc;
use axum::{
    routing::get,
    Router,
};

use crate::AppState;
use crate::logic::user::{
    get_all_users_handler,
    get_user_via_id_handler,
    insert_user_handler,
    update_user_handler,
    delete_user_handler
};

pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/:id", 
            get(get_user_via_id_handler)
            .put(update_user_handler)
            .delete(delete_user_handler))
        .route("/", 
            get(get_all_users_handler)
            .post(insert_user_handler))
        .with_state(state);
}
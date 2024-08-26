use std::sync::Arc;
use axum::{
    routing::get,
    Router,
};

use crate::AppState;
use crate::logic::user::{
    get_user_via_id_handler,
    update_user_handler,
    delete_user_handler
};
use crate::mw::auth::{
    jwt_auth
};


pub fn init_routes(state: Arc<AppState>) -> Router {
    return Router::new()
        .route("/:id", 
            get(get_user_via_id_handler)
            .put(update_user_handler)
            .delete(delete_user_handler))
        .with_state(state)
        .layer(axum::middleware::from_fn(jwt_auth));
}
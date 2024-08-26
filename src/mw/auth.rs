use axum::{
    http,
    response::Response,
    middleware::Next,
    Router,
    extract::Request,
};

pub async fn jwt_auth(mut req: Request, next: Next) -> Response {
    // Log the request Authorization header
    let auth_header = req.headers().get(http::header::AUTHORIZATION);
    if let Some(auth_header) = auth_header {
        // Check if the Authorization header contains Bearer at the start
        let auth_header = auth_header.to_str().unwrap();
        if !auth_header.starts_with("Bearer") {
            return http::Response::builder()
                .status(http::StatusCode::UNAUTHORIZED)
                .body("Unauthorized".into())
                .unwrap()
        }

        // Split the string up from Bearer to get just the JWT
        let jwt = auth_header.split("Bearer").collect::<Vec<&str>>()[1].trim();

        // Check if the JWT is valid
        let token_data = crate::logic::user::User::decode_token(String::from(jwt));
        
        // Create new AuthenticatedUser extension and insert the token data
        let authed_user = crate::logic::user::AuthenticatedUser {
            user_id: token_data.sub,
        };

        req.extensions_mut().insert(authed_user);
    } else {
        return http::Response::builder()
            .status(http::StatusCode::UNAUTHORIZED)
            .body("Unauthorized".into())
            .unwrap()
    }

    let response = next.run(req).await;
    response
}


fn unauthed() -> http::Response<String> {
    http::Response::builder()
        .status(http::StatusCode::UNAUTHORIZED)
        .body("Unauthorized".into())
        .unwrap()
}
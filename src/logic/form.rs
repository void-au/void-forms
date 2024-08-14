use serde::{Deserialize, Serialize};
use axum::extract::{Path, Json};
use serde_json::{Value, json};
use axum::extract::State;
use crate::AppState;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Deserialize)]
pub struct CreateForm {
    first_name: String,
    last_name: String,
    email: String,
    message: String,
}

#[derive(Serialize, Deserialize)]
pub struct Form {
    pub id: Uuid,
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub message: String,
    pub additional_data: Option<String>,
}

impl Form {
    pub fn new(id: Uuid, first_name: String, last_name: String, email: String, message: String, additional_data: Option<String>) -> Self {
        Form {
            id,
            first_name,
            last_name,
            email,
            message,
            additional_data,
        }
    }
}

pub async fn get_forms(State(state): State<Arc<AppState>>) -> Json<Value>{
    let client = state.db_client.clone();

    let query = "SELECT * FROM forms";
    let rows = client.query(query, &[]).await.unwrap();

    let mut forms = Vec::new();

    for row in rows {
        let id: Uuid = row.get(0);
        let first_name: String = row.get(1);
        let last_name: String = row.get(2);
        let email: String = row.get(3);
        let message: String = row.get(4);
        // let additional_data: Option<String> = row.get(5);

        let form = Form::new(id, first_name, last_name, email, message, None);
        forms.push(form);
    }

    Json(json!(forms))
}

pub async fn get_form_by_id(Path(form_id): Path<String>) -> Json<Value> {
    let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
    let form = get_form(form_id).await;

    Json(json!({
        "id": form.id.to_string(), // Convert Uuid to String
        "first_name": form.first_name,
        "last_name": form.last_name,
        "email": form.email,
        "message": form.message,
        // "additional_data": null,
    }))
}

pub async fn create_new_form(State(state): State<Arc<AppState>>, Json(form): Json<CreateForm>)  -> Json<Value> {
    let client = state.db_client.clone();

    let query = "INSERT INTO forms (first_name, last_name, email, message) VALUES ($1, $2, $3, $4) RETURNING id";
    let row = client.query_one(query, &[&form.first_name, &form.last_name, &form.email, &form.message]).await.unwrap();
    let id: Uuid = row.get(0);

    Json(json!({
        "id": id.to_string(), // Convert Uuid to String
        "first_name": form.first_name,
        "last_name": form.last_name,
        "email": form.email,
        "message": form.message,
        // "additional_data": null,
    }))
}


pub async fn update_form(State(state): State<Arc<AppState>>, Path(form_id): Path<String>, Json(update_form): Json<CreateForm>) -> Json<Value> {
    let client = state.db_client.clone();

    // Get the old form
    let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
    let form = get_form(form_id).await;

    // Update the form
    let query = "UPDATE forms SET first_name = $1, last_name = $2, email = $3, message = $4 WHERE id = $5";
    client.execute(query, &[&update_form.first_name, &update_form.last_name, &update_form.email, &update_form.message, &form.id]).await.unwrap();

    Json(json!({
        "first_name": form.first_name,
        "last_name": form.last_name,
        "email": form.email,
        "message": form.message,
        // "additional_data": null,
    }))
}


async fn get_form(form_id: Uuid) -> Form {
    let client = crate::db::connect().await.unwrap();
    let query = "SELECT * FROM forms WHERE id = $1";
    let row = client.query_one(query, &[&form_id]).await.unwrap();

    let id: Uuid = row.get(0);
    let first_name: String = row.get(1);
    let last_name: String = row.get(2);
    let email: String = row.get(3);
    let message: String = row.get(4);

    Form::new(id, first_name, last_name, email, message, None)
}


pub async fn remove_form(Path(form_id): Path<String>) -> Json<Value> {
    let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
    let client = crate::db::connect().await.unwrap();

    let query = "DELETE FROM forms WHERE id = $1";
    client.execute(query, &[&form_id]).await.unwrap();

    Json(json!({
        "message": "Form deleted successfully",
    }))
}
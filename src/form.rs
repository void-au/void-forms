use serde::{Deserialize, Serialize};
use axum::extract::{Path, Json};
use std::convert::Infallible;
use serde_json::{Value, json};
use axum::extract::State;
use crate::AppState;
use std::sync::Arc;


#[derive(Serialize, Deserialize)]
pub struct Form {
    pub id : String,
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub message: String,
    pub additional_data: Option<String>,
}

impl Form {
    pub fn new(id: String, first_name: String, last_name: String, email: String, message: String, additional_data: Option<String>) -> Self {
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


fn get_form_data() -> Vec<Form> {
    return vec![
        Form::new(
            "727d147b-78bb-44dc-9f77-3705733fda09".to_string(),
            "John".to_string(),
            "Doe".to_string(),
            "john@gmail.com".to_string(),
            "Hello, World!".to_string(),
            None,
        )
    ];
}


pub async fn get_forms(State(state): State<Arc<AppState>>) -> Json<Value>{
    let client = state.db_client.clone();

    let query = "SELECT * FROM forms";
    let rows = client.query(query, &[]).await.unwrap();

    let mut forms = Vec::new();

    for row in rows {
        let id: String = row.get(0);
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
    println!("Got the form id: {}", form_id);

    let forms = get_form_data();

    let form = forms.iter().find(|form| form.id == form_id);

    match form {
        Some(form) => Json(json!(form)),
        None => Json(json!({"error": "Form not found"}))
    }
}



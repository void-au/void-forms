use serde::{Deserialize, Serialize};
use axum::extract::{Path, Json};
use serde_json::{Value, json};
use axum::extract::State;
use crate::AppState;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Deserialize, Debug)]
pub struct CreateForm {
    first_name: String,
    last_name: String,
    email: String,
    message: String,
    additional_data: Option<serde_json::Value>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UpdateForm {
    first_name: Option<String>,
    last_name: Option<String>,
    email: Option<String>,
    message: Option<String>,    
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Form {
    pub id: Uuid,
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub message: String,
    pub additional_data: Option<serde_json::Value>,
}

impl Form {
    pub fn new(id: Uuid, first_name: String, last_name: String, email: String, message: String, additional_data: Option<serde_json::Value>) -> Self {
        Form {
            id,
            first_name,
            last_name,
            email,
            message,
            additional_data,
        }
    }

    pub async fn get_all(client: &tokio_postgres::Client) -> Result<Vec<Form>, tokio_postgres::Error> {
        let query = "SELECT * FROM forms";
        let rows = client.query(query, &[]).await?;

        let mut forms = Vec::new();

        for row in rows {
            let id: Uuid = row.get(0);
            let first_name: String = row.get(1);
            let last_name: String = row.get(2);
            let email: String = row.get(3);
            let message: String = row.get(4);
            let additional_data: Option<serde_json::Value> = row.get(5);

            forms.push(Form::new(id, first_name, last_name, email, message, additional_data));
        }

        Ok(forms)
    }

    pub async fn get_by_id(client: &tokio_postgres::Client, id: Uuid) -> Result<Form, tokio_postgres::Error> {
        let query = "SELECT * FROM forms WHERE id = $1";
        let row = client.query_one(query, &[&id]).await?;

        let id: Uuid = row.get(0);
        let first_name: String = row.get(1);
        let last_name: String = row.get(2);
        let email: String = row.get(3);
        let message: String = row.get(4);
        let additional_data: Option<serde_json::Value> = row.get(5);

        Ok(Form::new(id, first_name, last_name, email, message, additional_data))
    }

    pub async fn insert(client: &tokio_postgres::Client, form: CreateForm) -> Result<Form, tokio_postgres::Error> {
        // Ensure that the additional_data is not too big 
        // TODO: Extract this from some sort of configuration setting
        // TODO: Return an http error of some sort? -> How to handle this in rust?
        if let Some(additional_data) = &form.additional_data {
            println!("Additional data: {}", additional_data.to_string().len());
            if additional_data.to_string().len() > 1000 {
                // Panic if the additional_data is too big
                panic!("additional_data is too big");
            }
        }
        
        let query = "INSERT INTO forms (first_name, last_name, email, message, additional_data) VALUES ($1, $2, $3, $4, $5) RETURNING id";
        let row = client.query_one(query, &[&form.first_name, &form.last_name, &form.email, &form.message, &form.additional_data]).await?;
        let id: Uuid = row.get(0);
        Ok( Form::get_by_id(client, id).await.unwrap())
    }

    pub async fn update(client: &tokio_postgres::Client, id: Uuid, form: Form) -> Result<Form, tokio_postgres::Error> {
        let query = "UPDATE forms SET first_name = $1, last_name = $2, email = $3, message = $4 WHERE id = $5";
        client.execute(query, &[&form.first_name, &form.last_name, &form.email, &form.message, &id]).await.unwrap();
        Form::get_by_id(client, id).await
    }

    pub async fn delete(client: &tokio_postgres::Client, id: Uuid) -> Result<(), tokio_postgres::Error> {
        let query = "DELETE FROM forms WHERE id = $1";
        client.execute(query, &[&id]).await?;
        Ok(())
    }
}

// Gets all the forms
pub async fn get_all_forms_handler(State(state): State<Arc<AppState>>) -> Json<Value>{
    let client = state.db_client.clone();
    Json(json!(Form::get_all(&client).await.unwrap()))
}

// Gets a form via its id
pub async fn get_form_via_id_handler(Path(form_id): Path<String>) -> Json<Value> {
    let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
    let client = crate::db::connect().await.unwrap();
    Json(json!(Form::get_by_id(&client, form_id).await.unwrap()))
}


// Creates a new form
pub async fn insert_form_handler(State(state): State<Arc<AppState>>, Json(form): Json<CreateForm>)  -> Json<Value> {
    let client = state.db_client.clone();
    Json(json!(Form::insert(&client, form).await.unwrap()))
}

// Updates a form
pub async fn update_form_handler(State(state): State<Arc<AppState>>, Path(form_id): Path<String>, update_form: Option<Json<UpdateForm>>) -> Json<Value> {
    if let Some(update_form) = update_form {
        let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
        let client = state.db_client.clone();
        let form = Form::get_by_id(&client, form_id).await.unwrap();

        let merged_form = Form::new(
            form_id, 
            update_form.first_name.clone().unwrap_or(form.first_name),
            update_form.last_name.clone().unwrap_or(form.last_name),
            update_form.email.clone().unwrap_or(form.email),
            update_form.message.clone().unwrap_or(form.message),
            form.additional_data, // Keep the existing additional_data, or handle it accordingly
        );

        Json(json!(Form::update(&client, form_id, merged_form).await.unwrap()))
    } else {
        Json(json!({
            "message": "No data provided to update",
        }))
    }
}

// Delete a form
pub async fn delete_form_handler(Path(form_id): Path<String>) -> Json<Value> {
    let form_id: Uuid = form_id.parse().unwrap(); // Convert String to Uuid
    let client = crate::db::connect().await.unwrap();
    Form::delete(&client, form_id).await.unwrap();

    Json(json!({
        "message": "Form deleted successfully",
    }))
}
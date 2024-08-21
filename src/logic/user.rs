use serde::{Deserialize, Serialize};
use axum::extract::{Path, Json};
use serde_json::{Value, json};
use axum::extract::State;
use crate::AppState;
use std::sync::Arc;
use uuid::Uuid;
use bcrypt;
use chrono::{DateTime, Utc};

#[derive(Serialize, Deserialize, Debug)]
pub struct User {
    pub id: Uuid,
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

pub struct FullUser {
    pub id: Uuid,
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub password: String,
}


#[derive(Deserialize, Debug)]
pub struct CreateUser {
    pub email: String,
    pub password: String,
    pub first_name: String,
    pub last_name: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UpdateUser {
    pub email: Option<String>,
    pub first_name: Option<String>,
    pub last_name: Option<String>,
}

impl FullUser {
    pub fn new(id: Uuid, email: String, first_name: String, last_name: String, created_at: DateTime<Utc>, updated_at: DateTime<Utc>, password: String) -> Self {
        FullUser {
            id,
            email,
            first_name,
            last_name,
            created_at,
            updated_at,
            password,
        }
    }

    pub fn extract_user(row: tokio_postgres::Row) -> FullUser {
        let id: Uuid = row.get("id");
        let email: String = row.get("email");
        let first_name: String = row.get("first_name");
        let last_name: String = row.get("last_name");
        let created_at: DateTime<Utc> = row.get("created_at");
        let updated_at: DateTime<Utc> = row.get("updated_at");
        let password: String = row.get("password");

        FullUser::new(id, email, first_name, last_name, created_at, updated_at, password)
    }

    pub async fn get_by_id(client: &tokio_postgres::Client, id: Uuid) -> Result<FullUser, tokio_postgres::Error> {
        let query = "SELECT id, email, first_name, last_name, created_at, updated_at, password FROM user_account WHERE id = $1";
        let row = client.query_one(query, &[&id]).await?;
        Ok(FullUser::extract_user(row))
    }
}


impl User {
    pub fn new(id: Uuid, email: String, first_name: String, last_name: String, created_at: DateTime<Utc>, updated_at: DateTime<Utc>) -> Self {
        User {
            id,
            email,
            first_name,
            last_name,
            created_at,
            updated_at,
        }
    }

    
    pub fn extract_user(row: tokio_postgres::Row) -> User {
        let id: Uuid = row.get("id");
        let email: String = row.get("email");
        let first_name: String = row.get("first_name");
        let last_name: String = row.get("last_name");
        let created_at: DateTime<Utc> = row.get("created_at");
        let updated_at: DateTime<Utc> = row.get("updated_at");

        User::new(id, email, first_name, last_name, created_at, updated_at)
    }

    pub async fn email_exists(client: &tokio_postgres::Client, email: String) -> Result<bool, tokio_postgres::Error> {
        // Check if the email account exists in user_account and deactivated_user
        let query = "SELECT EXISTS(SELECT 1 FROM user_account WHERE email = $1) OR EXISTS(SELECT 1 FROM deleted_users WHERE email = $1)";
        let row = client.query_one(query, &[&email]).await?;
        Ok(row.get(0))
    }

    pub async fn get_all(client: &tokio_postgres::Client) -> Result<Vec<User>, tokio_postgres::Error> {
        let query = "SELECT id, email, first_name, last_name, created_at, updated_at FROM user_account";
        let rows = client.query(query, &[]).await?;
        let mut users = Vec::new();

        for row in rows {
            users.push(User::extract_user(row));
        }

        Ok(users)
    }


    pub async fn get_by_id(client: &tokio_postgres::Client, id: Uuid) -> Result<User, tokio_postgres::Error> {
        let query = "SELECT id, email, first_name, last_name, created_at, updated_at FROM user_account WHERE id = $1";
        let row = client.query_one(query, &[&id]).await?;
        Ok(User::extract_user(row))
    }


    pub async fn create(client: &tokio_postgres::Client, user: CreateUser) -> Result<User, tokio_postgres::Error> {
        // Check if the user already exists
        if User::email_exists(client, user.email.clone()).await.unwrap() {
            panic!("User already exists");
        }

        let password = bcrypt::hash(user.password, 12).unwrap();
        
        let query = "INSERT INTO user_account (email, password, first_name, last_name) VALUES ($1, $2, $3, $4) RETURNING *";
        let row = client.query_one(query, &[&user.email, &password, &user.first_name, &user.last_name]).await?;
        let id: Uuid = row.get(0);
        Ok(User::get_by_id(client, id).await.unwrap())
    }

    pub async fn update(client: &tokio_postgres::Client, id: Uuid, user: UpdateUser) -> Result<User, tokio_postgres::Error> {
        let query = "UPDATE user_account SET first_name = $1, last_name = $2 WHERE id = $3 RETURNING *";
        client.query_one(query, &[&user.first_name, &user.last_name, &id]).await?;
        Ok(User::get_by_id(client, id).await.unwrap())
    }

    pub async fn delete(client: &tokio_postgres::Client, id: Uuid) -> Result<(), tokio_postgres::Error> {
        let user = FullUser::get_by_id(client, id).await.unwrap();
        
        // Insert into deleted_users table
        let query = "INSERT INTO deactivated_user (user_id, email, first_name, last_name, password, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7)";
        client.execute(query, &[&user.id, &user.email, &user.first_name, &user.last_name, &user.password, &user.created_at, &user.updated_at]).await?;

        // Delete user from user_account table
        let query = "DELETE FROM user_account WHERE id = $1";
        client.execute(query, &[&id]).await?;
        Ok(())
    }
}


// Gets all the users
pub async fn get_all_users_handler(State(state): State<Arc<AppState>>) -> Json<Value>{
    let client = state.db_client.clone();
    Json(json!(User::get_all(&client).await.unwrap()))
}

// Gets a user by id
pub async fn get_user_via_id_handler(Path(id): Path<Uuid>, State(state): State<Arc<AppState>>) -> Json<Value>{
    println!("Got the id: {}", &id.to_string());
    let client = state.db_client.clone();
    Json(json!(User::get_by_id(&client, id).await.unwrap()))
}

// Inserts a user
pub async fn insert_user_handler(State(state): State<Arc<AppState>>, Json(user): Json<CreateUser>) -> Json<Value>{
    let client = state.db_client.clone();
    Json(json!(User::create(&client, user).await.unwrap()))
}

// Updates a user
pub async fn update_user_handler(State(state): State<Arc<AppState>>, Path(id): Path<Uuid>, Json(update_user): Json<UpdateUser>) -> Json<Value>{
    let client = state.db_client.clone();
    let user = User::get_by_id(&client, id).await.unwrap();
    println!("User: {:?}", user);    
    
    // Setup the new user with the optional fields
    let merged_user = UpdateUser {
        email: update_user.email.or(Some(user.email)),
        first_name: update_user.first_name.or(Some(user.first_name)),
        last_name: update_user.last_name.or(Some(user.last_name)),
    };

    Json(json!(User::update(&client, id, merged_user).await.unwrap()))
}

// Deletes a user
pub async fn delete_user_handler(Path(id): Path<Uuid>, State(state): State<Arc<AppState>>) -> Json<Value>{
    let client = state.db_client.clone();
    User::delete(&client, id).await.unwrap();
    Json(json!({"message": "User deleted"}))
}
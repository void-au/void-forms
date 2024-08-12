use tokio_postgres::{NoTls, Error}; 


pub async fn connect() -> Result<tokio_postgres::Client, Error> {    
    let (client, connection) = tokio_postgres::connect(
        "host=localhost user=user password=password dbname=db",
        NoTls,
    ).await?;

    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("connection error: {}", e);
        }
    });

    Ok(client)
}
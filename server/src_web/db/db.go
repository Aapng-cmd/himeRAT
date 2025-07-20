package db

import (
    "fmt"
    "time"
    "context"
    "database/sql"
    "log"
    
    _ "github.com/mattn/go-sqlite3"
    "golang.org/x/crypto/bcrypt"
    
    "himerat/models"
)

var DB *sql.DB

func InitDB() {
    var err error
    DB, err = sql.Open("sqlite3", "./../computers.db")
    if err != nil {
        log.Fatal(err)
    }

    createComputersTable := `CREATE TABLE IF NOT EXISTS computers (
        uuid TEXT PRIMARY KEY,
        pid INTEGER,
        user TEXT,
        local_ip TEXT
    );`
    _, err = DB.Exec(createComputersTable)
    if err != nil {
        log.Fatal(err)
    }

    createUsersTable := `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    );`
    _, err = DB.Exec(createUsersTable)
    if err != nil {
        log.Fatal(err)
    }
}

func UserExists(userID int) (bool, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    var username string
    query := "SELECT username FROM users WHERE id = ?"
    err := DB.QueryRowContext(ctx, query, userID).Scan(&username)
    if err != nil {
        if err == sql.ErrNoRows {
            return false, nil // User does not exist
        }
        return false, fmt.Errorf("error querying user: %v", err) // Some other error occurred
    }
    return true, nil // User exists
}

func CreateUser(username, password string) error {
    hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return fmt.Errorf("error hashing password: %v", err)
    }

    query := "INSERT INTO users (username, password) VALUES (?, ?)"
    _, err = DB.Exec(query, username, hashedPassword)
    if err != nil {
        return fmt.Errorf("error inserting user: %v", err)
    }
    return nil
}

func LoginUser (username, password string) (models.User, error) {
    var user models.User

    // Query to find the user by username
    query := "SELECT id, username, password FROM users WHERE username = ?"
    row := DB.QueryRow(query, username)

    // Scan the result into the user struct
    err := row.Scan(&user.ID, &user.Username, &user.Password)
    if err != nil {
        if err == sql.ErrNoRows {
            return user, fmt.Errorf("user not found")
        }
        return user, fmt.Errorf("error querying user: %v", err)
    }

    // Compare the provided password with the stored hashed password
    if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)); err != nil {
        return user, fmt.Errorf("invalid password")
    }

    return user, nil
}


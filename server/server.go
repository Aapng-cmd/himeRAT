package main

import (
    "database/sql"
    "log"

    "github.com/gin-gonic/gin"
    _ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

func initDB() {
    var err error
    db, err = sql.Open("sqlite3", "./computers.db")
    if err != nil {
        log.Fatal(err)
    }
    createTable := `CREATE TABLE IF NOT EXISTS computers (
        uuid TEXT PRIMARY KEY,
        pid INTEGER,
        user TEXT,
        local_ip TEXT
    );`
    _, err = db.Exec(createTable)
    if err != nil {
        log.Fatal(err)
    }
}

func initRoutes(router *gin.Engine) {
    router.POST("/register/:uuid", registerHandler)
    router.GET("/workout/:uuid", workoutHandler)
    router.GET("/statistics", statisticsHandler)
    router.GET("/tasks/:uuid", tasksSenderHandler)
}

func main() {
    initDB()
    defer db.Close()

    router := gin.Default()
    initRoutes(router)

    log.Fatal(router.Run(":8080"))
}


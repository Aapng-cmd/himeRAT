package main

import (
    "log"
    "path/filepath"

    "github.com/gin-gonic/gin"
    
    "himerat/routes"
    "himerat/db"
)


func main() {
    db.InitDB()
    defer db.DB.Close()

    router := gin.Default()
    router.Static("/css", filepath.Join("templates", "css"))
    router.LoadHTMLGlob(filepath.Join("templates", "*.html"))
    routes.InitRoutes(router)

    log.Fatal(router.Run(":8080"))
}


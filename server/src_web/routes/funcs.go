package routes

import (
    "fmt"
    "net/http"
    
    "github.com/gin-gonic/gin"
    
    "himerat/db"
)

func workoutHandler(c *gin.Context) {
    uuid := c.Param("uuid")
    c.String(http.StatusOK, fmt.Sprintf("Handling workout for UUID: %s", uuid))
}

func statisticsHandler(c *gin.Context) {
    var count int
    err := db.DB.QueryRow("SELECT COUNT(*) FROM computers").Scan(&count)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"registered_computers": count})
}

func registerHandler(c *gin.Context) {
    var input struct {
        Username string `json:"username" binding:"required"`
        Password string `json:"password" binding:"required"`
    }
    // Bind the JSON input to the input struct
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input"})
        return
    }
    // Call createUser  to register the new user
    err := db.CreateUser(input.Username, input.Password)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    // Respond with a success message
    c.JSON(http.StatusCreated, gin.H{"message": "User  registered successfully"})
}

func loginHandler(c *gin.Context) {   
    var input struct {
        Username string `json:"username" binding:"required"`
        Password string `json:"password" binding:"required"`
    }

    // Bind the JSON input to the input struct
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input"})
        return
    }

    // Call loginUser  to authenticate the user
    user, err := db.LoginUser (input.Username, input.Password)
    if err != nil {
        if err.Error() == "user not found" || err.Error() == "invalid password" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "Login/password not valid"})
            return
        }
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    // Generate JWT token
    jwtToken, err := GenerateJWT(user.ID)
    if err != nil {   
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    // Set the JWT token in a cookie
    c.SetCookie("token", jwtToken, 3600, "/", "", false, true)
    c.JSON(http.StatusOK, gin.H{"message": "Login successful"})
}


// templates

func homeHandlerT(c *gin.Context) {
    c.HTML(http.StatusOK, "home.html", nil)
}

func registerHandlerT(c *gin.Context) {
    c.HTML(http.StatusOK, "registration.html", nil)
}

func loginHandlerT(c *gin.Context) {
    c.HTML(http.StatusOK, "login.html", nil)
}

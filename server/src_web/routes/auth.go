package routes

import (
    "fmt"
    "net/http"
    "math/rand"
    "time"
    "log"
    
    "github.com/dgrijalva/jwt-go"
    "github.com/gin-gonic/gin"

    "himerat/db"
)

const letterBytes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

func RandStringBytes(n int) string {
    b := make([]byte, n)
    for i := range b {
        b[i] = letterBytes[rand.Intn(len(letterBytes))]
    }
    return string(b)
}

var (
    SECRET_KEY = []byte("asd") // RandStringBytes(32)
)

func AuthMiddleWare() gin.HandlerFunc {
    return func(c *gin.Context) {
        tokenString, err := c.Cookie("token")
        if err != nil {
            c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"Error": "No JWT provided"})
            return
        }

        claims := jwt.MapClaims{}
        token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
            if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
                return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
            }
            return SECRET_KEY, nil
        })

        if err != nil || !token.Valid {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"Error": "Invalid JWT token"})
            return
        }

        userID := int(claims["user_id"].(float64))
        if userID == 0 {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"Error": "User ID not found in token claims"})
            return
        }

        exists, err := db.UserExists(userID)
        if err != nil {
            c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"Error": "Error checking user existence"})
            return
        }
        if !exists {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"Error": "User  does not exist"})
            return
        }

        c.Set("userID", userID)

        c.Next()
    }
}

func GenerateJWT(userID int) (string, error) {
    claims := jwt.MapClaims{
        "user_id": userID,
        "exp":     time.Now().Add(time.Hour * 24).Unix(),
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    tokenString, err := token.SignedString(SECRET_KEY)
    if err != nil {
        log.Println("Error in JWT token generation")
        return "", err
    }
    return tokenString, nil
}



package routes

import (
    "github.com/gin-gonic/gin"
)

func InitRoutes(router *gin.Engine) {
    apiRoutes := router.Group("/api")
    {
        apiRoutes.POST("/register", registerHandler)
        apiRoutes.POST("/login", loginHandler)
    }
    
    apiR := router.Group("/api").Use(AuthMiddleWare())
    {
        apiR.GET("/workout/:uuid", workoutHandler)
        apiR.GET("/statistics", statisticsHandler)
    }
    
    roots := router.Group("").Use(AuthMiddleWare())
    {
        roots.GET("/home", homeHandlerT)
    }
    
    router.GET("/register", registerHandlerT)
    router.GET("/login", loginHandlerT)
    
    router.GET("/", loginHandlerT)
}

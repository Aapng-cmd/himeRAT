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
        apiR.POST("/computers/:id", computersHandler)
        apiR.GET("/statistics", statisticsHandler)
    }

    roots := router.Group("").Use(AuthMiddleWare())
    {
        roots.GET("/home", homeHandlerT)
        router.GET("/statistics", statisticsHandlerT)
        roots.GET("/computers/:id", computersHandlerT)
    }
    
    router.GET("/register", registerHandlerT)
    router.GET("/login", loginHandlerT)
    
    router.GET("/", loginHandlerT)
}

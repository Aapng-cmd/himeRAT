package routes

import (
	"github.com/gin-gonic/gin"
)

func InitRoutes(router *gin.Engine) {
	router.GET("/", loginHandlerT)
	router.GET("/login", loginHandlerT)
	router.GET("/register", registerHandlerT)

	router.POST("/api/register", registerHandler)
	router.POST("/api/login", loginHandler)

	auth := router.Group("/").Use(AuthMiddleWare())
	api := router.Group("/api").Use(AuthMiddleWare())

	auth.GET("/home", homeHandlerT)
	auth.GET("/statistics", statisticsHandlerT)
	auth.GET("/computers/:id", computersHandlerT)

	api.GET("/statistics", statisticsHandler)
	api.GET("/computers/:id", computerDetailHandler)
	api.POST("/computers/:id/task", enqueueTaskHandler)
}

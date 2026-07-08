package routes

import (
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"

	"himerat/db"
)

var taskNames = []string{
	"recon", "enum_suid", "enum_sudo", "enum_cron",
	"enum_kernel", "enum_capabilities", "enum_writable",
}

func statisticsHandler(c *gin.Context) {
	list, err := db.ListComputers()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, list)
}

func computerDetailHandler(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	computer, err := db.GetComputer(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "узел не найден"})
		return
	}
	results, err := db.ListResults(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"computer": computer, "results": results, "tasks": taskNames})
}

func enqueueTaskHandler(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	var body struct {
		Task string `json:"task"`
	}
	if err := c.ShouldBindJSON(&body); err != nil || body.Task == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "укажите task"})
		return
	}
	tid, err := db.EnqueueTask(id, body.Task)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"task_id": tid, "task": body.Task})
}

func registerHandler(c *gin.Context) {
	var input struct {
		Username string `json:"username" binding:"required"`
		Password string `json:"password" binding:"required"`
	}
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "неверные данные"})
		return
	}
	if err := db.CreateUser(input.Username, input.Password); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"message": "пользователь создан"})
}

func loginHandler(c *gin.Context) {
	var input struct {
		Username string `json:"username" binding:"required"`
		Password string `json:"password" binding:"required"`
	}
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "неверные данные"})
		return
	}
	user, err := db.LoginUser(input.Username, input.Password)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "логин или пароль неверны"})
		return
	}
	token, err := GenerateJWT(user.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	secure := os.Getenv("TLS_CERT") != ""
	c.SetCookie("token", token, 3600*24, "/", "", secure, true)
	c.JSON(http.StatusOK, gin.H{"message": "вход выполнен"})
}

func homeHandlerT(c *gin.Context) {
	c.HTML(http.StatusOK, "home.html", nil)
}

func registerHandlerT(c *gin.Context) {
	c.HTML(http.StatusOK, "registration.html", nil)
}

func loginHandlerT(c *gin.Context) {
	c.HTML(http.StatusOK, "login.html", nil)
}

func statisticsHandlerT(c *gin.Context) {
	c.HTML(http.StatusOK, "statistics.html", gin.H{"Tasks": taskNames})
}

func computersHandlerT(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	computer, err := db.GetComputer(id)
	if err != nil {
		c.HTML(http.StatusNotFound, "login.html", gin.H{"error": "не найдено"})
		return
	}
	results, _ := db.ListResults(id)
	c.HTML(http.StatusOK, "computers.html", gin.H{
		"Computer": computer,
		"Results":  results,
		"Tasks":    taskNames,
	})
}

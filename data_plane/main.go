package main

import (
	"log"
	"net/http"

	"github.com/faju85/devforge/data_plane/internal/grep"
	"github.com/faju85/devforge/data_plane/internal/tools"
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok", "service": "data-plane"})
	})

	r.POST("/tools/execute", tools.ExecuteHandler)
	r.POST("/grep", grep.Handler)

	log.Println("data-plane listening on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}

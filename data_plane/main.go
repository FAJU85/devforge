package main

import (
	"log"
	"net/http"

	"github.com/faju85/devforge/data_plane/internal/tools"
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok", "service": "data-plane"})
	})

	// Phase 2: tool execution endpoint (stub — implementation in Phase 2)
	r.POST("/tools/execute", tools.ExecuteHandler)

	log.Println("data-plane listening on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}

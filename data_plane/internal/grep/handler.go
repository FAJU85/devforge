package grep

import (
	"bufio"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	maxFileBytes = 1 << 20 // 1 MB — skip larger files
	maxResults   = 200
)

type Request struct {
	Pattern    string `json:"pattern" binding:"required"`
	Root       string `json:"root"`
	MaxResults int    `json:"max_results"`
}

type Match struct {
	File    string `json:"file"`
	Line    int    `json:"line"`
	Content string `json:"content"`
}

type Response struct {
	Matches    []Match `json:"matches"`
	Total      int     `json:"total"`
	DurationMs int64   `json:"duration_ms"`
}

// Handler accepts a pattern + optional root dir and returns regex matches
// across all text files under that directory.  It is intentionally simple:
// no concurrency, bounded by maxResults and maxFileBytes so it stays safe.
func Handler(c *gin.Context) {
	var req Request
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	limit := req.MaxResults
	if limit <= 0 {
		limit = 50
	}
	if limit > maxResults {
		limit = maxResults
	}

	re, err := regexp.Compile(req.Pattern)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid regex: " + err.Error()})
		return
	}

	root := req.Root
	if root == "" {
		root = "."
	}

	start := time.Now()
	var matches []Match

	filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || info.Size() > maxFileBytes || len(matches) >= limit {
			return nil
		}
		f, err := os.Open(path)
		if err != nil {
			return nil
		}
		defer f.Close()

		lineNum := 0
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			lineNum++
			if len(matches) >= limit {
				break
			}
			line := scanner.Text()
			if re.MatchString(line) {
				matches = append(matches, Match{
					File:    path,
					Line:    lineNum,
					Content: strings.TrimSpace(line),
				})
			}
		}
		return nil
	})

	c.JSON(http.StatusOK, Response{
		Matches:    matches,
		Total:      len(matches),
		DurationMs: time.Since(start).Milliseconds(),
	})
}

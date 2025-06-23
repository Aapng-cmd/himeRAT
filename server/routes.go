package main

import (
    "archive/zip"
    "fmt"
    "io"
    "bytes"
    "net/http"
    "os"
    "path/filepath"

    "github.com/gin-gonic/gin"
)

type Computer struct {
    UUID     string `json:"uuid"`
    PID      int    `json:"pid"`
    User     string `json:"user"`
    LocalIP  string `json:"local_ip"`
}

func registerHandler(c *gin.Context) {
    uuid := c.Param("uuid")
    var computer Computer
    if err := c.ShouldBindJSON(&computer); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    computer.UUID = uuid
    _, err := db.Exec("INSERT INTO computers (uuid, pid, user, local_ip) VALUES (?, ?, ?, ?)", computer.UUID, computer.PID, computer.User, computer.LocalIP)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.Status(http.StatusCreated)
}

func workoutHandler(c *gin.Context) {
    uuid := c.Param("uuid")
    c.String(http.StatusOK, fmt.Sprintf("Handling workout for UUID: %s", uuid))
}

func statisticsHandler(c *gin.Context) {
    var count int
    err := db.QueryRow("SELECT COUNT(*) FROM computers").Scan(&count)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"registered_computers": count})
}

func tasksSenderHandler(c *gin.Context) {
    uuid := c.Param("uuid")
    buf := new(bytes.Buffer)
    zipWriter := zip.NewWriter(buf)

    walker := func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }
        if info.IsDir() {
            return nil
        }
        file, err := os.Open(path)
        if err != nil {
            return err
        }
        defer file.Close()

        header, err := zip.FileInfoHeader(info)
        if err != nil {
            return err
        }
        header.Name = filepath.ToSlash(path[len("modules/"):])
        f, err := zipWriter.CreateHeader(header)
        if err != nil {
            return err
        }

        _, err = io.Copy(f, file)
        return err
    }

    err := filepath.Walk("modules", walker)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Could not zip files"})
        return
    }

    err = zipWriter.Close()
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Could not finalize zip"})
        return
    }

    c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=modules.zip", uuid))
    c.Header("Content-Type", "application/zip")
    c.Data(http.StatusOK, "application/zip", buf.Bytes())
}



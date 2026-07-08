package models

type Computer struct {
	ID         int    `json:"id"`
	SystemHash string `json:"system_hash"`
	PID        int    `json:"pid"`
	User       string `json:"user"`
	LocalIP    string `json:"local_ip"`
	Hostname   string `json:"hostname"`
	OsInfo     string `json:"os_info"`
	Kernel     string `json:"kernel"`
	Status     int    `json:"status"`
	LastSeen   string `json:"last_seen"`
}

type TaskResult struct {
	ID        int                    `json:"id"`
	TaskID    int                    `json:"task_id"`
	TaskName  string                 `json:"task_name"`
	CreatedAt string                 `json:"created_at"`
	Result    map[string]interface{} `json:"result"`
}

type User struct {
	ID       int    `json:"id"`
	Username string `json:"username"`
	Password string `json:"password"`
}

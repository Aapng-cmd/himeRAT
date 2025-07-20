package models


type Computer struct {
    UUID     string `json:"uuid"`
    PID      int    `json:"pid"`
    User     string `json:"user"`
    LocalIP  string `json:"local_ip"`
    SystemHash string `json:"system_hash"`
}

type User struct {
    ID     int `json:"id"`
    Username     string `json:"username"`
    Password string `json:"password"`
}

package models


type Computer struct {
    ID     int `json:"id"`
    SystemHash string `json:"system_hash"`
    PID      int    `json:"pid"`
    User     string `json:"user"`
    LocalIP  string `json:"local_ip"`
    State    string `json:"state"`
}

type User struct {
    ID     int `json:"id"`
    Username     string `json:"username"`
    Password string `json:"password"`
}

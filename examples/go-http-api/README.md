# Go HTTP API Example

Minimalne REST API w Go (bez frameworków) uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/go-http-api/README.md
```

---

```go markpact:file path=main.go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

type HealthResponse struct {
	Status string `json:"status"`
}

type EchoRequest struct {
	Message string `json:"message"`
}

type EchoResponse struct {
	Message string `json:"message"`
}

func main() {
	port := os.Getenv("MARKPACT_PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(HealthResponse{Status: "ok"})
	})

	http.HandleFunc("/echo", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		var req EchoRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(EchoResponse{Message: req.Message})
	})

	addr := ":" + port
	log.Printf("Listening on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
```

```bash markpact:run
go run main.go
```

```text markpact:test http
GET /health EXPECT 200
POST /echo BODY {"message":"hello"} EXPECT 200
```

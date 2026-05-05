package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
)

func main() {
	secrets, err := readSecrets()
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(secrets["api_key"])

	cmd := exec.Command("python3", "test.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		log.Fatal(err)
	}
}

func readSecrets() (map[string]any, error) {
	data, err := os.ReadFile("secrets.json")
	if err != nil {
		return nil, fmt.Errorf("read secrets.json: %w", err)
	}

	var secrets map[string]any
	if err := json.Unmarshal(data, &secrets); err != nil {
		return nil, fmt.Errorf("decode secrets.json: %w", err)
	}

	return secrets, nil
}

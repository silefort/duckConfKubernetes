package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	apiServer = "http://api-server:8080"
	sleepTime = 10 * time.Second
)

var (
	nodes        = []string{"node-1", "node-2", "node-3"}
	compteurNode = 0
)

type App struct {
	Image string `json:"image,omitempty"`
	Node  string `json:"node,omitempty"`
}

func log(message string) {
	fmt.Printf("[scheduler] %s\n", message)
}

func getApps(nodeName string) (map[string]App, error) {
	url := fmt.Sprintf("%s/apps?nodeName=%s", apiServer, nodeName)

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var apps map[string]App
	if err := json.Unmarshal(body, &apps); err != nil {
		return nil, err
	}

	return apps, nil
}

func putApp(appName, nodeName string) error {
	url := fmt.Sprintf("%s/app/%s", apiServer, appName)

	data := map[string]string{"node": nodeName}
	jsonData, err := json.Marshal(data)
	if err != nil {
		return err
	}

	client := &http.Client{Timeout: 5 * time.Second}
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	return nil
}

func main() {
	for {
		log("======================================================")
		log("SCHEDULER - BOUCLE DE CONTRÔLE")
		log("======================================================")

		// --- 01. CAPTEUR - Récupérer les applications qui n'ont pas de node assignés
		//                   sur l'API Server ---
		var appsSansNoeud map[string]App
		var err error

		appsSansNoeud, err = getApps("")
		if err != nil {
			log(fmt.Sprintf("API server non disponible: %v", err))
			appsSansNoeud = make(map[string]App)
		}
		log(fmt.Sprintf("01. CAPTEUR : apps en attente de scheduling = %v", appsSansNoeud))

		// --- 02. ETAT_DESIRE - Implicite : toutes les applications doivent avoir un noeud d'assigné ---
		log("02. ETAT_DESIRE : Implicite : toutes les applications doivent avoir un noeud d'assigné")

		// --- 03. COMPARATEUR - Identifier l'écart ---
		appsAAssigner := make([]string, 0, len(appsSansNoeud))
		for appName := range appsSansNoeud {
			appsAAssigner = append(appsAAssigner, appName)
		}
		log(fmt.Sprintf("03. COMPARATEUR : apps en attente de scheduling = %v", appsSansNoeud))

		// --- 04. ACTIONNEUR - Appliquer les changements ---
		for _, app := range appsAAssigner {
			node := nodes[compteurNode%len(nodes)]
			compteurNode++

			if err := putApp(app, node); err != nil {
				log(fmt.Sprintf("Erreur lors de l'assignation de %s: %v", app, err))
				continue
			}
			log(fmt.Sprintf("04. ACTIONNEUR : %s -> %s", app, node))
		}

		fmt.Println()
		time.Sleep(sleepTime)
	}
}

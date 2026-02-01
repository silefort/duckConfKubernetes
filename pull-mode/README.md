# Grands principes :

* Objectifs : Une API HTTP, 3 Noeuds
* Simulation de l'execution d'application = ajout/suppression de lignes dans un fichier exposé dans les noeuds

# Présentation app_controller.py
v app_controller.py

# Présentation api_server.py
* On stocke l'état désiré dans le fichier etat_desire.txt
* on a 1 route POST /api/apps pour créer une app dans l'état désiré
* on a 1 route GET /api/apps pour récupérer la liste des applications présentes dans l'état désiré

# Demo
* make stop
* make clean
* make run-mono
* make watch dans un autre onglet
* make create_app duck-1

# Ajout de 2 autres noeuds :
* RAF pour l'instant sur les noeuds

# Ajout d'un scheduler
scheduler.py pour pouvoir assigner une application à un noeud

# Ajout d'un node_controller 
node_controller.py pour pouvoir monitorer l'état des noeuds

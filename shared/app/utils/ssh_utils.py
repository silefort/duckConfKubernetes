#!/usr/bin/env python3
import paramiko

def ssh(node, cmd, timeout=5):
    """Execute une commande sur un noeud via SSH avec timeout"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(node, username="root", password="root", timeout=timeout)
        _, stdout, _ = client.exec_command(cmd)
        return stdout.read().decode().strip()
    except Exception as e:
        print(f"[ssh] Erreur sur {node}: {e}")
        return ""

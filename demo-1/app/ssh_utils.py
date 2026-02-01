#!/usr/bin/env python3
import paramiko

def ssh(node, cmd):
    """Execute une commande sur un noeud via SSH"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(node, username="root", password="root")
    _, stdout, _ = client.exec_command(cmd)
    return stdout.read().decode().strip()

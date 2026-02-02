import subprocess

def shell(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

import psutil

# Get all running processes
for proc in psutil.process_iter():
    try:
        # Check if the process is a Python process
        if proc.name() == "python.exe":
            # Kill the process
            print("Killing process: ", proc.name())
            proc.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
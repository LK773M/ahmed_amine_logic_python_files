import subprocess

def run_script(script_name):
    try:
        process = subprocess.Popen(["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Started {script_name} with PID {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start {script_name}: {e}")

if __name__ == "__main__":
    scripts = ["create_event.py", "delete_events_api.py", "reschedule_event.py"]
    processes = [run_script(script) for script in scripts]

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping all scripts...")
        for process in processes:
            process.terminate()
        print("All scripts terminated.")

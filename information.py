import psutil

print(f"CPU Usage: {psutil.cpu_percent()}%")


print(f"Physical cores: {psutil.cpu_count(logical=False)}")


print(f"Total cores: {psutil.cpu_count(logical=True)}")



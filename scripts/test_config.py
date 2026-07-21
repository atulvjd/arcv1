from core.config import Config

config = Config()

print("Application :", config.get("app_name"))
print("Version     :", config.get("version"))
print("Environment :", config.get("environment"))
print("Debug       :", config.get("debug"))
print("Log Level   :", config.get("log_level"))
print("Port        :", config.get("port"))
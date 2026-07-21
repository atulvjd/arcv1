from core.exceptions import ConfigurationError

try:
    raise ConfigurationError("Missing configuration: APP_NAME")
except ConfigurationError as error:
    print(error)
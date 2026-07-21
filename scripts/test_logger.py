from core.logger import get_logger

log = get_logger("ArcV1")

log.debug("Debug message")
log.info("Runtime started")
log.warning("Low memory")
log.error("Something failed")
log.critical("Critical error")

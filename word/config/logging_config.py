import logging
import sys
import os
import structlog
import re
import json
from structlog.stdlib import LoggerFactory
from dotenv import load_dotenv
from config.settings import OPENAI_API_KEY, LOGS_DIR

"""Strukturált naplózási konfiguráció JSON kimenettel és napi rotációval.

Ez a modul egy `structlog` alapú naplózót biztosít, amely JSON formátumú naplókat ír fájlba,
miközben olvasható szöveges kimenetet generál a konzolra. Támogatja az érzékeny adatok
szűrését és a naplófájlok napi rotációját.
"""


class SensitiveDataProcessor:
    def __init__(self, sensitive_strings: list):
        self.sensitive_strings = sensitive_strings
        self.patterns = [
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
            re.compile(r"\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{4,6}\b"),  # Telefonszám
            re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+\b"),  # API token
        ]

    def __call__(self, logger, method_name, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, str):
                for sensitive in self.sensitive_strings:
                    value = value.replace(sensitive, "****")
                for pattern in self.patterns:
                    value = pattern.sub("****", value)
                event_dict[key] = value
        return event_dict


class UTF8JSONRenderer(structlog.processors.JSONRenderer):
    def __init__(self, indent=None, sort_keys=True):
        super().__init__()
        self._indent = indent
        self._sort_keys = sort_keys

    def __call__(self, logger, name, event_dict):
        try:
            return (
                json.dumps(
                    event_dict,
                    ensure_ascii=False,
                    indent=self._indent,
                    sort_keys=True,
                    default=str,
                )
                .encode("utf-8")
                .decode("utf-8")
            )
        except Exception as e:
            logging.error(f"JSON renderelési hiba: {str(e)}", exc_info=True)
            raise


# Könyvtárak biztosítása
os.makedirs("logs", exist_ok=True)

# Log szint
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level, logging.INFO)

# Structlog konfiguráció
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        SensitiveDataProcessor([OPENAI_API_KEY]),
        structlog.stdlib.PositionalArgumentsFormatter(),
        UTF8JSONRenderer(indent=2),
    ],
    context_class=dict,
    logger_factory=LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Standard logging konfiguráció
logger = logging.getLogger()
logger.setLevel(log_level)

# Konzol handler (olvasható formátum)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(console_handler)

# Fájl handler (JSON formátum a structlog által) rotációval
log_filename = os.path.join(LOGS_DIR, "document_processing.log")
file_handler = logging.FileHandler(
    log_filename,
    encoding="utf-8",
)
file_handler.suffix = "%Y-%m-%d.log"
file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}\.log$")
file_handler.setFormatter(logging.Formatter("%(message)s"))
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Structlog logger
structlog_logger = structlog.get_logger()

__all__ = ["structlog_logger"]

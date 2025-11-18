from enum import Enum

class FileExtensions(Enum):
    PDF = ".pdf"
    DOC = ".doc"
    DOCX = ".docx"
    PPT = ".ppt"
    PPTX = ".pptx"
    XLS = ".xls"
    XLSX = ".xlsx"
    ZIP = ".zip"
    TAR = ".tar"
    GZ = ".gz"
    MP4 = ".mp4"
    MP3 = ".mp3"
    AVI = ".avi"
    MOV = ".mov"

class CrawlerStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AuditViolationLevel(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from engine.schemas.file_schemas import FileMetadata
from engine.utils.config_util import load_config
from engine.utils.generators_util import generate_timestamp_string
from engine.utils.logger_util import get_logger

# Setup logger for file utils with proper configuration
logger = get_logger("file_utils", log_path="logs/file_utils.log", level=logging.DEBUG)


def ensure_path(path: str) -> str:
    """Ensure the path exists and return it"""
    logger.debug(f"[FILE_UTILS] ensure_path called with: {path}")
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        path_exists = os.path.exists(path)
        is_dir = os.path.isdir(path)
        is_writable = os.access(path, os.W_OK) if path_exists else False
        logger.debug(f"[FILE_UTILS] Path ensured - exists: {path_exists}, is_dir: {is_dir}, writable: {is_writable}")
        return path
    except Exception as e:
        logger.error(f"[FILE_UTILS] Failed to ensure path '{path}': {str(e)}", exc_info=True)
        raise


logger.debug("[FILE_UTILS] Initializing BASE_PATH configuration")
config = load_config()
_file_path = config.get_variable("FILE_PATH", "files")
logger.debug(f"[FILE_UTILS] FILE_PATH from config: '{_file_path}' (type: {type(_file_path).__name__})")

# Normalize BASE_PATH to absolute path
# If relative, resolve relative to current working directory
# If absolute, use as-is
if os.path.isabs(_file_path):
    BASE_PATH = _file_path
    logger.debug(f"[FILE_UTILS] FILE_PATH is absolute, using as-is: {BASE_PATH}")
else:
    # Resolve relative to current working directory
    cwd = os.getcwd()
    logger.debug(f"[FILE_UTILS] FILE_PATH is relative, resolving against CWD: {cwd}")
    BASE_PATH = os.path.abspath(os.path.normpath(_file_path))
    logger.debug(f"[FILE_UTILS] Resolved BASE_PATH: {BASE_PATH}")

logger.info(f"[FILE_UTILS] BASE_PATH initialized to: {BASE_PATH}")

# Ensure BASE_PATH directory exists
logger.debug(f"[FILE_UTILS] Ensuring BASE_PATH directory exists: {BASE_PATH}")
try:
    ensure_path(BASE_PATH)
    base_path_exists = os.path.exists(BASE_PATH)
    base_path_is_dir = os.path.isdir(BASE_PATH) if base_path_exists else False
    base_path_readable = os.access(BASE_PATH, os.R_OK) if base_path_exists else False
    base_path_writable = os.access(BASE_PATH, os.W_OK) if base_path_exists else False
    
    logger.info(
        f"[FILE_UTILS] BASE_PATH directory status - "
        f"exists: {base_path_exists}, "
        f"is_dir: {base_path_is_dir}, "
        f"readable: {base_path_readable}, "
        f"writable: {base_path_writable}"
    )
    
    if not base_path_exists:
        logger.warning(f"[FILE_UTILS] BASE_PATH directory does not exist: {BASE_PATH}")
    if base_path_exists and not base_path_is_dir:
        logger.error(f"[FILE_UTILS] BASE_PATH exists but is not a directory: {BASE_PATH}")
    if base_path_exists and not base_path_readable:
        logger.warning(f"[FILE_UTILS] BASE_PATH directory is not readable: {BASE_PATH}")
    if base_path_exists and not base_path_writable:
        logger.warning(f"[FILE_UTILS] BASE_PATH directory is not writable: {BASE_PATH}")
except Exception as e:
    logger.error(f"[FILE_UTILS] Failed to ensure BASE_PATH directory: {str(e)}", exc_info=True)
    raise

# TODO : Add Config file for content types allowed in system
CONTENT_TYPES = {
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.zip': 'application/zip',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.csv': 'text/csv',
    '.mp4': 'video/mp4',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.mkv': 'video/x-matroska',
    '.flv': 'video/x-flv',
    '.wmv': 'video/x-ms-wmv'
}


def get_file_metadata(file_path: str, original_filename: str) -> FileMetadata:
    """Get file metadata including relative URL"""
    stat = os.stat(file_path)
    return FileMetadata(
        name=os.path.basename(file_path),
        original_filename=original_filename,
        url=os.path.relpath(file_path, BASE_PATH),
        content_type=get_content_type(file_path),
        size=stat.st_size,
        created_at=stat.st_ctime,
        modified_at=stat.st_mtime,
        full_path=file_path
    )


def get_content_type(file_path: str) -> str:
    """Get MIME type based on file extension"""
    extension = os.path.splitext(file_path)[1].lower()
    content_types = CONTENT_TYPES
    return content_types.get(extension, 'application/octet-stream')


def save_uploaded_file(file_data: Dict, path: Optional[str] = None) -> FileMetadata:
    """
    Save a single uploaded file and return its metadata
    Args:
        file_data: Dict containing 'content', 'filename' and other metadata
        path: Optional custom path, defaults to BASE_PATH
    Returns:
        FileMetadata object with file information
    """
    upload_path = ensure_path(path or BASE_PATH)
    original_filename = file_data['filename']
    extension = os.path.splitext(original_filename)[1]
    timestamp = generate_timestamp_string()
    new_filename = f"{timestamp}{extension}"
    file_path = os.path.join(upload_path, new_filename)

    # Write file
    with open(file_path, 'wb') as f:
        f.write(file_data['content'])

    return get_file_metadata(file_path, original_filename)


def save_uploaded_files(files: List[Dict], path: Optional[str] = None) -> List[FileMetadata]:
    """
    Save multiple uploaded files and return their metadata
    Args:
        files: List of dicts containing file data
        path: Optional custom path, defaults to BASE_PATH
    Returns:
        List of FileMetadata objects
    """
    return [save_uploaded_file(file_data, path) for file_data in files]


def list_directory_files(path: Optional[str] = None) -> List[FileMetadata]:
    """
    List all files in a directory with metadata
    Args:
        path: Optional custom path, defaults to BASE_PATH
    Returns:
        List of FileMetadata objects
    """
    target_path = path or BASE_PATH

    if not os.path.exists(target_path):
        return []

    results = []
    for root, _, files in os.walk(target_path):
        for filename in files:
            file_path = os.path.join(str(root), str(filename))
            results.append(get_file_metadata(file_path, filename))

    return results


def get_file_path(url: str) -> str:
    """
    Convert a relative URL back to a file path
    Args:
        url: Relative URL of the file
    Returns:
        Absolute file path
    """
    return os.path.join(BASE_PATH, url)

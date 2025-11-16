import os
from typing import List, Dict, Optional
from pathlib import Path
from engine.schemas.file_schemas import FileMetadata
from engine.utils.config_util import load_config
from engine.utils.generators_util import generate_timestamp_string

config = load_config()
BASE_PATH = config.get_variable("FILE_PATH", "files")

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


def ensure_path(path: str) -> str:
    """Ensure the path exists and return it"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


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

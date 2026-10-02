from typing import Literal

from pydantic import BaseModel


class OCRRequest(BaseModel):
    # Overrides OUTPUT_FOLDER_ID for this request.
    output_folder_id: str | None = None
    # Include per-line boxes/confidences in the HTTP response (always written to the .json file).
    include_lines: bool = False


class FolderRequest(BaseModel):
    # Ignored when recursive=true: results are then always written next to each CV.
    output_folder_id: str | None = None
    # Re-process CVs that already have an .ocr.txt result.
    overwrite: bool = False
    # Treat each subfolder as one candidate and OCR the files inside it (any depth).
    recursive: bool = False
    # recursive only: move each fully processed subfolder here. Overrides PROCESSED_FOLDER_ID.
    processed_folder_id: str | None = None


class OutputFile(BaseModel):
    id: str
    name: str
    webViewLink: str | None = None


class PageResult(BaseModel):
    page: int
    text: str
    lines: list[dict] | None = None


class OCRResponse(BaseModel):
    file_id: str
    file_name: str
    page_count: int
    text: str
    pages: list[PageResult]
    outputs: list[OutputFile]


class JobStatus(BaseModel):
    job_id: str
    folder_id: str
    status: Literal["queued", "running", "completed", "failed"]
    recursive: bool = False
    total: int = 0
    processed: list[str] = []
    skipped: list[str] = []
    moved_folders: list[str] = []
    errors: dict[str, str] = {}
    detail: str | None = None

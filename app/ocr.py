import io
import threading

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageSequence
from paddleocr import PaddleOCR

IMAGE_MIMES = {
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
    "image/webp",
    "image/gif",
}
SUPPORTED_MIMES = IMAGE_MIMES | {"application/pdf"}


def build_engine(lang: str, enable_mkldnn: bool = True) -> PaddleOCR:
    # Document orientation/unwarping models are overkill for CVs; text-line
    # orientation catches rotated snippets cheaply.
    return PaddleOCR(
        lang=lang,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
        enable_mkldnn=enable_mkldnn,
    )


class OCRService:
    def __init__(self, lang: str, pdf_dpi: int, max_pages: int, enable_mkldnn: bool = True):
        self._engine = build_engine(lang, enable_mkldnn)
        # PaddleOCR predictors are not thread-safe; serialize inference.
        self._lock = threading.Lock()
        self.pdf_dpi = pdf_dpi
        self.max_pages = max_pages

    def process(self, data: bytes, mime_type: str) -> list[dict]:
        """OCR a PDF or image. Returns one entry per page."""
        if mime_type == "application/pdf":
            images = self._pdf_to_images(data)
        elif mime_type in IMAGE_MIMES:
            images = self._decode_image(data)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        pages = []
        for number, img in enumerate(images, start=1):
            lines = self._ocr_image(img)
            pages.append(
                {
                    "page": number,
                    "text": "\n".join(line["text"] for line in lines),
                    "lines": lines,
                }
            )
        return pages

    def _pdf_to_images(self, data: bytes) -> list[np.ndarray]:
        images = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in list(doc)[: self.max_pages]:
                pix = page.get_pixmap(dpi=self.pdf_dpi, alpha=False)
                rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                images.append(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        return images

    def _decode_image(self, data: bytes) -> list[np.ndarray]:
        # PIL handles multi-page TIFFs and formats OpenCV can't decode.
        with Image.open(io.BytesIO(data)) as im:
            frames = [
                cv2.cvtColor(np.array(frame.convert("RGB")), cv2.COLOR_RGB2BGR)
                for frame in ImageSequence.Iterator(im)
            ]
        return frames[: self.max_pages]

    def _ocr_image(self, img: np.ndarray) -> list[dict]:
        with self._lock:
            results = self._engine.predict(img)

        lines = []
        for res in results:
            for text, score, poly in zip(res["rec_texts"], res["rec_scores"], res["rec_polys"]):
                if not text.strip():
                    continue
                lines.append(
                    {
                        "text": text,
                        "confidence": round(float(score), 4),
                        "box": np.asarray(poly).astype(int).tolist(),
                    }
                )
        return lines

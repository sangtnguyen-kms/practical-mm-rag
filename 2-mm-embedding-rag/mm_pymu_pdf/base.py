"""Read PDF files using PyMuPDF library."""
import base64
import io
import tempfile
from pathlib import Path
from PIL import Image
from typing import Dict, List, Optional, Union

from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document, ImageDocument


class PyMuPDFReader(BaseReader):
    """Read PDF files using PyMuPDF library."""

    def load_data(
        self,
        file_path: Union[Path, str],
        metadata: bool = True,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Loads list of documents from PDF file and also accepts
        extra information in dict format."""
        return self.load(file_path, metadata=metadata, extra_info=extra_info)

    def load(
        self,
        file_path: Union[Path, str],
        metadata: bool = True,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Loads list of documents from PDF file and also accepts extra
        information in dict format.

        Args:
            file_path (Union[Path, str]): file path of PDF file (accepts
            string or Path).
            metadata (bool, optional): if metadata to be included or not.
            Defaults to True.
            extra_info (Optional[Dict], optional): extra information related
            to each document in dict format. Defaults to None.

        Raises:
            TypeError: if extra_info is not a dictionary.
            TypeError: if file_path is not a string or Path.

        Returns:
            List[Document]: list of documents.
        """

        def encode_image(image_bytes):
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/jpeg;base64,{base64_image}"

        import fitz

        # check if file_path is a string or Path
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError("file_path must be a string or Path.")

        # open PDF file
        doc = fitz.open(file_path)

        # if extra_info is not None, check if it is a dictionary
        if extra_info:
            if not isinstance(extra_info, dict):
                raise TypeError("extra_info must be a dictionary.")

        normal_docs = []

        # if metadata is True, add metadata to each document
        if metadata:
            if not extra_info:
                extra_info = {}
            extra_info["total_pages"] = len(doc)
            extra_info["file_path"] = file_path

            # return list of documents
            normal_docs = [
                Document(
                    text=page.get_text().encode("utf-8"),
                    extra_info=dict(
                        extra_info,
                        **{
                            "source": f"{page.number+1}",
                        },
                    ),
                )
                for page in doc
            ]

        else:
            normal_docs = [
                Document(
                    text=page.get_text().encode("utf-8"),
                    extra_info=extra_info or {},
                )
                for page in doc
            ]

        images = []
        for page in doc:
            images.extend(page.get_images())

        image_docs = []

        for image in images:
            bytes_image = doc.extract_image(image[0])["image"]
            base64_image = encode_image(bytes_image)
            pil_image = Image.open(io.BytesIO(bytes_image))

            with tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False
            ) as fp:
                pil_image.save(fp.name)

                image_docs.append(
                    ImageDocument(image=fp.name, image_url=base64_image)
                )

        return [*normal_docs, *image_docs]

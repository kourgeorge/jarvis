import asyncio
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader


class PDFLoaderSchema(BaseModel):
    """Input schema for PDFLoader."""
    file_path: str = Field(..., description="Path to the PDF file to be loaded.")


class PDFLoaderTool(BaseTool):
    """Tool to load and parse a PDF file."""

    name: str = "pdf_loader"
    description: str = "Loads a PDF file and parses its content into documents for further processing."
    args_schema: Type[PDFLoaderSchema] = PDFLoaderSchema

    def _run(self, file_path: str) -> dict:
        """
        Load and parse the entire PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            dict: The parsed content of the entire PDF file.
        """
        try:
            # Load the PDF file
            loader = PyPDFLoader(file_path)
            docs = loader.load()

            # Combine the content of all pages/documents
            entire_content = "\n".join(doc.page_content for doc in docs)

            return {
                "status": "success",
                "message": "PDF loaded successfully.",
                "content": entire_content,
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"File '{file_path}' not found.",
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while loading the PDF: {error}",
            }

    async def _arun(self, file_path: str) -> dict:
        """
        Asynchronously load and parse the entire PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            dict: The parsed content of the entire PDF file.
        """
        try:
            # Use asyncio to run the blocking PDF loading in a separate thread
            loader = PyPDFLoader(file_path)
            docs = await asyncio.to_thread(loader.load)

            # Combine the content of all pages/documents
            entire_content = "\n".join(doc.page_content for doc in docs)

            return {
                "status": "success",
                "message": "PDF loaded successfully.",
                "content": entire_content,
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"File '{file_path}' not found.",
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while loading the PDF: {error}",
            }


# Example Usage
if __name__ == "__main__":
    # Initialize the PDFLoaderTool
    pdf_tool = PDFLoaderTool()

    # Define the file path
    file_path = "/Users/georgekour/Downloads/AILuminate Assessment Standard v1.0 11_29_24 FINAL.pdf"

    # Run the tool
    result = pdf_tool._run(file_path=file_path)

    # Print the result
    if result["status"] == "success":
        print("PDF Content:")
        print(result["content"])
    else:
        print("Error:", result["message"])
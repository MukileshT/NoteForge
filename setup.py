"""Setup script for Obsidian Notes Converter"""
from setuptools import setup, find_packages

setup(
    name="obsidian-notes-converter",
    version="2.0.0",
    description="Convert PDFs and images to Obsidian notes with OCR and AI",
    author="Obsidian Converter Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pillow>=11.0.0",
        "numpy>=1.26.0,<2.0.0",
        "opencv-python>=4.6.0,<=4.6.0.66",
        "easyocr>=1.7.2",
        "paddleocr>=2.7.3,<3.0.0",
        "paddlepaddle>=2.6.2,<3.0.0",
        "pdf2image>=1.17.0",
        "pypdfium2>=5.3.0",
        "openai>=2.15.0",
        "anthropic>=0.76.0",
        "google-genai>=1.58.0",
        "groq>=1.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "colorlog>=6.10.0",
    ],
    python_requires=">=3.10",
)

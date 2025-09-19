"""Image handling utilities."""

import os
import uuid
import hashlib
from typing import Optional, Tuple, BinaryIO
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
import aiofiles
import aiofiles.os
from fastapi import UploadFile, HTTPException

from app.config import settings


class ImageProcessor:
    """Image processing utilities."""

    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

    # Image size limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSIONS = (2048, 2048)  # Max width/height

    # Thumbnail sizes
    THUMBNAIL_SIZES = {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    }

    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """Validate uploaded image file."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ImageProcessor.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {', '.join(ImageProcessor.SUPPORTED_FORMATS)}"
            )

        # Check file size (if available)
        if hasattr(file, 'size') and file.size and file.size > ImageProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {ImageProcessor.MAX_FILE_SIZE // (1024*1024)}MB"
            )

    @staticmethod
    def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
        """Generate unique filename with optional prefix."""
        file_ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        if prefix:
            return f"{prefix}_{unique_id}{file_ext}"
        return f"{unique_id}{file_ext}"

    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    async def save_uploaded_file(
        file: UploadFile,
        upload_dir: str,
        filename: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Save uploaded file to disk.

        Returns:
            Tuple of (filename, file_path, file_size)
        """
        # Validate file
        ImageProcessor.validate_image_file(file)

        # Create upload directory if it doesn't exist
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if not filename:
            filename = ImageProcessor.generate_unique_filename(file.filename or "image.jpg")

        file_path = upload_path / filename

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Check file size
        if file_size > ImageProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {ImageProcessor.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return filename, str(file_path), file_size

    @staticmethod
    def resize_image(
        image_path: str,
        target_size: Tuple[int, int],
        output_path: Optional[str] = None,
        quality: int = 85
    ) -> str:
        """
        Resize image to target dimensions.

        Args:
            image_path: Path to source image
            target_size: Target (width, height)
            output_path: Output path (if None, overwrites source)
            quality: JPEG quality (1-100)

        Returns:
            Path to resized image
        """
        if not output_path:
            output_path = image_path

        with Image.open(image_path) as img:
            # Convert RGBA to RGB for JPEG
            if img.mode == 'RGBA' and Path(output_path).suffix.lower() in {'.jpg', '.jpeg'}:
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            # Resize with maintaining aspect ratio
            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

            # Save with optimization
            save_kwargs = {'optimize': True}
            if Path(output_path).suffix.lower() in {'.jpg', '.jpeg'}:
                save_kwargs['quality'] = quality
                save_kwargs['format'] = 'JPEG'

            img.save(output_path, **save_kwargs)

        return output_path

    @staticmethod
    def create_thumbnails(
        image_path: str,
        output_dir: str,
        base_name: str
    ) -> dict[str, str]:
        """
        Create thumbnails in different sizes.

        Returns:
            Dictionary mapping size name to file path
        """
        thumbnails = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for size_name, dimensions in ImageProcessor.THUMBNAIL_SIZES.items():
            thumbnail_filename = f"{base_name}_{size_name}.jpg"
            thumbnail_path = output_path / thumbnail_filename

            ImageProcessor.resize_image(
                image_path,
                dimensions,
                str(thumbnail_path),
                quality=80
            )

            thumbnails[size_name] = str(thumbnail_path)

        return thumbnails

    @staticmethod
    def optimize_image(image_path: str, quality: int = 85) -> None:
        """Optimize image for web usage."""
        with Image.open(image_path) as img:
            # Check if image is too large
            if img.width > ImageProcessor.MAX_DIMENSIONS[0] or img.height > ImageProcessor.MAX_DIMENSIONS[1]:
                img = ImageOps.fit(img, ImageProcessor.MAX_DIMENSIONS, Image.Resampling.LANCZOS)

            # Convert RGBA to RGB for JPEG
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            # Save optimized
            img.save(image_path, 'JPEG', quality=quality, optimize=True)

    @staticmethod
    async def delete_file(file_path: str) -> bool:
        """Delete file from disk."""
        try:
            await aiofiles.os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @staticmethod
    async def delete_product_images(product_id: int, upload_dir: str) -> None:
        """Delete all images associated with a product."""
        # Delete main image and thumbnails
        patterns = [
            f"product_{product_id}.*",
            f"product_{product_id}_small.*",
            f"product_{product_id}_medium.*",
            f"product_{product_id}_large.*"
        ]

        upload_path = Path(upload_dir)
        if upload_path.exists():
            for pattern in patterns:
                for file_path in upload_path.glob(pattern):
                    await ImageProcessor.delete_file(str(file_path))


class ImageUploadService:
    """Service for handling image uploads."""

    def __init__(self):
        self.upload_dir = getattr(settings, 'UPLOAD_DIR', 'uploads/products')
        self.base_url = settings.base_url

    async def upload_product_image(
        self,
        product_id: int,
        file: UploadFile,
        create_thumbnails: bool = True
    ) -> dict[str, str]:
        """
        Upload and process product image.

        Returns:
            Dictionary with image URLs
        """
        # Generate filename
        filename = ImageProcessor.generate_unique_filename(
            file.filename or "image.jpg",
            f"product_{product_id}"
        )

        # Save original file
        saved_filename, file_path, file_size = await ImageProcessor.save_uploaded_file(
            file, self.upload_dir, filename
        )

        # Optimize main image
        ImageProcessor.optimize_image(file_path)

        # Create result
        result = {
            'original': f"{self.base_url}/{self.upload_dir}/{saved_filename}",
            'file_size': file_size
        }

        # Create thumbnails if requested
        if create_thumbnails:
            base_name = Path(saved_filename).stem
            thumbnails = ImageProcessor.create_thumbnails(
                file_path,
                self.upload_dir,
                base_name
            )

            for size_name, thumb_path in thumbnails.items():
                thumb_filename = Path(thumb_path).name
                result[size_name] = f"{self.base_url}/{self.upload_dir}/{thumb_filename}"

        return result

    async def delete_product_image(self, product_id: int) -> bool:
        """Delete all images for a product."""
        await ImageProcessor.delete_product_images(product_id, self.upload_dir)
        return True
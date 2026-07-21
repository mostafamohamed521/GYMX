"""
Shared file-upload validators used across the project wherever a person can upload
a document (resumes, contracts, certifications, member documents).

Without these, any authenticated OR anonymous user (job applications are public!)
could upload an executable, script, or oversized file to the server.
"""
import os
from django.core.exceptions import ValidationError

# Extensions allowed for general "document" uploads (CVs, contracts, certificates)
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx']
MAX_DOCUMENT_SIZE_MB = 5

# Extensions allowed for image uploads (profile photos, gallery, logos)
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
MAX_IMAGE_SIZE_MB = 5


def validate_document_file(file):
    """Use on FileField(validators=[validate_document_file]) for CVs, contracts, certs."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed types: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}."
        )
    max_bytes = MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"File too large. Maximum size is {MAX_DOCUMENT_SIZE_MB}MB.")


def validate_image_file(file):
    """Use alongside ImageField for an extra explicit extension/size check.
    (ImageField already verifies the file is a real image via Pillow, but this
    adds an extension whitelist and a clear size cap.)"""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image type '{ext}'. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
        )
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"Image too large. Maximum size is {MAX_IMAGE_SIZE_MB}MB.")

import pytest

from app.services.product_image_validation import has_image_signature


@pytest.mark.parametrize(
    ("content_type", "data"),
    [
        ("image/jpeg", b"\xff\xd8\xff" + b"\x00" * 9),
        ("image/png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 4),
        ("image/webp", b"RIFF\x00\x00\x00\x00WEBP"),
    ],
)
def test_accepts_supported_image_signatures(content_type, data):
    assert has_image_signature(content_type, data)


@pytest.mark.parametrize(
    ("content_type", "data"),
    [
        ("image/jpeg", b"\x89PNG\r\n\x1a\n"),
        ("image/png", b"\xff\xd8\xff"),
        ("image/webp", b"RIFF\x00\x00\x00\x00NOPE"),
        ("image/gif", b"GIF89a"),
    ],
)
def test_rejects_mismatched_or_unsupported_signatures(content_type, data):
    assert not has_image_signature(content_type, data)

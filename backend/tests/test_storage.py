import pytest

from app.providers.errors import ProviderError
from app.providers.storage.local import LocalStorageProvider


@pytest.mark.asyncio
async def test_local_storage_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()

    provider = LocalStorageProvider()
    data = b"fake-image-bytes"
    path = await provider.upload(
        user_id="user-1",
        scan_id="scan-1",
        data=data,
        content_type="image/jpeg",
    )
    assert path == "user-1/scan-1.jpg"
    downloaded = await provider.download(path)
    assert downloaded == data

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_local_storage_missing_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()

    provider = LocalStorageProvider()
    with pytest.raises(ProviderError, match="not found"):
        await provider.download("missing/path.jpg")

    get_settings.cache_clear()

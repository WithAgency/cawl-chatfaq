"""Compare a Playwright screenshot with the committed baseline."""

import logging
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from pixelmatch.contrib.PIL import pixelmatch

logger = logging.getLogger(__name__)

SNAPSHOTS_DIRECTORY = Path(__file__).resolve().parents[1] / "__snapshots__"


@pytest.fixture
def assert_snapshot(pytestconfig: pytest.Config) -> Callable[..., Image.Image | None]:
    def compare(
        image_data: bytes,
        name: str,
        *,
        threshold: float = 0.2,
        max_diff_fraction: float = 0.0,
    ) -> Image.Image | None:
        SNAPSHOTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        file = SNAPSHOTS_DIRECTORY / name
        if pytestconfig.getoption("--update-snapshots"):
            file.write_bytes(image_data)
            return None
        if not file.exists():
            raise AssertionError(
                f"Snapshot {name} is missing. Run pytest with --update-snapshots."
            )

        old_image = Image.open(file).convert("RGBA")
        new_image = Image.open(BytesIO(image_data)).convert("RGBA")
        diff = pixelmatch(old_image, new_image, threshold=threshold)
        allowance = int(old_image.size[0] * old_image.size[1] * max_diff_fraction)
        if diff > allowance:
            logger.error("Found a difference of %s pixels for %s", diff, name)
            return ImageChops.difference(old_image, new_image)
        return None

    return compare

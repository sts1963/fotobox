from pathlib import Path

from PIL import Image

from app.services.collage import CollageGenerator


def create_test_image(
    path: Path,
    size: tuple[int, int],
) -> None:
    image = Image.new(
        "RGB",
        size,
        "gray",
    )

    image.save(path)


def test_create_grid_2x2(
    tmp_path: Path,
) -> None:
    photo_paths = []

    for number in range(1, 4):
        path = (
            tmp_path
            / f"photo_{number:02d}.jpg"
        )

        create_test_image(
            path,
            (1280, 720),
        )

        photo_paths.append(path)

    output = (
        tmp_path
        / "collage.jpg"
    )

    generator = CollageGenerator(
        width=1800,
        height=1200,
    )

    result = generator.create_grid_2x2(
        photo_paths=photo_paths,
        output_path=output,
        logo_path=None,
    )

    assert result == output
    assert output.exists()

    collage = Image.open(output)

    assert collage.size == (
        1800,
        1200,
    )


def test_create_grid_with_logo(
    tmp_path: Path,
) -> None:
    photo_paths = []

    for number in range(1, 4):
        path = (
            tmp_path
            / f"photo_{number:02d}.jpg"
        )

        create_test_image(
            path,
            (1280, 720),
        )

        photo_paths.append(path)

    logo = (
        tmp_path
        / "logo.png"
    )

    logo_image = Image.new(
        "RGBA",
        (500, 200),
        (0, 0, 0, 255),
    )

    logo_image.save(logo)

    output = (
        tmp_path
        / "collage.jpg"
    )

    generator = CollageGenerator()

    generator.create_grid_2x2(
        photo_paths=photo_paths,
        output_path=output,
        logo_path=logo,
    )

    assert output.exists()


def test_center_crop_size() -> None:
    processor = CollageGenerator().processor

    image = Image.new(
        "RGB",
        (1280, 720),
    )

    result = processor.fit_center_crop(
        image,
        864,
        564,
    )

    assert result.size == (
        864,
        564,
    )


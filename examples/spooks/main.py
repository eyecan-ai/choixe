from pathlib import Path
import tempfile
from abc import ABC, abstractmethod
from choixe.configurations import XConfig
import rich
from typing import Sequence
from choixe.spooks import Spook


class MyImageABC(ABC, Spook):
    def __init__(self, name: str, image_size: Sequence[int]) -> None:
        super().__init__()
        self._name = name
        self._image_size = image_size

    @classmethod
    def spook_schema(cls) -> dict:
        return {"name": str, "image_size": [int, int]}

    # Works with abstract classes too
    @abstractmethod
    def my_method(self) -> None:
        pass

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def to_dict(self) -> dict:
        return {"name": self._name, "image_size": self._image_size}


class MyImage(MyImageABC):
    def my_method(self) -> None:
        print("Hello")


class MyBundle(Spook):
    def __init__(self, name: str, images: Sequence[MyImage]) -> None:
        super().__init__()
        self._name = name
        self._images = images

    @property
    def images(self) -> Sequence[MyImage]:
        return self._images

    @classmethod
    def spook_schema(cls) -> dict:
        return {"name": str, "images": [MyImage.full_spook_schema()]}

    @classmethod
    def from_dict(cls, d: dict):
        return MyBundle(name=d["name"], images=[Spook.create(x) for x in d["images"]])

    def to_dict(self) -> dict:
        return {"name": self._name, "images": [x.serialize() for x in self._images]}


# Create Object
bundle = MyBundle(
    name="custom_bundle",
    images=[
        MyImage(name="image", image_size=[800, 600]),
        MyImage(name="mask", image_size=[256, 256]),
        MyImage(name="crop", image_size=[32, 32]),
    ],
)


# Serialization
bundle_serialized = bundle.serialize()
rich.print("Serialized object:", bundle_serialized)

# IO Write
cfg = XConfig.from_dict(bundle_serialized)
cfg_filename = Path(tempfile.mkdtemp()) / "cfg.yml"
cfg.save_to(cfg_filename)
rich.print("Stored config in:", cfg_filename)

# IO Read
cfg = XConfig(filename=cfg_filename)
hydrated_bundle: MyBundle = Spook.create(cfg)
rich.print("Hydrated object:", hydrated_bundle.serialize())

for image in hydrated_bundle.images:
    image.my_method()

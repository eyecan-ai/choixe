from choixe.configurations import XConfig
from rich import print

cfg = XConfig(filename="cfg.yml")
print(cfg.to_dict())

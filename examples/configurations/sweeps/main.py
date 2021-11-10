from choixe.configurations import XConfig
import rich
import tempfile
from pathlib import Path

cfg = XConfig(filename="cfg.yml")

# Create sweeps from single cfg
sweeped_cfgs = cfg.sweep()

folder = Path(tempfile.mkdtemp())
for idx, cfg in enumerate(sweeped_cfgs):
    rich.print("Sweep", "-" * 10)
    rich.print(cfg)
    filename = folder / f"sweep_{str(idx).zfill(5)}.yml"
    cfg.save_to(filename=filename)

rich.print("Output saved to:", folder)

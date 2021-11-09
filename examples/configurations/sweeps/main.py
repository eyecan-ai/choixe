from choixe.configurations import XConfig
import rich

from choixe.placeholders import Placeholder
from choixe.sweepers import Sweeper

cfg = XConfig(filename="cfg.yml")

sweeped_cfgs = cfg.sweep()
rich.print(sweeped_cfgs)

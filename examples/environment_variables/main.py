from choixe.configurations import XConfig
import rich


cfg = XConfig(filename='cfg.yml')
cfg.check_available_placeholders(close_app=True)
rich.print(cfg.to_dict())

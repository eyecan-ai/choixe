import rich
from choixe.configurations import XConfig
from choixe.inquirer import XInquirer


cfg = XConfig(filename='cfg.yml')

# Checks for placeholders before replace
rich.print("\nBefore Replace", cfg.to_dict())
cfg.check_available_placeholders(close_app=False)

new_cfg = XInquirer.prompt(cfg)

# Checks for placeholders after replace
rich.print("\nAfter Replace", new_cfg.to_dict())
new_cfg.check_available_placeholders(close_app=True)
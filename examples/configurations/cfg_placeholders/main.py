from choixe.configurations import XConfig
import rich

cfg = XConfig(filename='cfg.yml')

# Checks for placeholders before replace
rich.print("\nBefore Replace", cfg.to_dict())
cfg.check_available_placeholders(close_app=False)

# Iterate Placeholders
placeholders = cfg.available_placeholders()
for key, p in placeholders.items():
    # Replace default value if any
    if p.default_value is not None:
        cfg.replace_variable(p.name, p.default_value)  # Replace automatically Casts for CFG

# Checks for placeholders after replace
rich.print("\nAfter Replace", cfg.to_dict())

# Checks for placeholders after replace
cfg.deep_parse()
rich.print("\nAfter Second Deep Parse", cfg.to_dict())

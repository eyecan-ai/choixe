from choixe.configurations import XConfig
import rich


cfg = XConfig(filename="cfg.yml")

# Checks for placeholders before replace
rich.print("\nBefore Replace", cfg.to_dict())
cfg.check_available_placeholders(close_app=False)

# Iterate Placeholders
placeholders = cfg.available_placeholders()
for key, p in placeholders.items():
    rich.print("Placeholder:")
    rich.print("\tName:", p.name)
    rich.print("\tType:", p.type)
    rich.print("\tDefault:", p.default_value)

    # Replace default value if any
    if p.default_value is not None:
        cfg.replace_variable(p.name, p.default_value)

# Checks for placeholders after replace
rich.print("\nAfter Replace", cfg.to_dict())
cfg.check_available_placeholders(close_app=True)

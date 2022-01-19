from choixe.configurations import XConfig
import rich

cfg = XConfig(filename="cfg.yml")
for k, v in cfg.flatten().items():
    rich.print(f"[green]{k}[/green]", f"[red]{v}[/red]")

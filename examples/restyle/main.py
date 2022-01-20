from typing import Optional, Sequence
import re
import rich


class Directive:
    def __init__(self, match: re.Match):
        self._groupdict = match.groupdict()
        assert DirectivesParser.GROUP_DIRECTIVE_LABEL in self._groupdict
        assert DirectivesParser.GROUP_DIRECTVIE_CONTENT in self._groupdict
        self._label = self._groupdict[DirectivesParser.GROUP_DIRECTIVE_LABEL]
        self._content = self._groupdict[DirectivesParser.GROUP_DIRECTVIE_CONTENT]
        self._args = [x.strip() for x in self._content.split(",")]
        self._kwargs = list(filter(lambda x: "=" in x, self._args))
        self._args = list(filter(lambda x: "=" not in x, self._args))
        self._kwargs = {
            k.strip(): v.strip() for k, v in [x.split("=") for x in self._kwargs]
        }

    @property
    def label(self) -> str:
        return self._label

    @property
    def args(self) -> list:
        return self._args

    @property
    def kwargs(self) -> dict:
        return self._kwargs

    def dict(self) -> dict:
        return {
            "label": self._label,
            "args": self._args,
            "kwargs": self._kwargs,
        }


class DirectivesParser:
    DEFAULT_TRIGGER = "\$"
    GROUP_DIRECTIVE_LABEL = "label"
    GROUP_DIRECTVIE_CONTENT = "content"
    DIRECTIVE_REGEX = "{trigger}(?P<{label}>\w*)\((?P<{content}>[^)]+)\)"

    def __init__(self, trigger: Optional[str] = DEFAULT_TRIGGER):
        self._regex = DirectivesParser.DIRECTIVE_REGEX.format(
            trigger=trigger,
            label=DirectivesParser.GROUP_DIRECTIVE_LABEL,
            content=DirectivesParser.GROUP_DIRECTVIE_CONTENT,
        )
        self._re = re.compile(self._regex)

    def parse(self, s: str, allow_multiple: bool = True) -> Sequence[Directive]:
        directives = [Directive(match) for match in self._re.finditer(s)]
        if not allow_multiple and len(directives) > 1:
            raise ValueError(f"Multiple directives found in string: {s}")
        return directives


class DirectiveUser:
    def __init__(self, directive: Directive) -> None:
        self._directive = directive

    @property
    def directive(self) -> Directive:
        return self._directive


class Placeholder(DirectiveUser):
    def __init__(self, directive: Directive) -> None:
        super().__init__(directive)

    # @property
    # def name(self)->str:
    #     return


parser = DirectivesParser()
for p in parser.parse("$foo(bar), $miao(sadas,xsa = [3], dask,dsa  , d=2)"):
    rich.print(p.dict())

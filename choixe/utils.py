from typing import Any, Dict, List, Optional, Sequence, Tuple


class DictionaryWalker:
    @classmethod
    def flatten_as_lists(
        cls,
        d: dict,
        discard_keys: Optional[Sequence[str]] = None,
    ) -> Sequence[Tuple[List[str], Any]]:
        return cls.walk(d, discard_keys=discard_keys)

    @classmethod
    def flatten_as_tuples(
        cls,
        d: dict,
        discard_keys: Optional[Sequence[str]] = None,
    ) -> Sequence[Tuple[Tuple[str], Any]]:
        return [(tuple(x), y) for x, y in cls.walk(d, discard_keys=discard_keys)]

    @classmethod
    def flatten_as_dicts(
        cls,
        d: dict,
        discard_keys: Optional[Sequence[str]] = None,
    ) -> Sequence[Tuple[str, Any]]:

        return [
            (".".join(x), y)
            for x, y in cls.flatten_as_lists(d, discard_keys=discard_keys)
        ]

    @classmethod
    def flatten(
        cls,
        d: dict,
        discard_keys: Optional[Sequence[str]] = None,
    ) -> dict:

        return {k: v for k, v in cls.flatten_as_dicts(d, discard_keys=discard_keys)}

    @classmethod
    def walk(
        cls,
        d: Dict,
        path: Sequence = None,
        chunks: Sequence = None,
        discard_keys: Optional[Sequence[str]] = None,
    ) -> Sequence[Tuple[str, Any]]:
        """Deep visit of dictionary building a plain sequence of pairs(key, value) where key has a pydash notation
        : param d: input dictionary
        : type d: Dict
        : param path: private output value for path(not use), defaults to None
        : type path: Sequence, optional
        : param chunks: private output to be fileld with retrieved pairs(not use), defaults to None
        : type chunks: Sequence, optional
        : param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        : type discard_private_qualifiers: bool, optional
        : return: sequence of retrieved pairs
        : rtype: Sequence[Tuple[str, Any]]
        """

        discard_keys = discard_keys if discard_keys is not None else []
        root = False
        if path is None:
            path, chunks, root = [], [], True
        if isinstance(d, dict):
            for k, v in d.items():
                path.append(k)
                if isinstance(v, dict) or isinstance(v, list):
                    cls.walk(
                        v,
                        path=path,
                        chunks=chunks,
                        discard_keys=discard_keys,
                    )
                else:
                    keys = list(map(str, path))
                    if not (
                        len(discard_keys) > 0
                        and any([x for x in discard_keys if x in keys])
                    ):
                        chunks.append((keys, v))
                path.pop()
        elif isinstance(d, list):
            for idx, v in enumerate(d):
                path.append(idx)
                cls.walk(
                    v,
                    path=path,
                    chunks=chunks,
                    discard_keys=discard_keys,
                )
                path.pop()
        else:
            keys = list(map(str, path))
            chunks.append((keys, d))
        if root:
            return chunks

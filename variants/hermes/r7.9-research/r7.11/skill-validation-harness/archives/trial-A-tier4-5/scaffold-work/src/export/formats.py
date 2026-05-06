from typing import Protocol, List, Dict, Union

class Serializer(Protocol):
    def __call__(self, records: List[Dict]) -> Union[str, bytes]:
        ...

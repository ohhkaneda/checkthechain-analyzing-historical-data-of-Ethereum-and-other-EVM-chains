import typing


BinaryData = typing.Union[bytes, str]
BinaryInteger = typing.Union[int, BinaryData]
BlockSpec = typing.Union[
    int, BinaryData, typing.Literal['latest', 'earliest', 'pending']
]


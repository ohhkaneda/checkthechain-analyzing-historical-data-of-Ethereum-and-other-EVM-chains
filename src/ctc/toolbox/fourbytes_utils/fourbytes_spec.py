from __future__ import annotations

import os

from typing_extensions import TypedDict


root_url = 'https://www.4byte.directory'

endpoints = {
    'events': root_url + '/api/v1/event-signatures/',
    'functions': root_url + '/api/v1/signatures/',
}


class Entry(TypedDict):
    id: int
    created_at: str
    text_signature: str
    hex_signature: str
    bytes_signature: str


def get_default_path(datatype: str) -> str:
    import ctc.config

    return os.path.join(
        ctc.config.get_data_dir(),
        '4bytes',
        datatype + '.json',
    )


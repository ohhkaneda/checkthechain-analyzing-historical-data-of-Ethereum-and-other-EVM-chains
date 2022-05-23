from __future__ import annotations

import toolcli

from ctc import binary
from ctc import rpc
from ctc import spec


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': async_storage_command,
        'help': 'get value of storage slot',
        'args': [
            {'name': 'contract_address', 'help': 'address of contract'},
            {'name': 'slot', 'help': 'address of storage slot'},
            {'name': '--block', 'help': 'block number'},
            {
                'name': '--type',
                'help': 'decode data using this datatype',
                'dest': 'datatype',
            },
        ],
    }


async def async_storage_command(
    contract_address: str,
    slot: str,
    block: spec.BlockNumberReference | None,
    datatype: str | None,
) -> None:
    result = await rpc.async_eth_get_storage_at(
        contract_address,
        position=slot,
        block_number=block,
    )
    if datatype is None:
        print(result)
    else:
        as_bytes = binary.convert(result, 'binary')
        decoded = binary.decode_types(as_bytes, datatype)
        print(decoded)

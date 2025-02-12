from __future__ import annotations

import typing

from ctc import rpc
from ctc import spec

from . import connect_utils
from . import management
from . import schemas


if typing.TYPE_CHECKING:
    T = typing.TypeVar('T', int, spec.RPCBlock, spec.DBBlock)


async def async_is_block_fully_confirmed(
    block: int,
    *,
    context: spec.Context = None,
) -> bool:

    # check whether block is older than newest block in db
    max_db_block = await _async_get_max_block_number_in_db(context=context)
    if max_db_block is not None and block < max_db_block:
        return True

    # check whether block has enough confirmations
    rpc_latest_block = await rpc.async_eth_block_number(context=context)
    required_confirmations = management.get_required_confirmations(
        context=context
    )
    return bool(block <= rpc_latest_block - required_confirmations)


async def async_filter_fully_confirmed_blocks(
    blocks: typing.Sequence[T],
    *,
    context: spec.Context,
    latest_block_number: int | None = None,
) -> typing.Sequence[T]:

    if len(blocks) == 0:
        return []

    block_numbers = []
    for block in blocks:
        if isinstance(block, dict):
            block_numbers.append(block['number'])
        elif isinstance(block, int):
            block_numbers.append(block)
        else:
            raise Exception('unknown block format')

    # check whether all blocks older than newest block in db
    max_block_number = max(block_numbers)
    if latest_block_number is not None:
        max_db_block: int | None = latest_block_number
    else:
        max_db_block = await _async_get_max_block_number_in_db(context=context)
    if max_db_block is not None and max_db_block > max_block_number:
        return blocks

    # check whether blocks have enough confirmations
    if latest_block_number is not None:
        rpc_latest_block = latest_block_number
    else:
        rpc_latest_block = await rpc.async_eth_block_number(context=context)
    required_confirmations = management.get_required_confirmations(
        context=context,
    )
    max_allowed_block = rpc_latest_block - required_confirmations
    return [
        block
        for block, block_number in zip(blocks, block_numbers)
        if block_number <= max_allowed_block
    ]


async def _async_get_max_block_number_in_db(
    context: spec.Context = None,
) -> int | None:
    engine = connect_utils.create_engine(
        schema_name='block_timestamps',
        context=context,
    )
    if engine is None:
        raise Exception('could not connect to database')
    with engine.begin() as conn:
        return await schemas.async_select_max_block_number(
            conn=conn, context=context
        )


from __future__ import annotations

import copy
import typing

import toolsql

from ctc import config
from ctc import spec
from ctc.spec.typedefs import db_types

from . import schemas


def get_admin_schema_names() -> tuple[db_types.AdminSchemaName]:
    return db_types.AdminSchemaName.__args__  # type: ignore


def get_generic_schema_names() -> tuple[db_types.GenericSchemaName]:
    return db_types.GenericSchemaName.__args__  # type: ignore


def get_network_schema_names() -> tuple[db_types.NetworkSchemaName]:
    return db_types.NetworkSchemaName.__args__  # type: ignore


def get_all_schema_names() -> typing.Sequence[db_types.SchemaName]:
    schema_names = (
        get_admin_schema_names()
        + get_generic_schema_names()
        + get_network_schema_names()
    )
    return typing.cast(typing.Sequence[db_types.SchemaName], schema_names)


def get_raw_schema(schema_name: str) -> toolsql.DBSchema:
    if schema_name == 'block_timestamps':
        return schemas.block_timestamps_schema
    elif schema_name == 'block_gas':
        return schemas.block_gas_schema
    elif schema_name == 'blocks':
        return schemas.blocks_schema
    elif schema_name == 'contract_abis':
        return schemas.contract_abis_schema
    elif schema_name == 'contract_creation_blocks':
        return schemas.contract_creation_blocks_schema
    elif schema_name == 'dex_pools':
        return schemas.dex_pools_schema
    elif schema_name == 'erc20_metadata':
        return schemas.erc20_metadata_schema
    elif schema_name == 'events':
        return schemas.events_schema
    # elif schema_name == 'erc20_state':
    #     return schemas.erc20_state_schema
    elif schema_name == 'schema_versions':
        return schemas.schema_versions_schema
    elif schema_name == 'transactions':
        return schemas.transactions_schema
    #
    # # protocols
    #
    elif schema_name == '4byte':
        from ctc.protocols import fourbyte_utils

        return fourbyte_utils.fourbyte_schema
    elif schema_name == 'chainlink':
        from ctc.protocols.chainlink_utils import chainlink_db

        return chainlink_db.chainlink_schema
    elif schema_name == 'coingecko':
        from ctc.protocols.coingecko_utils import coingecko_db

        return coingecko_db.coingecko_schema
    else:
        raise Exception('unknown schema: ' + str(schema_name))


def get_prepared_schema(
    schema_name: str,
    context: spec.Context = None,
) -> toolsql.DBSchema:

    # get schema
    schema = get_raw_schema(schema_name)
    schema = copy.deepcopy(schema)

    # add network to table name
    for table_name, table in list(schema['tables'].items()):
        full_name = get_table_name(context=context, table_name=table_name)
        if table.get('name') is not None:
            table['name'] = full_name
        schema['tables'][full_name] = schema['tables'].pop(table_name)  # type: ignore

    return schema


def get_table_name(
    table_name: str,
    context: spec.Context = None,
) -> str:
    """get full table name, incorporating chain information"""
    chain_id = config.get_context_chain_id(context)
    return 'network_' + str(chain_id) + '__' + table_name


def get_schema_of_raw_table(table: str) -> spec.SchemaName:

    candidates = []
    for schema_name in get_all_schema_names():
        raw_schema = get_raw_schema(schema_name)
        for schema_table in raw_schema['tables'].keys():
            if table == schema_table:
                candidates.append(schema_name)

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) == 0:
        raise Exception('could not find any schema containing table ' + str(table))
    else:
        raise Exception('found multiple schemas containing table ' + str(table))


def get_complete_prepared_schema(
    networks: typing.Sequence[spec.NetworkReference] | None = None,
) -> toolsql.DBSchema:

    # include network schemas
    if networks is None:
        networks = config.get_networks_that_have_providers()
    schema_name: db_types.SchemaName
    all_schemas = []
    for network in networks:
        for schema_name in get_network_schema_names():
            schema = get_prepared_schema(
                context=dict(network=network), schema_name=schema_name
            )
            all_schemas.append(schema)

    # include generic schemas
    for schema_name in get_generic_schema_names():
        schema = get_raw_schema(schema_name)
        all_schemas.append(schema)

    # include admin schemas
    for schema_name in get_admin_schema_names():
        schema = get_raw_schema(schema_name)
        all_schemas.append(schema)

    return _combine_db_schemas(all_schemas)


def _combine_db_schemas(
    db_schemas: typing.Sequence[toolsql.DBSchema],
) -> toolsql.DBSchema:
    tables: typing.MutableMapping[str, toolsql.TableSpec] = {}
    for db_schema in db_schemas:
        for table_name, table_spec in db_schema.get('tables', {}).items():
            if table_name in tables:
                raise Exception('table name collision')
            tables[table_name] = table_spec
    combined_schema: toolsql.DBSchema = {'tables': tables}
    return combined_schema


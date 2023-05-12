import sqlite3
import argparse
import yaml
import logging
from pathlib import Path


def add_tables(db_cursor: sqlite3.Cursor):
    """
    Creates the telemetry and commands tables needed for the database.
    :param db_cursor: The cursor database handle.
    :return:
    """
    db_cursor.execute('create table if not exists modules('
                      'id INTEGER primary key,'
                      'name TEXT UNIQUE NOT NULL,'
                      'parent_module INTEGER,'
                      'FOREIGN KEY (parent_module) REFERENCES modules(id),'
                      'UNIQUE (name)'
                      ');')

    db_cursor.execute('create table if not exists telemetry('
                      'id INTEGER primary key, '
                      'name TEXT UNIQUE NOT NULL, '
                      'message_id INTEGER NOT NULL, '
                      'macro TEXT,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'min_rate INTEGER,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id), '
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, message_id, module)'
                      ');')

    db_cursor.execute('create table if not exists commands('
                      'id INTEGER primary key,'
                      'name TEXT NOT NULL,'
                      'command_code INTEGER NOT NULL,'
                      'message_id INTEGER NOT NULL,'
                      'macro TEXT,'
                      'symbol INTEGER NOT NULL, '
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, command_code, module, message_id));')

    db_cursor.execute('create table if not exists events('
                      'id INTEGER primary key,'
                      'event_id INTEGER,'
                      'name TEXT,'
                      'module INTEGER,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (event_id, module));')

    db_cursor.execute('create table if not exists configurations('
                      'id INTEGER primary key,'
                      'name TEXT NOT NULL,'
                      'value INTEGER,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, module));')

    db_cursor.execute('create table if not exists performance_ids('
                      'id INTEGER primary key,'
                      'name TEXT,'
                      'perf_id INTEGER NOT NULL,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, perf_id, module));')

    db_cursor.execute('create table if not exists algorithms('
                      'id INTEGER primary key,'
                      'name TEXT NOT NULL,'
                      'language TEXT NOT NULL,'
                      'script_path TEXT,'
                      'type TEXT,'
                      'module INTEGER NOT NULL,'
                      'FOREIGN KEY (module) REFERENCES modules(id),'
                      'UNIQUE (name, module));')

    db_cursor.execute('create table if not exists algorithm_triggers('
                      'id INTEGER primary key,'
                      'parameter_ref TEXT NOT NULL,'
                      'algorithm INTEGER NOT NULL,'
                      'FOREIGN KEY (algorithm) REFERENCES algorithms(id),'
                      'UNIQUE (parameter_ref, algorithm));')

    db_cursor.execute('create table if not exists algorithm_inputs('
                      'id INTEGER primary key,'
                      'parameter_ref TEXT NOT NULL,'
                      'input_name TEXT NOT NULL,'
                      'algorithm INTEGER NOT NULL,'
                      'FOREIGN KEY (algorithm) REFERENCES algorithms(id),'
                      'UNIQUE (parameter_ref, algorithm));')

    db_cursor.execute('create table if not exists algorithm_outputs('
                      'id INTEGER primary key,'
                      'parameter_ref TEXT NOT NULL,'
                      'output_name TEXT NOT NULL,'
                      'description TEXT NOT NULL,'
                      'algorithm INTEGER NOT NULL,'
                      'type INTEGER NOT NULL,'
                      'FOREIGN KEY (algorithm) REFERENCES algorithms(id),'
                      'FOREIGN KEY (type) REFERENCES symbols(id),'
                      'UNIQUE (parameter_ref, algorithm));')

    # db_cursor.execute('create table if not exists algorithm_aggregates('
    #                   'id INTEGER primary key,'
    #                   'name TEXT NOT NULL,'
    #                   'algorithm INTEGER NOT NULL,'
    #                   'FOREIGN KEY (algorithm) REFERENCES algorithms(id),'
    #                   'UNIQUE (name, algorithm));')
    #
    # db_cursor.execute('create table if not exists algorithm_aggregates_fields('
    #                   'id INTEGER primary key,'
    #                   'name TEXT NOT NULL,'
    #                   'type TEXT NOT NULL,'
    #                   'algorithm INTEGER NOT NULL,'
    #                   'FOREIGN KEY (algorithm) REFERENCES algorithms(id),'
    #                   'FOREIGN KEY (type) REFERENCES algorithm_aggregates(id),'
    #                   'UNIQUE (name, algorithm));')



def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


# FIXME:It looks like we don't use this function. We should remove it.
def get_module_id(module_name: str, db_cursor: sqlite3.Cursor) -> tuple:
    """
    Fetches the id of the module whose name module_name
    :param module_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    module_id = db_cursor.execute('SELECT * FROM modules where name =?',
                                  (module_name,))

    # FIXME: This is a possible approach to take when the module does not exist. Will re-address in the future.
    # if module_id is None:
    #     db_cursor.execute('INSERT INTO modules(name) '
    #                       'values(?)',
    #                       (module_name,))
    #     logging.warning(f'{module_name} module was added to the database.')

    # module_id = db_cursor.execute('SELECT * FROM modules where name =?',
    #                               (module_name,)).fetchone()

    return module_id.fetchone()


def get_symbol_id(symbol_name: str, db_cursor: sqlite3.Cursor) -> tuple:
    """
    Fetches the id of the symbol whose name symbol_name
    :param symbol_name: The name of the module as it appears in the database.
    :param db_cursor: The cursor that points to the databse.
    :return: The module id.
    """
    symbol_id = db_cursor.execute('SELECT * FROM symbols where name =?',
                                  (symbol_name,))
    return symbol_id.fetchone()


def write_module_records(module_data: dict, db_cursor, parent_module: str = None):
    """
    Scans module_data and writes each module to the database..
    :param parent_module:
    :param module_data:
    :param db_cursor:
    :return:
    """

    for module in module_data['modules']:
        if parent_module:
            try:
                db_cursor.execute('insert into modules(name, parent_module) values(?,?)',
                                  (module, get_module_id(parent_module, db_cursor)[0]))
            except sqlite3.IntegrityError:
                logging.warning(
                    f'The module "{module}" was not added. This is most likely due to trying to add it twice'
                    f' to the datbase. Please revise your configuration file. ')
        else:
            try:
                db_cursor.execute('insert into modules(name) values(?)', (module,))
            except sqlite3.IntegrityError:
                logging.warning(
                    f'The module "{module}" was not added. This is most likely due to trying to add it twice'
                    f' to the datbase. Please revise your configuration file. ')

        if 'modules' in module_data['modules'][module]:
            write_module_records(module_data['modules'][module], db_cursor, module)


def write_telemetry_records(telemetry_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans telemetry_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param telemetry_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    if telemetry_data['modules'] is None:
        # This has a 'modules' key, but its empty.  Skip it.
        pass
    else:
        for module_name in telemetry_data['modules']:
            if 'telemetry' in telemetry_data['modules'][module_name]:
                if telemetry_data['modules'][module_name]['telemetry'] is None:
                    # This has a 'telemetry' key, but its empty.  Skip it.
                    pass
                else:
                    for message in telemetry_data['modules'][module_name]['telemetry']:
                        message_id = None
                        symbol = None
                        message_dict = telemetry_data['modules'][module_name]['telemetry'][message]
                        name = message
                        min_rate = None

                        # Check for empty values
                        # FIXME: This logic is starting to look convoluted. The schema might help with this.
                        if 'msgID' in message_dict:
                            if message_dict['msgID'] is None:
                                logging.error(
                                    f"modules.{module_name}.telemetry.{name}.msgID must not be empty. Skipping.")
                                continue
                            else:
                                message_id = message_dict['msgID']
                        else:
                            logging.error(f"modules.{module_name}.telemetry.{name}.msgID key must exist.  Skipping.")

                        if 'min_rate' in message_dict:
                            if message_dict['min_rate'] is None:
                                continue
                            else:
                                min_rate = message_dict['min_rate']

                        if 'struct' in message_dict:
                            if message_dict['struct'] is None:
                                logging.error(
                                    f"modules.{module_name}.telemetry.{name}.struct must not be empty. Skipping.")
                                continue
                            else:
                                symbol = get_symbol_id(message_dict['struct'], db_cursor)
                        else:
                            logging.error(f"modules.{module_name}.telemetry.{name}.struct key must exist. Skipping.")

                        # If the symbol does not exist, we skip it
                        if symbol is None:
                            logging.error(
                                f"modules.{module_name}.telemetry.{name}.struct could not be found.  Skipping.")
                        else:
                            symbol_id = symbol[0]

                            # FIXME:Is there a point to this statement?
                            macro = name

                            # Write our telemetry record to the database.
                            db_cursor.execute(
                                'INSERT INTO telemetry(name, message_id, macro, symbol, module, min_rate) '
                                'VALUES (?, ?, ?, ?, ?, ?)',
                                (name, message_id, macro, symbol_id, modules_dict[module_name], min_rate))

            if 'modules' in telemetry_data['modules'][module_name]:
                write_telemetry_records(telemetry_data['modules'][module_name], modules_dict, db_cursor)


def write_algorithm_triggers_records(algorithm_data: dict,
                                     algorithms_dict: dict,
                                     telemetry_dict: dict,
                                     db_cursor: sqlite3.Cursor):
    """
    Scans algorithm_data and writes it to the database. Please note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param algorithm_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    if algorithm_data['modules'] is None:
        # This has a 'modules' key, but its empty.  Skip it.
        pass
    else:
        for module_name in algorithm_data['modules']:
            if 'algorithms' in algorithm_data['modules'][module_name]:
                if algorithm_data['modules'][module_name]['algorithms'] is None:
                    # This has a 'algorithms' key, but its empty.  Skip it.
                    pass
                else:
                    for algorithm in algorithm_data['modules'][module_name]['algorithms']:
                        for trigger in algorithm_data['modules'][module_name]['algorithms'][algorithm]['triggers']:
                            parameter_ref = trigger['parameter_ref']
                            # Write our telemetry record to the database.
                            db_cursor.execute(
                                'INSERT INTO algorithm_triggers(parameter_ref, algorithm) '
                                'VALUES (?, ?)',
                                (parameter_ref, algorithms_dict[algorithm]))

            if 'modules' in algorithm_data['modules'][module_name]:
                write_algorithm_triggers_records(algorithm_data['modules'][module_name],
                                                 algorithms_dict,
                                                 telemetry_dict,
                                                 db_cursor)


def write_algorithm_inputs_records(algorithm_data: dict,
                                   algorithms_dict: dict,
                                   db_cursor: sqlite3.Cursor):
    """
    Scans algorithm_data and writes it to the database. Please note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param algorithm_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    if algorithm_data['modules'] is None:
        # This has a 'modules' key, but its empty.  Skip it.
        pass
    else:
        for module_name in algorithm_data['modules']:
            if 'algorithms' in algorithm_data['modules'][module_name]:
                if algorithm_data['modules'][module_name]['algorithms'] is None:
                    # This has a 'algorithms' key, but its empty.  Skip it.
                    pass
                else:
                    for algorithm in algorithm_data['modules'][module_name]['algorithms']:
                        for input in algorithm_data['modules'][module_name]['algorithms'][algorithm]['inputs']:
                            parameter_ref = input['parameter_ref']
                            input_name = input['input_name']
                            # Write our telemetry record to the database.
                            db_cursor.execute(
                                'INSERT INTO algorithm_inputs(parameter_ref, input_name, algorithm) '
                                'VALUES (?, ?, ?)',
                                (parameter_ref, input_name, algorithms_dict[algorithm]))

            if 'modules' in algorithm_data['modules'][module_name]:
                write_algorithm_inputs_records(algorithm_data['modules'][module_name],
                                               algorithms_dict,
                                               db_cursor)


def write_algorithm_outputs_records(algorithm_data: dict,
                                    algorithms_dict: dict,
                                    symbols_dict: dict,
                                    db_cursor: sqlite3.Cursor):
    """
    Scans algorithm_data and writes it to the database. Please note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param algorithm_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    if algorithm_data['modules'] is None:
        # This has a 'modules' key, but its empty.  Skip it.
        pass
    else:
        for module_name in algorithm_data['modules']:
            if 'algorithms' in algorithm_data['modules'][module_name]:
                if algorithm_data['modules'][module_name]['algorithms'] is None:
                    # This has a 'algorithms' key, but its empty.  Skip it.
                    pass
                else:
                    for algorithm in algorithm_data['modules'][module_name]['algorithms']:
                        for output in algorithm_data['modules'][module_name]['algorithms'][algorithm]['outputs']:
                            parameter_name = output['parameter']['name']
                            description = output['parameter']['description']
                            p_type_name = output['parameter']['type']
                            new_type_name = p_type_name
                            p_type = 0
                            if p_type_name in symbols_dict:
                                p_type = symbols_dict[p_type_name]
                                continue
                            else:
                                if p_type_name != 'aggregate':
                                    logging.error(f"type '{p_type} must be either'"
                                                  f" an intrinsic type:[int64, "
                                                  f"int32, "
                                                  f"int16, "
                                                  f"int8, "
                                                  f"int, "
                                                  f"uint8, "
                                                  f"uint16, "
                                                  f"uint32, "
                                                  f"unsigned int, "
                                                  f"unsigned, "
                                                  f"uint,"
                                                  f" char, "
                                                  f"boolean, "
                                                  f"float, "
                                                  f"double, "
                                                  f"string] or 'aggregate'")
                                    continue

                                new_type_name = module_name + '_' + parameter_name + '_' + p_type_name + "_t"
                                new_type_byte_size = 0
                                if new_type_name in symbols_dict:
                                    logging.warning(f"Reusing the algorithms type '{new_type_name}'")
                                    p_type = symbols_dict[new_type_name]


                                # At the moment only flat aggregates are supported
                                else:
                                    for member in output['parameter']['members']:
                                        symbol_id = symbols_dict[member['type']]
                                        member_size = db_cursor.execute('select byte_size from symbols where id=?', (symbol_id,)).fetchone()
                                        new_type_byte_size += member_size[0]
                                elf = -1 # This symbol does not really have an elf...need to figure out if this is the best way to do this.

                                # Write our event record to the database.
                                db_cursor.execute('INSERT INTO symbols(elf, name, byte_size) '
                                                  'VALUES (?, ?, ?)',
                                                  (elf, new_type_name, new_type_byte_size))

                                p_type = db_cursor.execute('select id from symbols where name=?', (new_type_name,)).fetchone()[0]

                                current_member_offset = 0
                                for member in output['parameter']['members']:
                                    member_name = member['name']
                                    member_type = member['type']
                                    symbol_id = db_cursor.execute('select id from symbols where name=?', (member_type,)).fetchone()[0]
                                    member_size = db_cursor.execute('select byte_size from symbols where id=?',
                                                                    (symbol_id,)).fetchone()

                                    db_cursor.execute('INSERT INTO fields(symbol, name, byte_offset, type, '
                                                      'little_endian, bit_size, bit_offset)'
                                                      'VALUES (?, ?, ?, ?, ?, ?, ?)',
                                                      (p_type, member_name, current_member_offset, symbol_id, 0, 0, 0))

                                    current_member_offset += member_size[0]

                            # Write our algorithm_outputs record to the database.
                            db_cursor.execute(
                                'INSERT INTO algorithm_outputs(parameter_ref, output_name, description, algorithm, type) '
                                'VALUES (?, ?, ?, ?, ?)',
                                (module_name + '_' + parameter_name + '_' + p_type_name , parameter_name, description, algorithms_dict[algorithm], p_type))

            if 'modules' in algorithm_data['modules'][module_name]:
                write_algorithm_outputs_records(algorithm_data['modules'][module_name],
                                                algorithms_dict,
                                                symbols_dict,
                                                db_cursor)


def write_algorithm_records(algorithm_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans algorithm_data and writes it to the database. Please note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param algorithm_data:
    :param db_cursor:
    :param modules_dict: A dictionary of the form {module_id: module_name}
    :return:
    """
    if algorithm_data['modules'] is None:
        # This has a 'modules' key, but its empty.  Skip it.
        pass
    else:
        for module_name in algorithm_data['modules']:
            if 'algorithms' in algorithm_data['modules'][module_name]:
                if algorithm_data['modules'][module_name]['algorithms'] is None:
                    # This has a 'algorithms' key, but its empty.  Skip it.
                    pass
                else:
                    for algorithm in algorithm_data['modules'][module_name]['algorithms']:
                        name = algorithm_data['modules'][module_name]['algorithms'][algorithm]['name']
                        type = algorithm_data['modules'][module_name]['algorithms'][algorithm]['type']
                        if not (type in ['custom']):
                            logging.error(
                                f"modules.{module_name}.algorithms.type must be in the supported list{['custom']}. "
                                f"Skipping.")
                            continue
                        language = algorithm_data['modules'][module_name]['algorithms'][algorithm]['script']['language']

                        script_path = str(Path(algorithm_data['modules'][module_name]['algorithms'][algorithm]['script']['path']).resolve())



                        # Write our telemetry record to the database.
                        db_cursor.execute(
                            'INSERT INTO algorithms(name, language, script_path, type, module) '
                            'VALUES (?, ?, ?, ?, ?)',
                            (name, language, script_path, type, modules_dict[module_name]))

            if 'modules' in algorithm_data['modules'][module_name]:
                write_algorithm_records(algorithm_data['modules'][module_name], modules_dict, db_cursor)


def write_command_records(command_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans command_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param command_data:
    :param db_cursor:
    :return:
    """
    # This has a modules key, but its empty.  Skip it.
    if command_data['modules'] is None:
        return

    for module_name in command_data['modules']:
        # FIXME: We need that schema. If we had the schema, we wouldn't need all these checks and the code would look cleaner.
        if 'commands' in command_data['modules'][module_name]:
            if command_data['modules'][module_name]['commands'] is None:
                # This has a command key, but no commands are defined.  Skip it.
                continue

            for command in command_data['modules'][module_name]['commands']:
                command_dict = command_data['modules'][module_name]['commands'][command]

                if command_dict['msgID'] is None:
                    logging.error(f"modules.{module_name}.commands.{command}.msgID must not be empty.  Skipping.")
                    continue

                message_id = command_dict['msgID']

                if message_id is None:
                    logging.error(
                        f"modules.{module_name}.commands.{command} message does not have any msgID defined. Skipping.")
                    continue

                if command_data['modules'][module_name]['commands'] is None:
                    logging.error(
                        f"modules.{module_name}.commands.{command} message does not have any actual commands defined.  Skipping.")
                    continue

                sub_commands = command_data['modules'][module_name]['commands']

                if 'commands' in sub_commands[command]:
                    for sub_command in sub_commands[command]['commands']:
                        if sub_commands[command]['commands'] is None:
                            logging.error(
                                f"modules.{module_name}.commands.{command}.{sub_command} command is empty.  Skipping.")
                            continue

                        sub_command_dict = sub_commands[command]['commands']
                        name = sub_command

                        symbol = get_symbol_id(sub_command_dict[name]['struct'], db_cursor)

                        # If the symbol does not exist, we skip it
                        if not symbol:
                            logging.error(
                                f"modules.{module_name}.commands.{command}.{sub_command}.{sub_command_dict[name]['struct']} was not found.  Skipping.")
                        else:
                            symbol_id = symbol[0]

                            if sub_command_dict[name]['cc'] is None:
                                logging.error(
                                    f"modules.{module_name}.commands.{command}.cc must not be empty.  Skipping.")
                                continue

                            command_code = sub_command_dict[name]['cc']

                            macro = command

                            # Write our command record to the database.
                            db_cursor.execute(
                                'INSERT INTO commands(name, command_code, message_id, macro, symbol ,module) '
                                'VALUES (?, ?, ?, ?, ?, ?)',
                                (name, command_code, message_id, macro, symbol_id, modules_dict[module_name],))

        if 'modules' in command_data['modules'][module_name]:
            write_command_records(command_data['modules'][module_name], modules_dict, db_cursor)


def write_event_records(event_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans event_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param event_data:
    :param db_cursor:
    :return:
    """
    event_id = None
    macro = None

    # This has a modules key, but its empty.  Skip it.
    if event_data['modules'] is None:
        return

    for module_name in event_data['modules']:
        if 'events' in event_data['modules'][module_name]:
            if event_data['modules'][module_name]['events'] is None:
                logging.error(f"modules.{module_name}.events is empty.  Skipping.")
                continue

            for event in event_data['modules'][module_name]['events']:
                event_dict = event_data['modules'][module_name]['events'][event]

                if event_dict is None:
                    logging.error(f"modules.{module_name} .events.{event} must not be empty.  Skipping.")
                    continue

                if event_dict['id'] is None:
                    logging.error(f"modules.{module_name} .events.{event}.id must not be empty.  Skipping.")
                    continue

                event_id = event_dict['id']
                event_name = event

                # FIXME: Not sure if we'll read the macro in this step of the chain
                # macro = event_dict['macro']

                # Write our event record to the database.
                db_cursor.execute('INSERT INTO events(event_id, name, module) '
                                  'VALUES (?, ?, ?)',
                                  (event_id, event_name, modules_dict[module_name],))


def write_configuration_records(config_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans config_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param config_data:
    :param db_cursor:
    :return:
    """
    name = None
    macro = None
    value = None

    # This has a modules key, but its empty.  Skip it.
    if config_data['modules'] is None:
        return

    for module_name in config_data['modules']:
        if 'config' in config_data['modules'][module_name]:
            if config_data['modules'][module_name]['config'] is None:
                logging.error(f"modules.{module_name}.config is empty.  Skipping.")
                continue

            for config in config_data['modules'][module_name]['config']:
                config_dict = config_data['modules'][module_name]['config'][config]

                if config_dict is None:
                    logging.error(f"modules.{module_name}.config.{config} is empty.  Skipping.")
                    continue

                if config_dict['value'] is None:
                    logging.error(f"modules.{module_name}.config.{config}.value is empty.  Skipping.")
                    continue

                name = config
                # FIXME: Not sure if we'll read the macro in step of the chain
                # macro = event_dict['macro']
                value = config_dict['value']

                # Write our event record to the database.
                db_cursor.execute('INSERT INTO configurations(name, value ,module) '
                                  'VALUES (?, ?, ?)',
                                  (name, value, modules_dict[module_name]))


def write_perf_id_records(perf_id_data: dict, modules_dict: dict, db_cursor: sqlite3.Cursor):
    """
    Scans perf_id_data and writes it to the database. Pleas note that the database changes are not committed. Thus
    it is the responsibility of the caller to commit these changes to the database.
    :param perf_id_data:
    :param db_cursor:
    :return:
    """
    name = None
    macro = None
    module_id = None
    perf_id = None

    # This has a modules key, but its empty.  Skip it.
    if perf_id_data['modules'] is None:
        return

    for module_name in perf_id_data['modules']:
        if 'perf_ids' in perf_id_data['modules'][module_name]:
            if perf_id_data['modules'][module_name]['perf_ids'] is None:
                logging.error(f"modules.{module_name}.perf_ids is empty.  Skipping.")
                continue

            for perf_name in perf_id_data['modules'][module_name]['perfids']:
                perf_dict = perf_id_data['modules'][module_name]['perfids'][perf_name]

                if perf_dict is None:
                    logging.error(f"modules{module_name}.perfids.{perf_name} is empty.  Skipping.")
                    continue

                if perf_dict['id'] is None:
                    logging.error(f"modules.{module_name}.perfids.{perf_name}.id is empty.  Skipping.")
                    continue

                name = perf_name
                # FIXME: Not sure if we'll read the macro in step of the chain
                # macro = event_dict['macro']
                perf_id = perf_dict['id']

                # Write our event record to the database.
                db_cursor.execute('INSERT INTO performance_ids(name, perf_id ,module) '
                                  'VALUES (?, ?, ?)',
                                  (name, perf_id, modules_dict[module_name]))


def __is_base_type(type_name: str) -> tuple:
    """
    Checks if type_name is a base type as it appears in the database.
    :return: A tuple of the form (bool, str), where the bool is whether this is a basetype or not and what the
    base type maps to in our BaseType namespace. Please note that this function does not pre-append the BaseType
    namespace to the type, that is the responsibility of the caller. Please note that padding types are also
    considered base types. Padding types have the form of _padding[Number Of Bits] such as _padding8.

    NOTE:While strings are considered a base type, it should be noted that, as opposed to all of the other base types,
    they are created as needed. This is because we can't really predict their sizes, like we do
    ints, not even a range as a string could be of any size. Thus they are created on the fly.
    """
    out_base_type = (False, '')

    if type_name == 'int64' \
            or type_name == 'int32' \
            or type_name == 'int16' \
            or type_name == 'int8' \
            or type_name == 'int':
        out_base_type = (True, 'int')
    elif type_name == 'uint8' \
            or type_name == 'uint16' \
            or type_name == 'uint32' \
            or type_name == 'unsigned int' \
            or type_name == 'unsigned' \
            or type_name == 'uint64':
        out_base_type = (True, 'uint')
    # FIXME: char types need to be handled properly
    elif type_name == 'char':
        out_base_type = (True, 'int')
    elif type_name == 'boolean':
        out_base_type = (True, 'boolean')
    elif type_name == 'float' or type_name == 'double':
        out_base_type = (True, 'float')
    elif type_name[:8] == '_padding':
        out_base_type = (True, '_padding')
    elif type_name == 'string':
        out_base_type = (True, 'string')

    return out_base_type


def write_tlm_cmd_data(yaml_data: dict, db_cursor: sqlite3.Cursor):
    write_module_records(yaml_data, db_cursor)

    # Get all modules needed now that they are on the database.
    modules_dict = {}
    for module_id, module_name in db_cursor.execute('select id, name from modules').fetchall():
        modules_dict[module_name] = module_id

    write_telemetry_records(yaml_data, modules_dict, db_cursor)

    telemetry_dict = {}
    for tlm_id, tlm_name in db_cursor.execute('select id, name from telemetry').fetchall():
        telemetry_dict[tlm_name] = tlm_id

    write_command_records(yaml_data, modules_dict, db_cursor)
    write_event_records(yaml_data, modules_dict, db_cursor)
    write_configuration_records(yaml_data, modules_dict, db_cursor)
    write_perf_id_records(yaml_data, modules_dict, db_cursor)

    write_algorithm_records(yaml_data, modules_dict, db_cursor)

    # Get all algorithms needed now that they are on the database.
    # TODO:Add error-checking for these algorithm functions.
    algorithms_dict = {}
    for algorithm_id, algorithm_name in db_cursor.execute('select id, name from algorithms').fetchall():
        algorithms_dict[algorithm_name] = algorithm_id

    write_algorithm_triggers_records(yaml_data, algorithms_dict, telemetry_dict, db_cursor)

    write_algorithm_inputs_records(yaml_data, algorithms_dict, db_cursor)

    # Get all algorithms needed now that they are on the database.
    symbols_dict = {}
    for symbol_id, symbol_name in db_cursor.execute('select id, name from symbols').fetchall():
        symbols_dict[symbol_name] = symbol_id

    write_algorithm_outputs_records(yaml_data, algorithms_dict, symbols_dict, db_cursor)


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in paths to yaml file and sqlite database.')
    parser.add_argument('--yaml_path', type=str,
                        help='The file path to the YAML file which contains telemetry and command metadata.',
                        required=True)
    parser.add_argument('--sqlite_path', type=str,
                        help='The file path to the sqlite database', required=True)

    return parser.parse_args()


def merge_all(database_path: str, yaml_file: str):
    db_handle = sqlite3.connect(database_path)
    db_cursor = db_handle.cursor()

    add_tables(db_cursor)

    yaml_data = read_yaml(yaml_file)

    # Write all the data to the database.
    write_tlm_cmd_data(yaml_data, db_cursor)

    # Save our changes to the database.
    db_handle.commit()


def main():
    args = parse_cli()
    merge_all(args.sqlite_path, args.yaml_path)


if __name__ == '__main__':
    main()

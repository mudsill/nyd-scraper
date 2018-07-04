import os
import sqlite3
import logging

DB_TOOL = 'db-tool'


class DBTool(object):

    def __init__(self):
        self.db = sqlite3.connect(os.environ.get('NYD_DATABASE_URL'))
        self.logger = logging.getLogger(DB_TOOL)

    def  __del__(self):
        self.db.close()


    def create_table(self, table_name, **kwargs):
        schema = []

        for k, v in kwargs.items():
            schema.append('%s %s' % (k, v))

        schema = ', '.join(schema)
        schema = '(%s)' % schema

        create_table = "CREATE TABLE IF NOT EXISTS %s %s" % (table_name, schema)

        self.execute(create_table)


    def query(self, table_name, properties=[], order_by=None, **kwargs):
        properties = ', '.join(properties)

        if not len(properties):
            properties = '*'

        query_statement = "SELECT %s FROM %s" % (properties,
                                                 table_name)
        where = self.param_string(kwargs)
        if where is not None:
            query_statement += '  WHERE %s' % where

        if order_by is not None:
            query_statement += ' ORDER BY %s' % order_by

        return self.execute(query_statement)


    def insert(self, table_name, *args):
        if not len(args):
            return

        def process_value(value):
            if value is None:
                value = 'NULL'
            else:
                value = self.format_param(value)
            return value

        values = ','.join(map(process_value, args))
        values = '(%s)' % values
        insert_statement = "INSERT OR IGNORE INTO %s VALUES %s" % (table_name,
                                                                   values)
        self.execute(insert_statement)
        self.db.commit()


    def update(self, table_name, set_params, where_params):
        if not(len(set_params.keys())) or not(len(where_params.keys())):
            return

        set_to = self.param_string(set_params)
        where = self.param_string(where_params)
        update_statement = "UPDATE %s SET %s WHERE %s" % (table_name, set_to,
                                                          where)

        self.execute(update_statement)


    def delete(self, table_name, **kwargs):
        if not len(kwargs.keys()):
            return

        where = self.param_string(kwargs)
        delete_statement = "DELETE FROM %s WHERE %s" % (table_name, where)

        self.execute(delete_statement)
        self.db.commit()


    def param_string(self, params):
        if not len(params.keys()):
            return

        param_list = []
        for k, v in params.items():
            v = self.format_param(v)
            param_list.append("%s = %s" % (k, v))
        return ' and '.join(param_list)


    def format_param(self, param):
        if isinstance(param, str):
            param = param.replace('"', '\'')
            param = '"%s"' % param
        return str(param)


    def execute(self, statement):
        if not len(statement):
            return

        c = self.db.cursor()

        try:
            self.logger.info('Executing: %s', statement)
            c.execute(statement)
        except sqlite3.Error as e:
            self.logger.error('Error: %s', e)

        return c

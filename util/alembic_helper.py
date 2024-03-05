import logging
from sqlalchemy import create_engine

def create_db(url):

    split_url = url.split('/')
    database = split_url.pop()
    host = '/'.join(split_url)
    engine = create_engine(f'{host}/postgres')
    conn = engine.connect()
    logger = logging.getLogger('api')
    try:
        res = conn.execute('SELECT * FROM pg_database')
        existing_databases = [row.datname for row in res]
      
        if database not in existing_databases:
            query = f'CREATE DATABASE {database}'
            conn.execution_options(isolation_level='AUTOCOMMIT').execute(query)
            logger.info(f'Database {database} being created')
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
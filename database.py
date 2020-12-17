import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def save_nightlight(conn, data):
    """
    Save new nightlight config
    :param conn:
    :param data:
    :return:
    """

    query = ('INSERT INTO nightlight ("red", "green", "blue", "brightness", "description") '
             'VALUES (:red, :green, :blue, :brightness, :description);')
    params = {
        'red': data['red'],
        'green': data['green'],
        'blue': data['blue'],
        'brightness': data['brightness'],
        'description': data['description']
    }
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    
def select_all_nightlight_configs(conn):
    """
    Query all rows in the nightlight table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM nightlight")

    rows = cur.fetchall()
    return rows

def nightlight_delete(conn, light_id):
    """
    Delete specific rows in the nightlight table
    :param conn: the Connection object
    :param light_id: the nightlight config id
    :return:
    """
    params = {'id': light_id}
    query = 'SELECT count(*) FROM nightlight WHERE light.id = :id'
    cur = conn.cursor()
    cursor = cur.execute(query, params)

    # Check if sound exists
    if cursor.fetchone()[0] == 0:
        # Doesn't exist. Return.
        return

    # Delete it
    delete_query = 'DELETE FROM nightlight WHERE light.id = :id'
    cur.execute(delete_query, {'id': light_id})
    conn.commit()

def delete_all_nightlights(conn):
    """
    Delete all rows in the nightlight table
    :param conn: the Connection object
    :return:
    """
    sql = 'DELETE FROM nightlight'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def save_sound(conn, data):
    """
    Save new nightlight config
    :param conn:
    :param task:
    :return:
    """
    query = ('INSERT INTO sounds ("description", "fullpath", "isfavorite") '
             'VALUES (:description, :fullpath, :isfavorite);')
    params = {
        'description': data['description'],
        'fullpath': data['fullpath'],
        'isfavorite' : data['isfavorite']
    }
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    
def select_all_sounds(conn):
    """
    Query all rows in the sounds table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM sounds")

    rows = cur.fetchall()
    return rows

def sound_delete(conn, sound_id):
    """
    Delete specific rows in the sounds table
    :param conn: the Connection object
    :param light_id: the sound config id
    :return:
    """
    params = {'id': sound_id}
    query = 'SELECT count(*) FROM sounds WHERE sounds.id = :id'
    cur = conn.cursor()
    cursor = cur.execute(query, params)

    # Check if sound exists
    if cursor.fetchone()[0] == 0:
        # Doesn't exist. Return.
        return

    # Delete it
    delete_query = 'DELETE FROM sounds WHERE sounds.id = :id'
    cur.execute(delete_query, {'id': sound_id})
    conn.commit()

def delete_all_sounds(conn):
    """
    Delete all rows in the sounds table
    :param conn: the Connection object
    :return:
    """
    sql = 'DELETE FROM sounds'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
import psycopg2
from flask import jsonify
from src.config.database import get_db_connection

def insert_user(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (username, email, first_name, last_name) VALUES (%s, %s, %s, %s) RETURNING *',
            (args['username'], args['email'], args.get('first_name'), args.get('last_name'))
        )
        new_user = cursor.fetchone()
        conn.commit()
        return jsonify({'success': True, 'user': dict(new_user)})
    except psycopg2.IntegrityError as e:
        conn.rollback()
        return jsonify({'error': f'Username or email already exists: {str(e)}'}), 409
    finally:
        cursor.close()
        conn.close()

def get_users(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users ORDER BY id')
        users = cursor.fetchall()
        return jsonify({'users': [dict(user) for user in users]})
    finally:
        cursor.close()
        conn.close()

def get_user_by_id(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = %s', (args['user_id'],))
        user = cursor.fetchone()
        
        if user:
            return jsonify({'user': dict(user)})
        else:
            return jsonify({'error': 'User not found'}), 404
    finally:
        cursor.close()
        conn.close()

def update_user(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = %s', (args['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        fields_to_update = []
        values = []
        
        for field in ['username', 'email', 'first_name', 'last_name']:
            if field in args and field != 'user_id':
                fields_to_update.append(f'{field} = %s')
                values.append(args[field])
        
        if not fields_to_update:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(args['user_id'])
        
        cursor.execute(
            f'UPDATE users SET {", ".join(fields_to_update)} WHERE id = %s RETURNING *',
            values
        )
        updated_user = cursor.fetchone()
        conn.commit()
        return jsonify({'success': True, 'user': dict(updated_user)})
    except psycopg2.IntegrityError as e:
        conn.rollback()
        return jsonify({'error': f'Username or email already exists: {str(e)}'}), 409
    finally:
        cursor.close()
        conn.close()

def delete_user(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = %s', (args['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        cursor.execute('DELETE FROM users WHERE id = %s', (args['user_id'],))
        conn.commit()
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    finally:
        cursor.close()
        conn.close()

def get_users_for_llm():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, username, email, first_name, last_name FROM users ORDER BY id')
        users = cursor.fetchall()
        return users
    finally:
        cursor.close()
        conn.close()
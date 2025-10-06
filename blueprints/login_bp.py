from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conexao
import mysql.connector

users_dict = {'admin@gmail.com': '1234'}

login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login')
def login():
    return render_template('login.html', erro=False, action_url=url_for('login_bp.validar_usuario'))


@login_bp.route('/validar_usuario', methods=['POST'])
def validar_usuario():
    usuario = request.form['usuario']
    password = request.form['password']

    if usuario in users_dict and users_dict[usuario] == password:
        session['usuario'] = usuario
        return redirect(url_for('iot_bp.home'))

    conn = conexao()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE email = %s", (usuario,))
        user = cursor.fetchone()
        if user and user[0] == password:
            session['usuario'] = usuario
            return redirect(url_for('iot_bp.home'))  
        else:
            return render_template('login.html', erro=True, action_url=url_for('login_bp.validar_usuario'))
    except mysql.connector.Error as err:
        print("[ERRO MYSQL]", err)
        return "Erro no banco de dados", 500
    finally:
        cursor.close()
        conn.close()


@login_bp.route('/logout')
def logout():
    session.pop('usuario', None)  # limpa a sessão do usuário
    return redirect(url_for('login_bp.login'))


# CRUD
@login_bp.route('/usuarios')
def listar_usuarios():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    usuarios = []
    conn = conexao()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email FROM usuarios ORDER BY id ASC")
            usuarios = [{'id': row[0], 'email': row[1]} for row in cursor.fetchall()]
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
        finally:
            cursor.close()
            conn.close()

    return render_template("usuarios.html", usuarios=usuarios)


@login_bp.route('/adicionar_usuario', methods=['GET', 'POST'])
def adicionar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return "Dados inválidos", 400

        conn = conexao()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (email, senha) VALUES (%s, %s)", (email, password))
                conn.commit()
            except mysql.connector.Error as err:
                print("[ERRO MYSQL]", err)
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

        return redirect(url_for('login_bp.listar_usuarios'))

    return render_template('adicionar_usuario.html', action_url=url_for('login_bp.adicionar_usuario'))


@login_bp.route('/deletar_usuario', methods=['POST'])
def deletar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    email = request.form.get('email')
    if not email:
        return "Usuário inválido", 400

    conn = conexao()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE email = %s", (email,))
            conn.commit()
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('login_bp.listar_usuarios'))


@login_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    conn = conexao()
    cursor = conn.cursor()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return "Dados inválidos", 400

        try:
            cursor.execute("UPDATE usuarios SET email=%s, senha=%s WHERE id=%s", (email, password, id))
            conn.commit()
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login_bp.listar_usuarios'))

    cursor.execute("SELECT id, email FROM usuarios WHERE id=%s", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template(
        'editar_usuario.html',
        usuario={'id': usuario[0], 'email': usuario[1]},
        action_url=url_for('login_bp.editar_usuario', id=id)
    )

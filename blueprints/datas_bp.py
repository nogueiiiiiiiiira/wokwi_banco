from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conexao
import mysql.connector

datas_bp = Blueprint('datas_bp', __name__)

# CRUD
@datas_bp.route('/datas')
def listar_datas():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    datas = []
    conn = conexao()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, evento FROM datas ORDER BY id ASC")
            datas = [{'id': row[0], 'evento': row[1]} for row in cursor.fetchall()]
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
        finally:
            cursor.close()
            conn.close()

    return render_template("datas.html", datas=datas)


@datas_bp.route('/adicionar_data', methods=['GET', 'POST'])
def adicionar_data():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    if request.method == 'POST':
        evento = request.form.get('evento')
        descricao = request.form.get('descricao')

        if not evento or not descricao:
            return "Dados inválidos", 400

        conn = conexao()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO datas (evento, descricao) VALUES (%s, %s)", (evento, descricao))
                conn.commit()
            except mysql.connector.Error as err:
                print("[ERRO MYSQL]", err)
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

        return redirect(url_for('datas_bp.listar_datas'))

    return render_template('adicionar_data.html', action_url=url_for('datas_bp.adicionar_data'))


@datas_bp.route('/deletar_data', methods=['POST'])
def deletar_data():
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    evento = request.form.get('evento')
    if not evento:
        return "Evento inválido", 400

    conn = conexao()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM datas WHERE evento = %s", (evento,))
            conn.commit()
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('datas_bp.listar_datas'))


@datas_bp.route('/editar_data/<int:id>', methods=['GET', 'POST'])
def editar_data(id):
    if 'usuario' not in session:
        return redirect(url_for('login_bp.login'))

    conn = conexao()
    cursor = conn.cursor()

    if request.method == 'POST':
        evento = request.form.get('evento')
        descricao = request.form.get('descricao')

        if not evento or not descricao:
            return "Dados inválidos", 400

        try:
            cursor.execute("UPDATE datas SET evento=%s, descricao=%s WHERE id=%s", (evento, descricao, id))
            conn.commit()
        except mysql.connector.Error as err:
            print("[ERRO MYSQL]", err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('datas_bp.listar_datas'))

    cursor.execute("SELECT id, evento, descricao FROM datas WHERE id=%s", (id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template(
        'editar_data.html',
        data={'id': data[0], 'evento': data[1], 'descricao': data[2]},
        action_url=url_for('datas_bp.editar_data', id=id)
    )

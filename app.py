from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
import sqlite3
import os
import pandas as pd
from functools import wraps
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'practice_score_system_secret_key_2024'

# ==================== 用户配置 ====================
USERS = {
    # 超级管理员（2人）- 所有功能
    'AIPRM01': {'password': 'rgzn@M01', 'role': 'super_admin', 'display_name': '王淇锋'},
    'AIPRM02': {'password': 'rgzn@M02', 'role': 'super_admin', 'display_name': '包瞳'},

    # 管理员（6人）- 查询 + 录入
    'AIPRD01': {'password': 'rgzn@D01', 'role': 'admin', 'display_name': '张邓淅'},
    'AIPRD02': {'password': 'rgzn@D02', 'role': 'admin', 'display_name': '王钰涵'},
    'AIPRD03': {'password': 'rgzn@D03', 'role': 'admin', 'display_name': '张铭铭'},
    'AIPRD04': {'password': 'rgzn@D04', 'role': 'admin', 'display_name': '朱昌鹏'},
    'AIPRD05': {'password': 'rgzn@D05', 'role': 'admin', 'display_name': '史禹含'},
    'AIPRD06': {'password': 'rgzn@D06', 'role': 'admin', 'display_name': '孙楚茗'},

    # 普通用户（10人）- 查询 + 录入
    'AIPRS01': {'password': 'rgzn@S01', 'role': 'user', 'display_name': '杨羽欣'},
    'AIPRS02': {'password': 'rgzn@S02', 'role': 'user', 'display_name': '沙思辰'},
    'AIPRS03': {'password': 'rgzn@S03', 'role': 'user', 'display_name': '姜玥'},
    'AIPRS04': {'password': 'rgzn@S04', 'role': 'user', 'display_name': '李姿萱'},
    'AIPRS05': {'password': 'rgzn@S05', 'role': 'user', 'display_name': '李梦晴'},
    'AIPRS06': {'password': 'rgzn@S06', 'role': 'user', 'display_name': '王天宇'},
    'AIPRS07': {'password': 'rgzn@S07', 'role': 'user', 'display_name': '霍东元'},
    'AIPRS08': {'password': 'rgzn@S08', 'role': 'user', 'display_name': '张灵铄'},
    'AIPRS09': {'password': 'rgzn@S09', 'role': 'user', 'display_name': '张浩楠'},
    'AIPRS10': {'password': 'rgzn@S10', 'role': 'user', 'display_name': '牟海文'},
}

# 数据库路径
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'score.db')


# ==================== 数据库操作 ====================
def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def get_all_grades():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'grade_%'")
    tables = cursor.fetchall()
    conn.close()
    grades = [t['name'].replace('grade_', '') for t in tables]
    return sorted(grades)

#此函数放弃使用，只作为排除异常情况，初始化数据库请使用init_db.py文件
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    for grade in ['22', '23', '24', '25']:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS grade_{grade} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                semester_1 REAL DEFAULT 0,
                semester_2 REAL DEFAULT 0,
                semester_3 REAL DEFAULT 0,
                semester_4 REAL DEFAULT 0,
                semester_5 REAL DEFAULT 0,
                semester_6 REAL DEFAULT 0,
                semester_7 REAL DEFAULT 0,
                semester_8 REAL DEFAULT 0,
                remark TEXT DEFAULT ''
            )
        ''')
    conn.commit()
    conn.close()
    print("数据库初始化完成！")


# ==================== 权限装饰器 ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """需要管理员或用户权限（查询+录入）"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('login'))
        if session.get('role') not in ['admin', 'user', 'super_admin']:
            flash('权限不足！', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'super_admin':
            flash('需要超级管理员权限！', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# ==================== 路由 ====================
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            session['display_name'] = USERS[username]['display_name']
            flash(f'欢迎回来，{USERS[username]["display_name"]}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误！', 'danger')

    return render_template('login.html')


@app.route('/guest')
def guest():
    session['username'] = 'guest'
    session['role'] = 'guest'
    session['display_name'] = '访客'
    return redirect(url_for('query'))


@app.route('/logout')
def logout():
    session.clear()
    flash('已成功退出！', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html',
                           role=session.get('role'),
                           display_name=session.get('display_name'))


# ==================== 查询功能 ====================
@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'username' not in session:
        return redirect(url_for('login'))

    result = None
    searched = False
    grades = get_all_grades()

    if request.method == 'POST':
        searched = True
        search_type = request.form.get('search_type')
        search_value = request.form.get('search_value', '').strip()
        grade = request.form.get('grade')

        if not search_value:
            flash('请输入查询内容！', 'warning')
        elif grade not in grades:
            flash('请选择有效的年级！', 'warning')
        else:
            conn = get_db()
            cursor = conn.cursor()

            try:
                if search_type == 'student_id':
                    cursor.execute(f"SELECT * FROM grade_{grade} WHERE student_id = ?", (search_value,))
                else:
                    cursor.execute(f"SELECT * FROM grade_{grade} WHERE name LIKE ?", (f'%{search_value}%',))

                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    total = sum(result.get(f'semester_{i}', 0) or 0 for i in range(1, 9))
                    result['total_score'] = total
                    result['grade'] = grade
                else:
                    flash('未找到该学生信息！', 'info')
            except Exception as e:
                flash(f'查询出错：{str(e)}', 'danger')
            finally:
                conn.close()

    return render_template('query.html',
                           result=result,
                           grades=grades,
                           role=session.get('role'),
                           searched=searched)


# ==================== API接口 ====================
@app.route('/api/get_student/<grade>/<student_id>')
def api_get_student(grade, student_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT name FROM grade_{grade} WHERE student_id = ?", (student_id,))
        result = cursor.fetchone()
        if result:
            return jsonify({'success': True, 'name': result['name']})
        return jsonify({'success': False, 'name': ''})
    except:
        return jsonify({'success': False, 'name': ''})
    finally:
        conn.close()


@app.route('/api/check_semester_score')
def api_check_semester_score():
    """
    检查指定学期是否已有成绩
    
    GET参数:
        grade: 年级（如 "22", "23"）
        student_id: 学号
        semester: 学期编号（1-8）
    
    返回JSON:
        {"success": bool, "has_score": bool, "score": float, "student_name": str}
    """
    grade = request.args.get('grade', '').strip()
    student_id = request.args.get('student_id', '').strip()
    semester = request.args.get('semester', '').strip()
    
    # 验证参数
    if not all([grade, student_id, semester]):
        return jsonify({
            'success': False,
            'has_score': False,
            'score': 0,
            'student_name': ''
        })
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 查询学生信息和指定学期成绩
        cursor.execute(
            f"SELECT name, semester_{semester} FROM grade_{grade} WHERE student_id = ?",
            (student_id,)
        )
        result = cursor.fetchone()
        
        if result:
            student_name = result['name']
            score = result[f'semester_{semester}']
            
            # 判断是否已有成绩（大于0为已有成绩）
            if score and score > 0:
                return jsonify({
                    'success': True,
                    'has_score': True,
                    'score': float(score),
                    'student_name': student_name
                })
            else:
                return jsonify({
                    'success': True,
                    'has_score': False,
                    'score': 0,
                    'student_name': student_name
                })
        else:
            # 学生不存在
            return jsonify({
                'success': False,
                'has_score': False,
                'score': 0,
                'student_name': ''
            })
    except Exception as e:
        # 数据库错误或其他异常
        return jsonify({
            'success': False,
            'has_score': False,
            'score': 0,
            'student_name': ''
        })
    finally:
        conn.close()


# ==================== 录入功能 ====================
@app.route('/input', methods=['GET', 'POST'])
@admin_required
def input_score():
    grades = get_all_grades()

    if request.method == 'POST':
        grade = request.form.get('grade')
        student_id = request.form.get('student_id', '').strip()
        semester = request.form.get('semester')
        score = request.form.get('score', '0').strip()
        remark = request.form.get('remark', '').strip()

        if not all([grade, student_id, semester, score]):
            flash('请填写完整信息！', 'warning')
        else:
            try:
                score = float(score)
                conn = get_db()
                cursor = conn.cursor()

                # 先查询当前学期成绩，检查是否已有数据
                cursor.execute(
                    f"SELECT semester_{semester} FROM grade_{grade} WHERE student_id = ?",
                    (student_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    # 学生不存在
                    flash('未找到该学生，请检查学号是否正确！', 'warning')
                    conn.close()
                    return render_template('input.html', grades=grades, role=session.get('role'))
                
                current_score = result[f'semester_{semester}']
                
                # 检查是否已有成绩（大于0为已有成绩）
                if current_score and current_score > 0:
                    flash(f'该学期已有成绩：{current_score}分，不允许重复录入！', 'warning')
                    conn.close()
                    return render_template('input.html', grades=grades, role=session.get('role'))
                
                # 允许录入：更新成绩和备注
                cursor.execute(
                    f"UPDATE grade_{grade} SET semester_{semester} = ?, remark = ? WHERE student_id = ?",
                    (score, remark, student_id)
                )
                conn.commit()
                conn.close()
                
                # 录入成功，不显示提示消息（按需求3.5）
                
            except ValueError:
                flash('分数格式不正确！', 'danger')
            except Exception as e:
                flash(f'录入失败：{str(e)}', 'danger')

    return render_template('input.html', grades=grades, role=session.get('role'))


# ==================== 添加功能 ====================
@app.route('/add', methods=['GET', 'POST'])
@super_admin_required
def add():
    grades = get_all_grades()

    if request.method == 'POST':
        action = request.form.get('action')

        conn = get_db()
        cursor = conn.cursor()

        try:
            if action == 'add_grade':
                new_grade = request.form.get('new_grade', '').strip()
                if not new_grade:
                    flash('请输入年级！', 'warning')
                elif new_grade in grades:
                    flash(f'{new_grade}级已存在！', 'warning')
                else:
                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS grade_{new_grade} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            student_id TEXT UNIQUE NOT NULL,
                            name TEXT NOT NULL,
                            semester_1 REAL DEFAULT 0,
                            semester_2 REAL DEFAULT 0,
                            semester_3 REAL DEFAULT 0,
                            semester_4 REAL DEFAULT 0,
                            semester_5 REAL DEFAULT 0,
                            semester_6 REAL DEFAULT 0,
                            semester_7 REAL DEFAULT 0,
                            semester_8 REAL DEFAULT 0,
                            remark TEXT DEFAULT ''
                        )
                    ''')
                    conn.commit()
                    flash(f'成功创建{new_grade}级数据表！', 'success')
                    grades = get_all_grades()

            elif action == 'add_student':
                grade = request.form.get('grade')
                student_id = request.form.get('student_id', '').strip()
                name = request.form.get('name', '').strip()
                remark = request.form.get('remark', '').strip()

                if not all([grade, student_id, name]):
                    flash('请填写完整信息！', 'warning')
                else:
                    cursor.execute(f"INSERT INTO grade_{grade} (student_id, name, remark) VALUES (?, ?, ?)",
                                   (student_id, name, remark))
                    conn.commit()
                    flash(f'成功添加学生：{name}（{student_id}）', 'success')

            elif action == 'batch_add':
                grade = request.form.get('grade')
                batch_data = request.form.get('batch_data', '').strip()

                if not batch_data:
                    flash('请输入批量数据！', 'warning')
                else:
                    lines = batch_data.strip().split('\n')
                    success_count = 0
                    fail_count = 0

                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            student_id, name = parts[0], parts[1]
                            remark = parts[2] if len(parts) >= 3 else ''
                            try:
                                cursor.execute(f"INSERT INTO grade_{grade} (student_id, name, remark) VALUES (?, ?, ?)",
                                               (student_id, name, remark))
                                success_count += 1
                            except:
                                fail_count += 1

                    conn.commit()
                    flash(f'批量添加完成！成功：{success_count}，失败：{fail_count}', 'info')

        except sqlite3.IntegrityError:
            flash('学号已存在！', 'danger')
        except Exception as e:
            flash(f'操作失败：{str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('add.html', grades=grades, role=session.get('role'))


# ==================== 删除功能 ====================
@app.route('/delete', methods=['GET', 'POST'])
@super_admin_required
def delete():
    grades = get_all_grades()

    if request.method == 'POST':
        action = request.form.get('action')

        conn = get_db()
        cursor = conn.cursor()

        try:
            if action == 'delete_grade':
                grade = request.form.get('grade')
                confirm = request.form.get('confirm')

                if confirm != grade:
                    flash('确认输入不匹配，删除取消！', 'warning')
                else:
                    cursor.execute(f"DROP TABLE IF EXISTS grade_{grade}")
                    conn.commit()
                    flash(f'成功删除{grade}级数据表！', 'success')
                    grades = get_all_grades()

            elif action == 'delete_student':
                grade = request.form.get('grade')
                student_id = request.form.get('student_id', '').strip()

                if not student_id:
                    flash('请输入学号！', 'warning')
                else:
                    cursor.execute(f"DELETE FROM grade_{grade} WHERE student_id = ?", (student_id,))
                    conn.commit()

                    if cursor.rowcount > 0:
                        flash('成功删除学生！', 'success')
                    else:
                        flash('未找到该学生！', 'warning')

        except Exception as e:
            flash(f'操作失败：{str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('delete.html', grades=grades, role=session.get('role'))


# ==================== 修改功能 ====================
@app.route('/modify', methods=['GET', 'POST'])
@super_admin_required
def modify():
    grades = get_all_grades()
    student_data = None

    if request.method == 'POST':
        action = request.form.get('action')
        grade = request.form.get('grade')

        conn = get_db()
        cursor = conn.cursor()

        try:
            if action == 'search':
                search_type = request.form.get('search_type')
                search_value = request.form.get('search_value', '').strip()

                if not search_value:
                    flash('请输入查询内容！', 'warning')
                else:
                    if search_type == 'student_id':
                        cursor.execute(f"SELECT * FROM grade_{grade} WHERE student_id = ?", (search_value,))
                    else:
                        cursor.execute(f"SELECT * FROM grade_{grade} WHERE name LIKE ?", (f'%{search_value}%',))

                    result = cursor.fetchone()
                    if result:
                        student_data = dict(result)
                        student_data['grade'] = grade
                    else:
                        flash('未找到该学生！', 'info')

            elif action == 'update':
                student_id = request.form.get('student_id')
                new_name = request.form.get('new_name', '').strip()
                new_remark = request.form.get('new_remark', '').strip()

                updates = []
                values = []

                if new_name:
                    updates.append('name = ?')
                    values.append(new_name)

                # 始终更新备注（即使为空）
                if 'new_remark' in request.form:
                    updates.append('remark = ?')
                    values.append(new_remark)

                for i in range(1, 9):
                    score = request.form.get(f'semester_{i}', '').strip()
                    if score:
                        try:
                            updates.append(f'semester_{i} = ?')
                            values.append(float(score))
                        except ValueError:
                            pass

                if updates:
                    values.append(student_id)
                    sql = f"UPDATE grade_{grade} SET {', '.join(updates)} WHERE student_id = ?"
                    cursor.execute(sql, values)
                    conn.commit()
                    flash('修改成功！', 'success')
                else:
                    flash('没有需要修改的内容！', 'info')

        except Exception as e:
            flash(f'操作失败：{str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('modify.html', grades=grades, student_data=student_data, role=session.get('role'))


# ==================== 导出功能 ====================
@app.route('/export')
@super_admin_required
def export():
    grades = get_all_grades()
    return render_template('export.html', grades=grades, role=session.get('role'))


@app.route('/export/<grade>')
@super_admin_required
def export_grade(grade):
    conn = get_db()

    try:
        df = pd.read_sql_query(f"SELECT * FROM grade_{grade}", conn)

        semester_cols = [f'semester_{i}' for i in range(1, 9)]
        df['total_score'] = df[semester_cols].sum(axis=1)

        df = df.rename(columns={
            'id': '序号',
            'student_id': '学号',
            'name': '姓名',
            'semester_1': '第1学期',
            'semester_2': '第2学期',
            'semester_3': '第3学期',
            'semester_4': '第4学期',
            'semester_5': '第5学期',
            'semester_6': '第6学期',
            'semester_7': '第7学期',
            'semester_8': '第8学期',
            'total_score': '总分',
            'remark': '备注'
        })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=f'{grade}级成绩')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{grade}级社会实践成绩.xlsx'
        )
    except Exception as e:
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('export'))
    finally:
        conn.close()


@app.route('/export/all')
@super_admin_required
def export_all():
    grades = get_all_grades()
    conn = get_db()

    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for grade in grades:
                df = pd.read_sql_query(f"SELECT * FROM grade_{grade}", conn)

                semester_cols = [f'semester_{i}' for i in range(1, 9)]
                df['total_score'] = df[semester_cols].sum(axis=1)

                df = df.rename(columns={
                    'id': '序号',
                    'student_id': '学号',
                    'name': '姓名',
                    'semester_1': '第1学期',
                    'semester_2': '第2学期',
                    'semester_3': '第3学期',
                    'semester_4': '第4学期',
                    'semester_5': '第5学期',
                    'semester_6': '第6学期',
                    'semester_7': '第7学期',
                    'semester_8': '第8学期',
                    'total_score': '总分',
                    'remark': '备注'
                })

                df.to_excel(writer, index=False, sheet_name=f'{grade}级')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='全部年级社会实践成绩.xlsx'
        )
    except Exception as e:
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('export'))
    finally:
        conn.close()


@app.route('/export/insufficient/<grade>')
@super_admin_required
def export_insufficient(grade):
    """导出指定年级学分不满足的学生名单（总分<2）"""
    conn = get_db()

    try:
        df = pd.read_sql_query(f"SELECT * FROM grade_{grade}", conn)

        semester_cols = [f'semester_{i}' for i in range(1, 9)]
        df['total_score'] = df[semester_cols].sum(axis=1)

        # 筛选总分小于2的学生
        df_insufficient = df[df['total_score'] < 2].copy()

        if df_insufficient.empty:
            flash(f'{grade}级所有学生均已达标！', 'success')
            return redirect(url_for('export'))

        df_insufficient = df_insufficient.rename(columns={
            'id': '序号',
            'student_id': '学号',
            'name': '姓名',
            'semester_1': '第1学期',
            'semester_2': '第2学期',
            'semester_3': '第3学期',
            'semester_4': '第4学期',
            'semester_5': '第5学期',
            'semester_6': '第6学期',
            'semester_7': '第7学期',
            'semester_8': '第8学期',
            'total_score': '总分',
            'remark': '备注'
        })

        # 添加缺少学分列
        df_insufficient['缺少学分'] = 2 - df_insufficient['总分']

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_insufficient.to_excel(writer, index=False, sheet_name=f'{grade}级未达标学生')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{grade}级学分不满足学生名单.xlsx'
        )
    except Exception as e:
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('export'))
    finally:
        conn.close()


@app.route('/export/insufficient/all')
@super_admin_required
def export_insufficient_all():
    """导出所有年级学分不满足的学生名单"""
    grades = get_all_grades()
    conn = get_db()

    try:
        output = BytesIO()
        has_data = False

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for grade in grades:
                df = pd.read_sql_query(f"SELECT * FROM grade_{grade}", conn)

                semester_cols = [f'semester_{i}' for i in range(1, 9)]
                df['total_score'] = df[semester_cols].sum(axis=1)

                # 筛选总分小于2的学生
                df_insufficient = df[df['total_score'] < 2].copy()

                if not df_insufficient.empty:
                    has_data = True
                    df_insufficient = df_insufficient.rename(columns={
                        'id': '序号',
                        'student_id': '学号',
                        'name': '姓名',
                        'semester_1': '第1学期',
                        'semester_2': '第2学期',
                        'semester_3': '第3学期',
                        'semester_4': '第4学期',
                        'semester_5': '第5学期',
                        'semester_6': '第6学期',
                        'semester_7': '第7学期',
                        'semester_8': '第8学期',
                        'total_score': '总分',
                        'remark': '备注'
                    })

                    # 添加缺少学分列
                    df_insufficient['缺少学分'] = 2 - df_insufficient['总分']

                    df_insufficient.to_excel(writer, index=False, sheet_name=f'{grade}级未达标')

        if not has_data:
            flash('所有年级的学生均已达标！', 'success')
            return redirect(url_for('export'))

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='全部年级学分不满足学生名单.xlsx'
        )
    except Exception as e:
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('export'))
    finally:
        conn.close()


# ==================== 启动应用 ====================
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        print("数据库初始化完成！")
    else:
        print("数据库已存在，跳过初始化")

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
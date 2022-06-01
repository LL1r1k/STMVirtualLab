from datetime import datetime
from urllib.request import Request
from datetime import datetime
import json

from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import current_user, login_user, logout_user, login_required
from flask_socketio import emit  
from werkzeug.urls import url_parse
from pygments.lexers import get_lexer_for_filename

from gdbgui import __version__, htmllistformatter
from gdbgui.backend import app, db, _state, SIGNAL_NAME_TO_OBJ, USING_WINDOWS
from gdbgui.app.forms import LoginForm, RegistrationForm, AccessRequestForm
from gdbgui.app.models import User, Role, Access_Request

from gdbgui.app.utils import *

@app.route('/')
@app.route('/index')
@login_required
def index():
    users = []
    if current_user.is_admin():
        users = User.query.all()
        for user in users:
            update_request_status(user)
    else:
        update_request_status(current_user)

    return render_template('index.html', title='Home', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/access_request', methods=['GET', 'POST'])
@login_required
def access_request():
    form = AccessRequestForm()
    if form.validate_on_submit():

        start_time = datetime.strptime(form.start_at.data, '%d-%m-%Y %H:%M:%S')
        end_time = datetime.strptime(form.end_at.data, '%d-%m-%Y %H:%M:%S')
        req = Access_Request(comment=form.comment.data, time_start=start_time, time_end=end_time, status="Created", author=current_user)

        db.session.add(req)
        db.session.commit()
        flash('Запрос отправлен')
        return redirect(url_for('index'))
    return render_template('access_request.html', title='Запрос доступа', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)

        user_role = Role.query.filter_by(name="User").first()
        user.set_role(user_role)

        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/remove_request", methods=["POST"])
def remove_request():
    request_id = int(request.form.get("request_id"))

    req = Access_Request.query.filter_by(id=request_id).first()
    if req is not None:
        db.session.delete(req)
        db.session.commit()
        flash('Request deleted')
    else:
        flash('Request not found')

    return jsonify({})

@app.route("/change_request_status", methods=["POST"])
def change_request_status():
    request_id = int(request.form.get("request_id"))
    new_status = request.form.get("new_status")

    req = Access_Request.query.filter_by(id=request_id).first()
    if req is not None:
        if req.status != "Ready":
            req.status=new_status
            db.session.commit()

            flash('Request changed')
        else:
            flash('Request cannot be changed ')
    else:
        flash('Request not found')

    return jsonify({})
    
@app.route("/remove_gdb_controller", methods=["POST"])
def remove_gdb_controller():
    gdbpid = int(request.form.get("gdbpid"))

    orphaned_client_ids = _state.remove_gdb_controller_by_pid(gdbpid)
    num_removed = len(orphaned_client_ids)

    send_msg_to_clients(
        orphaned_client_ids,
        "The underlying gdb process has been killed. This tab will no longer function as expected.",
        error=True,
    )

    msg = "removed %d gdb controller(s) with pid %d" % (num_removed, gdbpid)
    if num_removed:
        return jsonify({"message": msg})

    else:
        return jsonify({"message": msg}), 500

@app.route("/compile_and_flash", methods=["POST"])
def compile_and_flash():
    code = request.form.get("code")
    pid_str = str(request.form.get("pid"))
    try:
        pid_int = int(pid_str)
    except ValueError:
        return (
            jsonify(
                {
                    "message": "The pid %s cannot be converted to an integer."
                    % (pid_str)
                }
            ),
            400,
        )

    try:
        file_name = compile_program(code)

        return (
            jsonify(
                {
                    "message":  "The file is successfully compiled.",
                    "file_name" : file_name
                }
            )        
        )
    except ValueError as error:
        return (
            jsonify(
                {
                    "message":  f"Error during compilation: {error}."
                }
            ),
            400,
        )

@app.route("/gdbgui", methods=["GET"])
def gdbgui():
    """Render the main gdbgui interface"""
    interpreter = "lldb" if app.config["LLDB"] else "gdb"
    gdbpid = request.args.get("gdbpid", 0)
    initial_gdb_user_command = request.args.get("initial_gdb_user_command", "")

    THEMES = ["monokai", "light"]
    # fmt: off
    initial_data = {
        "gdbgui_version": __version__,
        "gdbpid": gdbpid,
        "initial_gdb_user_command": initial_gdb_user_command,
        "interpreter": interpreter,
        "initial_binary_and_args": app.config["initial_binary_and_args"],
        "project_home": app.config["project_home"],
        "remap_sources": app.config["remap_sources"],
        "rr": app.config["rr"],
        "themes": THEMES,
        "signals": SIGNAL_NAME_TO_OBJ,
        "using_windows": USING_WINDOWS,
    }
    # fmt: on

    return render_template(
        "gdbgui.html",
        version=__version__,
        debug=app.debug,
        interpreter=interpreter,
        initial_data=initial_data,
        themes=THEMES,
    )


@app.route("/send_signal_to_pid", methods=["POST"])
def send_signal_to_pid():
    signal_name = request.form.get("signal_name", "").upper()
    pid_str = str(request.form.get("pid"))
    try:
        pid_int = int(pid_str)
    except ValueError:
        return (
            jsonify(
                {
                    "message": "The pid %s cannot be converted to an integer. Signal %s was not sent."
                    % (pid_str, signal_name)
                }
            ),
            400,
        )

    if signal_name not in SIGNAL_NAME_TO_OBJ:
        raise ValueError("no such signal %s" % signal_name)
    signal_value = int(SIGNAL_NAME_TO_OBJ[signal_name])
    try:
        os.kill(pid_int, signal_value)
    except Exception:
        return (
            jsonify(
                {
                    "message": "Process could not be killed. Is %s an active PID?"
                    % pid_int
                }
            ),
            400,
        )
    return jsonify(
        {
            "message": "sent signal %s (%s) to process id %s"
            % (signal_name, signal_value, pid_str)
        }
    )


@app.route("/get_last_modified_unix_sec", methods=["GET"])
def get_last_modified_unix_sec():
    """Get last modified unix time for a given file"""
    path = request.args.get("path")
    if path and os.path.isfile(path):
        try:
            last_modified = os.path.getmtime(path)
            return jsonify({"path": path, "last_modified_unix_sec": last_modified})

        except Exception as e:
            return client_error({"message": "%s" % e, "path": path})

    else:
        return client_error({"message": "File not found: %s" % path, "path": path})


@app.route("/read_file", methods=["GET"])
def read_file():
    """Read a file and return its contents as an array"""
    path = request.args.get("path")
    start_line = int(request.args.get("start_line"))
    end_line = int(request.args.get("end_line"))

    start_line = max(1, start_line)  # make sure it's not negative

    try:
        highlight = json.loads(request.args.get("highlight", "true"))
    except Exception as e:
        if app.debug:
            print("Raising exception since debug is on")
            raise e

        else:
            highlight = (
                True  # highlight argument was invalid for some reason, default to true
            )

    if path and os.path.isfile(path):
        try:
            last_modified = os.path.getmtime(path)
            with open(path, "r") as f:
                raw_source_code_list = f.read().split("\n")
                num_lines_in_file = len(raw_source_code_list)
                end_line = min(
                    num_lines_in_file, end_line
                )  # make sure we don't try to go too far

                # if leading lines are '', then the lexer will strip them out, but we want
                # to preserve blank lines. Insert a space whenever we find a blank line.
                for i in range((start_line - 1), (end_line)):
                    if raw_source_code_list[i] == "":
                        raw_source_code_list[i] = " "
                raw_source_code_lines_of_interest = raw_source_code_list[
                    (start_line - 1) : (end_line)
                ]
            try:
                lexer = get_lexer_for_filename(path)
            except Exception:
                lexer = None

            if lexer and highlight:
                highlighted = True
                # convert string into tokens
                tokens = lexer.get_tokens("\n".join(raw_source_code_lines_of_interest))
                # format tokens into nice, marked up list of html
                formatter = (
                    htmllistformatter.HtmlListFormatter()
                )  # Don't add newlines after each line
                source_code = formatter.get_marked_up_list(tokens)
            else:
                highlighted = False
                source_code = raw_source_code_lines_of_interest

            return jsonify(
                {
                    "source_code_array": source_code,
                    "path": path,
                    "last_modified_unix_sec": last_modified,
                    "highlighted": highlighted,
                    "start_line": start_line,
                    "end_line": end_line,
                    "num_lines_in_file": num_lines_in_file,
                }
            )

        except Exception as e:
            return client_error({"message": "%s" % e})

    else:
        return client_error({"message": "File not found: %s" % path})

@socketio.on("connect", namespace="/gdb_listener")
def client_connected():
    if is_cross_origin(request):
        logger.warning("Received cross origin request. Aborting")
        abort(403)

    # see if user wants to connect to existing gdb pid
    desired_gdbpid = int(request.args.get("gdbpid", 0))

    payload = _state.connect_client(request.sid, desired_gdbpid)
    logger.info(
        'Client websocket connected in async mode "%s", id %s'
        % (socketio.async_mode, request.sid)
    )

    # tell the client browser tab which gdb pid is a dedicated to it
    emit("gdb_pid", payload)

    # Make sure there is a reader thread reading. One thread reads all instances.
    if _state.gdb_reader_thread is None:
        _state.gdb_reader_thread = socketio.start_background_task(
            target=read_and_forward_gdb_output
        )
        logger.info("Created background thread to read gdb responses")


@socketio.on("run_gdb_command", namespace="/gdb_listener")
def run_gdb_command(message):
    """
    Endpoint for a websocket route.
    Runs a gdb command.
    Responds only if an error occurs when trying to write the command to
    gdb
    """
    controller = _state.get_controller_from_client_id(request.sid)
    if controller is not None:
        try:
            # the command (string) or commands (list) to run
            cmd = message["cmd"]
            controller.write(cmd, read_response=False)

        except Exception:
            err = traceback.format_exc()
            logger.error(err)
            emit("error_running_gdb_command", {"message": err})
    else:
        emit("error_running_gdb_command", {"message": "gdb is not running"})

@socketio.on("disconnect", namespace="/gdb_listener")
def client_disconnected():
    """do nothing if client disconnects"""
    _state.disconnect_client(request.sid)
    logger.info("Client websocket disconnected, id %s" % (request.sid))


@socketio.on("Client disconnected")
def test_disconnect():
    print("Client websocket disconnected", request.sid)
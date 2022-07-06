from datetime import datetime
import random
import subprocess
import string
import traceback
import os

from flask import jsonify 
from pygdbmi.gdbcontroller import NoGdbProcessError 

from gdbgui.app.models import Access_Request
from gdbgui.backend import logger, socketio, db, _state

def update_request_status(user):
    reqs = user.acess_requests
    cur_time = datetime.today()
    update = False
    for req in reqs:
        if cur_time >= req.time_start and cur_time <= req.time_end:
            request_db = Access_Request.query.filter_by(id=req.id).first()
            request_db.status = "Ready"
            update = True
        
    if update:
        db.session.commit()

def can_connect_to_gdb(user):
    reqs = user.acess_requests
    cur_time = datetime.today()
    for req in reqs:
        if cur_time >= req.time_start and cur_time <= req.time_end:
            return True
    return False

def send_msg_to_clients(client_ids, msg, error=False):
    """Send message to all clients"""
    if error:
        stream = "stderr"
    else:
        stream = "stdout"

    response = [{"message": None, "type": "console", "payload": msg, "stream": stream}]

    for client_id in client_ids:
        logger.info("emiting message to websocket client id " + client_id)
        socketio.emit(
            "gdb_response", response, namespace="/gdb_listener", room=client_id
        )

def compile_program(code):
    clear_tmp_dir()

    random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    file_name = './tmp/' + random_name
    os.makedirs(os.path.dirname(f'{file_name}.s'), exist_ok=True)
    with open(f'{file_name}.s', "w", newline='\n') as f:
        f.write(code, )

    compile_str = f'arm-none-eabi-as -g -o {file_name}.o {file_name}.s'

    compile_proc = subprocess.Popen(compile_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    error = compile_proc.communicate()[1].decode("utf-8")

    if len(error) > 0:
        logger.info(f'Compile Error: {error}')
        raise ValueError(error)

    link_str = f'arm-none-eabi-ld -o {file_name}.elf -T stm32f103.ld {file_name}.o'

    link_proc = subprocess.Popen(link_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    error = link_proc.communicate()[1].decode("utf-8")
    
    if len(error) > 0:
        logger.info(f'Link Error: {error}')
        raise ValueError(error)

    return file_name + '.elf'

def clear_tmp_dir():
    path = './tmp/'
    if os.path.exists(path) :
        for file_name in os.listdir(path):
            file = path + file_name
            if os.path.isfile(file):
                os.remove(file)
    else :
        os.mkdir(path)

def server_error(obj):
    return jsonify(obj), 500


def client_error(obj):
    return jsonify(obj), 400
    
def is_cross_origin(request):
    """Compare headers HOST and ORIGIN. Remove protocol prefix from ORIGIN, then
    compare. Return true if they are not equal
    example HTTP_HOST: '127.0.0.1:5000'
    example HTTP_ORIGIN: 'http://127.0.0.1:5000'
    """
    origin = request.environ.get("HTTP_ORIGIN")
    host = request.environ.get("HTTP_HOST")
    if origin is None:
        # origin is sometimes omitted by the browser when origin and host are equal
        return False

    if origin.startswith("http://"):
        origin = origin.replace("http://", "")
    elif origin.startswith("https://"):
        origin = origin.replace("https://", "")
    return host != origin

    
def read_and_forward_gdb_output():
    """A task that runs on a different thread, and emits websocket messages
    of gdb responses"""

    while True:
        socketio.sleep(0.05)
        controllers_to_remove = []
        controller_items = _state.controller_to_client_ids.items()
        for controller, client_ids in controller_items:
            try:
                try:
                    response = controller.get_gdb_response(
                        timeout_sec=0, raise_error_on_timeout=False
                    )
                except NoGdbProcessError:
                    response = None
                    send_msg_to_clients(
                        client_ids,
                        "The underlying gdb process has been killed. This tab will no longer function as expected.",
                        error=True,
                    )
                    controllers_to_remove.append(controller)

                if response:
                    for client_id in client_ids:
                        logger.info(
                            "emiting message to websocket client id " + client_id
                        )
                        socketio.emit(
                            "gdb_response",
                            response,
                            namespace="/gdb_listener",
                            room=client_id,
                        )
                else:
                    # there was no queued response from gdb, not a problem
                    pass

            except Exception:
                logger.error(traceback.format_exc())

        for controller in controllers_to_remove:
            _state.remove_gdb_controller(controller)
# Copyright (c) 2019 GalaxyLearning Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import json
import logging
from flask import Flask, send_from_directory, request
from werkzeug.serving import run_simple
from gfl.entity.runtime_config import RuntimeServerConfig
from gfl.core.job_manager import JobManager
from gfl.utils.json_utils import JsonUtil
from gfl.settings import JOB_SERVER_DIR_PATH, BASE_MODEL_DIR_PATH, RUNTIME_CONFIG_SERVER_PATH
from gfl.utils.utils import JobEncoder, return_data_decorator, LoggerFactory, RuntimeConfigUtils

API_VERSION = "/api/v1"

logger = LoggerFactory.getLogger(__name__, logging.INFO)

app = Flask(__name__)


@app.route("/test/<name>")
@return_data_decorator
def test_flask_server(name):
    return name, 200


@app.route("/register/<ip>/<port>/<client_id>", methods=['POST'], endpoint='register_trainer')
@return_data_decorator
def register_trainer(ip, port, client_id):
    trainer_host = ip + ":" + port

    if not os.path.exists(RUNTIME_CONFIG_SERVER_PATH):
        return 'server has internal error', 203

    runtime_server_config = RuntimeConfigUtils.get_obj_from_runtime_config_file(RUNTIME_CONFIG_SERVER_PATH,
                                                                                RuntimeServerConfig)
    if trainer_host not in runtime_server_config.CONNECTED_TRAINER_LIST:
        job_list = JobManager.get_job_list(JOB_SERVER_DIR_PATH)
        for job in job_list:
            job_model_client_dir = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job.get_job_id()),
                                                "models_{}".format(client_id))
            if not os.path.exists(job_model_client_dir):
                os.makedirs(job_model_client_dir)
        runtime_server_config.CONNECTED_TRAINER_LIST.append(trainer_host)
        RuntimeConfigUtils.write_obj_to_runtime_config_file(runtime_server_config, RUNTIME_CONFIG_SERVER_PATH)
        return 'register_success', 200
    else:
        return 'already connected', 201


@app.route("/offline/<ip>/<port>", methods=['PUT'], endpoint='offline')
@return_data_decorator
def offline(ip, port):
    trainer_host = ip + ":" + port
    runtime_server_config = RuntimeConfigUtils.get_obj_from_runtime_config_file(RUNTIME_CONFIG_SERVER_PATH,
                                                                                RuntimeServerConfig)
    if trainer_host in runtime_server_config.CONNECTED_TRAINER_LIST:
        runtime_server_config.CONNECTED_TRAINER_LIST.remove(trainer_host)
        RuntimeConfigUtils.write_obj_to_runtime_config_file(runtime_server_config, RUNTIME_CONFIG_SERVER_PATH)
        return 'offline success', 200
    return 'already offline', 201


@app.route("/jobs", methods=['GET'], endpoint='acquire_job_list')
@return_data_decorator
def acquire_job_list():
    job_str_list = []
    job_list = JobManager.get_job_list(JOB_SERVER_DIR_PATH)
    for job in job_list:
        job_str = json.dumps(job, cls=JobEncoder)
        job_str_list.append(job_str)
    return job_str_list, 200


@app.route("/modelpars/<job_id>", methods=['GET'], endpoint='acquire_init_model_pars')
def acquire_init_model_pars(job_id):
    init_model_pars_dir = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id))
    return send_from_directory(init_model_pars_dir, "init_model_pars_{}".format(job_id), as_attachment=True)


@app.route("/init_model/<job_id>", methods=['GET'], endpoint='acquire_init_model')
def acquire_init_model(job_id):
    init_model_path = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id))
    return send_from_directory(init_model_path, "init_model_{}".format(job_id), as_attachment=True)


@app.route("/modelpars/<client_id>/<job_id>/<fed_step>", methods=['POST'], endpoint='submit_model_parameter')
@return_data_decorator
def submit_model_parameter(client_id, job_id, fed_step):
    tmp_parameter_file = request.files['tmp_parameter_file']
    model_pars_dir = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id), "models_{}".format(client_id))
    if not os.path.exists(model_pars_dir):
        os.makedirs(model_pars_dir)
    model_pars_path = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id), "models_{}".format(client_id),
                                   "tmp_parameters_{}".format(fed_step))
    with open(model_pars_path, "wb") as f:
        for line in tmp_parameter_file.readlines():
            f.write(line)

    return 'submit_success', 200


@app.route("/otherparameters/<job_id>/<client_id>/<fed_step>", methods=['GET'], endpoint='get_other_parameters')
def get_other_parameters(job_id, client_id, fed_step):
    tmp_parameter_dir = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id), "models_{}".format(client_id))
    tmp_parameter_path = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id), "models_{}".format(client_id),
                                      "tmp_parameters_{}".format(fed_step))

    if not os.path.exists(tmp_parameter_path):
        return 'file not prepared', 201

    return send_from_directory(tmp_parameter_dir, "tmp_parameters_{}".format(fed_step), as_attachment=True), 202


@app.route("/otherclients/<job_id>", methods=['GET'], endpoint='get_connected_clients')
@return_data_decorator
def get_connected_clients(job_id):
    connected_clients_id = []
    job_model_path = os.path.join(BASE_MODEL_DIR_PATH, "models_{}".format(job_id))
    for model_dir in os.listdir(job_model_path):
        if model_dir.find("models_") != -1:
            connected_clients_id.append(int(model_dir.split("_")[-1]))

    return connected_clients_id, 200


@app.route("/aggregatepars", methods=['GET'], endpoint='get_aggregate_parameter')
@return_data_decorator
def get_aggregate_parameter():
    return ''


def start_communicate_server(api_version, ip, port):
    app.url_map.strict_slashes = False
    run_simple(hostname=ip, port=port, application=app, threaded=True)
    logger.info("galaxy learning server started")

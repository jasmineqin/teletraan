# Copyright 2016 Pinterest, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

# -*- coding: utf-8 -*-
"""Collection of all environs related calls"""

import logging
from deploy_board.webapp.helpers.deployclient import DeployClient
from deploy_board.settings import IS_PINTEREST

log = logging.getLogger(__name__)


DEFAULT_ENV_SIZE = 30
BUILD_STAGE = "BUILD"

DEPLOY_STAGE_VALUES = [
    "UNKNOWN",
    "PRE_DOWNLOAD",
    "DOWNLOADING",
    "POST_DOWNLOAD",
    "STAGING",
    "PRE_RESTART",
    "RESTARTING",
    "POST_RESTART",
    "SERVING_BUILD",
    "STOPPING",
    "STOPPED",
]

DEPLOY_PRIORITY_VALUES = ["LOWER", "LOW", "NORMAL", "HIGH", "HIGHER"]

ACCEPTANCE_TYPE_VALUES = ["AUTO", "MANUAL"]

ACCEPTANCE_STATUS_VALUES = [
    "PENDING_DEPLOY",
    "OUTSTANDING",
    "PENDING_ACCEPT",
    "ACCEPTED",
    "REJECTED",
    "TERMINATED",
]

AGENT_STATE_VALUES = [
    "NORMAL",
    "PAUSED_BY_SYSTEM",
    "PAUSED_BY_USER",
    "RESET",
    "RESET_BY_SYSTEM",
    "DELETE",
    "UNREACHABLE",
    "STOP",
]

AGENT_STATUS_VALUES = [
    "SUCCEEDED",
    "UNKNOWN",
    "AGENT_FAILED",
    "RETRYABLE_AGENT_FAILED",
    "SCRIPT_FAILED",
    "ABORTED_BY_SERVICE",
    "SCRIPT_TIMEOUT",
    "TOO_MANY_RETRY",
    "RUNTIME_MISMATCH",
]

PROMOTE_TYPE_VALUES = ["MANUAL", "AUTO"]

PROMOTE_FAILED_POLICY_VALUES = ["CONTINUE", "DISABLE", "ROLLBACK"]

PROMOTE_DISABLE_POLICY_VALUES = ["MANUAL", "AUTO"]

OVERRIDE_POLICY_VALUES = ["OVERRIDE", "WARN"]

DEPLOY_CONSTRAINT_TYPES = ["GROUP_BY_GROUP", "ALL_GROUPS_IN_PARALLEL"]

# Fetch from backend to avoid maintainng at multiple places?
STAGE_TYPES = ["DEFAULT", "LATEST", "DEV", "STAGING", "CANARY", "CONTROL", "PRODUCTION"]

deployclient = DeployClient()

if IS_PINTEREST:
    from deploy_board.webapp.helpers.nimbusclient import NimbusClient

    nimbusclient = NimbusClient()

# Nimbus-related helpers


def create_identifier_for_new_stage(request, env_name, stage_name):
    """Create a Nimbus Identifier for the new stage. Assumes that the environment has at least one stage with externalId set.
    This is needed so that the method knows which project to associate the new stage to.

    If the environment has no stage with externalId set, this method will not attempt to create an Identifier.
    """
    # Only create identifier for Pinterest environments
    if not IS_PINTEREST:
        return None

    # get all stages within this environment
    all_env_stages = get_all_env_stages(request, env_name)
    stage_with_external_id = None

    # find a stage in this environment that has externalId set
    for env_stage in all_env_stages:
        if env_stage["externalId"] is not None:
            stage_with_external_id = env_stage
            break

    if stage_with_external_id is None:
        return None

    # retrieve Nimbus identifier for existing_stage
    existing_stage_identifier = get_nimbus_identifier(
        request, stage_with_external_id["externalId"]
    )
    # create Nimbus Identifier for the new stage
    new_stage_identifier = None
    if existing_stage_identifier is not None:
        nimbus_request_data = existing_stage_identifier.copy()
        nimbus_request_data["stage_name"] = stage_name
        nimbus_request_data["env_name"] = env_name
        new_stage_identifier = create_nimbus_identifier(request, nimbus_request_data)

    # if there is no stage in this env with externalId, still create the new stage
    if new_stage_identifier is None:
        return None
    return new_stage_identifier.get("uuid")


def get_nimbus_identifier(request, name):
    return nimbusclient.get_one_identifier(name, token=request.teletraan_user_id.token)


def create_nimbus_identifier(request, data):
    return nimbusclient.create_one_identifier(
        data, token=request.teletraan_user_id.token
    )


def delete_nimbus_identifier(request, name):
    # Nimbus identifiers are only for Pinterest environments
    if not IS_PINTEREST:
        return None
    return nimbusclient.delete_one_identifier(
        name, token=request.teletraan_user_id.token
    )


def get_nimbus_project_console_url(project_name):
    return nimbusclient.get_one_project_console_url(project_name)


# Teletraan Deploy client helpers


def set_external_id_on_stage(request, env_name, stage_name, external_id):
    return deployclient.post(
        "/envs/{}/{}/external_id".format(env_name, stage_name),
        request.teletraan_user_id.token,
        data=external_id,
    )


def get_all_env_names(
    request, name_filter=None, name_only=True, index=1, size=DEFAULT_ENV_SIZE
):
    params = [("pageIndex", index), ("pageSize", size)]
    if name_filter:
        params.append(("nameFilter", name_filter))
    return deployclient.get(
        "/envs/names", request.teletraan_user_id.token, params=params
    )


def get_all_env_stages(request, env_name):
    return deployclient.get(
        "/envs", request.teletraan_user_id.token, params=[("envName", env_name)]
    )


def get_all_envs_by_group(request, group_name):
    params = [("groupName", group_name)]
    return deployclient.get("/envs/", request.teletraan_user_id.token, params=params)


def get_all_sidecar_envs(request):
    return deployclient.get("/envs/sidecars", request.teletraan_user_id.token)


def get(request, id):
    return deployclient.get("/envs/%s" % id, request.teletraan_user_id.token)


def get_env_by_stage(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s" % (env_name, stage_name), request.teletraan_user_id.token
    )


def get_env_capacity(request, env_name, stage_name, capacity_type=None):
    params = []
    if capacity_type:
        params.append(("capacityType", capacity_type))
    return deployclient.get(
        "/envs/%s/%s/capacity" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
    )


def update_env_capacity(request, env_name, stage_name, capacity_type=None, data=None):
    params = []
    if capacity_type:
        params.append(("capacityType", capacity_type))
    return deployclient.put(
        "/envs/%s/%s/capacity" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=data,
    )


def add_env_capacity(request, env_name, stage_name, capacity_type=None, data=None):
    params = []
    if capacity_type:
        params.append(("capacityType", capacity_type))
    return deployclient.post(
        "/envs/%s/%s/capacity" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=data,
    )


def remove_env_capacity(request, env_name, stage_name, capacity_type=None, data=None):
    params = []
    if capacity_type:
        params.append(("capacityType", capacity_type))
    return deployclient.delete(
        "/envs/%s/%s/capacity" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=data,
    )


def create_env(request, data):
    return deployclient.post("/envs", request.teletraan_user_id.token, data=data)


def update_env_basic_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_script_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/script_configs" % (env_name, stage_name),
        request.teletraan_user_id.token,
    )


def update_env_script_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/script_configs" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_agent_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/agent_configs" % (env_name, stage_name),
        request.teletraan_user_id.token,
    )


def update_env_agent_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/agent_configs" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_alarms_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/alarms" % (env_name, stage_name), request.teletraan_user_id.token
    )


def update_env_alarms_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/alarms" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_metrics_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/metrics" % (env_name, stage_name), request.teletraan_user_id.token
    )


def update_env_metrics_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/metrics" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_hooks_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/web_hooks" % (env_name, stage_name),
        request.teletraan_user_id.token,
    )


def update_env_hooks_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/web_hooks" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def get_env_promotes_config(request, env_name, stage_name):
    return deployclient.get(
        "/envs/%s/%s/promotes" % (env_name, stage_name), request.teletraan_user_id.token
    )


def update_env_promotes_config(request, env_name, stage_name, data):
    return deployclient.put(
        "/envs/%s/%s/promotes" % (env_name, stage_name),
        request.teletraan_user_id.token,
        data=data,
    )


def delete_env(request, env_name, stage_name):
    return deployclient.delete(
        "/envs/%s/%s" % (env_name, stage_name), request.teletraan_user_id.token
    )


def get_config_history(request, env_name, stage_name, index, size):
    params = [("pageIndex", index), ("pageSize", size)]
    return deployclient.get(
        "/envs/%s/%s/history" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
    )


def set_active_max_parallel(env):
    max_parallel_pecentage = int(env["maxParallelPct"])
    env["showNumber"] = True
    if max_parallel_pecentage > 0:
        env["showNumber"] = False


def enable_all_env_changes(request, description):
    params = [("actionType", "ENABLE"), ("description", description)]
    return deployclient.post(
        "/envs/actions", request.teletraan_user_id.token, params=params
    )


def disable_all_env_changes(request, description):
    params = [("actionType", "DISABLE"), ("description", description)]
    return deployclient.post(
        "/envs/actions", request.teletraan_user_id.token, params=params
    )


def enable_env_changes(request, env_name, stage_name, description):
    params = [("actionType", "ENABLE"), ("description", description)]
    return deployclient.post(
        "/envs/%s/%s/actions" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
    )


def disable_env_changes(request, env_name, stage_name, description):
    params = [("actionType", "DISABLE"), ("description", description)]
    return deployclient.post(
        "/envs/%s/%s/actions" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
    )


def pause_hosts(request, env_name, stage_name, host_ids):
    params = [("actionType", "PAUSED_BY_USER")]
    return deployclient.put(
        "/envs/%s/%s/deploys/hostactions" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=host_ids,
    )


def resume_hosts(request, env_name, stage_name, host_ids):
    params = [("actionType", "NORMAL")]
    return deployclient.put(
        "/envs/%s/%s/deploys/hostactions" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=host_ids,
    )


def reset_hosts(request, env_name, stage_name, host_ids):
    params = [("actionType", "RESET")]
    return deployclient.put(
        "/envs/%s/%s/deploys/hostactions" % (env_name, stage_name),
        request.teletraan_user_id.token,
        params=params,
        data=host_ids,
    )


def get_env_pindeploy(request, env_name, stage_name):
    params = [("envName", env_name), ("stageName", stage_name)]
    return deployclient.get(
        "/pindeploy", request.teletraan_user_id.token, params=params
    )

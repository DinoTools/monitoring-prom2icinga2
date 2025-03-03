# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
from datetime import datetime
import json
import logging
from pprint import pprint
import re
import types
from typing import Any, Dict, List, Optional, Set

import httpx
import jinja2
from pydantic import BaseModel

from .config import g_check_configs, CheckConfig
from .prometheus import query_prometheus

logger = logging.getLogger()
icinga2_service_cache: Dict[str, Dict] = {}


class IcingaHost(list):
    def __init__(self, name: str, icinga2_client: httpx.AsyncClient):
        super().__init__()
        self.name = name
        self.prom_queries: Set[str] = set()
        self.icinga2_client = icinga2_client

    def append(self, item: "IcingaService"):
        if not isinstance(item, IcingaService):
            raise ValueError("Wrong type for item")

        self.prom_queries.update(set(item.prom_queries.values()))
        item.icinga_host = self
        super().append(item)

    async def process(self, prometheus_client: httpx.AsyncClient):
        fetched_metrics = {}

        prometheus_query_tasks: Dict[str, Any] = {}
        for prom_query in self.prom_queries:
            prometheus_query_tasks[prom_query] = asyncio.create_task(
                query_prometheus(
                    prometheus_client,
                    prom_query
                )
            )

        for prom_query, query_task in prometheus_query_tasks.items():
            result_data = await query_task
            results = result_data["data"]["result"]
            fetched_metrics[prom_query] = results

        icinga_tasks = []
        for icinga_service in self:
            icinga_tasks.append(
                asyncio.create_task(
                    icinga_service.process(
                        fetched_metrics
                    )
                )
            )

        for icinga_task in icinga_tasks:
            await icinga_task


class IcingaService:
    def __init__(
            self,
            name: str,
            check,
            group_label_value: Optional[str] = None,
            group_label_value_regex: bool = False,
            query_labels: Optional[Dict[str, str]] = None,
            value_threshold_configs: Optional[Dict[str, "Icinga2ServiceThresholdConfig"]] = None):
        self.name = name
        self.check = check
        self.icinga_host: Optional[IcingaHost] = None

        prom_check = g_check_configs.get(self.check)
        if prom_check is None:
            raise Exception(f"Unable to get prom check with name '{self.check}' from config")
        self.check_config: CheckConfig = prom_check

        self.group_label_value: Optional[re.Pattern] = None
        if isinstance(group_label_value, str):
            if group_label_value_regex:
                self.group_label_value = re.compile(group_label_value)
            else:
                self.group_label_value = re.compile(re.escape(group_label_value))

        self.query_labels: Dict[str, str] = {}
        if query_labels is not None:
            self.query_labels.update(query_labels)

        self.long_output_template: Optional[jinja2.environment.Template] = None
        if self.check_config.long_output:
            self.long_output_template = jinja2.Environment().from_string(self.check_config.long_output)

        self.prom_queries: Dict[str, str] = {}
        self.value_conditions: Dict[str, types.CodeType] = {}
        self.value_thresholds: Dict[str, "Threshold"] = {}

        if not isinstance(value_threshold_configs, dict):
            value_threshold_configs = {}

        for value_name, value_config in self.check_config.values.items():
            # Queries
            formated_query_labels: List[str] = []
            for n, v in self.query_labels.items():
                formated_query_labels.append(f'{n} = "{v}"')

            self.prom_queries[value_name] = value_config.query.format(labels=", ".join(formated_query_labels))

            # Thresholds
            value_warning = value_config.warning
            value_critical = value_config.critical
            value_condition = value_config.condition
            value_threshold_config = value_threshold_configs.get(value_name)
            if value_threshold_config:
                if value_threshold_config.warning:
                    value_warning = value_threshold_config.warning
                if value_threshold_config.critical:
                    value_critical = value_threshold_config.critical
                if value_threshold_config.condition:
                    value_condition = value_threshold_config.condition

            self.value_thresholds[value_name] = Threshold(
                value_name,
                condition=value_condition,
                warning=value_warning,
                critical=value_critical,
            )

    async def process(self, fetched_metrics: Dict[str, Any]):
        if self.group_label_value is None:
            await self.process_values(fetched_metrics)
        else:
            await self.process_group_values(fetched_metrics)

    async def process_group_values(self, fetched_metrics):
        value_groups = {}
        for value_name, prom_query in self.prom_queries.items():
            metrics = fetched_metrics.get(prom_query)
            for metric in metrics:
                group_label_value = metric["metric"].get(self.check_config.group_label_name)
                if not group_label_value:
                    continue
                if not self.group_label_value.match(group_label_value):
                    continue
                if group_label_value not in value_groups:
                    value_groups[group_label_value] = {}
                value_groups[group_label_value][value_name] = float(metric["value"][1])

        result_value_groups = {}
        for value_group_name, value_group_values in value_groups.items():
            result_values = {}
            for name, value in value_group_values.items():
                threshold = self.value_thresholds.get(name)
                if not threshold:
                    result_values[name] = ResultValue(value)
                else:
                    result_values[name] = threshold.check(value, value_group_values)
            result_value_groups[value_group_name] = result_values

        result_status: int = 0
        output_messages: List[str] = []
        for result_values in result_value_groups.values():
            for result_value in result_values.values():
                if result_value.status > result_status:
                    result_status = result_value.status
                    output_messages = []
                if result_value.status == result_status:
                    output_messages.extend(result_value.output_messages)

        long_output_messages: List[str] = []
        if self.long_output_template:
            logger.debug("Rendering long output")
            long_output_messages.append(
                self.long_output_template.render(
                    result_group_values=result_value_groups
                )
            )

        await self.report(
            result_status=result_status,
            output_messages=output_messages,
            long_output_messages=long_output_messages,
        )

    async def process_values(self, fetched_metrics):
        values = {}
        result_status = 0
        output_messages: List[str] = []

        for value_name, prom_query in self.prom_queries.items():
            metrics = fetched_metrics.get(prom_query)
            if len(metrics) == 0:
                values[value_name] = None
            else:
                values[value_name] = float(metrics[0]["value"][1])

        result_values = {}
        for name, value in values.items():
            threshold = self.value_thresholds.get(name)
            if not threshold:
                result_values[name] = ResultValue(value)
            else:
                result_values[name] = threshold.check(value, values)

        for result_value in result_values.values():
            if result_value.status > result_status:
                result_status = result_value.status
                output_messages = []
            if result_value.status == result_status:
                output_messages.extend(result_value.output_messages)

        await self.report(
            result_status=result_status,
            output_messages=output_messages,
        )

    async def report(
            self,
            result_status: int,
            output_messages: Optional[List[str]] = None,
            long_output_messages: Optional[List[str]] = None):
        if self.icinga_host is None:
            raise Exception("Internal error: Unable to report because icinga host not connected")

        output: List[str] = []

        if output_messages and len(output_messages) > 0:
            output.append(f"OK - {'; '.join(output_messages)}")
        else:
            output.append("OK")

        if long_output_messages and len(long_output_messages) > 0:
            output.append("")
            output.extend(long_output_messages)

        post_data = {
            "type": "Service",
            "filter": f"host.name==\"{self.icinga_host.name}\" && service.name==\"{self.name}\"",
            "state": result_status,
            "exit_status": result_status,
            "plugin_output": "\n".join(output),

            # "check_source": "example.localdomain"
        }

        post_data_raw = json.dumps(post_data)
        rp_req = self.icinga_host.icinga2_client.build_request(
            "post",
            "/v1/actions/process-check-result",
            headers={
                "Accept": "application/json",
            },
            content=post_data_raw
        )
        await self.icinga_host.icinga2_client.send(rp_req)

    @classmethod
    def from_config(cls, name, config: "Icinga2ServiceConfig"):
        return cls(
            name=name,
            check=config.check,
            group_label_value=config.group_label_value,
            group_label_value_regex=config.group_label_value_regex,
            query_labels=config.query_labels,
            value_threshold_configs=config.value_thresholds,
        )


class Icinga2ServiceConfig(BaseModel):
    check: str
    group_label_value: Optional[str] = None
    group_label_value_regex: bool = False
    query_labels: Dict[str, str]
    value_thresholds: Dict[str, "Icinga2ServiceThresholdConfig"] = {}


class Icinga2ServiceThresholdConfig(BaseModel):
    warning: Optional[str] = None
    critical: Optional[str] = None
    condition: Optional[str] = None


class ResultValue:
    STATUS_TEXT_MAPPINGS: Dict[int, str] = {
        0: "OK",
        1: "Warning",
        2: "Critical",
        3: "Unkown"
    }

    def __init__(
            self,
            value,
            status: int = 0,
            threshold: Optional["Threshold"] = None,
            output_messages: Optional[List[str]] = None):
        self.value = value
        self.status = status
        self.threshold = threshold
        if output_messages is None:
            self.output_messages = []
        else:
            self.output_messages = output_messages

    @property
    def status_text(self):
        return self.STATUS_TEXT_MAPPINGS.get(self.status, "n/a")


class Threshold:
    REGEX = re.compile(r"(?P<value>\d+)((?P<percent>%)(?P<reference_name>\w+))")
    REGEX_SIMPLE = re.compile(r"^(?P<operator>(>|<|=|<=|>=|!=)).*")

    def __init__(self, name, condition, warning, critical):
        self.name = name

        self.condition = None
        if condition:
            self.condition = compile(
                condition,
                condition,
                "eval"
            )

        self.warning = None
        if warning:
            self.warning = self._compile_threshold(warning)

        self.critical = None
        if critical:
            self.critical = self._compile_threshold(critical)

    def _compile_threshold(self, threshold_value):
        def _replace_percent(match_obj):
            value = float(match_obj.group("value"))
            value /= 100
            return f"{value} * {match_obj.group('reference_name')}"

        threshold_value = threshold_value.strip()
        m = self.REGEX_SIMPLE.match(threshold_value)
        if m:
            threshold_code = "value " + self.REGEX.sub(_replace_percent, threshold_value, 1)
        else:
            threshold_code = self.REGEX.sub(_replace_percent, threshold_value)

        return compile(threshold_code, threshold_code, "eval")

    def check(self, value: float, values: Dict[str, float]):
        local_values = {"value": value}
        local_values.update(values)

        if self.condition and not eval(self.condition, {}, local_values):
            return ResultValue(
                value,
                status=0,
                threshold=self,
            )

        if value is None:
            return ResultValue(
                value,
                status=3,
                threshold=self,
                output_messages=[f"Unable to get value for '{self.name}'"]
            )
        if self.critical and eval(self.critical, {}, local_values):
            return ResultValue(
                value,
                status=2,
                threshold=self,
            )
        if self.warning and eval(self.warning, {}, local_values):
            return ResultValue(
                value,
                status=1,
                threshold=self,
            )
        return ResultValue(
            value,
            status=0,
            threshold=self,
        )


async def get_icinga2_host(host_name: str, icinga2_client: httpx.AsyncClient):
    global icinga2_service_cache
    cache_entry_name = f"{host_name}"
    cached_services = icinga2_service_cache.get(cache_entry_name)
    if cached_services:
        timedelta = datetime.now() - cached_services["timestamp"]
        if timedelta.seconds < 600:
            print("use cache")
            return cached_services["services"]

    req_data = {
        "attrs": ["name", "vars"],
        "filter": "host_name == host.name && service.vars.prom2icinga_check",
        "filter_vars": {
            "host_name": host_name,
        },
    }
    pprint(req_data)
    req_data_json = json.dumps(req_data)
    rp_req = icinga2_client.build_request(
        "post",
        "/v1/objects/services",
        headers={
            "Accept": "application/json",
            "X-HTTP-Method-Override": "GET",
        },
        content=req_data_json
    )
    rp_resp = await icinga2_client.send(rp_req)
    rp_resp_data = rp_resp.json()

    services = IcingaHost(name=host_name, icinga2_client=icinga2_client)

    for service in rp_resp_data["results"]:
        attributes = service["attrs"]
        tmp_config = {}
        for n, v in attributes["vars"].items():
            base_name, _, value_name = n.partition("_")
            if base_name == "prom2icinga":
                tmp_config[value_name] = v

        services.append(
            IcingaService.from_config(
                attributes["name"],
                Icinga2ServiceConfig.model_validate(tmp_config)
            )
        )

    icinga2_service_cache[cache_entry_name] = {
        "services": services,
        "timestamp": datetime.now(),
    }
    return services

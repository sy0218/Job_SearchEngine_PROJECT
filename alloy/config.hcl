logging {
  level = "info"
}

loki.write "default" {
  endpoint {
    url = "http://192.168.122.59:3100/loki/api/v1/push"
  }
}

local.file_match "collector_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/collector/*.log",
    job      = "collector",
    host     = constants.hostname,
  }]
}

loki.source.file "collector" {
  targets    = local.file_match.collector_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "consumer_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/consumer/*.log",
    job      = "consumer",
    host     = constants.hostname,
  }]
}

loki.source.file "consumer" {
  targets    = local.file_match.consumer_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "hadoop_upload_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/hadoop_upload/*.log",
    job      = "hadoop_upload",
    host     = constants.hostname,
  }]
}

loki.source.file "hadoop_upload" {
  targets    = local.file_match.hadoop_upload_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "hadoop_event_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/hadoop_event/*.log",
    job      = "hadoop_event",
    host     = constants.hostname,
  }]
}

loki.source.file "hadoop_event" {
  targets    = local.file_match.hadoop_event_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "ocr_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/ocr/*.log",
    job      = "ocr",
    host     = constants.hostname,
  }]
}

loki.source.file "ocr" {
  targets    = local.file_match.ocr_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "warehouse_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/warehouse/*.log",
    job      = "warehouse",
    host     = constants.hostname,
  }]
}

loki.source.file "warehouse" {
  targets    = local.file_match.warehouse_logs.targets
  forward_to = [loki.write.default.receiver]
}

local.file_match "es_upload_logs" {
  path_targets = [{
    __path__ = "/work/jsy/job_project/logs/es_upload/*.log",
    job      = "es_upload",
    host     = constants.hostname,
  }]
}

loki.source.file "es_upload" {
  targets    = local.file_match.es_upload_logs.targets
  forward_to = [loki.write.default.receiver]
}

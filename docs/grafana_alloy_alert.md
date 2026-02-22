# 📈 Grafana 기반 중앙 로그 수집 및 에러 알람 시스템 구축


# 🛑 Problem (문제)

> **서비스가 확장되고 서버가 많아질수록 기존 방식의 로그 확인은 다음과 같은 한계를 가짐**

- 서버마다 ssh 접속 → 로그 직접 확인해야 함  
- 에러/오류 탐지가 지연됨  
- 특정 서비스/호스트에서 나타나는 문제의 원인 파악 시간이 매우 오래 걸림  
- **전체 시스템 장애 파악이 어려워 운영 비용이 증가함**

**기존 방식 예시:**
```bash
ssh server1
tail -f consumer.log

ssh server2
grep ERROR service.log
```
> **분산된 로그 확인은 운영 비용이 증가 → 로그 통합 필요성 체감**

---
<br>

## ⚙ 트러블슈팅 방법 (Solution)
> **서비스 로그를 중앙집중식으로 수집, 검색, 시각화, 알람까지 동시에 처리할 수 있는 구조로 전환**
---
### 1️⃣ Promtail vs Alloy
- 처음엔 단순 로그 수집 목적이라 Promtail을 생각했습니다.
- 그런데 조사해보니 → Promtail은 2026년 3월 EOL 예정.

#### 🤔 왜?
- 요즘은 OpenTelemetry 기반 표준화 흐름
로그 + 메트릭 + 트레이스 → 이걸 하나의 에이전트로 통합하는 방향
> 장기적으로 확장성을 고려해 Alloy를 선택
---
### 2️⃣ 아키텍처 선택
- Grafana Alloy → Grafana Loki → Grafana 시각화 & Alert 시스템
```bash
[App Servers]
     ↓
 Alloy (Central Collector Agent)
     ↓
 Loki (Log 저장 + 검색)
     ↓
 Grafana (시각화 + Alert)
     ↓
 Slack (에러 알람)
```
#### ✔ 서버 접속 없이 로그 필터링 가능
#### ✔ 서비스/호스트 단위로 로그 확인 가능
#### ✔ 조건 만족 시 실시간 에러 알림 가능
---
### 3️⃣ Loki 서버 구축
#### **✔ Loki-config.yaml**
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s
  wal:
    enabled: true
    dir: /loki/wal

schema_config:
  configs:
    - from: 2026-02-19
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/index_cache
    cache_ttl: 24h
  filesystem:
    directory: /loki/chunks

limits_config:
  retention_period: 72h

compactor:
  working_directory: /loki/compactor
```
#### **✔ Docker 실행**
```bash
docker run -d --name loki \
  -p 3100:3100 \
  -v -v /work/jsy/job_project/loki/loki-config.yaml:/etc/loki/config.yaml \
  -v /work/jsy/job_project/loki/data:/loki \
  -v /etc/localtime:/etc/localtime:ro \
  -v /etc/timezone:/etc/timezone:ro \
  grafana/loki:2.9.4 \
  -config.file=/etc/loki/config.yaml
```
#### **✔ Loki 정상 기동 확인**
```bash
curl http://LOKI_IP:3100/ready
# ready → 정상
```
----
### 4️⃣ Grafana에 Loki 데이터 소스 연결
> Grafana UI → Settings → Data Sources → Add → Loki
- URL: `http://LOKI_IP:3100`
- 연결 성공 시 데이터 소스 준비 완료
---
### 5️⃣ Alloy 설치 (각 서버)
> Alloy는 실서버 로그를 Loki로 전달하는 에이전트
```bash
wget https://github.com/grafana/alloy/releases/latest/download/alloy-linux-amd64.zip
unzip alloy-linux-amd64.zip
chmod +x alloy-linux-amd64
mv alloy-linux-amd64 /usr/local/bin/alloy
```
#### **✔ config.hcl**
```hcl
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
```
#### ✔ **systemd 서비스 등록**
```INI
[Unit]
Description=Alloy Log Collector

[Service]
ExecStart=/usr/local/bin/alloy run /opt/alloy/config.hcl
User=root

[Install]
WantedBy=multi-user.target
```
#### ✔ **systemd 서비스 실행**
```bash
systemctl daemon-reload
systemctl start alloy
systemctl enable alloy
```
#### ✔ **Grafana에서 확인**
```bash
Explore → Loki
{job="ocr"}
→ 로그가 쭉 나오면 성공 🎉
```
---
### 6️⃣ 에러 알람 설정
#### ✔ **Slack Webhook 만들기**
>생성 사이트 → https://api.slack.com/apps 
- Slack 접속
- Create App → Incoming Webhooks 활성화 → Webhook URL 생성
- URL 복사 ( ex.. : https://hooks.slack.com/services/XXXXX/XXXXX/XXXXX )


#### ✔ **Grafana에서 Slack 연결**
> Grafana ui 접속 → Grafana 좌측 메뉴 → Alerting → Contact points
- Create contact point
- Type → Slack 선택
- Webhook URL 붙여넣기
- **메시지 템플릿 설정 ( Optional Slack settings )**
```Plain text
Title : {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}
Text  : {{ with index .Alerts 0 }}{{ .Annotations.description }}{{ end }}
```
- 테스트 발송 → Slack 채널에 정상적으로 도착하는지 확인


#### ✔ **Loki 기반 Alert Rule 만들기**
> Grafana ui 접속 → Grafana 좌측 메뉴 → Alerting → Alert rules → New alert rule
```text
1. Enter alert rule name - 기본 정보 설정
> ocr_alert

2. Define query and alert condition - Query 및 Alert 조건 정의
> Loki 선택 ( Time range → 5m to now )
> Alert Condition ( WHEN Query is above 0 )
> 쿼리 ⤵
----------------------------
(
  sum by (job, host) (
    count_over_time({job="ocr"} |= "ERROR"[5m])
  )
) or vector(0)
----------------------------
> ERROR가 1건 이상 발생하면 알람 트리거

3. Add folder and labels - Folder 및 Labels 설정
> Folder : job_project_alerts

4. Set evaluation behavior - Evaluation Behavior 설정 (핵심)
> Evaluation Group : 같은 그룹의 알람은 동일한 주기로 평가됨
  - Group: job_project_alerts
  - Interval: 5m
> Pending period (For) : 조건이 몇 분 동안 유지되어야 알람을 울릴 것인가?
  - None → 조건 만족 시 즉시 알람
> Keep firing for : 정상 상태로 돌아온 후에도 알람 상태를 유지할 시간
  - None

5. Configure notifications - 알람이 울렸을 떄 누가 어떻게 받을지 설정
> Recipient : 알람을 받을 대상
  - Contact point 선택 → job_alarm
> configure no data and error handling : 데이터가 없으면 어케할거임?
  - Normal → 로그는 없을 수도 있기 때문에

6. Configure notification message - 알람 내용을 꾸미는 단계
> Summary → OCR 서비스 ERROR 발생
> Description → OCR 서비스에서 ERROR 로그가 {{ (index $values "A").Value }} 건 감지되었습니다.
# Slack 메시지 본문에 ERROR 발생 건수를 동적으로 표시
```

---

### **7️⃣ 최종 Error 로그 알람 테스트**
![error_log](https://github.com/user-attachments/assets/ffb2b2c0-823b-4fe4-aa7a-54a0f7e45224)

> OCR 로그 에러 발생

---
<br><br>

# 📊 결과 (Result)
| 항목       | 기존 방식     | 구축 후       |
| -------- | --------- | ---------- |
| 로그 확인 방식 | 개별 서버 SSH | 중앙 탐색/필터링  |
| 에러 대응 속도 | 지연        | 실시간        |
| 알람 체계    | 수동        | 자동 (Slack) |
| 장애 원인 파악 | 어려움       | 효율적        |

---

## ⚡ 장점
- 서버 접속 없이 로그 확인 가능
- 특정 서비스/호스트 단위 필터링
- ERROR 발생 시 실시간 알림
-운영 효율성 향상
---
## ⚡ 단점 / 고려 사항
- 환경 구성 복잡도 증가

---
<br><br>

# 🏆 성과 요약
| 지표           | 기존            | 개선                 |
| ------------ | ------------- | ------------------ |
| **로그 확인 방식** | 서버별 SSH 접속    | Grafana 중앙 조회      |
| **에러 감지**    | 수동 확인         | 자동 Alert (Slack)   |
| **운영 대응 속도** | 지연            | 실시간 대응             |
| **확장성**      | 서버 증가 시 관리 복잡 | 서버 추가 시 유연하게 대응 가능 |

---

## 📌 결론
- 로그는 운영 안정성의 핵심 지표
- SSH 기반 로그 확인 방식은 운영 리스크가 큼
- Grafana + Loki + Alloy 도입으로 **중앙 로그 관리 체계 확보**
- Alert 시스템 구축으로 장애 대응 속도 대폭 향상
- 서버 추가/서비스 확장에도 유연하게 대응 가능

---

## ✅ 최종 선택
- Grafana + Loki 기반 중앙 로그 아키텍처
- Alloy Agent 기반 로그 수집
- Slack 연동 실시간 Alert 시스템
- 서버 확장 시 유연하게 대응 가능한 구조
---

# 📦 Ubuntu에서 Kafka + Schema Registry + Avro 직렬화 환경 구축

---

## 📌 개요
- Ubuntu 환경에서 **Kafka + Schema Registry 기반 Avro 직렬화 메시징 환경** 구축 가이드
- Kafka 메시지를 **Avro 포맷으로 직렬화**하여 전송
- **Schema Registry를 통한 스키마 중앙 관리**
- Python Producer / Avro Consumer 실습 포함
- Selenium 크롤링 데이터 Kafka 전송 시나리오 기준

🚀 **Ansible 기반 자동화 구성 예시는** 🔗 [`Ansible 레포지토리`](https://github.com/sy0218/Ansible-Multi-Server-Setup) 참고

---
<br>

## 📌 구성 아키텍처
```text
Producer (Python)
 └─ Avro Serializer
     └─ Schema Registry (Schema ID 발급)
         └─ Kafka Cluster (3 Brokers)
                 └─ Consumer (Avro / Plain Kafka)
```
```yaml
- Kafka Cluster      : 메시지 브로커
- Schema Registry    : Avro 스키마 중앙 관리
- Producer (Python)  : Avro 직렬화 메시지 전송
- Consumer           : Avro 역직렬화 메시지 소비
```

---
<br>

## 🔗 버전 호환성 확인 (필수)
- Schema Registry ↔ Kafka 버전 호환성은 아래 문서를 기준으로 확인 👉 https://docs.confluent.io/platform/current/installation/versions-interoperability.html

---
<br>

## ⚙️ Kafka & Zookeeper 기동
> ⚠️ 자체 스크립트 기준
```bash
# Zookeeper 실헹
zookeeper.sh start

# Kafka 실행
kafka.sh start
```

---
<br>

## ⚙️ Schema Registry 실행 (Docker)
```bash
docker run -d \
  --name schema-registry \
  -p 8081:8081 \
  -e SCHEMA_REGISTRY_HOST_NAME=schema-registry \
  -e SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS=PLAINTEXT://192.168.56.60:9092,PLAINTEXT://192.168.56.61:9092,PLAINTEXT://192.168.56.62:9092 \
  -e SCHEMA_REGISTRY_KAFKASTORE_TOPIC_REPLICATION_FACTOR=3 \
  confluentinc/cp-schema-registry:7.6.0
```
---
### ✔ 정상 기동 확인
```bash
curl http://localhost:8081/subjects
```
```text
[]
```
- 초기 상태에서는 등록된 스키마가 없음 → **빈 배열**

---
<br>

## ⚙️ Kafka Avro 직렬화 동작 흐름
```graphql
Producer
 ├─ 로컬 Avro 스키마(.avsc) 로드
 ├─ 메시지 전송 시
 │   ├─ Schema Registry에 스키마 존재 여부 확인
 │   ├─ 없으면 자동 등록
 │   └─ schema_id 발급
 └─ schema_id + payload 를 Kafka로 전송
```
---
### 🔑 핵심 포인트
- 매번 스키마를 등록하는 것이 아님
- Producer는 Schema Registry를 **확인만 함**
- 대부분 라이브러리는 로컬 캐시 사용

```text
1. Producer가 로컬 캐시에서 schema_id 확인
2. 있으면 → Registry 호출 없이 바로 사용
3. 없으면 → Registry 조회 / 등록 → schema_id 저장
4. 이후 메시지부터 캐시된 schema_id 재사용
```

---
<br>

## ⚙️ Avro 스키마 정의
### ✔ job_header.avsc
```json
{
  "type": "record",
  "name": "JobHeader",
  "namespace": "job.crawler",
  "fields": [
    { "name": "domain", "type": "string" },
    { "name": "href", "type": "string" },
    { "name": "company", "type": "string" },
    { "name": "title", "type": "string" }
  ]
}
```

---
<br>

## ⚙️ KafkaHook 클래스 구현
- 일반 Kafka / Avro Kafka 분리 설계
```python
from confluent_kafka import Producer
from confluent_kafka.avro import AvroProducer
from confluent_kafka import avro


class KafkaHook:
    """
    Kafka 연결 및 Producer 관리 클래스
    """
    def __init__(self, brokers):
        self.brokers = brokers
        self.conn = None

    def connect(self, **configs):
        conf = {
            "bootstrap.servers": self.brokers,
            **configs
        }
        self.conn = Producer(conf)

    def avro_connect(self, schema_registry_url, schema_path, **configs):
        value_schema = avro.load(schema_path)

        conf = {
            "bootstrap.servers": self.brokers,
            "schema.registry.url": schema_registry_url,
            **configs
        }

        self.conn = AvroProducer(
            conf,
            default_value_schema=value_schema
        )

    def __getattr__(self, name):
        return getattr(self.conn, name)
```

---
<br>

## ⚙️ Avro Producer 사용 예시
```python
kafka = KafkaHook(
    brokers="192.168.56.60:9092,192.168.56.61:9092,192.168.56.62:9092"
)

kafka.avro_connect(
    schema_registry_url="http://192.168.56.60:8081",
    schema_path="/work/test/schemas/job_header.avsc"
)

kafka.produce(
    topic="job_header_topic",
    value=job_header
)

kafka.flush()
```

---
<br>

## ⚙️ Schema Registry 관리 명령어
### ✔ 등록된 Subject 목록
```bash
curl http://192.168.56.60:8081/subjects
```
---
### ✔ 특정 Topic 스키마 확인
```bash
curl http://192.168.56.60:8081/subjects/job_header_topic-value/versions/latest
```
---
### ✔ 스키마 삭제
```bash
# value 스키마 삭제
curl -XDELETE http://localhost:8081/subjects/job_header_topic-value?permanent=true

# key 스키마 삭제
curl -XDELETE http://localhost:8081/subjects/job_header_topic-key?permanent=true
```

---
<br>

## ⚙️ Avro Consumer로 메시지 확인
```bash
docker exec -it schema-registry kafka-avro-console-consumer \
  --bootstrap-server 192.168.56.60:9092 \
  --topic job_header_topic \
  --from-beginning \
  --property schema.registry.url=http://localhost:8081
```
```json
{"domain":"Remember","href":"https://career.rememberapp.co.kr/job/posting/289554","company":"AK아이에스(주)","title":"[애경그룹] AK아이에스 PL/개발"}
{"domain":"Remember","href":"https://career.rememberapp.co.kr/job/posting/289451","company":"한화솔루션(주)","title":"[한화큐셀] BMS 하드웨어 엔지니어"}
```

---
<br>

## ⚙️ 일반 Kafka Consumer로 확인
```bash
kafka-console-consumer.sh \
  --bootstrap-server 192.168.56.60:9092 \
  --topic job_header_topic \
  --from-beginning
```
```text
Rememberfhttps://career.rememberapp.co.kr/job/posting/248686"(주)베스펙스&Front-end Developer
Rememberfhttps://career.rememberapp.co.kr/job/posting/289183(주)이노션L[플랫폼] 커머스 플랫폼 기획
```

---
<br>

## ✅ 참고 사항
- Schema Registry는 **항상 실행 상태 유지**
- 스키마 등록은 **Producer가 자동 처리**
- Avro 메시지는 **schema_id + payload** 구조
- 일반 Kafka Consumer에서는 **Avro 메시지가 깨져 보이는 것이 정상**
- 실운영 환경에서는 Schema Registry **이중화 구성 권장**
---

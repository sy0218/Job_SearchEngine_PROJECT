# 📤 Ubuntu에서 Elasticsearch 8.4.2 설치 & 검색엔진 환경 구축

---

## 📌 개요
- Ubuntu 환경에서 **Elasticsearch 클러스터 설치, 노드 설정, JVM 튜닝, 템플릿 및 인덱스 생성** 가이드
- 공고 **제목/본문 색인**, **키워드 검색**, **유사 공고 추천** 기능 지원
- **조회 전용 노드(AP) 분리** → 검색 성능 최적화
- **JVM Heap / OS 튜닝 포함한 실운영 기준 설정**
- `systemd` 기반 서비스 등록으로 안정적 운영

🚀 **Ansible로 자동화된 환경 설정 예시는** 🔗 [`Ansible 레포지토리`](https://github.com/sy0218/Ansible-Multi-Server-Setup)에서 확인하세요!

---
<br>

## ⚙️ Elasticsearch 다운로드 및 설치

```bash
apt-get install -y apt-transport-https
apt-get update -y && apt-get install -y wget curl

echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

apt-get update
apt-get install -y elasticsearch=8.4.2
```

---
<br>

## ⚙️ OS 레벨 사전 튜닝 (필수)
```bash
# 파일 디스크립터 / 스레드 제한
echo "elasticsearch - nproc 4096" >> /etc/security/limits.conf

# mmap 제한
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p
```

---
<br>

## ⚙️ 디렉토리 생성 및 권한 설정
```bash
# 조회 노드
mkdir -p /data/esdata
chown -R elasticsearch:elasticsearch /data/esdata

# 데이터 노드
mkdir -p /esdata
chown -R elasticsearch:elasticsearch /esdata
```

---
<br>

## ⚙️ JVM 옵션 설정 (중요)
- 설정 파일 → `/etc/elasticsearch/jvm.options`
---
### ✔ 데이터 노드 ( m1, m2, s1 )
```text
-Xms16g
-Xmx16g
```
---
### ✔ 조회 전용 노드 ( ap )
```text
-Xms2g
-Xmx2g
```
---
### ✔ Heap 적용 확인 로그
- `/var/log/elasticsearch/job/job-cluster.log`
```text
[m1] heap size [16gb], compressed ordinary object pointers [true]
[ap] heap size [2gb], compressed ordinary object pointers [true]
```

---
<br>

## ⚙️ Elasticsearch 노드 설정
### ✔ 조회 전용 노드 ( ap )
```yaml
cluster.name: job-cluster
node.name: ap

node.roles: []

path.data: /data/esdata
path.logs: /var/log/elasticsearch

network.host: 192.168.122.59
http.port: 9200

discovery.seed_hosts: ["m1", "m2", "s1"]

xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
```
---
### ✔ 데이터 노드 (m1, m2, s1)
```yaml
cluster.name: job-cluster
node.name: m1   # 노드별로 고유 설정

path.data: /esdata
path.logs: /var/log/elasticsearch

network.host: 0.0.0.0
network.publish_host: 192.168.122.63
http.port: 9200

discovery.seed_hosts: ["m1", "m2", "s1"]
cluster.initial_master_nodes: ["m1"]

xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
```

---
<br>

## ⚙️ Elasticsearch 실행
```bash
# 모든 클러스터
systemctl start elasticsearch.service
```

---
<br>

## 🔍 클러스터 상태 확인
```bash
curl -XGET ap:9200/_cat/nodes?v
```
```text
ip             heap.percent ram.percent cpu load_1m load_5m load_15m node.role   master name
192.168.122.65            2          54   0    0.04    0.08     0.11 cdfhilmrstw -      s1
192.168.122.63            1          49   1    0.00    0.08     0.13 cdfhilmrstw *      m1
192.168.122.64            2          59   0    0.10    0.13     0.15 cdfhilmrstw -      m2
192.168.122.59            7          67   0    0.44    0.23     0.14 -           -      ap
```

---
<br>

## 📄 Elasticsearch 템플릿 생성
```bash
curl -XPUT "ap:9200/_index_template/job_postings_template" \
-H "Content-Type: application/json" -d '
{
  "index_patterns": ["job_posting*"],
  "priority": 1,
  "template": {
    "settings": {
      "number_of_replicas": 2,
      "analysis": {
        "tokenizer": {
          "two_gram_tokenizer": {
            "type": "ngram",
            "min_gram": 2,
            "max_gram": 2
          }
        },
        "analyzer": {
          "two_gram_analyzer": {
            "type": "custom",
            "tokenizer": "two_gram_tokenizer",
            "filter": ["lowercase"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "domain":    { "type": "keyword" },
        "href":      { "type": "keyword" },
        "company":   { "type": "keyword" },
        "title":     { "type": "text", "analyzer": "two_gram_analyzer" },
        "msgid":     { "type": "keyword" },
        "pay":       { "type": "keyword" },
        "location":  { "type": "keyword" },
        "career":    { "type": "keyword" },
        "education": { "type": "keyword" },
        "deadline":  { "type": "keyword" },
        "body_text": { "type": "text", "analyzer": "two_gram_analyzer" },
        "type":      { "type": "keyword" },
        "morph":     { "type": "keyword" }
      }
    }
  }
}'
```

---
<br>

## 📝 템플릿 확인
```bash
curl -XGET "ap:9200/_index_template/job_postings_template?pretty"
```

---
<br>

## 📦 인덱스 생성
```bash
curl -XPUT "ap:9200/job_posting"
```

---
<br>

## 📊 인덱스 목록 확인
```bash
curl -XGET ap:9200/_cat/indices?pretty
```
```text
green open job_posting 3OqcT0ySRsud1qWdl8Ei0A 1 2 0 0 675b 225b
```

---
<br>

## 🔍 매핑 확인
```bash
curl -XGET "ap:9200/job_posting/_mapping?pretty"
```
```json
{
  "job_posting" : {
    "mappings" : {
      "properties" : {
        "body_text" : {
          "type" : "text",
          "analyzer" : "two_gram_analyzer"
        },
        "career" : {
          "type" : "keyword"
        },
        "company" : {
          "type" : "keyword"
        },
        "deadline" : {
          "type" : "keyword"
        },
        "domain" : {
          "type" : "keyword"
        },
        "education" : {
          "type" : "keyword"
        },
        "href" : {
          "type" : "keyword"
        },
        "location" : {
          "type" : "keyword"
        },
        "morph" : {
          "type" : "keyword"
        },
        "msgid" : {
          "type" : "keyword"
        },
        "pay" : {
          "type" : "keyword"
        },
        "title" : {
          "type" : "text",
          "analyzer" : "two_gram_analyzer"
        },
        "type" : {
          "type" : "keyword"
        }
      }
    }
  }
}
```

---
<br>

## ✅ 참고 사항
- 데이터 노드 Heap은 **RAM의 50% 이하 / 32GB 미만**으로 설정 권장 (Compressed OOPs 유지 목적)
- 조회 전용 노드(AP)는 **Heap 최소화(예: 2GB)** → GC 부담 감소, 검색 응답 안정화
- `vm.max_map_count=262144`, `nproc` 미설정 시 **Elasticsearch 기동 실패 또는 인덱스 생성 오류 발생 가능**
- `path.data` 디렉토리는 **사전 생성 및 쓰기 권한 필수**
- 조회 노드는 반드시 `node.roles: []` 로 설정하여 **데이터 쓰기 / 샤드 할당 방지**
- `discovery.seed_hosts`에는 **모든 데이터 노드**를 포함
- `cluster.initial_master_nodes`는 **최초 클러스터 구성 시에만 사용**
- 템플릿 변경 사항은 **기존 인덱스에는 적용되지 않으며**, **신규 인덱스 생성 시부터 반영**
- `systemd` 서비스 등록을 통해 **서버 재부팅 시 Elasticsearch 자동 기동 보장**
---

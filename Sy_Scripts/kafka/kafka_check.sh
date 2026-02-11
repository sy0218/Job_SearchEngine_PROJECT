#!/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh

set -e

echo "------------------------------------------"
echo "   Kafka 접속 정보 설정"
echo "------------------------------------------"

# 1. Kafka Bootstrap Server
read -p "Kafka Bootstrap Server를 입력하세요 (예: 192.168.122.60:9092): " BOOTSTRAP_SERVER
if [ -z "${BOOTSTRAP_SERVER}" ]; then
    log_error "Bootstrap Server 주소가 입력되지 않았습니다."
    exit 1
fi

# 2. Schema Registry URL
read -p "Schema Registry URL을 입력하세요 (예: http://192.168.122.59:8081): " SCHEMA_REGISTRY_URL
if [ -z "${SCHEMA_REGISTRY_URL}" ]; then
    log_error "Schema Registry URL이 입력되지 않았습니다."
    exit 1
fi

log_info "연결 설정 완료: [${BOOTSTRAP_SERVER}] / [${SCHEMA_REGISTRY_URL}]"

# ------------------------------------------
# 메인 루프
# ------------------------------------------
while true; do
    echo ""
    echo "------------------------------------------"
    echo "   Kafka & Schema Registry 관리 도구"
    echo "------------------------------------------"
    echo "1) 모든 Subject(스키마) 목록 확인"
    echo "2) 특정 토픽의 최신 스키마 확인"
    echo "3) 특정 토픽의 상세 정보(Describe)"
    echo "4) 모든 토픽 목록 확인"
    echo "5) 특정 토픽 메시지 샘플 조회 (최근 1개)"
    echo "6) 특정 토픽 스키마 삭제"
    echo "7) 특정 토픽 삭제"
    echo "8) 토픽 생성 (파티션/레플리카/리텐션)"
    echo "9) 컨슈머 그룹 오프셋 리셋"
    echo "q) 종료"
    echo "------------------------------------------"
    read -p "번호를 선택하세요: " choice

    case $choice in
        1)
            log_info "Schema Registry Subject 목록 조회..."
            curl -s "${SCHEMA_REGISTRY_URL}/subjects"
            ;;
        2)
            read -p "스키마를 확인할 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue
            curl -s "${SCHEMA_REGISTRY_URL}/subjects/${target_topic}-value/versions/latest" | jq . || true
            ;;
        3)
            read -p "상세 정보를 확인할 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue
            kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --describe --topic "${target_topic}"
            ;;
        4)
            kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --list
            ;;
        5)
            read -p "데이터를 확인할 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue
            kafka-console-consumer.sh \
                --bootstrap-server "${BOOTSTRAP_SERVER}" \
                --topic "${target_topic}" \
                --from-beginning \
                --max-messages 1 \
                --timeout-ms 10000 || log_error "데이터 없음"
            ;;
        6)
            read -p "스키마를 삭제할 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue
            curl -s -X DELETE "${SCHEMA_REGISTRY_URL}/subjects/${target_topic}-value" || true
            curl -s -X DELETE "${SCHEMA_REGISTRY_URL}/subjects/${target_topic}-value?permanent=true" || true
            log_info "스키마 삭제 완료"
            ;;
        7)
            read -p "삭제할 Kafka 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue
            kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --delete --topic "${target_topic}" || true
            log_info "토픽 삭제 완료"
            ;;
        8)
            read -p "생성할 Kafka 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue

            read -p "파티션 수 (기본 3): " partitions
            partitions=${partitions:-3}

            read -p "레플리카 수 (기본 1): " replication
            replication=${replication:-1}

            read -p "리텐션 (일, 기본 7): " retention_days
            retention_days=${retention_days:-7}

            RETENTION_MS=$(( retention_days * 24 * 60 * 60 * 1000 ))

            echo "------------------------------------------"
            log_info "토픽 생성"
            echo "  Topic      : ${target_topic}"
            echo "  Partitions : ${partitions}"
            echo "  Replicas   : ${replication}"
            echo "  Retention  : ${retention_days} days (${RETENTION_MS} ms)"
            echo "------------------------------------------"

            kafka-topics.sh \
                --bootstrap-server "${BOOTSTRAP_SERVER}" \
                --create \
                --topic "${target_topic}" \
                --partitions "${partitions}" \
                --replication-factor "${replication}" \
                --config retention.ms="${RETENTION_MS}"

            log_info "토픽 생성 완료"

            echo ""
            log_info "토픽 설정 확인"
            kafka-configs.sh \
                --bootstrap-server "${BOOTSTRAP_SERVER}" \
                --entity-type topics \
                --entity-name "${target_topic}" \
                --describe
            ;;
        9)
            read -p "Consumer Group ID를 입력하세요: " target_group
            [ -z "${target_group}" ] && log_error "Group ID 누락" && continue

            read -p "초기화할 토픽명을 입력하세요: " target_topic
            [ -z "${target_topic}" ] && log_error "토픽명 누락" && continue

            echo "------------------------------------------"
            log_info "오프셋 초기화 대상"
            echo "  Group : ${target_group}"
            echo "  Topic : ${target_topic} (모든 파티션)"
            echo "------------------------------------------"

            read -p "!!정말 초기화하시겠습니까? (yes/no): " confirm
            if [ "${confirm}" != "yes" ]; then
                log_info "취소되었습니다."
                continue
            fi

            kafka-consumer-groups.sh \
                --bootstrap-server "${BOOTSTRAP_SERVER}" \
                --group "${target_group}" \
                --topic "${target_topic}" \
                --reset-offsets \
                --to-earliest \
                --execute

            log_info "오프셋 초기화 완료"

            echo ""
            log_info "초기화 결과 확인"
            kafka-consumer-groups.sh \
                --bootstrap-server "${BOOTSTRAP_SERVER}" \
                --describe \
                --group "${target_group}"
            ;;
        q|Q)
            log_info "스크립트를 종료합니다."
            break
            ;;
        *)
            log_error "잘못된 선택입니다."
            ;;
    esac

    echo ""
    read -p $'\e[32m계속하려면 엔터를 누르세요...\e[0m'
done


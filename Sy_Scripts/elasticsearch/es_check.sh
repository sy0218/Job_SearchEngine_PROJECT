#!/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh

set -e

echo "------------------------------------------"
echo "   Elasticsearch 접속 정보 설정"
echo "------------------------------------------"

# 1. Elasticsearch URL
read -p "Elasticsearch 주소를 입력하세요 (예: http://192.168.122.59:9200): " ES_URL
if [ -z "${ES_URL}" ]; then
    log_error "Elasticsearch 주소가 입력되지 않았습니다."
    exit 1
fi

log_info "Elasticsearch 연결 설정 완료: [${ES_URL}]"

# ------------------------------------------
# 메인 루프
# ------------------------------------------
while true; do
    echo ""
    echo "------------------------------------------"
    echo "   Elasticsearch 관리 도구"
    echo "------------------------------------------"
    echo "1) 클러스터 상태 확인"
    echo "2) 노드 목록 확인"
    echo "3) 전체 인덱스 목록 확인"
    echo "4) 특정 인덱스 정보 확인"
    echo "5) 특정 인덱스 문서 수 확인"
    echo "6) 특정 인덱스 샘플 문서 조회 (1건)"
    echo "7) 특정 인덱스 삭제"
    echo "8) 인덱스 생성 (shard/replica)"
    echo "9) 특정 인덱스 모든 데이터 삭제 (index유지)"
    echo "q) 종료"
    echo "------------------------------------------"
    read -p "번호를 선택하세요: " choice

    case $choice in
        1)
            log_info "클러스터 상태 조회..."
            curl -s "${ES_URL}/_cluster/health?pretty"
            ;;
        2)
            log_info "노드 목록 조회..."
            curl -s "${ES_URL}/_cat/nodes?v"
            ;;
        3)
            log_info "인덱스 목록 조회..."
            curl -s "${ES_URL}/_cat/indices?v"
            ;;
        4)
            read -p "확인할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue
            curl -s "${ES_URL}/${index}?pretty" || log_error "조회 실패"
            ;;
        5)
            read -p "문서 수를 확인할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue
            curl -s "${ES_URL}/${index}/_count?pretty"
            ;;
        6)
            read -p "샘플을 확인할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue
            curl -s "${ES_URL}/${index}/_search?size=1&pretty"
            ;;
        7)
            read -p "삭제할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue
            read -p "⚠ 정말 삭제하시겠습니까? (y/N): " confirm
            if [[ "${confirm}" =~ ^[Yy]$ ]]; then
                curl -s -X DELETE "${ES_URL}/${index}?pretty"
                log_info "인덱스 삭제 완료"
            else
                log_info "삭제 취소"
            fi
            ;;
        8)
            read -p "생성할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue

            read -p "Shard 수 (기본 3): " shards
            shards=${shards:-3}

            read -p "Replica 수 (기본 1): " replicas
            replicas=${replicas:-1}

            echo "------------------------------------------"
            log_info "인덱스 생성"
            echo "  Index    : ${index}"
            echo "  Shards   : ${shards}"
            echo "  Replicas : ${replicas}"
            echo "------------------------------------------"

            curl -s -X PUT "${ES_URL}/${index}" \
                -H "Content-Type: application/json" \
                -d "{
                    \"settings\": {
                        \"number_of_shards\": ${shards},
                        \"number_of_replicas\": ${replicas}
                    }
                }" | jq .

            log_info "인덱스 생성 완료"
            ;;
        9)
            read -p "데이터를 모두 삭제할 인덱스명을 입력하세요: " index
            [ -z "${index}" ] && log_error "인덱스명 누락" && continue

            echo "인덱스는 유지되고 모든 문서만 삭제됩니다."
            read -p "정말 실행하시겠습니까? (y/N): " confirm

            if [[ "${confirm}" =~ ^[Yy]$ ]]; then
                log_info "전체 문서 삭제 실행..."

                curl -s -X POST "${ES_URL}/${index}/_delete_by_query?pretty" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "query": {
                            "match_all": {}
                        }
                    }' | jq .

                log_info "전체 문서 삭제 완료"
            else
                log_info "작업 취소"
            fi
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

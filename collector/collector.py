#!/usr/bin/python3
from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker, DataPreProcessor
from common.crawling_class import ChromeDriver, JobParser
from common.redis_hook import RedisHook
from common.kafka_hook import KafkaHook

from selenium.common.exceptions import TimeoutException

import sys, time
logger = setup_logger(__name__)

def _main():
    """
    메인 수집 로직
    - 웹 크롤링
    - Redis 중복 체크
    - Kafka Avro Producer 전송
    """

    def _get_xpaths(domain):
        """
        도메인 + 직무 타입별 XPath 정보 반환
        """
        return {
            "response": properties["xpath"][f"{domain}.response"],
            "href": properties["xpath"][f"{domain}.href"],
            "company": properties["xpath"][f"{domain}.company"],
            "title": properties["xpath"][f"{domain}.title"],
            "wait": properties["xpath"][f"{domain}.wait"]
        }

    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        collector_env = Get_env._collector()
        redis_env = Get_env._redis()
        kafka_env = Get_env._kafka()
        properties = Get_properties(collector_env["config_path"])

        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Redis 연결 (중복 데이터 체크용)
        # ===============================
        redis = RedisHook(
            redis_env["redis_host"],
            redis_env["redis_port"],
            redis_env["redis_job_db"],
            redis_env["redis_password"]
        )
        redis.connect()
        logger.info("Redis 연결 완료")

        # ===============================
        # Kafka + Schema Registry 연결
        # ===============================
        kafka = KafkaHook(kafka_env["kafka_host"])
        kafka.avro_producer_connect(
            kafka_env["schema_registry"],
            properties["schema"]["job_header"]
        )
        logger.info("Kafka Avro Producer 연결 완료")

        # ===============================
        # Chrome 브라우저 기동
        # ===============================
        browser = ChromeDriver()
        logger.info("ChromeDriver 시작")

        domain_lst = properties["domain"]["catagory"].split(',')
        job_count = int(properties["job_catagory_count"]["count"])

        # ===============================
        # 메인 수집 루프
        # ===============================
        while True:
            for domain in domain_lst:
                for number in range(1, job_count + 1):
                    # ===============================
                    # 종료 플래그 체크
                    # ===============================
                    if StopChecker._job_stop(
                        collector_env["stop_dir"],
                        collector_env["stop_file"]
                    ):
                        logger.warning("Stop 파일 감지 → Collector 종료")
                        sys.exit(0)

                    job_type = properties["url_number"][f"url{number}"]
                    xpaths = _get_xpaths(domain)

                    logger.info(f"수집 시작 | domain={domain}, job_type={job_type}")

                    crawling_type = properties["option"][f"{domain}.crawling_type"]
                    if crawling_type == "page":
                        page = 1
                        pg_check = 0

                    # 크롤링 결과 저장 자료구조
                    redis_pipe = redis.pipeline(transaction=False)
                    job_headers = []

                    while True:
                        if crawling_type == "page":
                            job_url = properties["url"][f"{domain}.url.{job_type}"].format(page = page)
                        elif crawling_type == "scroll":
                            job_url = properties["url"][f"{domain}.url.{job_type}"]

                        # 페이지 접속
                        browser.get(job_url)
                        logger.debug(f"접속 URL: {job_url}")

                        # 사전작업 셋팅( 필요 사이트만! )
                        if properties["option"][f"{domain}.setup_flag"] == "y":
                            setup_list = properties["auto_setup"][f"{domain}.{job_type}"].split("\t")
                            browser.Jobplanet_Auto_Mation(setup_list, 30)

                        # 페이지 로딩 체크
                        try:
                            browser.wait_css(xpaths["wait"], 10)
                        except TimeoutException:
                            pg_check += 1
                            logger.warning(f"페이지에 더 이상 검색 결과가 없습니다 - retry: {pg_check}")
                            if pg_check == 3:
                                break
                            continue

                        # 스크롤다운 ( 필요 사이트만! )
                        if properties["option"][f"{domain}.crawling_type"] == "scroll":
                            browser.autoscroll(xpaths["wait"], 30, 1, 3)

                        parser = JobParser(browser)
                        response = parser.get_response()
                        # ===============================
                        # 채용 공고 파싱
                        # ===============================
                        parser = JobParser(browser)
                        response = parser.get_response()
                        for job_html in response.xpath(xpaths["response"]):
                            job_header = parser.get_job(
                                domain,
                                job_html,
                                xpaths["href"],
                                xpaths["company"],
                                xpaths["title"]
                            )

                            # href 기준 해시 (중복 판별 키)
                            href_hash = DataPreProcessor._hash(job_header["href"] + job_header["title"])

                            # msgid 필드에 href_hash 추가
                            job_header["msgid"] = href_hash

                            # Redis pipeline 적재 및 채용공고 헤더 수집
                            redis_pipe.sadd(redis_env["redis_jobhead_key"], href_hash)
                            job_headers.append(job_header)

                        if crawling_type == "scroll":
                            break
                        page += 1


                    # Redis 전송
                    redis_info = redis_pipe.execute()
                    total_count = len(job_headers)
                    skip, send = 0, 0
                    # ===============================
                    # Redis 중복 체크 처리
                    # ===============================
                    for job_header, flag in zip(job_headers, redis_info):
                        if flag == 0:
                            #logger.debug(
                            #    f"중복 데이터 스킵 (Redis) | href={job_header['href']}"
                            #)
                            skip += 1
                        else:
                            # ===============================
                            # Kafka 전송 ( Avro 직렬화)
                            # ===============================
                            kafka.produce(
                                topic=kafka_env["job_topic"],
                                value=job_header
                            )
                            #logger.info(
                            #    f"Kafka 전송 완료 | topic={kafka_env['job_topic']} | company={job_header['company']} | title={job_header['title']}"
                            #)
                            send += 1

                    # 프로듀서 버퍼에 남은 메시지 모두 전송
                    kafka.flush()
                    logger.info(
                        f"작업 완료 | 총 건수: {total_count} | 성공: {send} | 스킵: {skip}"
                    )
                    time.sleep(3)

    except Exception as e:
        logger.error("Collector 실행 중 오류 발생", exc_info=True)

    finally:
        # ===============================
        # 리소스 정리
        # ===============================
        browser.quit()
        redis.close()
        kafka.flush()
        logger.info("Collector 정상 종료")


if __name__ == "__main__":
    _main()

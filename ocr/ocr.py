from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker
from common.redis_hook import RedisHook
from common.kafka_hook import KafkaHook

import easyocr, os, warnings, time

from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import numpy as np

logger = setup_logger(__name__)

os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
warnings.filterwarnings("ignore")

# ===============================
# Main 함수 (순차 처리)
# ===============================
def _main():
    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        ocr_env = Get_env._ocr()
        kafka_env = Get_env._kafka()
        redis_env = Get_env._redis()
        nfs_env = Get_env._nfs()
        properties = Get_properties(ocr_env["config_path"])
        poll_size = int(properties["poll_opt"]["poll_size"])
        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Kafka Consumer 연결
        # ===============================
        kafka_consumer = KafkaHook(kafka_env["kafka_host"])
        kafka_consumer.consumer_connect(
            kafka_env["ocr_topic"],
            int(properties["partition_num"]["num"]),
            kafka_env["ocr_group_id"]
        )
        logger.info("Kafka Consumer 연결 완료")
    
        # ===============================
        # Redis 연결
        # ===============================
        redis = RedisHook(
                redis_env["redis_host"],
                redis_env["redis_port"],
                redis_env["redis_img_db"],
                redis_env["redis_password"],
                decode_responses=True
            )
        redis.connect()
        logger.info("Redis 연결 완료")
    
        # ===============================
        # EasyOCR Reader 객체 생성
        # ===============================
        img_reader = easyocr.Reader(['ko', 'en'], gpu=False)  # GPU 없음

        while True:
            # Stop 파일 체크
            if StopChecker._job_stop(ocr_env["stop_dir"], ocr_env["stop_file"]):
                logger.warning("Stop 파일 감지 → 종료 프로세스 진입")
                break

            batch = []
            while len(batch) < poll_size:
                msg = kafka_consumer.poll(5.0)
                if msg is None:
                    break
                batch.append(msg)

            if len(batch) < poll_size:
                logger.info(f"[INFO] 아직 메시지 없음! 현재 batch size: {len(batch)}.. 30초 대기..")
                time.sleep(30)
                continue

            offset_info = f"partition-{batch[0].partition()} : {batch[0].offset()} ~ {batch[-1].offset()}"
            logger.info(f"==== 배치 순차 처리 시작.. {offset_info} ====")

            # ===============================
            # 메시지 순차 처리
            # ===============================
            for m in batch:
                img_hash = m.value().decode('utf-8')
                # NFS 경로 변환
                img_path = os.path.join(
                    nfs_env["nfs_img"],
                    img_hash[0] + img_hash[1],
                    img_hash[2] + img_hash[3],
                    img_hash
                )
                logger.info(f"OCR 처리 시작: {img_path}")

                # Redis에 있는지 확인
                check_redis = redis.exists(img_hash)
                if check_redis:
                    logger.info(f"OCR 이미 처리됨, Skip: {img_path}")
                    continue

                try:
                    with Image.open(img_path) as img:
                        img = img.convert('RGB')

                        max_side = int(properties["ocr"]["max_side"])
                        w, h = img.size
                        if max(w, h) > max_side:
                            scale = max_side / float(max(w, h))
                            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                            img = img.resize((new_w, new_h), Image.LANCZOS)
                            logger.info(f"이미지 리사이즈: {w}x{h} → {new_w}x{new_h}")

                        img_np = np.array(img.convert('RGB'))
                
                    img_text = img_reader.readtext(img_np)
                    text = " ".join([
                        r[1] for r in img_text
                        if r[2] >= float(properties["ocr"]["confidence"])
                    ])

                    # 결과 Redis 저장
                    redis.set(img_hash, text)
                    logger.info(f"OCR 결과 Redis 저장 완료: {img_hash} → ( {img_path}: {text} )")
                except FileNotFoundError:
                    logger.warning(f"OCR 처리 실패 - 파일 없음, Skip: {img_path}")
                    continue
                except OSError as e:
                    logger.warning(f"손상 이미지 Skip: {img_path} ({e})")
                    continue
                except Exception as e:
                    logger.error(f"OCR 처리 실패: {img_path} {e}")
                    raise

            # Kafka 오프셋 커밋 (필요시)
            kafka_consumer.commit(batch[-1])
            logger.info(f"==== 배치 순차 처리 완료.. {offset_info} ====")

            time.sleep(3)

    except Exception as e:
        logger.error("OCR 실행 중 오류 발생, 모든 배치 중단", exc_info=True)

    finally:
        kafka_consumer.close()
        redis.close()
        logger.info("프로세스 종료. 모든 자원 반납 완료.")


if __name__ == "__main__":
    _main()

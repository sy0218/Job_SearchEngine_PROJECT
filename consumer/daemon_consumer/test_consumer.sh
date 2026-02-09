#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
#exec python3 -u ${CONSUMER_WORK_DIR}/test.py
#exec python3 -u ${CONSUMER_WORK_DIR}/single_consumer.py
#exec python3 -u ${CONSUMER_WORK_DIR}/consumer.py

exec python3 -u ${CONSUMER_WORK_DIR}/saramin.py

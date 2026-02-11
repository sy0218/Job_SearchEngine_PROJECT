import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.hdfs.DistributedFileSystem;
import org.apache.hadoop.hdfs.DFSInotifyEventInputStream;
import org.apache.hadoop.hdfs.inotify.Event;
import org.apache.hadoop.hdfs.inotify.EventBatch;

import java.io.FileWriter;
import java.io.IOException;
import java.io.FileInputStream;
import java.util.Properties;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class HdfsCloseWatcher {

    // 감시할 HDFS 경로
    private static String WATCH_PATH;
    // 로그 파일 경로
    private static String LOG_FILE;

    // PostgreSQL env
    private static final String PG_HOST = System.getenv("POSTGRESQL_HOST");
    private static final String PG_PORT = System.getenv("POSTGRESQL_PORT");
    private static final String PG_DB   = System.getenv("POSTGRESQL_DB");
    private static final String PG_USER = System.getenv("POSTGRESQL_USER");
    private static final String PG_PASS = System.getenv("POSTGRESQL_PASSWORD");

    private static final String PG_URL =
        "jdbc:postgresql://" + PG_HOST + ":" + PG_PORT + "/" + PG_DB;

    // Config 로드
    private static void loadConfig() throws Exception {

        String configPath = System.getenv("HD_EVENT_CONFIG_PATH");
        String logDir     = System.getenv("HD_EVENT_LOG_DIR");

        if (configPath == null) {
            System.err.println("HD_EVENT_CONFIG_PATH is not set");
            System.exit(1);
        }
        if (logDir == null) {
            System.err.println("HD_EVENT_LOG_DIR is not set");
            System.exit(1);
        }

        Properties props = new Properties();
        try (FileInputStream fis = new FileInputStream(configPath)) {
            props.load(fis);
        }

        WATCH_PATH = props.getProperty("watch.path");
        if (WATCH_PATH == null) {
            System.err.println("watch.path is missing in properties");
            System.exit(1);
        }

        String today = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);

        LOG_FILE = logDir + "/hdfs_close_" + today + ".log";
    }


    // 로그 기록 메소드
    private static void logToFile(String message) {
        try (FileWriter fw = new FileWriter(LOG_FILE, true)) {
            fw.write(message + "\n");
            fw.flush();
        } catch (IOException e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    // Postgresql 메소드
    private static Connection pgConn;
    private static void initPostgres() throws Exception {
        try {
            Class.forName("org.postgresql.Driver");
            pgConn = DriverManager.getConnection(PG_URL, PG_USER, PG_PASS);
            logToFile("[INIT] PostgreSQL connected");
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static final String INSERT_SQL =
        "INSERT INTO job.hadoop_event (file_path, file_size) VALUES (?, ?)";

    private static void insertEvent(String path, long size) {
        try (PreparedStatement ps = pgConn.prepareStatement(INSERT_SQL)) {
            ps.setString(1, path);
            ps.setLong(2, size);
            ps.executeUpdate();
        } catch (Exception e) {
            logToFile("[ERROR][DB] " + e.getMessage());
            System.exit(1);
        }
    }

    public static void main(String[] args) throws Exception {
        loadConfig();
        initPostgres();

        // Hadoop 설정 로드 (HADOOP_CONF_DIR 기준)
        Configuration conf = new Configuration();

        // HDFS 연결
        DistributedFileSystem dfs =
                (DistributedFileSystem) new Path("/").getFileSystem(conf);

        // inotify 이벤트 스트림
        DFSInotifyEventInputStream eventStream =
                dfs.getInotifyEventStream();

        logToFile("[START] HDFS CLOSE watcher started");
        logToFile("[WATCH] Path prefix: " + WATCH_PATH);

        // 이벤트 감시 루프 (블로킹)
        while (true) {
            EventBatch batch = eventStream.take();

            for (Event event : batch.getEvents()) {

                // CLOSE 이벤트만 처리
                if (event.getEventType() == Event.EventType.CLOSE) {

                    Event.CloseEvent closeEvent =
                            (Event.CloseEvent) event;

                    String path = closeEvent.getPath();

                    // 감시 대상 경로만 필터
                    if (path != null && path.startsWith(WATCH_PATH)) {

                        // _COPYING_ 제거 (로그용)
                        String cleanPath =
                                path.replace("._COPYING_", "");

                        long fileSize = closeEvent.getFileSize();

                        logToFile(
                            "[CLOSE] path=" + cleanPath +
                            ", fileSize=" + fileSize
                        );

                        insertEvent(cleanPath, fileSize);
                    }
                }
            }
        }
    }
}

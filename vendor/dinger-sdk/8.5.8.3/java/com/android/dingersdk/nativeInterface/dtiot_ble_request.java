package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class dtiot_ble_request {
    public static final int BLE_REQUEST_AUDIO_RECORD_OPT = 256;
    public static final int BLE_REQUEST_AUDIO_REMARK = 258;
    public static final int BLE_REQUEST_AUTH = 9;
    public static final int BLE_REQUEST_CLOSE_AP = 289;
    public static final int BLE_REQUEST_CONNECT_DEVICE = 307;
    public static final int BLE_REQUEST_DISCONNECT_DEVICE = 308;
    public static final int BLE_REQUEST_FILE_BLOCK_SEND = 277;
    public static final int BLE_REQUEST_FILE_DELETE = 275;
    public static final int BLE_REQUEST_FILE_HEADER_SEND = 276;
    public static final int BLE_REQUEST_FILE_SYNC = 273;
    public static final int BLE_REQUEST_FILE_SYNC_CANCLE = 274;
    public static final int BLE_REQUEST_GET_ACTIVE_INFO = 6;
    public static final int BLE_REQUEST_GET_FILE_LIST = 272;
    public static final int BLE_REQUEST_GET_RANDOM = 8;
    public static final int BLE_REQUEST_GET_TRANS_INFO = 304;
    public static final int BLE_REQUEST_GET_WEBSVR_INFO = 291;
    public static final int BLE_REQUEST_GRAY_SWITCH = 311;
    public static final int BLE_REQUEST_OPEN_AP = 288;
    public static final int BLE_REQUEST_QUERY_FW_VERSION = 309;
    public static final int BLE_REQUEST_RESET_DEVICE = 4;
    public static final int BLE_REQUEST_START_AP_WEBSVR = 290;
    public static final int BLE_REQUEST_STOP_AP_WEBSVR = 292;
    public static final int BLE_REQUEST_STREAM_HEADER_SEND = 278;
    public static final int BLE_REQUEST_STREAM_PACKET_SEND = 279;
    public static final int BLE_REQUEST_SYNC_DEV_STATUS = 306;
    public static final int BLE_REQUEST_SYNC_TIME = 305;
    public static final int BLE_REQUEST_SYS_CONTROL = 310;
    public static final int DINGER_CMD_DEVICE_DUMP = 317;
    public static final int DINGER_CMD_DEVICE_SETTING = 318;
    public static final int DINGER_CMD_PLAY_STREAM_CONTROL = 285;
    public static final int DINGER_CMD_PLAY_STREAM_HEADER_SEND = 283;
    public static final int DINGER_CMD_PLAY_STREAM_PACKET_SEND = 284;
    public static final int DINGER_CMD_QUERY_FILE_UPDATE = 280;
    public static final int DINGER_CMD_SWITCH_MASTER = 314;
    public static final int DINGER_CMD_UT_REPORT = 12;
    public static final int DINGER_CMD_VENDOR_GET = 313;
    public static final int DINGER_CMD_VENDOR_NOTIFY = 316;
    public static final int DINGER_CMD_VENDOR_SET = 312;

    public static class dtiot_gray_switch_control_key {
        public static final int GRAY_SWITCH_CONTROL_KEY_EXE_CMD = 3;
        public static final int GRAY_SWITCH_CONTROL_KEY_REBOOT = 1;
        public static final int GRAY_SWITCH_CONTROL_KEY_SHUTDOWN = 2;
        public static final int GRAY_SWITCH_CONTROL_KEY_UPLOAD_FILE = 4;
    }

    public static class dtiot_sys_control_key {
        public static final int SYS_CONTROL_KEY_GET_BATTERY_PERCENT = 10001;
        public static final int SYS_CONTROL_KEY_SET_CLEAR_OTAZIP = 3;
        public static final int SYS_CONTROL_KEY_SET_FORMAT_AUDIO = 2;
        public static final int SYS_CONTROL_KEY_SET_REBOOT = 1;
    }

    public static class magic {
        public static final int MAGIC_NOTIFY = 20;
        public static final int MAGIC_REQUEST = 19;
        public static final int MAGIC_RESPONSE = 49;
    }
}

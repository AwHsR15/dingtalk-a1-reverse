package com.android.dingersdk.nativeInterface;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class DingerAudioTools {
    public static final int AUDIO_MODE_LOOPBACK = 2;
    public static final int AUDIO_MODE_MIXED = 1;
    public static final int AUDIO_MODE_PASSTHROUGH = 0;
    public static final int DOWNLINK_STREAM_DUAL = 4;
    public static final int DOWNLINK_STREAM_HFP_TX = 2;
    public static final int DOWNLINK_STREAM_SPEAKER = 1;
    public static int FILE_TYPE_OFFLINE_MENO = 1;
    public static int FILE_TYPE_REAL_STREAM = 2;
    public static int FILE_TYPE_RECORD = 0;
    public static int MAGIC_RESP = 49;
    public static int MAGIC_SEND = 19;
    public static String STREAM_SOURCE_APP = "app";
    public static String STREAM_SOURCE_DEVICE = "device";
    public static String STREAM_STATUS_PROCESS = "process";
    public static String STREAM_STATUS_START = "start";
    public static String STREAM_STATUS_STOP = "stop";
    private static final String TAG = "DingerAudioTools";
    public static final int UPSTREAM_CB_DEFAULT = 1;
    public static final int UPSTREAM_CB_DUAL = 6;
    public static final int UPSTREAM_CB_HFP_MIC = 4;
    public static final int UPSTREAM_CB_HFP_RX = 2;
    public static List<RecvMsgCallback> recvMsgCallbackList = new ArrayList();

    public interface AudioClipCallback {
        void onClipComplete(AudioClipErrorCode audioClipErrorCode, String str, long j, long j2);
    }

    public enum AudioClipErrorCode {
        SUCCESS(0),
        INVALID_PARAM(-1),
        INVALID_FILE_PATH(-2),
        FILE_OPEN_FAILED(-3),
        FILE_READ_ERROR(-4),
        FILE_WRITE_ERROR(-5),
        CANCELLED(-6),
        UNKNOWN_ERROR(-7);

        private final int value;

        AudioClipErrorCode(int i) {
            this.value = i;
        }

        public static AudioClipErrorCode fromValue(int i) {
            for (AudioClipErrorCode audioClipErrorCode : values()) {
                if (audioClipErrorCode.value == i) {
                    return audioClipErrorCode;
                }
            }
            return UNKNOWN_ERROR;
        }

        public int getValue() {
            return this.value;
        }
    }

    public enum ExportErrorCode {
        SUCCESS(0),
        INVALID_PARAM(-1),
        INVALID_FILE_PATH(-2),
        UNSUPPORTED_EXPORT_TYPE(-3),
        FILE_OPEN_FAILED(-4),
        FILE_READ_ERROR(-5),
        FILE_WRITE_ERROR(-6),
        ENCODING_ERROR(-7),
        EXPORT_INCOMPLETE(-8),
        CANCELLED(-9),
        UNKNOWN_ERROR(-10);

        private final int value;

        ExportErrorCode(int i) {
            this.value = i;
        }

        public static ExportErrorCode fromValue(int i) {
            for (ExportErrorCode exportErrorCode : values()) {
                if (exportErrorCode.value == i) {
                    return exportErrorCode;
                }
            }
            return UNKNOWN_ERROR;
        }

        public int getValue() {
            return this.value;
        }
    }

    public enum MergeErrorCode {
        SUCCESS(0),
        INVALID_PARAM(-1),
        INSUFFICIENT_FILES(-2),
        INVALID_FILE_PATH(-3),
        FILE_OPEN_FAILED(-4),
        FILE_READ_ERROR(-5),
        FILE_WRITE_ERROR(-6),
        MERGE_INCOMPLETE(-7),
        ENCODING_ERROR(-8),
        CANCELLED(-9),
        UNKNOWN_ERROR(-10);

        private final int value;

        MergeErrorCode(int i) {
            this.value = i;
        }

        public static MergeErrorCode fromValue(int i) {
            for (MergeErrorCode mergeErrorCode : values()) {
                if (mergeErrorCode.value == i) {
                    return mergeErrorCode;
                }
            }
            return UNKNOWN_ERROR;
        }

        public int getValue() {
            return this.value;
        }
    }

    public interface SmartClipCallback {
        void onProgress(SmartClipCallbackType smartClipCallbackType, AudioClipErrorCode audioClipErrorCode, int i, String str, long[] jArr, long j, long j2, String str2);
    }

    public enum SmartClipCallbackType {
        PROCESS(1),
        END(2);

        private final int value;

        SmartClipCallbackType(int i) {
            this.value = i;
        }

        public static SmartClipCallbackType fromValue(int i) {
            for (SmartClipCallbackType smartClipCallbackType : values()) {
                if (smartClipCallbackType.value == i) {
                    return smartClipCallbackType;
                }
            }
            throw new IllegalArgumentException("Invalid SmartClipCallbackType value: " + i);
        }

        public int getValue() {
            return this.value;
        }
    }

    static {
        System.loadLibrary("DingerSdk");
    }

    public static native String AESDecrypt(String str, String str2);

    public static native String AESEncrypt(String str, String str2);

    public static native void AudioClipWithProgress(AudioClipParam audioClipParam, AudioClipCallback audioClipCallback);

    public static native void AudioFileClose();

    public static native boolean CancelExportAudio();

    public static native boolean CancelMergeFiles();

    public static native boolean CancelSmartClip();

    @CalledByNative
    public static void EventCallback(int i, String str) {
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null) {
                recvMsgCallback.EventCallback(i, str);
            }
        }
    }

    public static native int ExportAudioWithProgress(AudioFileParam audioFileParam, String str, String[] strArr, ExportProgressCallback exportProgressCallback);

    public static native long GetOpusFileSize(String str);

    public static native String GetSdkVer();

    @CalledByNative
    public static int GraySwitchCallback(String str) {
        int iGraySwitchCallback;
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null && (iGraySwitchCallback = recvMsgCallback.GraySwitchCallback(str)) >= 0) {
                return iGraySwitchCallback;
            }
        }
        return -1;
    }

    public static native int InitConfig(String str);

    @CalledByNative
    public static void LogCallback(String str) {
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null) {
                recvMsgCallback.LogCallback(str);
            }
        }
    }

    public static native int MergeFilesWithProgress(AudioFileParam[] audioFileParamArr, String[] strArr, MergeProgressCallback mergeProgressCallback);

    @CalledByNative
    public static void MsgCallback(int i, int i2, String str) {
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null) {
                recvMsgCallback.MsgCallback(i, i2, str);
            }
        }
    }

    @CalledByNative
    public static void OnSendData(int i, byte[] bArr, int i2) {
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null) {
                recvMsgCallback.OnSendData(i, bArr, i2);
            }
        }
    }

    public static native int OpusConvertToOgg(String str);

    public static native void OtaSendDataNotify(boolean z);

    public static native void PauseAsr(boolean z);

    public static native int PushBleRecvData(byte[] bArr, int i);

    public static synchronized void RegistMsgCallback(RecvMsgCallback recvMsgCallback) {
        if (!recvMsgCallbackList.contains(recvMsgCallback)) {
            recvMsgCallbackList.add(recvMsgCallback);
        }
        StringBuilder sb = new StringBuilder();
        sb.append("[RegistMsgCallback] size: ");
        sb.append(recvMsgCallbackList.size());
        SetCallback();
    }

    public static native int SendCmdToDevice(int i, String str);

    public static native int SendFileSyncCmd(String str, int i, int i2, int i3);

    private static native void SetCallback();

    public static native void SmartClipWithProgress(AudioClipParam audioClipParam, SmartClipCallback smartClipCallback);

    public static native int StartAsr(String str);

    public static native int StartOta(String str);

    public static native int StartSendFile(String str);

    public static native int StopAsr();

    public static native int StopOta();

    @CalledByNative
    public static void StreamDataCallback(byte[] bArr, int i, String str) {
        StringBuilder sb = new StringBuilder();
        sb.append("[DBG-UPLINK][java-entry] len=");
        sb.append(i);
        sb.append(" header=");
        sb.append(str);
        sb.append(" callbackCount=");
        sb.append(recvMsgCallbackList.size());
        for (RecvMsgCallback recvMsgCallback : recvMsgCallbackList) {
            if (recvMsgCallback != null) {
                recvMsgCallback.StreamDataCallback(bArr, i, str);
            }
        }
    }

    public static synchronized void UnRegistMsgCallback(RecvMsgCallback recvMsgCallback) {
        recvMsgCallbackList.remove(recvMsgCallback);
    }

    public static native int closeDownlinkStream(long j);

    public static native byte[] decodeOpusFrame(byte[] bArr, int i);

    public static native String getAudioFileAttributes();

    public static native String getAudioFileInfo();

    public static native float getCurrentPosition();

    public static native void notifyEvent(int i, int i2);

    public static native boolean openAudioFile(String str, String str2, AudioFileAttr audioFileAttr);

    public static native long openDownlinkStream(String str, int i);

    public static native int readAudioFrames(AudioFrameBuffer audioFrameBuffer);

    public static native void resetOpusDecoder();

    public static native boolean seekToPosition(float f);

    public static native boolean seekToSecond(int i);

    public static native int sendDownlinkStreamFramePcm(long j, byte[] bArr, int i, int i2);

    public static native int sendDownlinkStreamFrameRawOpus(long j, byte[] bArr, int i);

    public static native void setAudioProcessMode(int i);

    public static native void setGraySwitches(Map<String, Boolean> map);

    public static native void setUpstreamChannelCallback(int i);
}

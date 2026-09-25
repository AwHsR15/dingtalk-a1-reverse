package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public interface RecvMsgCallback {
    public static final int MAGIC_RECV = 49;
    public static final int MAGIC_SEND = 19;

    void EventCallback(int i, String str);

    int GraySwitchCallback(String str);

    void LogCallback(String str);

    void MsgCallback(int i, int i2, String str);

    void OnSendData(int i, byte[] bArr, int i2);

    void StreamDataCallback(byte[] bArr, int i, String str);
}

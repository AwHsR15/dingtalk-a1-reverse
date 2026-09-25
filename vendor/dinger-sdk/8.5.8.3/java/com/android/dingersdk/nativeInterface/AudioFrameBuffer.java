package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class AudioFrameBuffer {
    public byte[] buffer;
    public int bufferLen;
    public int dataLen;

    public AudioFrameBuffer() {
        this.buffer = null;
        this.bufferLen = 0;
        this.dataLen = 0;
    }

    public void setBuffer(byte[] bArr, int i) {
        this.buffer = bArr;
        this.bufferLen = i;
        this.dataLen = 0;
    }

    public String toString() {
        return "AudioFrameBuffer{bufferLen=" + this.bufferLen + ", dataLen=" + this.dataLen + '}';
    }

    public AudioFrameBuffer(byte[] bArr, int i) {
        this.buffer = bArr;
        this.bufferLen = i;
        this.dataLen = 0;
    }
}

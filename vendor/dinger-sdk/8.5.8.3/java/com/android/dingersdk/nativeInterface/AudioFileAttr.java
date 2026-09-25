package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class AudioFileAttr {
    public int channels;
    public int containerSampleRate;
    public int depthBit;
    public int duration;
    public long fileSize;
    public int inputSampleRate;
    public boolean isEncrypted;

    public AudioFileAttr() {
        this.isEncrypted = false;
        this.duration = 0;
        this.fileSize = 0L;
        this.containerSampleRate = 48000;
        this.inputSampleRate = 0;
        this.channels = 1;
        this.depthBit = 16;
    }

    public String toString() {
        return "AudioFileAttr{isEncrypted=" + this.isEncrypted + ", duration=" + this.duration + ", fileSize=" + this.fileSize + ", containerSampleRate=" + this.containerSampleRate + ", inputSampleRate=" + this.inputSampleRate + ", channels=" + this.channels + ", depthBit=" + this.depthBit + '}';
    }

    public AudioFileAttr(boolean z, int i, int i2, int i3, int i4, int i5) {
        this.isEncrypted = z;
        this.duration = i;
        this.fileSize = i2;
        this.containerSampleRate = i3;
        this.channels = i4;
        this.depthBit = i5;
    }
}

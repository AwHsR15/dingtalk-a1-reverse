package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class AudioClipParam {
    public AudioFileParam audioFileParam;
    public long endTime;
    public long startTime;

    public AudioClipParam() {
        this.audioFileParam = new AudioFileParam();
        this.startTime = 0L;
        this.endTime = 0L;
    }

    public String toString() {
        return "AudioClipParam{audioFileParam=" + this.audioFileParam + ", startTime=" + this.startTime + ", endTime=" + this.endTime + '}';
    }

    public AudioClipParam(AudioFileParam audioFileParam, long j, long j2) {
        this.audioFileParam = audioFileParam;
        this.startTime = j;
        this.endTime = j2;
    }
}

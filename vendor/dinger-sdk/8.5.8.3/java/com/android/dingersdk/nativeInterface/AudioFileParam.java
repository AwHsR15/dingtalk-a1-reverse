package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class AudioFileParam {
    public String audioFilePath;
    public int duration;
    public boolean isEncrypted;
    public String secretMd5;

    public AudioFileParam() {
        this.audioFilePath = "";
        this.secretMd5 = "";
        this.isEncrypted = false;
        this.duration = 0;
    }

    public String toString() {
        return "AudioFileParam{audioFilePath='" + this.audioFilePath + "', secretMd5='" + this.secretMd5 + "', isEncrypted=" + this.isEncrypted + ", duration=" + this.duration + '}';
    }

    public AudioFileParam(String str, String str2, boolean z, int i) {
        this.audioFilePath = str;
        this.secretMd5 = str2;
        this.isEncrypted = z;
        this.duration = i;
    }
}

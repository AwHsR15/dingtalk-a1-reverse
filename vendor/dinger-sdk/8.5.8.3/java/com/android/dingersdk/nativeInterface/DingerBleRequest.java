package com.android.dingersdk.nativeInterface;

import androidx.annotation.NonNull;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class DingerBleRequest {
    public int msgId;
    public int reqCmd;
    public byte[] reqData;
    public int reqLen;

    public void setCmd(int i) {
        this.reqCmd = i;
    }

    public void setData(byte[] bArr) {
        this.reqData = bArr;
    }

    public void setLen(int i) {
        this.reqLen = i;
    }

    public void setMsgId(int i) {
        this.msgId = i;
    }

    @NonNull
    public String toString() {
        return "DingerBleRequest{reqData=" + this.reqData + ", reqLen='" + this.reqLen + "', reqCmd='" + this.reqCmd + "', msgId='" + this.msgId + "'}";
    }
}

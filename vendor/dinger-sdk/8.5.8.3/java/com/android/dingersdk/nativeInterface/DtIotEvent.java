package com.android.dingersdk.nativeInterface;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public enum DtIotEvent {
    BleOpen(1),
    BleClose(2),
    BleConnect(3),
    BleDisconnect(4),
    WiFiOpen(11),
    WiFiClose(12),
    WiFiConnect(13),
    WiFiDisconnect(14);

    private final int value;

    DtIotEvent(int i) {
        this.value = i;
    }

    public int getValue() {
        return this.value;
    }
}

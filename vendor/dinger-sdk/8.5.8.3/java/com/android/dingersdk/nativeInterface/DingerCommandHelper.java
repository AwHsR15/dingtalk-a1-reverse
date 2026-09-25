package com.android.dingersdk.nativeInterface;

import android.util.Log;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public class DingerCommandHelper {
    private static final String TAG = "DingerCommandHelper";

    public static int sendAudioRecordOpt(String str, String str2, JSONArray jSONArray) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("action", str2);
            if (jSONArray != null) {
                jSONObject.put("params", jSONArray);
            }
            return DingerAudioTools.SendCmdToDevice(256, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendAudioRecordOpt failed", e);
            return -1;
        }
    }

    public static int sendAuth(String str, String str2, String str3) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("timestamp", str);
            jSONObject.put("payload", str2);
            jSONObject.put("did", str3);
            return DingerAudioTools.SendCmdToDevice(9, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendAuth failed", e);
            return -1;
        }
    }

    public static int sendCloseAp(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            return DingerAudioTools.SendCmdToDevice(289, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendCloseAp failed", e);
            return -1;
        }
    }

    public static int sendConnectDevice(String str, String str2, String str3, String str4, long j, String str5) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("corpId", str);
            jSONObject.put("did", str2);
            jSONObject.put("token", str3);
            jSONObject.put("model", str4);
            jSONObject.put("timestamp", j);
            jSONObject.put("sdk_ver", str5);
            return DingerAudioTools.SendCmdToDevice(307, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendConnectDevice failed", e);
            return -1;
        }
    }

    public static int sendDisconnectDevice(String str, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("corpId", str);
            jSONObject.put("did", str2);
            return DingerAudioTools.SendCmdToDevice(308, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendDisconnectDevice failed", e);
            return -1;
        }
    }

    public static int sendFileDelete(String str, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("fid", str2);
            return DingerAudioTools.SendCmdToDevice(275, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendFileDelete failed", e);
            return -1;
        }
    }

    public static int sendFileSyncCancel(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            return DingerAudioTools.SendCmdToDevice(274, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendFileSyncCancel failed", e);
            return -1;
        }
    }

    public static int sendGetFileList(String str, String str2, String str3, int i) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("s_fid", str2);
            jSONObject.put("e_fid", str3);
            jSONObject.put("recently", i);
            return DingerAudioTools.SendCmdToDevice(272, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGetFileList failed", e);
            return -1;
        }
    }

    public static int sendGetRandom(String str, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("corpId", str);
            jSONObject.put("did", str2);
            return DingerAudioTools.SendCmdToDevice(8, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGetRandom failed", e);
            return -1;
        }
    }

    public static int sendGetTransInfo(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("corpId", str);
            return DingerAudioTools.SendCmdToDevice(304, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGetTransInfo failed", e);
            return -1;
        }
    }

    public static int sendGraySwitchControl(String str, int i, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("action", "control");
            JSONObject jSONObject2 = new JSONObject();
            jSONObject2.put("key", i);
            if (str2 != null && !str2.isEmpty()) {
                jSONObject2.put("val", str2);
            }
            jSONObject.put("params", jSONObject2);
            return DingerAudioTools.SendCmdToDevice(dtiot_ble_request.BLE_REQUEST_GRAY_SWITCH, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGraySwitchControl failed", e);
            return -1;
        }
    }

    public static int sendGraySwitchGet(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("action", "get");
            return DingerAudioTools.SendCmdToDevice(dtiot_ble_request.BLE_REQUEST_GRAY_SWITCH, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGraySwitchGet failed", e);
            return -1;
        }
    }

    public static int sendGraySwitchSet(String str, JSONObject jSONObject) throws JSONException {
        try {
            JSONObject jSONObject2 = new JSONObject();
            jSONObject2.put("did", str);
            jSONObject2.put("action", "set");
            jSONObject2.put("params", jSONObject);
            return DingerAudioTools.SendCmdToDevice(dtiot_ble_request.BLE_REQUEST_GRAY_SWITCH, jSONObject2.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendGraySwitchSet failed", e);
            return -1;
        }
    }

    public static int sendOpenAp(String str, int i) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("type", i);
            return DingerAudioTools.SendCmdToDevice(288, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendOpenAp failed", e);
            return -1;
        }
    }

    public static int sendQueryFwVersion(String str, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            if (str2 != null && !str2.isEmpty()) {
                jSONObject.put("new_ver", str2);
            }
            return DingerAudioTools.SendCmdToDevice(309, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendQueryFwVersion failed", e);
            return -1;
        }
    }

    public static int sendResetDevice(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            return DingerAudioTools.SendCmdToDevice(4, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendResetDevice failed", e);
            return -1;
        }
    }

    public static int sendSwitchMaster(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            return DingerAudioTools.SendCmdToDevice(dtiot_ble_request.DINGER_CMD_SWITCH_MASTER, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendSwitchMaster failed", e);
            return -1;
        }
    }

    public static int sendSyncDevStatus(String str) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            return DingerAudioTools.SendCmdToDevice(306, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendSyncDevStatus failed", e);
            return -1;
        }
    }

    public static int sendSysControl(String str, int i, String str2) throws JSONException {
        try {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("did", str);
            jSONObject.put("key", i);
            if (str2 != null && !str2.isEmpty()) {
                jSONObject.put("val", str2);
            }
            return DingerAudioTools.SendCmdToDevice(dtiot_ble_request.BLE_REQUEST_SYS_CONTROL, jSONObject.toString());
        } catch (Exception e) {
            Log.e(TAG, "sendSysControl failed", e);
            return -1;
        }
    }
}

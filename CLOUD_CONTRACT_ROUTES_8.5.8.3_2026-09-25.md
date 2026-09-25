# Official 8.5.8.3 selected non-OTA IDL inventory

Generated from local APK classes28. These are logical RPC routes, not HTTP URLs or proof every method is used by this A1.
Field types/tags, full signatures and recursively referenced models are in the companion JSON. Requiredness is not inferred.

| Service | Methods |
| --- | ---: |
| com.dingtalk.device.client.DeviceIService | 24 |
| com.dingtalk.device.client.DeviceMonitorIService | 2 |
| com.dingtalk.deviceStatus.client.DeviceStatusService | 2 |
| com.dingtalk.device_connection.client.DeviceConnectionIService | 5 |
| com.dingtalk.device_setting.client.DeviceSettingIService | 2 |
| com.dingtalk.dtiot_a1_ai_assistant.client.DingerAiAssistantI | 5 |
| com.dingtalk.dtiot_ai_scene.client.DeviceAiSceneIService | 15 |
| com.dingtalk.dtiot_device_task.client.DeviceTaskIService | 10 |
| com.dingtalk.dtiot_file.client.DeviceFileIService | 16 |
| com.dingtalk.dtiot_minutes.client.FlashMinutesCommerceLwpService | 5 |
| com.dingtalk.dtiot_note.client.DeviceNoteIService | 4 |

## com.dingtalk.device.client.DeviceIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceI/active` | String str, String str2, String str3 | com.dingtalk.device.models.ActiveDeviceModel |
| `/r/Adaptor/DeviceI/agreeBindPermission` | String str, String str2, Long l, String str3, String str4 | java.lang.Void |
| `/r/Adaptor/DeviceI/askForBindPermission` | com.dingtalk.device.models.DeviceBindPermissionModel | com.dingtalk.device.models.BindPermissionResultModel |
| `/r/Adaptor/DeviceI/askForBindPermissionNeedAdminAgree` | com.dingtalk.device.models.DeviceBindPermissionModel | com.dingtalk.device.models.BindPermissionResultModel |
| `/r/Adaptor/DeviceI/bind` | String str, String str2, String str3, String str4, String str5, String str6 | com.dingtalk.device.models.BindDeviceModel |
| `/r/Adaptor/DeviceI/bindAndActive` | com.dingtalk.device.models.BindAndActiveModel | com.dingtalk.device.models.BindDeviceModel |
| `/r/Adaptor/DeviceI/checkDeviceManager` | Integer num, Long l | com.dingtalk.device.models.DeviceAuthModel |
| `/r/Adaptor/DeviceI/getDeviceEndorsementV2` | com.dingtalk.device.models.DeviceEncryptModel | com.dingtalk.device.models.EndorseModel |
| `/r/Adaptor/DeviceI/getDeviceInfo` | Integer num, Long l | com.dingtalk.device.models.DeviceModel |
| `/r/Adaptor/DeviceI/getDeviceLiteAppUrl` | Integer num, Long l | java.lang.String |
| `/r/Adaptor/DeviceI/getDeviceSecret` | Integer num, Long l | java.lang.String |
| `/r/Adaptor/DeviceI/getDeviceStatus` | String str, Long l | com.dingtalk.device.models.DeviceStatusModel |
| `/r/Adaptor/DeviceI/listDevices` | List<Long> list, String str, Integer num | List<ListDeviceModel> |
| `/r/Adaptor/DeviceI/provideActiveCode` | String str, String str2 | com.dingtalk.device.models.ActiveCodeModel |
| `/r/Adaptor/DeviceI/queryDeviceInfo` | com.dingtalk.device.models.DeviceQueryParam | com.dingtalk.device.models.DeviceModel |
| `/r/Adaptor/DeviceI/queryUserBindDevices` | com.dingtalk.device.models.QueryUserBindDevicesRequestModel | com.dingtalk.device.models.QueryUserBindDevicesResultModel |
| `/r/Adaptor/DeviceI/report` | String str, String str2, String str3, String str4, Map<String, String> map | java.lang.Void |
| `/r/Adaptor/DeviceI/unbind` | String str, String str2, String str3, String str4 | java.lang.Void |
| `/r/Adaptor/DeviceI/unbindByDeviceSelf` | Integer num, Long l, String str, String str2 | java.lang.Void |
| `/r/Adaptor/DeviceI/unbindV2` | String str, String str2, String str3, Long l | java.lang.Void |
| `/r/Adaptor/DeviceI/unbindV3` | com.dingtalk.device.models.DeviceUnBindRequestModel | com.dingtalk.device.models.DeviceUnBindResultModel |
| `/r/Adaptor/DeviceI/updateDevcieNick` | Integer num, Long l, String str | java.lang.Void |
| `/r/Adaptor/DeviceI/updateDeviceProperties` | com.dingtalk.device.models.UpdateDevicePropertiesRequestModel | com.dingtalk.device.models.UpdateDevicePropertiesResultModel |
| `/r/Adaptor/DeviceI/validForBind` | String str, String str2 | com.dingtalk.device.models.OrgModel |

## com.dingtalk.device.client.DeviceMonitorIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceMonitorI/queryUserBindDevices` | com.dingtalk.device.models.QueryUserBindDevicesRequestModel | com.dingtalk.device.models.QueryUserBindDevicesResultModel |
| `/r/Adaptor/DeviceMonitorI/updateDeviceProperties` | com.dingtalk.device.models.UpdateDevicePropertiesRequestModel | com.dingtalk.device.models.UpdateDevicePropertiesResultModel |

## com.dingtalk.deviceStatus.client.DeviceStatusService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceStatus/subscribe` | com.dingtalk.deviceStatus.models.Subscribe | com.dingtalk.deviceStatus.models.Result |
| `/r/Adaptor/DeviceStatus/unSubscribe` | com.dingtalk.deviceStatus.models.UnSubscribe | com.dingtalk.deviceStatus.models.Result |

## com.dingtalk.device_connection.client.DeviceConnectionIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceConnectionI/createDeviceConnection` | com.dingtalk.device_connection.models.CreateDeviceConnectionRequestModel | com.dingtalk.device_connection.models.CreateDeviceConnectionResultModel |
| `/r/Adaptor/DeviceConnectionI/deleteDeviceConnections` | com.dingtalk.device_connection.models.DeleteDeviceConnectionsRequestModel | com.dingtalk.device_connection.models.DeleteDeviceConnectionsResultModel |
| `/r/Adaptor/DeviceConnectionI/queryDeviceConnections` | com.dingtalk.device_connection.models.QueryDeviceConnectionListRequestModel | com.dingtalk.device_connection.models.QueryDeviceConnectionListResultModel |
| `/r/Adaptor/DeviceConnectionI/requestDeviceConnections` | com.dingtalk.device_connection.models.RequestDeviceConnectionsRequestModel | com.dingtalk.device_connection.models.RequestDeviceConnectionsResultModel |
| `/r/Adaptor/DeviceConnectionI/updateDeviceConnection` | com.dingtalk.device_connection.models.UpdateDeviceConnectionRequestModel | com.dingtalk.device_connection.models.UpdateDeviceConnectionResultModel |

## com.dingtalk.device_setting.client.DeviceSettingIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceSettingI/queryDeviceSettings` | com.dingtalk.device_setting.models.QueryDeviceSettingRequestModel | com.dingtalk.device_setting.models.QueryDeviceSettingResultModel |
| `/r/Adaptor/DeviceSettingI/updateDeviceSetting` | com.dingtalk.device_setting.models.UpdateDeviceSettingRequestModel | com.dingtalk.device_setting.models.UpdateDeviceSettingResultModel |

## com.dingtalk.dtiot_a1_ai_assistant.client.DingerAiAssistantI

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DingerAiAssistantI/createAudioMemo` | com.dingtalk.dtiot_a1_ai_assistant.models.CreateAudioMemoReqModel | com.dingtalk.dtiot_a1_ai_assistant.models.CreateAudioMemoRspModel |
| `/r/Adaptor/DingerAiAssistantI/executeEmptyMission` | com.dingtalk.dtiot_a1_ai_assistant.models.ExecuteEmptyMissionReqModel | com.dingtalk.dtiot_a1_ai_assistant.models.ExecuteEmptyMissionRspModel |
| `/r/Adaptor/DingerAiAssistantI/getMissionList` | com.dingtalk.dtiot_a1_ai_assistant.models.GetMissionListReqModel | com.dingtalk.dtiot_a1_ai_assistant.models.GetMissionListRspModel |
| `/r/Adaptor/DingerAiAssistantI/getUserHomeLink` | com.dingtalk.dtiot_a1_ai_assistant.models.GetUserHomeLinkReqModel | com.dingtalk.dtiot_a1_ai_assistant.models.GetUserHomeLinkRspModel |
| `/r/Adaptor/DingerAiAssistantI/searchMission` | com.dingtalk.dtiot_a1_ai_assistant.models.SearchMissionReqModel | com.dingtalk.dtiot_a1_ai_assistant.models.SearchMissionRspModel |

## com.dingtalk.dtiot_ai_scene.client.DeviceAiSceneIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceAiSceneI/createAiScene` | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneRequestModel | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneResultModel |
| `/r/Adaptor/DeviceAiSceneI/createAiSceneRule` | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneRuleRequestModel | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneRuleResultModel |
| `/r/Adaptor/DeviceAiSceneI/createAiSceneSummary` | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneSummaryRequestModel | com.dingtalk.dtiot_ai_scene.models.CreateAiSceneSummaryResultModel |
| `/r/Adaptor/DeviceAiSceneI/createVoiceAssistantFunctionCall` | com.dingtalk.dtiot_ai_scene.models.CreateVoiceAssistantFunctionCallRequestModel | com.dingtalk.dtiot_ai_scene.models.CreateVoiceAssistantFunctionCallResultModel |
| `/r/Adaptor/DeviceAiSceneI/deleteAiScene` | com.dingtalk.dtiot_ai_scene.models.DeleteAiSceneRequestModel | com.dingtalk.dtiot_ai_scene.models.DeleteAiSceneResultModel |
| `/r/Adaptor/DeviceAiSceneI/deleteAiSceneRule` | com.dingtalk.dtiot_ai_scene.models.DeleteAiSceneRuleRequestModel | com.dingtalk.dtiot_ai_scene.models.DeleteAiSceneRuleResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAiSceneAvatarList` | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneAvatarListRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneAvatarListResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAiSceneById` | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneByIdRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneByIdResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAiSceneList` | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneListRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneListResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAiSceneRuleList` | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneRuleListRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneRuleListResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAiSceneSummaryList` | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneSummaryListRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAiSceneSummaryListResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryAssistantByDeviceId` | com.dingtalk.dtiot_ai_scene.models.QueryAssistantByDeviceIdRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryAssistantByDeviceIdResultModel |
| `/r/Adaptor/DeviceAiSceneI/queryDeviceByAssistantId` | com.dingtalk.dtiot_ai_scene.models.QueryDeviceByAssistantIdRequestModel | com.dingtalk.dtiot_ai_scene.models.QueryDeviceByAssistantIdResultModel |
| `/r/Adaptor/DeviceAiSceneI/updateAiScene` | com.dingtalk.dtiot_ai_scene.models.UpdateAiSceneRequestModel | com.dingtalk.dtiot_ai_scene.models.UpdateAiSceneResultModel |
| `/r/Adaptor/DeviceAiSceneI/updateAiSceneRule` | com.dingtalk.dtiot_ai_scene.models.UpdateAiSceneRuleRequestModel | com.dingtalk.dtiot_ai_scene.models.UpdateAiSceneRuleResultModel |

## com.dingtalk.dtiot_device_task.client.DeviceTaskIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceTaskI/createGenerateMinutesTask` | com.dingtalk.dtiot_device_task.models.CreateGenerateMinutesTaskRequestModel | com.dingtalk.dtiot_device_task.models.CreateGenerateMinutesTaskResultModel |
| `/r/Adaptor/DeviceTaskI/createRecordTask` | com.dingtalk.dtiot_device_task.models.CreateRecordTaskRequestModel | com.dingtalk.dtiot_device_task.models.CreateRecordTaskResultModel |
| `/r/Adaptor/DeviceTaskI/createSyncFileTask` | com.dingtalk.dtiot_device_task.models.CreateSyncFileTaskRequestModel | com.dingtalk.dtiot_device_task.models.CreateSyncFileTaskResultModel |
| `/r/Adaptor/DeviceTaskI/createTranslateTask` | com.dingtalk.dtiot_device_task.models.CreateTranslateTaskRequestModel | com.dingtalk.dtiot_device_task.models.CreateTranslateTaskResultModel |
| `/r/Adaptor/DeviceTaskI/createUploadFileTask` | com.dingtalk.dtiot_device_task.models.CreateUploadFileTaskRequestModel | com.dingtalk.dtiot_device_task.models.CreateUploadFileTaskResultModel |
| `/r/Adaptor/DeviceTaskI/queryOngoingScheduleDeviceTask` | com.dingtalk.dtiot_device_task.models.QueryOngoingScheduleDeviceTaskRequestModel | com.dingtalk.dtiot_device_task.models.QueryOngoingScheduleDeviceTaskResultModel |
| `/r/Adaptor/DeviceTaskI/queryRecordTask` | com.dingtalk.dtiot_device_task.models.QueryRecordTaskRequestModel | com.dingtalk.dtiot_device_task.models.QueryRecordTaskResultModel |
| `/r/Adaptor/DeviceTaskI/sendDeviceTaskCommand` | com.dingtalk.dtiot_device_task.models.SendDeviceTaskCommandRequestModel | com.dingtalk.dtiot_device_task.models.SendDeviceTaskCommandResultModel |
| `/r/Adaptor/DeviceTaskI/updateDeviceTask` | com.dingtalk.dtiot_device_task.models.UpdateDeviceTaskRequestModel | com.dingtalk.dtiot_device_task.models.UpdateDeviceTaskResultModel |
| `/r/Adaptor/DeviceTaskI/updateRecordTask` | com.dingtalk.dtiot_device_task.models.UpdateRecordTaskRequestModel | com.dingtalk.dtiot_device_task.models.UpdateRecordTaskResultModel |

## com.dingtalk.dtiot_file.client.DeviceFileIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceFileI/batchUpdateFileToGroup` | com.dingtalk.dtiot_file.models.BatchUpdateFileToGroupRequestModel | com.dingtalk.dtiot_file.models.BatchUpdateFileToGroupResultModel |
| `/r/Adaptor/DeviceFileI/createFile` | com.dingtalk.dtiot_file.models.CreateFileRequestModel | com.dingtalk.dtiot_file.models.CreateFileResultModel |
| `/r/Adaptor/DeviceFileI/createFileGroup` | com.dingtalk.dtiot_file.models.CreateFileGroupRequestModel | com.dingtalk.dtiot_file.models.CreateFileGroupResultModel |
| `/r/Adaptor/DeviceFileI/deleteFileGroups` | com.dingtalk.dtiot_file.models.DeleteFileGroupsRequestModel | com.dingtalk.dtiot_file.models.DeleteFileGroupsResultModel |
| `/r/Adaptor/DeviceFileI/deleteFiles` | com.dingtalk.dtiot_file.models.DeleteFilesRequestModel | com.dingtalk.dtiot_file.models.DeleteFilesResultModel |
| `/r/Adaptor/DeviceFileI/listNews` | com.dingtalk.dtiot_file.models.ListNewFileListRequestModel | com.dingtalk.dtiot_file.models.ListNewFileListResultModel |
| `/r/Adaptor/DeviceFileI/loadHistory` | com.dingtalk.dtiot_file.models.LoadHistoryFileListRequestModel | com.dingtalk.dtiot_file.models.LoadHistoryFileListResultModel |
| `/r/Adaptor/DeviceFileI/queryFile` | com.dingtalk.dtiot_file.models.QueryFileRequestModel | com.dingtalk.dtiot_file.models.QueryFileResultModel |
| `/r/Adaptor/DeviceFileI/queryFileDownloadInfo` | com.dingtalk.dtiot_file.models.QueryFileDownloadInfoRequestModel | com.dingtalk.dtiot_file.models.QueryFileDownloadInfoResultModel |
| `/r/Adaptor/DeviceFileI/queryFileGroupList` | com.dingtalk.dtiot_file.models.QueryFileGroupListRequestModel | com.dingtalk.dtiot_file.models.QueryFileGroupListResultModel |
| `/r/Adaptor/DeviceFileI/queryFileList` | com.dingtalk.dtiot_file.models.QueryFileListRequestModel | com.dingtalk.dtiot_file.models.QueryFileListResultModel |
| `/r/Adaptor/DeviceFileI/queryGenerateMinutesConfig` | com.dingtalk.dtiot_file.models.GenerateMinutesConfigQueryRequestModel | com.dingtalk.dtiot_file.models.GenerateMinutesConfigQueryResultModel |
| `/r/Adaptor/DeviceFileI/recoverFiles` | com.dingtalk.dtiot_file.models.RecoverFilesRequestModel | com.dingtalk.dtiot_file.models.RecoverFilesResultModel |
| `/r/Adaptor/DeviceFileI/syncFileList` | com.dingtalk.dtiot_file.models.SyncFileListRequestModel | com.dingtalk.dtiot_file.models.SyncFileListResultModel |
| `/r/Adaptor/DeviceFileI/updateFile` | com.dingtalk.dtiot_file.models.UpdateFileRequestModel | com.dingtalk.dtiot_file.models.UpdateFileResultModel |
| `/r/Adaptor/DeviceFileI/updateFileGroup` | com.dingtalk.dtiot_file.models.UpdateFileGroupRequestModel | com.dingtalk.dtiot_file.models.UpdateFileGroupResultModel |

## com.dingtalk.dtiot_minutes.client.FlashMinutesCommerceLwpService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/FlashMinutesCommerceLwp/bookMinutes` | com.dingtalk.dtiot_minutes.models.BookMinutesRequestModel | com.dingtalk.dtiot_minutes.models.BookMinutesResponseModel |
| `/r/Adaptor/FlashMinutesCommerceLwp/checkMinutesCommerce` | com.dingtalk.dtiot_minutes.models.CheckMinutesCommerceRequestModel | com.dingtalk.dtiot_minutes.models.CheckMinutesCommerceResponseModel |
| `/r/Adaptor/FlashMinutesCommerceLwp/getMinutesCommerce` | com.dingtalk.dtiot_minutes.models.GetMinutesCommerceRequestModel | com.dingtalk.dtiot_minutes.models.GetMinutesCommerceResponseModel |
| `/r/Adaptor/FlashMinutesCommerceLwp/getScreenInfo` | com.dingtalk.dtiot_minutes.models.GetScreenInfoRequestModel | com.dingtalk.dtiot_minutes.models.GetScreenInfoResponseModel |
| `/r/Adaptor/FlashMinutesCommerceLwp/reportScreenUpper` | com.dingtalk.dtiot_minutes.models.ReportScreenUpperRequestModel | com.dingtalk.dtiot_minutes.models.ReportScreenUpperResponseModel |

## com.dingtalk.dtiot_note.client.DeviceNoteIService

| Logical route | Request | Response |
| --- | --- | --- |
| `/r/Adaptor/DeviceNoteI/createNote` | com.dingtalk.dtiot_note.models.CreateNoteRequestModel | com.dingtalk.dtiot_note.models.CreateNoteResultModel |
| `/r/Adaptor/DeviceNoteI/deleteNote` | com.dingtalk.dtiot_note.models.DeleteNoteRequestModel | com.dingtalk.dtiot_note.models.DeleteNoteResultModel |
| `/r/Adaptor/DeviceNoteI/queryNoteList` | com.dingtalk.dtiot_note.models.QueryNoteListRequestModel | com.dingtalk.dtiot_note.models.QueryNoteListResultModel |
| `/r/Adaptor/DeviceNoteI/updateNote` | com.dingtalk.dtiot_note.models.UpdateNoteRequestModel | com.dingtalk.dtiot_note.models.UpdateNoteResultModel |

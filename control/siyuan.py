import json
import logging

from api.siyuan import APISiyuan
from define.base import ResourceType, EndPoint
from define.siyuan import SiyuanMessage
from entity.siyuan import SiyuanBlockResource
from interface import EndPointMap, ISiyuan, ICloud123
from log import get_logger
from tools.base import SingletonMeta

control_log = get_logger("control")


# noinspection SqlNoDataSourceInspection
class SiyuanControl(metaclass=SingletonMeta):

    @classmethod
    async def download_file(cls, resource: SiyuanBlockResource, custom_record, log_level=logging.INFO, end_point_enum=EndPoint.SIYUAN, toast=True):
        if resource.typ != ResourceType.WEB:
            return  # 本地资源  跳过
        end_point: ISiyuan = EndPointMap[end_point_enum]
        if not (new_url := await end_point.receive(resource, log_level)):
            return False
        toast and await APISiyuan.async_push_msg(SiyuanMessage.下载成功_单文件.format(filename=resource.filename))
        await cls._UpdateInfo(resource, new_url, custom_record)
        return True

    @classmethod
    async def upload_file(cls, resource: SiyuanBlockResource, custom_record, log_level=logging.INFO, end_point_enum=EndPoint.CLOUD_123, toast=True):
        end_point: ICloud123 = EndPointMap[end_point_enum]
        if end_point.is_same_as_record(resource.filename, custom_record.get(resource.id)):
            return False
        if not (new_url := await end_point.receive(resource, log_level)):
            return False
        toast and await APISiyuan.async_push_msg(SiyuanMessage.上传成功_单文件.format(filename=resource.filename))
        await cls._UpdateInfo(resource, new_url, custom_record)
        return True

    @classmethod
    async def _UpdateInfo(cls, resource: SiyuanBlockResource, new_url, record):
        new_data = resource.markdown.replace(resource.url, new_url)
        await APISiyuan.update_block(resource.id, new_data)
        record[resource.id] = new_url

    # region Record
    """
    自定义文档属性 custom-record
    快速检查 block_id - 资源 是否对应
    如果对应则返回
    不对应  则更新
    """

    @classmethod
    async def GetCustomRecord(cls, notebook_id):
        record = (await APISiyuan.get_block_attr(notebook_id))["data"].get("custom-record", {})
        return record and json.loads(record)

    @classmethod
    async def SetCustomRecord(cls, notebook_id, record):
        await APISiyuan.set_block_attr(notebook_id, {
            "custom-record": json.dumps(record),
        })
    # endregion

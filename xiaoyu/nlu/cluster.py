"""未识别数据的归集，去重和标记."""
import random
import time

import pymysql

from xiaoyu.utils.funcs import generate_uint, post_rpc

__all__ = ["run_cluster"]


# 读取未归集数据用到的sql语句
SQL_READ_RAW = r"""
    SELECT
        `id`, `bot_id`, `flow_id`, `unrid_type`, `says`, `coll_status`, `callout_status`
    FROM
        dialog_unird_says
    WHERE
        bot_id='{robot_code}' AND coll_status=0
"""

# 写入归集的类别用到的sql语句
SQL_WRITE_CLUSTER = r"""
    INSERT INTO
        dialog_unird_clustering
    (
        `id`,
        `bot_id`,
        `flow_id`,
        `question`,
        `frequency`,
        `reference_faq_id`,
        `callout_status`,
        `create_time`,
        `update_user_id`,
        `update_user_name`,
        `update_time`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

SQL_DELETE_RELATION = r"""
    DELETE FROM
        dialog_unird_clustering_says
    WHERE clustering_id =
        ( SELECT `id` FROM dialog_unird_clustering WHERE bot_id = '{robot_code}' )
"""

# 重新归集，删除已有的归集类别
SQL_DELETE_CLUSTER = r"""
    DELETE FROM dialog_unird_clustering WHERE bot_id = '{robot_code}'
"""

# 写入归集类别与数据之间的关系
SQL_WRITE_CLUSTER_RELATION = r"""
    INSERT INTO
        dialog_unird_clustering_says
    (
        `clustering_id`,
        `says_id`
    )
    VALUES (%s, %s)
"""


def run_cluster(robot_code):
    """
    未识别数据的归集，去重和标记.

    Args:
        robot_code (str): 机器人编码.
    """
    conn = pymysql.connect(**DATABASE_CONFIG)

    # read raw data
    with conn.cursor() as cursor:
        cursor.execute(SQL_READ_RAW.format(robot_code=robot_code))
        raw_data = cursor.fetchall()

    if len(raw_data) == 0:
        return -1

    # clustering
    questions = [item[4] for item in raw_data]
    # 调用`clusters`接口的返回值示例
    """json
    [
        {
            "cluster": [0, 1],
            "question": "",
            "answer": "",
            "confidence": ""
        }
    ]
    """
    clusters = post_rpc(URL, {"robot_code": robot_code, "questions": questions})["data"]

    # 删除之前的归集数据
    with conn.cursor() as cursor:
        cursor.execute(SQL_DELETE_RELATION.format(robot_code=robot_code))
        cursor.execute(SQL_DELETE_CLUSTER.format(robot_code=robot_code))

        clusters_data = []
        relations_data = []
        for item in clusters:
            indexes = item["cluster"]

            example_index = random.choice(indexes)
            example = raw_data[example_index]
            cur = time.strftime("%Y-%m-%d %H:%M:%S")
            uid = (generate_uint(),)  # id
            data = [
                uid,
                robot_code,  # bot_id
                raw_data[indexes[0]][2],  # flow_id
                example[4],  # question
                len(indexes),  # frequency
                item["faq_id"],  # reference_faq_id
                0,  # callout_status
                cur,  # create_time
                0,  # update_user_id
                "xiaoyu_ai",  # update_user_name
                cur,  # update_time
            ]
            clusters_data.append(data)

            for index in indexes:
                data = [uid, raw_data[index][0]]
                relations_data.append(data)

        cursor.executemany(SQL_WRITE_CLUSTER, clusters_data)
        cursor.executemany(SQL_WRITE_CLUSTER_RELATION, relations_data)
    conn.commit()

    # 将归集后的数据写入数据库
    conn.close()
    return 0

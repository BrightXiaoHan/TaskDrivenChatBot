"""Test cases for the cluster interface."""
import pymysql
import pytest

import backend.nlu.cluster as cluster
from config import DATABASE_CONFIG
from utils.funcs import generate_uint


@pytest.fixture(scope="module")
def mysql_conn():
    """Create a connection to the database."""
    conn = pymysql.connect(**DATABASE_CONFIG)
    return conn


@pytest.fixture(scope="module", autouse=True)
def auto_insert_data(robot_code: int, mysql_conn: pymysql.connections.Connection):
    """Insert some test data to database."""
    # delete original data from database
    delete_sql = "DELETE FROM `dialog_unird_says` WHERE `bot_id` = '{}'".format(
        robot_code
    )
    mysql_conn.cursor().execute(delete_sql)

    sql = """
        INSERT INTO `dialog_unird_says`
            (`id`, `bot_id`, `flow_id`, `unrid_type`, `says`, `coll_status`, `callout_status`, `create_time`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = [
        [generate_uint(), robot_code, 0, 1, "你好", 0, 0, "2019-01-01 00:00:00"],
        [generate_uint(), robot_code, 0, 1, "你也好", 0, 0, "2019-01-01 00:00:00"],
        [generate_uint(), robot_code, 0, 1, "Apple手机多少钱", 0, 0, "2019-01-01 00:00:00"],
        [generate_uint(), robot_code, 0, 1, "苹果手机多少钱", 0, 0, "2019-01-01 00:00:00"],
    ]

    # insert test data
    with mysql_conn.cursor() as cursor:
        cursor.executemany(sql, values)
    mysql_conn.commit()
    yield values

    # Delete test data
    with mysql_conn.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM `dialog_unird_clustering_says`
            WHERE `says_id` in
                (SELECT id FROM `dialog_unird_says` WHERE `bot_id` = '{}')
            """.format(
                robot_code
            )
        )
        cursor.execute(
            "DELETE FROM `dialog_unird_says` WHERE `bot_id` = '{}'".format(robot_code)
        )
        cursor.execute(
            "DELETE FROM `dialog_unird_clustering` WHERE `bot_id` = '{}'".format(
                robot_code
            )
        )
    mysql_conn.commit()


@pytest.mark.asyncio
async def test_cluster(robot_code: int, mysql_conn: pymysql.connections.Connection):
    """Test the cluster interface."""
    cluster.run_cluster(robot_code)
    with mysql_conn.cursor() as cursor:
        cursor.execute(
            "SELECT `question`, `frequency` FROM `dialog_unird_clustering` WHERE `bot_id` = '{}'".format(
                robot_code
            )
        )
        result = cursor.fetchall()
        assert len(result) == 2
        assert result[0][0] in ["你好", "你也好"]
        assert result[0][1] == 2
        assert result[1][0] in ["Apple手机多少钱", "苹果手机多少钱"]
        assert result[1][1] == 2

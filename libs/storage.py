import sqlite3
from enum import Enum
import logging


class StorageBackend(Enum):
    SQLITE = 0


class Storage(object):
    def __init__(self, db: str, backend: StorageBackend = StorageBackend.SQLITE):
        self.conn = sqlite3.connect(db, isolation_level='EXCLUSIVE', check_same_thread=False)
        self.logger = logging.getLogger('storage:' + db)
        self.logger.debug("init")
        self.update()
        self.sync()

    def update(self):
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS user(
            userid VARCHAR(50) PRIMARY KEY,
            chips INT
            );""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS usertable(
            tableid VARCHAR(50),
            userid VARCHAR(50),
            chips INT,
            FOREIGN KEY(userid) REFERENCES user(userid),
            primary key (tableid,userid)
            );""")
        cursor.execute("""COMMIT;""")
        cursor.close()

    def sync(self):
        self.logger.debug("sync")
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        try:
            cursor.execute(
                """SELECT tableid, userid, chips FROM usertable;"""
            )
            self.logger.debug("sync fetch all")
            for record in cursor.fetchall():
                self.logger.debug("sync fetch all %s", str(record))
                cursor.execute("""SELECT chips FROM user WHERE user.userid = ?""", (record[1],))
                current_chips = cursor.fetchone()[0]
                cursor.execute(
                    """UPDATE user SET chips = ? WHERE userid = ?;""",
                    (current_chips + record[2], record[1]))
            cursor.execute("""DELETE FROM usertable;""")
        except Exception:
            pass
        finally:
            cursor.execute("""COMMIT;""")
            cursor.close()

    def create_user(self, userid: str, chips: int) -> str:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""BEGIN""")
            cursor.execute(
                """INSERT INTO user (userid, chips) VALUES (?, ?);""",
                (userid, chips))
        except sqlite3.IntegrityError:
            pass
        except Exception:
            return "cannot create user"
        finally:
            cursor.execute("""COMMIT""")
            cursor.close()

    def fetch_user_chip(self, userid) -> (int, str):
        """Given userid, return (chips, err)"""
        try:
            return self.conn.execute("""SELECT chips FROM user WHERE user.userid = ?""", (userid,)).fetchone()[0], None
        except Exception:
            return 0, "user not exist"

    def transfer_user_chip_to_table(self, userid: str, max_chip: int, tableid: str) -> (int, int, str):
        """Transfer user chip to a specific table

        Args:
            userid (str): target user
            max_chip (int): expected chips to pay for entering the table
            tableid (str): table id

        Returns:
            actual_paid (int): the chips that the user actually paid
            err (str): None for success
        """
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        chip_used = 0
        try:
            chips, err = self.fetch_user_chip(userid)
            if err is not None:
                return 0, err
            chip_used = min(chips, max_chip)
            cursor.execute(
                """UPDATE user
                SET chips = ?
                WHERE userid = ?;""",
                (chips - chip_used, userid)
            )
            cursor.execute(
                """INSERT INTO usertable (tableid, userid, chips)
                VALUES (?, ?, ?);""",
                (tableid, userid, chip_used)
            )
        except Exception:
            pass
        finally:
            cursor.execute("""COMMIT""")
            cursor.close()
        return chip_used, None

    def change_user_chip(self, userid: str, chips: int) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        pre_chips, err = self.fetch_user_chip(userid)
        if err is not None:
            return err
        cursor.execute(
            """UPDATE user
            SET chips = ?
            WHERE userid = ?;""",
            (pre_chips + chips, userid)
        )
        cursor.execute("""COMMIT;""")
        cursor.close()

    def leave_table(self, userid: str, tableid: str, remainChip: int):
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        try:
            current_chips, err = self.fetch_user_chip(userid)
            if err is not None:
                return err
            cursor.execute(
                """UPDATE user
                SET chips = ?
                WHERE userid = ?;""",
                (current_chips + remainChip, userid)
            )
            cursor.execute(
                """DELETE FROM usertable WHERE usertable.userid = ? and usertable.tableid = ?""",
                (userid, tableid)
            )
        except Exception:
            pass
        finally:
            cursor.execute("""COMMIT;""")
            cursor.close()

    def change_table_chip(self, userid: str, tableid: str, chips: int):
        cursor = self.conn.cursor()
        cursor.execute("""BEGIN""")
        try:
            cursor.execute(
                """UPDATE usertable
                SET chips = ?
                WHERE tableid=? and userid = ?;""",
                (chips, tableid, userid)
            )
        except Exception:
            return "change table chip failed"
        finally:
            cursor.execute("""COMMIT;""")
            cursor.close()


if __name__ == '__main__':
    s = Storage('test')
    s.create_user('test', 200)
    print(s.fetch_user_chip('test'))
    t = s.transfer_user_chip_to_table('test', 50, 'table')
    print(s.fetch_user_chip('test'))
    s.leave_table('test', 'table', 20)
    print(s.fetch_user_chip('test'))

    print(s.fetch_user_chip('testttt'))
    t = s.transfer_user_chip_to_table('testttt', 50, 'table')
    print(t)

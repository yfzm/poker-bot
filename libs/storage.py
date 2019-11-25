import sqlite3
from enum import Enum


class StorageBackend(Enum):
    SQLITE = 0


class Storage(object):
    def __init__(self, db: str, backend: StorageBackend = StorageBackend.SQLITE):
        self.conn = sqlite3.connect(db)
        self.update()

    def update(self):
        user = """create table IF NOT EXISTS user(
            userid VARCHAR(50) PRIMARY KEY,
            chips INT
        );"""
        self.conn.execute(user)
        self.conn.commit()

    def createUser(self, userid: str, chips: int):
        user = """INSERT INTO user (userid, chips)
            VALUES (?, ?);"""
        res = self.conn.execute(user, (userid, chips)).fetchone()
        self.conn.commit()
        return res

    def getUserChip(self, userid: str):
        chip = """select chips from user where user.userid = ?"""
        res = self.conn.execute(chip, (userid,)).fetchone()
        self.conn.commit()
        return res

    def setUserChip(self, userid: str, chips: int):
        chip = """UPDATE user
        SET chips = ?
        WHERE userid = ?;"""
        res = self.conn.execute(chip, (chips, userid)).fetchone()
        self.conn.commit()
        return res


if __name__ == '__main__':
    s = Storage('test')
    s.createUser('test', 200)
    print(s.getUserChip('test'))
    print(s.setUserChip('test', 100))
    print(s.getUserChip('test'))

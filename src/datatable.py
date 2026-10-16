"""Implement Datatable for writing and reading data that should be stored on the disk."""

from abc import abstractmethod
import csv
from pathlib import Path
from typing import Any, Protocol, Self

from src.cli import CommandError, command

DATAPATH = Path('data')


class Datarow(Protocol):
    """Protocol for data row objects that can be stored in a Datatable."""
    @classmethod
    @abstractmethod
    def unserialize(cls, fields: list[str]) -> Self: ...

    @abstractmethod
    def serialize(self) -> list[str]: ...

class Datatable[T: Datarow](dict[str, T]):
    """Represent the dictionary associated with a CSV file."""
    datatables: dict[str, Datatable[Any]] = {}

    def __init__(self, name: str, row_type: type[T]) -> None:
        """Create a Datatable with associated CSV filename and field mapping names."""
        if name in self.datatables:
            raise ValueError(f"Datatable already exists: {name}")
        self.name = name
        self.path = DATAPATH / (name + '.csv')
        self.row_type = row_type
        super().__init__()
        self.datatables[self.name] = self

    def load(self) -> None:
        """Load data from the associated CSV file on the disk."""
        self.clear()
        if not self.path.exists():
            return
        with self.path.open('r', newline='') as csvFile:
            self.update({fields[0]: self.row_type.unserialize(fields[1:]) for fields in csv.reader(csvFile)})

    def save(self) -> None:
        """Save data into the associated CSV file on the disk."""
        DATAPATH.mkdir(exist_ok= True)
        with self.path.open('w', newline='') as csvFile:
            writer = csv.writer(csvFile)
            for id, value in self.items():
                writer.writerow([id, *value.serialize()])

    @classmethod
    def save_all(cls) -> None:
        """Save all registered Datatable."""
        for table in cls.datatables.values():
            table.save()

    @classmethod
    def load_all(cls) -> None:
        """Load all registered Datatable."""
        for table in cls.datatables.values():
            table.load()


@command('datatable')
def datatable(action: str, tablename: str | None = None) -> None:
    """操作現有資料表（除錯用）。
    
    語法：
    * datatable list
      - 列出現有資料表。
    * datatable print <名稱>
      - 傾印資料表。
    * datatable save [<名稱>]
      - 將指定或所有資料表儲存至磁碟中。
    * datatable reload [<名稱>]
      - 從磁碟中載入指定或所有資料表。
    """
    if not action in ('list', 'print', 'save', 'reload'):
        raise CommandError(f'未知操作：{action}！')

    if action == 'list':
        if tablename is not None:
            raise CommandError('datatable list 不接受額外參數！')
        print('存在以下資料表：')
        print(', '.join(Datatable.datatables.keys()) if Datatable.datatables else '無資料表。')
        return

    if tablename is not None and tablename not in Datatable.datatables:
        raise CommandError(f'資料表 {tablename} 不存在！')

    if action == 'print':
        if not tablename:
            raise CommandError('資料表未指定！')
        print(f'資料表 {tablename} 內容：')
        print(Datatable.datatables[tablename])
    elif action == 'reload':
        try:
            if not tablename:
                Datatable.load_all()
            else:
                Datatable.datatables[tablename].load()
        except Exception as err:
            raise CommandError(f'載入失敗：{err}') from err
        print(f'成功載入資料表。')
    elif action == 'save':
        try:
            if not tablename:
                Datatable.save_all()
            else:
                Datatable.datatables[tablename].save()
        except Exception as err:
            raise CommandError(f'儲存失敗：{err}') from err
        print(f'成功儲存資料表。')
from collections.abc import Sequence
import csv
from pathlib import Path
from typing import Self

from src.cli import CommandError, command

datapath = Path('../data')

class Datatable(dict[str, dict[str, str]]):
	datatables: dict[str, Self] = {}

	def __init__(self, name: str, fieldnames: Sequence[str]) -> None:
		if name in Datatable.datatables:
			raise ValueError(f"Datatable already exists: {name}")
		self.name = name
		self.fieldnames = fieldnames
		self.path = datapath / (name + '.csv')
		super().__init__()
		if self.path.exists():
			self.load()
		Datatable.datatables[self.name] = self

	def load(self):
		self.clear()
		with self.path.open('r', newline='') as csvFile:
			self.update({fields[0]: dict(zip(self.fieldnames, fields[1:])) for fields in csv.reader(csvFile)})
	
	def save(self):
		datapath.mkdir(exist_ok= True)
		with self.path.open('w', newline='') as csvFile:
			writer = csv.writer(csvFile)
			for id, values in self.items():
				writer.writerow([id] + [values[field] for field in self.fieldnames])

def saveAll():
	for table in Datatable.datatables.values():
		table.save()

@command('datatable')
def datatable(action: str, tablename: str = ''):
	"""操作現有資料表（除錯用）
	
	語法：
	* datatable list
	* datatable print <名稱>
	* datatable save [<名稱>]
	* datatable reload [<名稱>]
	"""
	if not action in ('list', 'print', 'save', 'reload'):
		raise CommandError(f'未知操作：{action}！')
	if action == 'list':
		if tablename:
			raise CommandError('datatable list 不接受額外參數！')
		print('存在以下資料表：')
		print(', '.join([*Datatable.datatables.keys()]))
		return

	if tablename and tablename not in Datatable.datatables:
		raise CommandError(f'資料表 {tablename} 不存在！')

	datatables = [Datatable.datatables[tablename]] if tablename else [*Datatable.datatables.values()]

	if action == 'print':
		if not tablename:
			raise CommandError('資料表未指定！')
		print(datatables[0])
		return

	for table in datatables:
		try:
			table.load() if action == 'reload' else table.save()
		except Exception as err:
			raise CommandError(f'資料表 {table.name} 讀寫失敗：{err}') from err
	print(f'成功讀寫資料表 {', '.join(map(lambda x: x.name, datatables))}。')
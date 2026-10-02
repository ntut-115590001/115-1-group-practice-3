import json
import csv
from pathlib import Path
from typing import Iterable, NamedTuple

from src.cli import command

type datatable = dict[str, dict[str, str]]
datatables: dict[datatable, tuple[Path, str, list[str]]] = {}

datapath = Path('../data')

class Datatable(dict[str, dict[str, str]]):
	def __init__(self, name: str, fieldnames: list[str]) -> None:
		datapath.mkdir(exist_ok= True)
		self.name = name
		self.fieldnames = fieldnames
		self.path = datapath / (name + '.csv')
		if self.path.exists():
			with open(self.path, 'r', newline='') as csvFile:
				super().__init__({fields[0]: dict(zip(fieldnames, fields[1:])) for fields in csv.reader(csvFile)})
		else:
			super().__init__()

	def save(self):
		with open(self.path, 'w', newline='') as csvFile:
			writer = csv.writer(csvFile)
			for id, values in self.items():
				writer.writerows([id] + [values[field] for field in self.fieldnames])

def loadTable(name: str, fieldnames: list[str]):
	datapath.mkdir(exist_ok= True)
	path = datapath / (name + '.csv')
	table: datatable = {}
	if path.exists():
		with open(path, 'r', newline='') as csvFile:
			table.update({fields[0]: dict(zip(fieldnames, fields[1:])) for fields in csv.reader(csvFile)})
	datatables[table] = (path, name, fieldnames)
	return table

def save(table: datatable):
	if table not in datatables:
		raise ValueError("The input table wasn't registered!")
	path, name, fieldnames = datatables[table]
	with open(path, 'w', newline='') as csvFile:
		writer = csv.writer(csvFile)
		for id, values in table.items():
			writer.writerows([id] + [values[field] for field in fieldnames])

def saveAll():
	for table in datatables.keys():
		save(table)

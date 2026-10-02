import src.cli as cli
import src.datatable as datatable

print('歡迎使用本系統！輸入 > help 以取得指令清單。')

try:
	while True:
		try:
			result = cli.run(input('> '))
			if result == cli.Result.EXIT: # > exit
				break
		except KeyboardInterrupt: # Ctrl+C
			print()
			print('退出系統！')
			break
		except EOFError: # Ctrl+Z
			print('退出系統！')
			break
finally:
	datatable.saveAll()
	pass
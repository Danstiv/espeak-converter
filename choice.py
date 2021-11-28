def choice(text, choices=['1', '2']):
	while True:
		print(text)
		answer=input()
		if answer in choices:
			return answer

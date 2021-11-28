import cgi
import glob
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import chardet
import requests
from choice import choice
from custom_logging_formatter import Formatter
from fb2_parser import FB2Parser


DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
VERSION = '0.10'
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))
log.addHandler(console_handler)
file_handler = logging.FileHandler('log.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(Formatter('%(asctime)s - %(levelname)s - %(module)s.%(funcName)s (%(lineno)d)\n%(message)s'))
log.addHandler(file_handler)


def convert_book(url):
	log.info(f'Скачивание файла ({url})')
	while True:
		try:
			r = requests.post('https://downloader.danstiv.ru', json={'url': url, 'headers': {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}}, timeout=300)
		except requests.RequestException:
			log.info('Не удалось скачать файл, повторная попытка через 30 секунд.')
			time.sleep(30)
			continue
		if r.status_code != 200:
			log.info(f'Сервер вернул код {r.status_code}, повторная попытка через 10 секунд.')
			time.sleep(10)
			continue
		break
	content = r.content
	filename = cgi.parse_header(r.headers.get('content-disposition', ''))[1].get('filename', '')
	if not filename:
		filename = os.path.split(url)[-1]
	if '/' in filename or '..' in filename or len(filename.encode())>255:
		return 'Некорректное имя файла.'
	file, extension = os.path.splitext(filename)
	dirname = os.path.join(DIR, 'books')
	if not os.path.isdir(dirname):
		os.mkdir(dirname)
	extension = extension.lower()
	extensions = ['.txt', '.fb2']
	if extension=='.fb2':
		content = FB2Parser(content, lang='ru').parse()
		extension = '.txt'
	if extension=='.txt':
		files = [os.path.join(dirname, file)+'.txt']
		f = open(files[0], 'wb')
		f.write(content)
		f.close()
	else:
		temp_file = tempfile.mkstemp(suffix=extension)
		f = open(temp_file[0], 'wb')
		f.write(r.content)
		f.close()
		temp_dir = tempfile.mkdtemp()
		log.info('Распаковка архива.')
		process = subprocess.Popen([f'{DIR}\\lib\\unar.exe', '-o', temp_dir, temp_file[1]], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		while process.poll()==None:
			time.sleep(0.1)
		os.remove(temp_file[1])
		files = filter(lambda x: x.lower()[-4:] in extensions and os.path.isfile(x), glob.iglob(temp_dir+'/**', recursive=True))
		new_files = []
		for f in files:
			if f.lower()[-4:]=='.fb2':
				fl = open(f, 'rb')
				data = fl.read()
				fl.close()
				data = FB2Parser(data, lang='ru').parse()
				f = os.path.splitext(f)[0]+'.txt'
				fl = open(f, 'wb')
				fl.write(data.encode())
				fl.close()
			shutil.move(f, dirname)
			new_files.append(os.path.join(dirname, os.path.split(f)[-1]))
		files = new_files
		shutil.rmtree(temp_dir)
	if not files:
		return 'Текстовые файлы в архиве не обнаружены.'
	error = False
	processes = []
	processed_files = []
	log.info('Преобразование.')
	while files or processed_files or processes:
		if files:
			fl = files.pop(0)
			f = open(fl, 'rb')
			data=f.read()
			f.close()
			try:
				data = data.decode().encode()
			except Exception:
				log.info('Определение кодировки.')
				enc=chardet.detect(data)['encoding']
				log.info('Кодировка определена.')
				if not enc:
					[os.remove(f) for f in files]
					return 'Не удалось определить кодировку'
				if enc=='MacCyrillic':
					enc='1251'
				data=data.decode(enc).encode()
			f = open(fl, 'wb')
			f.write(data)
			f.close()
			processed_files.append(fl)
		if len(processes)<2 and processed_files:
			fl = processed_files[0]
			mp3_file = os.path.join(dirname, f'{os.path.splitext(os.path.split(fl)[-1])[0]}.mp3')
			process = subprocess.Popen([f'{DIR}\\lib\\eSpeak\\command_line\\espeak.exe', f'--path={DIR}\\lib\\eSpeak', '-f', fl, '-w', 'stdout', '-v', 'ru', '-s', '450', '|', f'{DIR}\\lib\\lame.exe', '--ignorelength', '-b', '96', '-', mp3_file], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			process.mp3_file = mp3_file
			process.txt_file = fl
			processes.append(process)
			del processed_files[0]
		i = 0
		while i<len(processes):
			p = processes[i]
			if p.poll()==None:
				i += 1
				continue
			if p.returncode:
				error = True
			os.remove(p.txt_file)
			if not os.path.isfile(p.mp3_file):
				error = True
			del processes[i]
		time.sleep(1)
	msgs = ['При преобразовании произошли ошибки'] if error else []
	msgs.insert(0, f'Книга "{os.path.splitext(file)[0]}" преобразована.')
	return '\n'.join(msgs)


def save_urls(urls):
	f = open('urls.txt', 'wb')
	f.write('\n'.join(urls).encode())
	f.close()

def get_urls():
	if not os.path.isfile('urls.txt'):
		return []
	f = open('urls.txt', 'rb')
	urls = f.read()
	f.close()
	try:
		urls = urls.decode()
	except UnicodeError:
		return []
	return [i for i in urls.replace('\r', '').split('\n') if i]


if __name__=='__main__':
	log.info(f'eSpeak converter V {VERSION}')
	urls = get_urls()
	if urls:
		log.info(f'Загружено {len(urls)} URL')
	while True:
		if urls and choice('1. Добавить url.\n2. Начать выполнение.')=='2':
			break

		url = input('Введите url на fb2 или txt файл: ')
		if not url:
			sys.exit()
		urls.append(url)
		save_urls(urls)
		log.debug(f'Добавлен URL {url}')
	for url in list(urls):
		try:
			log.info(convert_book(url))
			urls.remove(url)
			save_urls(urls)
		except Exception:
			log.exception(f'Произошло необработанное исключение:')
	if not urls:
		os.remove('urls.txt')
	input('Нажмите Enter для выхода')

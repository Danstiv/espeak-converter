Данная программа позволяет преобразовывать текстовые книги в mp3 формат.
Внимание, эта программа очень узкоспециализирована, она является временным решением, и её поддержка, скорее всего, будет прекращена после того, как сервис [Текст в речь](https://data2data.ru/tts) получит обновление.
## Алгоритм работы программы
1. Пользователь вводит один или несколько url-адресов на книги в формате txt или fb2 (или архив с книгой / книгами в данном формате).
2. Программа последовательно скачивает книги и преобразовывает их синтезатором eSpeak в формат mp3 (используется lame).
Для запуска из исходников установите [eSpeak](http://sourceforge.net/projects/espeak/files/espeak/espeak-1.48/setup_espeak-1.48.04.exe) и скопируйте папку, в которую был установлен eSpeak в папку lib, находящуюся в корне проекта.
Убедитесь в том, что папка называется "eSpeak".
Помимо скачивания установщика можно скачать один из релизов и скопировать eSpeak оттуда.
## Описание структуры проекта
Папка lib содержит:
1. lame - используется для преобразования wave-данных в mp3.
2. unar - используется для распаковки архивов.
3. eSpeak - используется для преобразования текста в речь (не включён в проект, инструкции для получения и добавления смотрите выше).

Файл downloader.py содержит код веб-сервера, используемого для скачивания книг (псевдо-прокси, иные варианты не всегда работают с разными провайдерами и книжными библиотеками).
Для использования создайте файл constants.py, с переменной PROXY вида PROXY = 'socks5://123.123.123.123:1234'
Файл espeak_converter.spec является конфигом для pyinstaller.

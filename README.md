# Микросервис с выводом графиков по землетрясениям

## Описание
Основной целью данного микросервиса является визуализация графиков по землетрясениям. Главными используемыми библиотеками являются **FastAPI** для создания программного интерфейса (API), **loguru** для осуществления логирования,**pytest** для автоматизации модульного тестирования, **conda** для создания виртуального окружения и управления зависимостями и **turkeq_eq** (https://github.com/EkaterinaKugot/Turkey_EQ_notebook.git) для расчетов данных по землетрясениям.

Данный микросервис запрашивает у пользователя файлы с данными о землетрясениях для их визуализации и параметры вывода графиков, такие как время, диапазон цветовой шкалы, приближённость карты (минимальная и максимальная широта и долгота), количество выводимых графиков за раз. У пользователя есть возможность создавать, удалять и изменять свой аккаунт. А также загружать один файл или zip-архив с файлами, удалять их и получать информацию об уже загруженных данных.

## Описание некоторых функций
### create_user
Данная функция **create_user** создает нового пользователя в базе данных и директорию для пользователя в файловой системе, если такого пользователя не существует.

Аргументы функции:

- user: UserIn - объект, содержащий информацию о пользователе (email и пароль), переданную в функцию.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращает объект нового пользователя, созданного в базе данных.

### update_user_email
Данная функция **update_user_email** обновляет электронную почту пользователя в базе данных.

Аргументы функции:

- new_email: EmailStr - новый адрес электронной почты, который нужно установить для пользователя.
- user: UserIn - объект, содержащий информацию о пользователе, переданную в функцию.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращает объект пользователя с измененным email.

### delete_user
Данная функция **delete_user** удаляет пользователя из базы данных и его директорию в файловой системе.

Аргументы функции:

- user: UserIn - объект, содержащий информацию о пользователе, переданную в функцию.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращается None, в случае успешного удаления.

### upload_file
Данная функция **upload_file** загружает файл или zip-архив на сервер, ассоциирует его с пользователем и сохраняет информацию в базе данных. В случае загрузки уже существующих файлов, заменяет их и изменяет данные в базе данных. 

Аргументы функции:

- emailIn: EmailStr - адрес электронной почты пользователя.
- passwordIn: str - пароль пользователя.
- startDate: datetime - начальная дата для файла.
- endDate: datetime - конечная дата для файла.
- type: str - тип данных файла.
- epc_date: datetime - дата эпицентра.
- epc_lat: float - широта эпицентра.
- epc_lon: float - долгота эпицентра.
- up_file: UploadFile - объект загружаемого файла.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращается список загруженных файлов.

### get_last_files и get_by_date
Данные функции **get_last_files** и **get_by_date** проводят выборку последнего загруженного файла и файла по дате из базы данных.

Аргументы функций:

- emailIn: EmailStr - адрес электронной почты пользователя.
- passwordIn: str - пароль пользователя.
- date: date -  дата, для которой требуется получить данные (только в **get_by_date**).
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращаются результаты запроса - данные, связанные с файлами пользователя.

### delete_file
Данная функция **delete_file** удаляет файл, связанный с определенной датой, из базы данных и директории пользователя.

Аргументы функции:

- user: UserIn - объект, содержащий информацию о пользователе, переданную в функцию.
- date: date - дата, для которой требуется удалить файл.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращается None, в случае успешного удаления.

### draw_map, draw_distance_time, draw_support_plot
Данные функции **draw_map**, **draw_distance_time**, **draw_support_plot** отвечают за генерацию графиков на основе заданных параметров, которые включают переданные файлы, ограничения цветовой шкалы, даты, ограничения широты и долготы, количество строк и столбцов на карте.

Аргументы функций:

- emailIn: EmailStr - адрес электронной почты пользователя.
- passwordIn: str - пароль пользователя.
- mapFiles: MapIn, distanceTime: DistanceTime, supportPlot: SupportPlot - объекты, содержащий информацию о файлах и параметрах графиков.
- db: Session = Depends(get_db) - сеанс базы данных, полученный с помощью зависимости get_db.

Возвращают пользователю архив с графиками.

Это весь основной функционал данного микросервиса.:sunglasses:

## Инструкция по установке
Для начала необходимо активировать своё виртуальное окружение (на примере Anaconda).
```bash
conda deactivate
conda create -n turkey_eq python=3.10
conda activate turkey_eq
```

Теперь установим cartopy и poetry.
```bash
conda install -c conda-forge cartopy
pip install poetry
```

Клонируем репозиторий и перейдем в папку с микросервисом.
```bash
git clone https://github.com/EkaterinaKugot/Turkey_EQ_practice.git
cd */Turkey_EQ_practice
```

Установим необходимые зависимости и библиотеку с расчетами.
```bash
poetry install
pip install turkey_eq-1.7-py3-none-any.whl
```
Библиотеку можно скачать [по ссылке](https://test.pypi.org/project/turkey-eq/).

Запустим микросервис.
```bash
uvicorn app.main:api --reload --port 8083
```

или..
```bash
python app/main.py
```

## Contributors
<a href="https://github.com/EkaterinaKugot/Turkey_EQ_practice/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=EkaterinaKugot/Turkey_EQ_practice" />
</a>

## Контактная информация
:wink:EkaterinaKugot - lika.kugot@gmail.com 

:relaxed:Yulya-S - yulya_shabsnova_03@mail.ru

## Лицензия
MIT
